# app/formatter/rows.py

import logging
import os
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import datetime as dt
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

from jinja2 import Environment, StrictUndefined

from app.utils.filecache import load_yaml_cached

LOGGER = logging.getLogger(__name__)

_FORMAT_DEBUG_ENABLED = os.getenv("FORMAT_DEBUG") == "1"

_ENTITY_ROOT = Path("data/entities")
_FORMATTING_POLICY_PATH = Path("data/policies/formatting.yaml")


def _setup_format_debug_file_logger() -> None:
    """
    Configura logging em arquivo para diagnóstico de formatação quando FORMAT_DEBUG=1.
    Não altera regras de detecção/formatadores; apenas garante observabilidade.
    """
    if not _FORMAT_DEBUG_ENABLED:
        return

    # Evita duplicar handlers em reload/import múltiplo
    for h in list(LOGGER.handlers):
        try:
            if isinstance(h, logging.FileHandler) and getattr(
                h, "baseFilename", ""
            ).endswith(("format_debug.log",)):
                return
        except Exception:
            continue

    log_path_primary = Path("/logs/format_debug.log")
    log_path_fallback = Path("/tmp/format_debug.log")

    log_path = log_path_primary
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        # Teste de escrita (abre/fecha) para garantir permissão
        with log_path.open("a", encoding="utf-8"):
            pass
    except Exception:
        log_path = log_path_fallback
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8"):
                pass
        except Exception:
            # Se nem /tmp funcionar, não há como garantir arquivo.
            # Mantemos o comportamento atual (silencioso), mas deixamos um aviso em stderr.
            try:
                sys.stderr.write(
                    "[format_debug] failed to init file logger (no writable path)\n"
                )
            except Exception:
                pass
            return

    handler = logging.FileHandler(str(log_path), encoding="utf-8")
    handler.setLevel(logging.INFO)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )

    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)
    LOGGER.propagate = False
    LOGGER.info("[format_debug] file logger initialized path=%s", str(log_path))


_setup_format_debug_file_logger()


def _entity_yaml_path(entity: str) -> Path:
    base_dir = _ENTITY_ROOT / entity
    new_path = base_dir / f"{entity}.yaml"
    legacy_path = base_dir / "entity.yaml"
    if new_path.exists():
        return new_path
    if legacy_path.exists():
        return legacy_path
    return new_path


def _load_formatting_policy() -> Dict[str, Any]:
    try:
        policy = load_yaml_cached(str(_FORMATTING_POLICY_PATH))
    except Exception as exc:  # pragma: no cover - hard to force in tests
        LOGGER.info("Falha ao carregar policy de formatação: %s", exc, exc_info=True)
        return {}
    return policy if isinstance(policy, dict) else {}


_FORMAT_POLICY = _load_formatting_policy()
_SEPARATORS = (
    _FORMAT_POLICY.get("separators") if isinstance(_FORMAT_POLICY, dict) else {}
)
_DECIMAL_SEPARATOR = (
    _SEPARATORS.get("decimal") if isinstance(_SEPARATORS, dict) else ","
) or ","
_THOUSANDS_SEPARATOR = (
    _SEPARATORS.get("thousands") if isinstance(_SEPARATORS, dict) else "."
) or "."

_CURRENCY_CFG = (
    _FORMAT_POLICY.get("currency") if isinstance(_FORMAT_POLICY, dict) else {}
)
_CURRENCY_SYMBOL = (
    _CURRENCY_CFG.get("symbol") if isinstance(_CURRENCY_CFG, dict) else "R$"
) or "R$"
_CURRENCY_SPACE = (
    bool(_CURRENCY_CFG.get("space")) if isinstance(_CURRENCY_CFG, dict) else True
)
_CURRENCY_PRECISION = (
    int(_CURRENCY_CFG.get("precision"))
    if isinstance(_CURRENCY_CFG, dict) and _CURRENCY_CFG.get("precision") is not None
    else 2
)

_PERCENT_CFG = _FORMAT_POLICY.get("percent") if isinstance(_FORMAT_POLICY, dict) else {}
_PERCENT_MULTIPLY_BY_100 = (
    bool(_PERCENT_CFG.get("multiply_by_100"))
    if isinstance(_PERCENT_CFG, dict)
    else True
)
_PERCENT_PRECISION = (
    int(_PERCENT_CFG.get("precision"))
    if isinstance(_PERCENT_CFG, dict) and _PERCENT_CFG.get("precision") is not None
    else 2
)

_NUMBER_CFG = _FORMAT_POLICY.get("number") if isinstance(_FORMAT_POLICY, dict) else {}
_NUMBER_PRECISION = (
    int(_NUMBER_CFG.get("precision"))
    if isinstance(_NUMBER_CFG, dict) and _NUMBER_CFG.get("precision") is not None
    else 2
)
_NUMBER_TRIM = (
    bool(_NUMBER_CFG.get("trim_trailing_zeros"))
    if isinstance(_NUMBER_CFG, dict)
    else True
)
_NUMBER_THOUSANDS = (
    bool(_NUMBER_CFG.get("thousands")) if isinstance(_NUMBER_CFG, dict) else True
)

_INT_CFG = _NUMBER_CFG if isinstance(_NUMBER_CFG, dict) else {}
_INT_THOUSANDS = bool(_INT_CFG.get("thousands")) if isinstance(_INT_CFG, dict) else True

_FILTERS_CFG = _FORMAT_POLICY.get("filters") if isinstance(_FORMAT_POLICY, dict) else {}

_PLACEHOLDERS = (
    _FORMAT_POLICY.get("placeholders") if isinstance(_FORMAT_POLICY, dict) else []
)

_FIELD_TO_FILTER: Dict[str, str] = {}
if isinstance(_PLACEHOLDERS, list):
    for ph in _PLACEHOLDERS:
        if not isinstance(ph, dict):
            continue
        field = ph.get("field")
        flt = ph.get("filter")
        if isinstance(field, str) and isinstance(flt, str):
            _FIELD_TO_FILTER[field.lower()] = flt

if _FORMAT_DEBUG_ENABLED:
    resolved_policy_path_obj = None
    resolved_policy_path_str = None
    try:
        resolved_policy_path_obj = _FORMATTING_POLICY_PATH.resolve()
        resolved_policy_path_str = str(resolved_policy_path_obj)
    except Exception as exc:  # pragma: no cover - debug logging only
        resolved_policy_path_str = f"{_FORMATTING_POLICY_PATH} (resolve error: {exc})"

    LOGGER.info("[format_debug] formatting policy path: %s", resolved_policy_path_str)
    # 2.1: checar existência no MESMO path resolvido (evita confusão por CWD/working_dir)
    exists_on_resolved = None
    try:
        if isinstance(resolved_policy_path_obj, Path):
            exists_on_resolved = resolved_policy_path_obj.exists()
    except Exception:  # pragma: no cover - debug logging only
        exists_on_resolved = None
    LOGGER.info(
        "[format_debug] formatting policy exists (resolved): %s", exists_on_resolved
    )
    LOGGER.info(
        "[format_debug] formatting policy exists (relative): %s",
        _FORMATTING_POLICY_PATH.exists(),
    )

    LOGGER.info(
        "[format_debug] formatting policy top-level keys: %s",
        list(_FORMAT_POLICY.keys()) if isinstance(_FORMAT_POLICY, dict) else [],
    )
    LOGGER.info(
        "[format_debug] formatting policy placeholders count: %s",
        len(_PLACEHOLDERS) if isinstance(_PLACEHOLDERS, list) else 0,
    )
    currency_filter_cfg = (
        _FILTERS_CFG.get("currency_br") if isinstance(_FILTERS_CFG, dict) else None
    )
    LOGGER.info(
        "[format_debug] filters.currency_br is currency: %s",
        bool(
            isinstance(currency_filter_cfg, dict)
            and currency_filter_cfg.get("type") == "currency"
        ),
    )
    LOGGER.info(
        "[format_debug] placeholder mapping benchmark_value: %s",
        _FIELD_TO_FILTER.get("benchmark_value"),
    )
    LOGGER.info(
        "[format_debug] placeholder mapping portfolio_amount: %s",
        _FIELD_TO_FILTER.get("portfolio_amount"),
    )

if isinstance(_FORMAT_POLICY, dict):
    _DATE_CFG = _FORMAT_POLICY.get("date_br") or _FORMAT_POLICY.get("date")
else:
    _DATE_CFG = None
_DATE_FORMAT = "%d/%m/%Y"
if isinstance(_DATE_CFG, dict):
    _DATE_FORMAT = _DATE_CFG.get("format") or _DATE_FORMAT

if isinstance(_FORMAT_POLICY, dict):
    _DATETIME_CFG = _FORMAT_POLICY.get("datetime_br") or _FORMAT_POLICY.get("datetime")
else:
    _DATETIME_CFG = None
_DATETIME_FORMAT = "%d/%m/%Y %H:%M"
if isinstance(_DATETIME_CFG, dict):
    _DATETIME_FORMAT = _DATETIME_CFG.get("format") or _DATETIME_FORMAT

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


def _format_decimal_br(
    value: Decimal,
    places: int,
    *,
    thousands: bool = True,
    trim_trailing_zeros: bool = False,
) -> str:
    quant = Decimal(1).scaleb(-places)
    quantized = value.quantize(quant, rounding=ROUND_HALF_UP) if places else value
    if thousands:
        formatted = f"{quantized:,.{places}f}"
    else:
        formatted = f"{quantized:.{places}f}"
    formatted = formatted.replace(",", "_")
    formatted = formatted.replace(".", _DECIMAL_SEPARATOR)
    formatted = formatted.replace("_", _THOUSANDS_SEPARATOR)
    if trim_trailing_zeros and _DECIMAL_SEPARATOR in formatted:
        formatted = formatted.rstrip("0").rstrip(_DECIMAL_SEPARATOR)
    return formatted


def _format_date(value: Any) -> Any:
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    return value


def _format_percentage(value: Any) -> Any:
    decimal_value = _to_decimal(value)
    if decimal_value is None:
        return value
    if _PERCENT_MULTIPLY_BY_100:
        decimal_value = decimal_value * Decimal(100)
    formatted = _format_decimal_br(
        decimal_value,
        _PERCENT_PRECISION,
        thousands=bool(_PERCENT_CFG.get("thousands", False)),
    )
    suffix = "%" if not bool(_PERCENT_CFG.get("space", False)) else " %"
    return f"{formatted}{suffix}"


def _format_percentage_no_mul(value: Any) -> Any:
    """
    Versão alternativa de percent que NÃO multiplica por 100.
    Útil para campos que já vêm na base em pontos percentuais.
    """
    decimal_value = _to_decimal(value)
    if decimal_value is None:
        return value

    formatted = _format_decimal_br(
        decimal_value,
        _PERCENT_PRECISION,
        thousands=bool(_PERCENT_CFG.get("thousands", False)),
    )
    suffix = "%" if not bool(_PERCENT_CFG.get("space", False)) else " %"
    return f"{formatted}{suffix}"


def _format_currency(value: Any) -> Any:
    decimal_value = _to_decimal(value)
    if decimal_value is None:
        return value
    formatted = _format_decimal_br(
        decimal_value.copy_abs(),
        _CURRENCY_PRECISION,
        thousands=bool(_CURRENCY_CFG.get("thousands", True)),
    )
    space = " " if _CURRENCY_SPACE else ""
    sign = "-" if decimal_value < 0 else ""
    return f"{sign}{_CURRENCY_SYMBOL}{space}{formatted}"


def _format_number(value: Any) -> Any:
    decimal_value = _to_decimal(value)
    if decimal_value is None:
        return value
    formatted = _format_decimal_br(
        decimal_value,
        _NUMBER_PRECISION,
        thousands=_NUMBER_THOUSANDS,
        trim_trailing_zeros=_NUMBER_TRIM,
    )
    return formatted


def _format_int(value: Any) -> Any:
    decimal_value = _to_decimal(value)
    if decimal_value is None:
        return value
    quantized = decimal_value.quantize(Decimal(1), rounding=ROUND_HALF_UP)
    formatted = f"{quantized:,}" if _INT_THOUSANDS else f"{quantized}"
    formatted = formatted.replace(",", _THOUSANDS_SEPARATOR)
    return formatted


def _try_parse_date(value: str) -> Optional[dt.datetime]:
    try:
        return dt.datetime.fromisoformat(value)
    except Exception:
        return None


def _format_date_br(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.strftime(_DATE_FORMAT)
    if isinstance(value, dt.date):
        return value.strftime(_DATE_FORMAT)
    if isinstance(value, str):
        parsed = _try_parse_date(value)
        if parsed:
            return parsed.strftime(_DATE_FORMAT)
    return value


def _format_datetime_br(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.strftime(_DATETIME_FORMAT)
    if isinstance(value, dt.date):
        return dt.datetime.combine(value, dt.time.min).strftime(_DATETIME_FORMAT)
    if isinstance(value, str):
        parsed = _try_parse_date(value)
        if parsed:
            return parsed.strftime(_DATETIME_FORMAT)
    return value


def _mask_cnpj(value: Any) -> Any:
    if value is None:
        return value
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if len(digits) != 14:
        return value
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


def _get_filter_formatter(filter_name: str) -> Optional[Callable[[Any], Any]]:
    """
    Dado o nome de um filtro declarado em data/policies/formatting.yaml,
    devolve a função de formatação apropriada.
    """
    cfg = _FILTERS_CFG.get(filter_name) if isinstance(_FILTERS_CFG, dict) else None
    if not isinstance(cfg, dict):
        return None

    ftype = cfg.get("type")

    if ftype == "currency":
        return _format_currency

    if ftype == "percent":
        # Prioriza override no filtro; se não houver, usa default global
        multiply = cfg.get("multiply_by_100")
        if multiply is None:
            multiply = _PERCENT_MULTIPLY_BY_100
        return _format_percentage if multiply else _format_percentage_no_mul

    if ftype == "number":
        return _format_number

    if ftype == "integer":
        return _format_int

    if ftype == "date":
        return _format_date_br

    if ftype == "datetime":
        return _format_datetime_br

    if ftype == "mask":
        # Hoje só temos CNPJ; se surgirem outros, expandimos aqui.
        pattern = cfg.get("pattern")
        if pattern == "##.###.###/####-##":
            return _mask_cnpj

    return None


def _register_jinja_filters() -> None:
    filters_map: Dict[str, Callable[[Any], Any]] = {}

    # Registra filtros declarados em data/policies/formatting.yaml
    if isinstance(_FILTERS_CFG, dict):
        for name, cfg in _FILTERS_CFG.items():
            if not isinstance(name, str):
                continue
            fmt = _get_filter_formatter(name)
            if fmt:
                filters_map[name] = fmt

    # Garantia de retrocompatibilidade mínima se algo não vier do YAML
    filters_map.setdefault("currency_br", _format_currency)
    filters_map.setdefault("percent_br", _format_percentage)
    filters_map.setdefault("percent_raw_br", _format_percentage_no_mul)
    filters_map.setdefault("number_br", _format_number)
    filters_map.setdefault("int_br", _format_int)
    filters_map.setdefault("date_br", _format_date_br)
    filters_map.setdefault("datetime_br", _format_datetime_br)
    filters_map.setdefault("cnpj_mask", _mask_cnpj)

    _JINJA_ENV.filters.update(filters_map)


_register_jinja_filters()


def _detect_formatter(column_name: str) -> Optional[Callable[[Any], Any]]:
    lowered = (column_name or "").lower()

    if _FORMAT_DEBUG_ENABLED and lowered in {"benchmark_value", "portfolio_amount"}:
        # 2.2: diagnóstico do caminho real usado pela detecção
        placeholder_filter = _FIELD_TO_FILTER.get(lowered)
        cfg = None
        ftype = None
        try:
            cfg = (
                _FILTERS_CFG.get(placeholder_filter)
                if isinstance(_FILTERS_CFG, dict)
                else None
            )
            ftype = cfg.get("type") if isinstance(cfg, dict) else None
        except Exception:
            cfg = None
            ftype = None
        LOGGER.info(
            "[format_debug] detect_formatter enter col=%s lowered=%s placeholder_filter=%s filter_cfg_type=%s filter_type=%s",
            column_name,
            lowered,
            placeholder_filter,
            type(cfg).__name__ if cfg is not None else "None",
            ftype,
        )

    # 1) Preferência: mapping declarativo em data/policies/formatting.yaml (placeholders)
    filter_name = _FIELD_TO_FILTER.get(lowered)
    if filter_name:
        fmt = _get_filter_formatter(filter_name)
        if fmt:
            if _FORMAT_DEBUG_ENABLED and lowered in {
                "benchmark_value",
                "portfolio_amount",
            }:
                LOGGER.info(
                    "[format_debug] detect_formatter via placeholders col=%s filter_name=%s fmt=%s",
                    column_name,
                    filter_name,
                    getattr(fmt, "__name__", "<callable>"),
                )
            return fmt

    # 2) Fallback legado por sufixo (para campos ainda não mapeados em placeholders)
    if lowered.endswith("_at") or lowered.endswith("_date"):
        if _FORMAT_DEBUG_ENABLED and lowered in {"benchmark_value", "portfolio_amount"}:
            LOGGER.info(
                "[format_debug] detect_formatter via suffix col=%s matched=date",
                column_name,
            )
        return _format_date
    if lowered.endswith("_pct") or lowered.endswith("_ratio"):
        if _FORMAT_DEBUG_ENABLED and lowered in {"benchmark_value", "portfolio_amount"}:
            LOGGER.info(
                "[format_debug] detect_formatter via suffix col=%s matched=percent",
                column_name,
            )
        return _format_percentage
    if lowered.endswith("_amt"):
        if _FORMAT_DEBUG_ENABLED and lowered in {"benchmark_value", "portfolio_amount"}:
            LOGGER.info(
                "[format_debug] detect_formatter via suffix col=%s matched=currency",
                column_name,
            )
        return _format_currency

    if _FORMAT_DEBUG_ENABLED and lowered in {"benchmark_value", "portfolio_amount"}:
        LOGGER.info(
            "[format_debug] detect_formatter exit col=%s formatter_found=%s",
            column_name,
            False,
        )
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


def _extract_ticker(
    identifiers: Optional[Dict[str, Any]], rows: List[Dict[str, Any]]
) -> str:
    if isinstance(identifiers, dict):
        ticker = identifiers.get("ticker") or identifiers.get("symbol")
        if ticker:
            return str(ticker)
    for row in rows:
        if isinstance(row, dict):
            ticker = row.get("ticker") or row.get("symbol")
            if ticker:
                return str(ticker)
    return ""


def get_entity_presentation_kind(entity: str) -> Optional[str]:
    """Retorna presentation.kind do entity.yaml, se disponível."""

    cfg_path = _entity_yaml_path(entity)
    try:
        cfg = load_yaml_cached(str(cfg_path))
    except Exception:
        return None

    if not isinstance(cfg, dict):
        return None

    presentation = cfg.get("presentation") if isinstance(cfg, dict) else None
    if not isinstance(presentation, dict):
        return None

    kind = presentation.get("kind") if isinstance(presentation, dict) else None
    if isinstance(kind, str) and kind.strip():
        return kind.strip()
    return None


def render_rows_template(
    entity: str,
    rows: List[Dict[str, Any]],
    *,
    identifiers: Optional[Dict[str, Any]] = None,
    aggregates: Optional[Dict[str, Any]] = None,
) -> str:
    """Renderiza a resposta declarativa via templates de entidade."""
    rows_list = list(rows or [])
    identifiers_safe = identifiers if isinstance(identifiers, dict) else {}

    # 1) Carrega entity.yaml
    cfg_path = _entity_yaml_path(entity)
    try:
        cfg = load_yaml_cached(str(cfg_path))
    except Exception as exc:
        return ""

    if not isinstance(cfg, dict):
        return ""

    # 2) presentation.kind
    presentation = cfg.get("presentation") or {}
    kind = presentation.get("kind") if isinstance(presentation, dict) else None
    if not isinstance(kind, str) or not kind.strip():
        return ""
    kind = kind.strip()

    template_path = _ENTITY_ROOT / entity / "responses" / f"{kind}.md.j2"

    # 3) Caminho do template
    try:
        template_path_resolved = template_path.resolve(strict=False)
    except Exception as exc:
        return ""

    if not str(template_path_resolved).startswith(str(_ENTITY_ROOT.resolve())):
        return ""

    if not template_path_resolved.exists():
        return ""

    fields_cfg = presentation.get("fields") if isinstance(presentation, dict) else {}
    key_field = fields_cfg.get("key") if isinstance(fields_cfg, dict) else None
    value_field = fields_cfg.get("value") if isinstance(fields_cfg, dict) else None
    if kind == "list" and (not key_field or not value_field):
        return ""

    context = {
        "rows": rows_list,
        "fields": {"key": key_field, "value": value_field},
        "empty_message": presentation.get("empty_message"),
        "identifiers": identifiers_safe or {},
        "aggregates": aggregates if isinstance(aggregates, dict) else {},
        "ticker": _extract_ticker(identifiers_safe, rows_list),
    }

    try:
        template = _JINJA_ENV.from_string(
            template_path_resolved.read_text(encoding="utf-8")
        )
        rendered = template.render(**context)
    except Exception as exc:
        return ""

    return (rendered or "").strip()


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
            if _FORMAT_DEBUG_ENABLED and col_name in {
                "benchmark_value",
                "portfolio_amount",
            }:
                placeholder_filter = _FIELD_TO_FILTER.get(col_name.lower())
                LOGGER.info(
                    "[format_debug] before format col=%s value=%r type=%s placeholder_filter=%s formatter_found=%s",
                    col_name,
                    col_value,
                    type(col_value).__name__,
                    placeholder_filter,
                    bool(formatter),
                )
            if formatter:
                item[col_name] = formatter(col_value)
                if _FORMAT_DEBUG_ENABLED and col_name in {
                    "benchmark_value",
                    "portfolio_amount",
                }:
                    LOGGER.info(
                        "[format_debug] after format col=%s value=%r",
                        col_name,
                        item[col_name],
                    )
        out.append(item)
    return out
