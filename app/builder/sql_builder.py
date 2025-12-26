# app/builder/sql_builder.py

"""SQL builder guided exclusively by entity YAML configuration."""

from pathlib import Path
import datetime as dt
import logging
from typing import Dict, Tuple, List, Any, Optional, Sequence

from app.utils.filecache import load_yaml_cached

logger = logging.getLogger(__name__)

ENTITIES_DIR = Path("data/entities")
_METRIC_PLACEHOLDERS = {
    "{{ticker}}": "%(ticker)s",
    "{{period_start}}": "%(period_start)s",
    "{{period_end}}": "%(period_end)s",
    "{{window_months}}": "%(window_months)s",
    "{{window_kind}}": "%(window_kind)s",
    "{{window_value}}": "%(window_value)s",
}
_METRIC_COLUMN_TYPES = {
    "ticker": "text",
    "metric": "text",
    "value": "numeric",
    "window_months": "int",
    "period_start": "date",
    "period_end": "date",
}


def _entity_yaml_path(entity: str) -> Path:
    base_dir = ENTITIES_DIR / entity
    new_path = base_dir / f"{entity}.yaml"
    legacy_path = base_dir / "entity.yaml"
    if new_path.exists():
        return new_path
    if legacy_path.exists():
        return legacy_path
    return new_path


def _load_entity_yaml(entity: str) -> dict:
    ypath = _entity_yaml_path(entity)
    data = load_yaml_cached(str(ypass := ypath))
    if not isinstance(data, dict) or not data:
        message = f"Entity YAML not found or empty for '{entity}' at {ypass}"
        logger.error(message)
        raise ValueError(message)
    return data


def _require_dict(config: dict, path: Sequence[str], entity: str) -> dict:
    current: Any = config
    for key in path:
        if not isinstance(current, dict) or key not in current:
            joined = ".".join(path)
            message = f"Missing key '{joined}' for entity '{entity}'"
            logger.error(message)
            raise ValueError(message)
        current = current[key]
    if not isinstance(current, dict):
        joined = ".".join(path)
        message = f"Expected dict at '{joined}' for entity '{entity}'"
        logger.error(message)
        raise ValueError(message)
    return current


def _require_list(config: dict, path: Sequence[str], entity: str) -> List[Any]:
    parent = _require_dict(config, path[:-1], entity) if len(path) > 1 else config
    key = path[-1]
    value = parent.get(key)
    if not isinstance(value, list) or not value:
        joined = ".".join(path)
        message = f"Expected non-empty list at '{joined}' for entity '{entity}'"
        logger.error(message)
        raise ValueError(message)
    return list(value)


def _require_str(config: dict, path: Sequence[str], entity: str) -> str:
    parent = _require_dict(config, path[:-1], entity) if len(path) > 1 else config
    key = path[-1]
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        joined = ".".join(path)
        message = f"Expected non-empty string at '{joined}' for entity '{entity}'"
        logger.error(message)
        raise ValueError(message)
    return value.strip()


def _column_names(config: dict, entity: str) -> List[str]:
    columns_cfg = _require_list(config, ["columns"], entity)
    column_names: List[str] = []
    for idx, entry in enumerate(columns_cfg):
        name: Optional[str]
        if isinstance(entry, dict):
            raw = entry.get("name")
            name = str(raw).strip() if isinstance(raw, str) else None
        elif isinstance(entry, str):
            name = entry.strip()
        else:
            name = None
        if not name:
            message = f"Column index {idx} missing name for entity '{entity}'"
            logger.error(message)
            raise ValueError(message)
        column_names.append(name)
    return column_names


def _normalize_period_value(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    return value


def _parse_window(window: Optional[str]) -> Tuple[Optional[str], Optional[int]]:
    if not window:
        return None, None
    try:
        kind, raw = str(window).split(":", 1)
    except ValueError:
        return None, None
    try:
        value = int(raw)
    except ValueError:
        value = None
    return kind, value


def _normalize_limit(limit: Any) -> Optional[int]:
    if limit is None:
        return None
    try:
        value = int(limit)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _infer_sql_type_from_name(column: str) -> Optional[str]:
    lower = (column or "").lower()
    if lower.endswith("_at"):
        return "timestamp"
    if lower.endswith("_date"):
        return "date"
    if lower.endswith("_amt") or lower.endswith("_price"):
        return "numeric"
    if lower.endswith("_pct") or lower.endswith("_ratio"):
        return "numeric"
    return None


def _null_expression(column: str) -> str:
    inferred = _infer_sql_type_from_name(column)
    return f"NULL::{inferred}" if inferred else "NULL"


def _literal_expression(column: str) -> str:
    inferred = _infer_sql_type_from_name(column)
    cast = f"::{inferred}" if inferred else ""
    return f"%({column})s{cast}"


def _select_order_value(
    requested: Any,
    preferred_direction: Optional[str],
    whitelist: List[str],
    default_column: Optional[str] = None,
) -> Optional[str]:
    if not whitelist:
        return None
    normalized = {entry.lower(): entry for entry in whitelist}
    if requested:
        key = str(requested).strip().lower()
        if key in normalized:
            return normalized[key]
    if default_column:
        for entry in whitelist:
            parts = entry.strip().split()
            if len(parts) == 2 and parts[0] == default_column:
                if not preferred_direction or parts[1].lower() == preferred_direction:
                    return entry
        for entry in whitelist:
            parts = entry.strip().split()
            if len(parts) == 2 and parts[0] == default_column:
                return entry
    if preferred_direction:
        direction = preferred_direction.lower()
        for entry in whitelist:
            parts = entry.strip().split()
            if len(parts) == 2 and parts[1].lower() == direction:
                return entry
    return whitelist[0]


def _months_from_window(window: Optional[str], default: int = 12) -> int:
    if not window:
        return default
    try:
        kind, raw = str(window).split(":", 1)
    except ValueError:
        return default
    if kind != "months":
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def _build_metrics_sql(
    metrics_cfg: List[Dict[str, Any]],
    identifiers: Dict[str, Any],
    agg_params: Dict[str, Any],
    result_key: str,
    return_cols: List[str],
) -> Tuple[str, Dict[str, Any], str, List[str]]:
    requested = agg_params.get("metric")
    selected_metrics: List[Dict[str, Any]]
    if requested:
        selected_metrics = [m for m in metrics_cfg if m.get("name") == requested]
        if not selected_metrics:
            selected_metrics = metrics_cfg
    else:
        selected_metrics = metrics_cfg

    ticker = identifiers.get("ticker") if identifiers else None
    if isinstance(ticker, str):
        ticker = ticker.upper()

    window_months = agg_params.get("window_months")
    try:
        window_months = int(window_months)
    except Exception:
        window_months = None

    window_raw = agg_params.get("window")
    window_kind: Optional[str] = None
    window_value: Optional[int] = None
    if isinstance(window_raw, str):
        try:
            window_kind, raw_value = window_raw.split(":", 1)
            window_value = int(raw_value)
        except Exception:
            window_kind = None
            window_value = None

    if window_kind == "months":
        if not window_months:
            window_months = window_value or _months_from_window(window_raw)
        if window_value is None:
            window_value = window_months
    elif window_kind == "count":
        if window_value is None and window_months:
            window_value = window_months
        if window_months:
            try:
                window_months = int(window_months)
            except Exception:
                window_months = None
    else:
        window_kind = "months"
        if not window_months:
            window_months = _months_from_window(window_raw)
        window_value = window_months

    period_start = agg_params.get("period_start")
    if isinstance(period_start, dt.date):
        period_start = period_start.isoformat()
    period_end = agg_params.get("period_end")
    if isinstance(period_end, dt.date):
        period_end = period_end.isoformat()
    today_iso = dt.date.today().isoformat()
    if not period_end:
        period_end = today_iso
    if not period_start:
        period_start = today_iso

    params: Dict[str, Any] = {
        "ticker": ticker,
        "window_months": window_months,
        "period_start": period_start,
        "period_end": period_end,
        "window_kind": window_kind,
        "window_value": window_value,
    }

    sql_parts: List[str] = []
    for metric in selected_metrics:
        raw_sql = (metric.get("sql") or "").strip()
        if not raw_sql:
            continue
        rendered = raw_sql
        for placeholder, repl in _METRIC_PLACEHOLDERS.items():
            rendered = rendered.replace(placeholder, repl)
        rendered = rendered.rstrip(";\n ")
        sql_parts.append(f"({rendered})")

    if not sql_parts:
        casts = []
        for col in return_cols:
            ctype = _METRIC_COLUMN_TYPES.get(col, "text")
            casts.append(f"NULL::{ctype} AS {col}")
        empty_cols = ", ".join(casts)
        sql = f"SELECT {empty_cols} WHERE 1=0"
    else:
        sql = " UNION ALL ".join(sql_parts)

    return sql, params, result_key, return_cols


def _build_numeric_aggregation_sql(
    *,
    entity: str,
    function: str,
    return_cols: List[str],
    view_name: str,
    where_sql: str,
    order_clause: str,
    window_kind: Optional[str],
    window_value: Optional[int],
    params: Dict[str, Any],
) -> str:
    if len(return_cols) < 3:
        message = "Entity '{entity}' requires at least 3 columns for aggregation"
        logger.error(message)
        raise ValueError(message)

    value_index = 2
    value_column = return_cols[value_index]
    select_parts: List[str] = []
    group_by: List[str] = []

    first_column = return_cols[0]
    if first_column in params:
        select_parts.append(f"{_literal_expression(first_column)} AS {first_column}")
    else:
        select_parts.append(f"{first_column} AS {first_column}")
        group_by.append(first_column)

    for idx, column in enumerate(return_cols[1:], start=1):
        if idx == value_index:
            select_parts.append(f"{function}({value_column}) AS {column}")
        else:
            select_parts.append(f"{_null_expression(column)} AS {column}")

    count_limit = (
        window_value
        if window_kind == "count" and isinstance(window_value, int) and window_value > 0
        else None
    )

    if count_limit:
        order_segment = order_clause if order_clause else ""
        subquery = (
            f"(SELECT {', '.join(return_cols)} FROM {view_name}{where_sql}"
            f"{order_segment} LIMIT {count_limit}) windowed"
        )
        from_sql = f" FROM {subquery}"
        literal_group = first_column in params
    else:
        from_sql = f" FROM {view_name}{where_sql}"
        literal_group = False

    sql = "SELECT " + ", ".join(select_parts) + from_sql
    if not literal_group and group_by:
        sql += " GROUP BY " + ", ".join(group_by)
    return sql


def build_select_for_entity(
    entity: str,
    identifiers: Dict[str, Any],
    agg_params: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Dict[str, Any], str, List[str]]:
    """
    Constrói SELECT baseado no YAML da entidade.
    - view real = sql_view declarado no contrato.
    - return_columns = colunas derivadas de columns[].
    - WHERE opcional por identificadores (p.ex., ticker).
    - Suporte a compute-on-read (aggregations.* no YAML + infer_params).
    """
    cfg = _load_entity_yaml(entity)
    result_key = _require_str(cfg, ["result_key"], entity)
    return_cols = _column_names(cfg, entity)

    view_name = _require_str(cfg, ["sql_view"], entity)
    params: Dict[str, Any] = {}
    where_terms: List[str] = []

    # Normaliza parâmetros de agregação declarativos (pode conter ticker, janela, etc.)
    agg_params = agg_params if isinstance(agg_params, dict) else {}

    identifiers = identifiers or {}
    identifier_specs = cfg.get("identifiers") or []
    identifier_names = [
        spec.get("name")
        for spec in identifier_specs
        if isinstance(spec, dict) and spec.get("name")
    ]
    options_cfg = cfg.get("options") or {}
    supports_multi_ticker = bool(options_cfg.get("supports_multi_ticker"))
    multi_ticker_values: List[str] = []
    if supports_multi_ticker:
        raw_multi = identifiers.get("tickers")
        if isinstance(raw_multi, (list, tuple, set)):
            for value in raw_multi:
                if not isinstance(value, str):
                    continue
                normalized = value.strip().upper()
                if not normalized:
                    continue
                if normalized in multi_ticker_values:
                    continue
                multi_ticker_values.append(normalized)

    for name in identifier_names:
        # 1) Primeiro tenta o identificador canônico extraído do texto
        value = identifiers.get(name)

        # 2) Se vier vazio, tenta resolver via parâmetros inferidos
        #    (ex.: ticker herdado do contexto em agg_params).
        if (value is None or value == "") and name in agg_params:
            alt = agg_params.get(name)
            if not (
                alt is None
                or alt == ""
                or (isinstance(alt, (list, tuple, set)) and not alt)
            ):
                value = alt

        if name == "ticker" and multi_ticker_values:
            if len(multi_ticker_values) == 1:
                params[name] = multi_ticker_values[0]
                where_terms.append(f"{name} = %({name})s")
            else:
                params["tickers"] = list(multi_ticker_values)
                where_terms.append(f"{name} = ANY(%(tickers)s)")
            continue
        if value is None or value == "":
            continue
        if name == "ticker" and isinstance(value, str):
            value = value.upper()
        params[name] = value
        where_terms.append(f"{name} = %({name})s")

    is_metrics_request = (agg_params.get("agg") or "").lower() == "metrics"
    period_start = _normalize_period_value(agg_params.get("period_start"))
    period_end = _normalize_period_value(agg_params.get("period_end"))
    default_date_field = cfg.get("default_date_field") or None

    if (period_start or period_end) and not is_metrics_request:
        if not default_date_field:
            message = (
                "Entity '{entity}' missing default_date_field for period filtering"
            )
            logger.error(message)
            raise ValueError(message)
        if not period_start or not period_end:
            message = "Entity '{entity}' requires both period_start and period_end for filtering"
            logger.error(message)
            raise ValueError(message)
        params["period_start"] = period_start
        params["period_end"] = period_end
        where_terms.append(
            f"{default_date_field} BETWEEN %(period_start)s AND %(period_end)s"
        )

    agg_cfg = cfg.get("aggregations") or {}
    agg_enabled = bool(agg_cfg.get("enabled", False))
    agg_defaults = agg_cfg.get("defaults") or {}
    list_defaults = agg_defaults.get("list") or {}
    default_limit = _normalize_limit(list_defaults.get("limit"))
    default_order_dir_raw = list_defaults.get("order")
    default_order_dir = (
        default_order_dir_raw.strip().lower()
        if isinstance(default_order_dir_raw, str) and default_order_dir_raw.strip()
        else None
    )

    order_by_whitelist = [
        str(entry).strip()
        for entry in (cfg.get("order_by_whitelist") or [])
        if str(entry).strip()
    ]

    metrics_cfg = cfg.get("metrics") or []
    if metrics_cfg and is_metrics_request:
        return _build_metrics_sql(
            metrics_cfg,
            identifiers or {},
            agg_params,
            result_key,
            return_cols,
        )

    agg_mode = (agg_params.get("agg") or "").lower()
    window = agg_params.get("window")
    requested_limit = _normalize_limit(agg_params.get("limit"))

    preferred_order_dir: Optional[str] = None
    order_param = agg_params.get("order")
    if isinstance(order_param, str) and order_param.strip():
        preferred_order_dir = order_param.strip().lower()
    elif default_order_dir:
        preferred_order_dir = default_order_dir

    is_latest_requested = agg_mode == "latest"
    if is_latest_requested:
        agg_mode = "list"
        window = window or "count:1"
        requested_limit = 1
        preferred_order_dir = "desc"

    limit_value = requested_limit if requested_limit is not None else default_limit
    window_kind, window_value = _parse_window(window)

    where_with_window = list(where_terms)
    if window_kind == "months" and window_value:
        if not default_date_field:
            message = (
                "Entity '{entity}' missing default_date_field for window filtering"
            )
            logger.error(message)
            raise ValueError(message)
        where_with_window.append(
            f"({default_date_field})::timestamp >= (CURRENT_DATE - INTERVAL '{window_value} months')"
        )

    order_value = _select_order_value(
        agg_params.get("order_by"),
        preferred_order_dir,
        order_by_whitelist,
        default_date_field,
    )
    order_clause = f" ORDER BY {order_value}" if order_value else ""

    where_sql = f" WHERE {' AND '.join(where_with_window)}" if where_with_window else ""

    if not agg_enabled or agg_mode in ("", None):
        agg_mode = "list"

    is_count_one_window = window_kind == "count" and window_value == 1
    latest_per_ticker = (
        supports_multi_ticker and len(multi_ticker_values) > 1 and (is_latest_requested or is_count_one_window)
    )

    if agg_mode == "list":
        if latest_per_ticker:
            window_order_by = (
                order_value
                or (f"{default_date_field} DESC" if default_date_field else None)
                or return_cols[0]
            )
            base_select = ", ".join(return_cols)
            sql = (
                f"SELECT {', '.join(f't.{col}' for col in return_cols)} "
                f"FROM (SELECT {base_select}, ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY {window_order_by}) AS rn "
                f"FROM {view_name}{where_sql}) t "
                "WHERE t.rn = 1 "
                "ORDER BY t.ticker"
            )
            return sql, params, result_key, return_cols

        limit_clause = f" LIMIT {limit_value}" if limit_value else ""
        sql = (
            f"SELECT {', '.join(return_cols)} FROM {view_name}{where_sql}"
            f"{order_clause}{limit_clause}"
        )
        return sql, params, result_key, return_cols

    if agg_mode in ("avg", "sum"):
        function = "AVG" if agg_mode == "avg" else "SUM"
        order_for_window = order_clause if window_kind == "count" else ""
        sql = _build_numeric_aggregation_sql(
            entity=entity,
            function=function,
            return_cols=return_cols,
            view_name=view_name,
            where_sql=where_sql,
            order_clause=order_for_window,
            window_kind=window_kind,
            window_value=window_value,
            params=params,
        )
        return sql, params, result_key, return_cols

    limit_clause = f" LIMIT {limit_value}" if limit_value else ""
    sql = (
        f"SELECT {', '.join(return_cols)} FROM {view_name}{where_sql}"
        f"{order_clause}{limit_clause}"
    )
    return sql, params, result_key, return_cols


__all__ = ["build_select_for_entity"]
