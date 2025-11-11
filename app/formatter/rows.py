# app/formatter/rows.py

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import datetime as dt
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

from jinja2 import Environment, StrictUndefined

from app.utils.filecache import load_yaml_cached

_ENTITY_ROOT = Path("data/entities")
_JINJA_ENV = Environment(
    autoescape=False,
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        try:
            return Decimal(value)
        except InvalidOperation:
            return None
    return None


def _format_decimal_br(value: Decimal, places: int) -> str:
    quant = Decimal(1).scaleb(-places)
    quantized = value.quantize(quant, rounding=ROUND_HALF_UP) if places else value
    formatted = f"{quantized:,.{places}f}" if places else f"{quantized:,}"
    return formatted.replace(",", "_").replace(".", ",").replace("_", ".")


def _format_date(value: Any) -> Any:
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    return value


def _format_percentage(value: Any) -> Any:
    decimal_value = _to_decimal(value)
    if decimal_value is None:
        return value
    if decimal_value.copy_abs() <= Decimal("1"):
        decimal_value = decimal_value * Decimal(100)
    return f"{_format_decimal_br(decimal_value, 2)}%"


def _format_currency(value: Any) -> Any:
    decimal_value = _to_decimal(value)
    if decimal_value is None:
        return value
    return f"R$ {_format_decimal_br(decimal_value, 2)}"


def _detect_formatter(column_name: str) -> Optional[Callable[[Any], Any]]:
    lowered = (column_name or "").lower()
    # TODO: tornar declarativo em data/ontology quando existir mapa dedicado.
    if lowered.endswith("_at") or lowered.endswith("_date"):
        return _format_date
    if lowered.endswith("_pct") or lowered.endswith("_ratio"):
        return _format_percentage
    if lowered.endswith("_amt"):
        return _format_currency
    return None


def format_metric_value(metric_key: str, value: Any) -> Any:

    if value is None:
        return value

    metric = (metric_key or "").strip()
    decimal_value = _to_decimal(value)

    if decimal_value is None:
        return value

    if metric in {"dividends_sum", "price_avg"}:
        return f"R$ {_format_decimal_br(decimal_value, 2)}"

    if metric == "dividends_count":
        integer_value = decimal_value.to_integral_value(rounding=ROUND_HALF_UP)
        return f"{integer_value}"

    if metric == "dy_avg":
        return f"{_format_decimal_br(decimal_value, 2)}%"

    return value


def render_rows_template(entity: str, rows: List[Dict[str, Any]]) -> str:
    """Renderiza a resposta declarativa via templates de entidade."""

    try:
        cfg = load_yaml_cached(str((_ENTITY_ROOT / entity / "entity.yaml")))
    except Exception:
        cfg = None
    if not isinstance(cfg, dict):
        return ""

    presentation = cfg.get("presentation") or {}
    kind = presentation.get("kind") if isinstance(presentation, dict) else None
    if not isinstance(kind, str) or not kind.strip():
        return ""
    template_path = _ENTITY_ROOT / entity / "responses" / f"{kind}.md.j2"

    # Normalize and ensure template_path is within _ENTITY_ROOT
    try:
        template_path_resolved = template_path.resolve(strict=False)
    except Exception:
        return ""
    if not str(template_path_resolved).startswith(str(_ENTITY_ROOT.resolve())):
        # Outside allowed root directory
        return ""
    if not template_path_resolved.exists():
        return ""

    fields = presentation.get("fields") if isinstance(presentation, dict) else {}
    key_field = fields.get("key") if isinstance(fields, dict) else None
    value_field = fields.get("value") if isinstance(fields, dict) else None
    if not key_field or not value_field:
        return ""

    context = {
        "rows": list(rows or []),
        "fields": {"key": key_field, "value": value_field},
        "empty_message": presentation.get("empty_message"),
    }
    try:
        template = _JINJA_ENV.from_string(
            template_path_resolved.read_text(encoding="utf-8")
        )
        rendered = template.render(**context)
    except Exception:
        return ""
    return rendered.strip()


def format_rows(rows: List[Dict[str, Any]], columns: List[str]) -> List[Dict[str, Any]]:
    """
    Formatação mínima: mantém apenas as colunas pedidas e preserva tipos simples.
    (Datas/decimais podem ser normalizados aqui quando necessário.)
    """
    out: List[Dict[str, Any]] = []
    for r in rows:
        item = {c: r.get(c) for c in columns}
        meta = r.get("meta") if isinstance(r, dict) else None
        metric_key = meta.get("metric_key") if isinstance(meta, dict) else None
        if metric_key and "value" in item:
            item["value"] = format_metric_value(metric_key, item.get("value"))
        for col_name, col_value in list(item.items()):
            if col_value is None:
                continue
            formatter = _detect_formatter(col_name)
            if formatter:
                item[col_name] = formatter(col_value)
        out.append(item)
    return out
