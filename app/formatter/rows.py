# app/formatter/rows.py

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import datetime as dt
from typing import List, Dict, Any, Optional


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


DATE_COLUMNS = {"published_at", "initiation_date", "updated_at", "created_at"}
PERCENT_COLUMNS = {"vacancy_ratio", "non_compliant_ratio", "loss_risk_pct"}
CURRENCY_COLUMNS = {"cause_amt"}


def _format_date(value: Any) -> Any:
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    return value


def _format_percentage(value: Any) -> Any:
    decimal_value = _to_decimal(value)
    if decimal_value is None:
        return value
    if decimal_value.copy_abs() <= Decimal('1'):
        decimal_value = decimal_value * Decimal(100)
    return f"{_format_decimal_br(decimal_value, 2)}%"


def _format_currency(value: Any) -> Any:
    decimal_value = _to_decimal(value)
    if decimal_value is None:
        return value
    return f"R$ {_format_decimal_br(decimal_value, 2)}"

def format_metric_value(metric_key: str, value: Any) -> Any:
    """Formata valores de métricas fiis_metrics conforme a regra declarada."""

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
            if col_name in DATE_COLUMNS and col_value is not None:
                item[col_name] = _format_date(col_value)
            elif col_name in PERCENT_COLUMNS and col_value is not None:
                item[col_name] = _format_percentage(col_value)
            elif col_name in CURRENCY_COLUMNS and col_value is not None:
                item[col_name] = _format_currency(col_value)
        out.append(item)
    return out
