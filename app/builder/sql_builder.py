# app/builder/sql_builder.py

from pathlib import Path
import datetime as dt
from typing import Dict, Tuple, List, Any, Optional

from app.utils.filecache import load_yaml_cached

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


def _load_entity_yaml(entity: str) -> dict:
    ypath = ENTITIES_DIR / f"{entity}.yaml"
    return load_yaml_cached(str(ypass := ypath)) or {}


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
        # Count não usa window_months como cardinalidade obrigatória
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


def build_select_for_entity(
    entity: str,
    identifiers: Dict[str, Any],
    agg_params: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Dict[str, Any], str, List[str]]:
    """
    Constrói SELECT baseado no YAML da entidade.
    - view real = nome da entidade (contrato Araquem).
    - return_columns = colunas que vão para a resposta.
    - WHERE opcional por identificadores (p.ex., ticker).
    - Suporte a compute-on-read (aggregations.* no YAML + infer_params).
    """
    cfg = _load_entity_yaml(entity)
    result_key: str = cfg["presentation"]["result_key"]
    return_cols: List[str] = cfg["presentation"]["return_columns"]

    view_name = entity  # entidade lógica == view real
    where = []
    params: Dict[str, Any] = {}

    if identifiers and identifiers.get("ticker"):
        where.append("ticker = %(ticker)s")
        params["ticker"] = identifiers["ticker"].upper()

    # ---------- Aggregations (compute-on-read) ----------
    agg_cfg = cfg.get("aggregations") or {}
    agg_enabled = bool(agg_cfg.get("enabled", False))
    default_date_field = cfg.get("default_date_field") or None

    def _months_window_sql(field: str, months: int) -> str:
        # Usa CURRENT_DATE - INTERVAL '<n> months'
        return f"{field} >= (CURRENT_DATE - INTERVAL '{months} months')"

    def _apply_window(where_list: List[str], window: Optional[str]) -> None:
        if not window or not default_date_field:
            return
        try:
            kind, raw = str(window).split(":", 1)
            n = int(raw)
        except Exception:
            return
        if kind == "months":
            where_list.append(_months_window_sql(default_date_field, n))
        # kind == "count" é tratado na camada de ORDER/LIMIT (subqueries)

    def _entity_is_dividendos() -> bool:
        return entity == "fiis_dividendos"

    # Compute-on-read metrics: custom SQLs por métrica
    if cfg.get("metrics") and (agg_params or {}).get("agg") == "metrics":
        metrics_cfg = cfg.get("metrics") or []
        return _build_metrics_sql(
            metrics_cfg,
            identifiers or {},
            agg_params or {},
            result_key,
            return_cols,
        )

    # Campos base (p/ manter contract de return_columns mesmo em avg/sum)
    base_cols_sql = ", ".join(return_cols)

    # Escolha de via: simples SELECT (sem agg) OU com agg_params
    if not (agg_enabled and agg_params and isinstance(agg_params, dict)):
        where_sql = f" WHERE {' AND '.join(where)}" if where else ""
        cols_sql = base_cols_sql
        sql = f"SELECT {cols_sql} FROM {view_name}{where_sql} LIMIT 100"
        return sql, params, result_key, return_cols

    # Temos parâmetros inferidos
    agg = (agg_params.get("agg") or "").lower()
    window = agg_params.get("window")
    order = (agg_params.get("order") or "desc").lower()
    limit = int(agg_params.get("limit") or 10)

    # Normaliza "latest" -> list + count:1, order desc, limit 1 (sem alterar meta)
    if agg == "latest":
        agg = "list"
        order = "desc"
        limit = 1
        window = window or "count:1"

    # Whitelist de ORDER do YAML da entidade
    order_whitelist = [str(x) for x in (cfg.get("order_by_whitelist") or [])]
    # Fallback de coluna de ordenação temporal se não houver whitelist:
    order_col = default_date_field or (
        order_whitelist[0].split()[0] if order_whitelist else None
    )
    if order_col is None and agg == "list":
        # sem coluna de data — não força ORDER
        order_clause = ""
    else:
        # Se whitelist existir, tenta respeitar (direção vem de 'order')
        if order_whitelist:
            # mantém a primeira coluna autorizada e só varia a direção
            base_ord_col = order_whitelist[0].split()[0]
            order_clause = f" ORDER BY {base_ord_col} {order}"
        else:
            order_clause = f" ORDER BY {order_col} {order}" if order_col else ""

    # WHERE + janela temporal (months)
    where_local = list(where)
    _apply_window(where_local, window)
    where_sql = f" WHERE {' AND '.join(where_local)}" if where_local else ""

    # Implementação por modo:
    if agg in ("list", "", None):
        # Lista simples respeitando janela e limites
        cols_sql = base_cols_sql
        sql = (
            f"SELECT {cols_sql} FROM {view_name}{where_sql}{order_clause} LIMIT {limit}"
        )
        return sql, params, result_key, return_cols

    # Para avg/sum precisamos escolher a coluna numérica alvo
    # Regras: fiis_dividendos -> dividend_amt; fiis_precos -> close_price (média/soma)
    if _entity_is_dividendos():
        metric_col = "dividend_amt"
        null_date_cast = "NULL::timestamp"
        other_null = "NULL::timestamp"
    else:
        # preços: usar close_price como métrica padrão (contrato simples)
        metric_col = "close_price"
        null_date_cast = "NULL::date"
        other_null = "NULL::date"

    if agg in ("avg", "sum"):
        fun = "AVG" if agg == "avg" else "SUM"
        # Suporte a window count:N — usar subquery limitada + agregação
        try:
            kind, raw = str(window).split(":", 1) if window else ("", "")
            n_count = int(raw) if kind == "count" else None
        except Exception:
            n_count = None

        if n_count is not None and order_col:
            # subselect com último N registros, depois agrega
            base_sub = f"SELECT {metric_col} FROM {view_name}{where_sql}{order_clause} LIMIT {n_count}"
            sql = (
                "SELECT "
                "ticker, "
                f"{null_date_cast} AS {cfg['presentation']['return_columns'][1]}, "  # payment_date/ traded_at
                f"{fun}({metric_col}) AS {cfg['presentation']['return_columns'][2]}, "  # metric at pos 2
                f"{other_null} AS {cfg['presentation']['return_columns'][3]} "  # traded_until_date ou outro
                f"FROM ({base_sub}) t, (SELECT %(ticker)s::text AS ticker) tk"
                if "ticker" in params
                else "SELECT "
                "'*'::text AS ticker, "
                f"{null_date_cast} AS {cfg['presentation']['return_columns'][1]}, "
                f"{fun}({metric_col}) AS {cfg['presentation']['return_columns'][2]}, "
                f"{other_null} AS {cfg['presentation']['return_columns'][3]} "
                f"FROM ({base_sub}) t"
            )
            return sql, params, result_key, return_cols

        # caso geral: months:N (já aplicado no WHERE) ou sem window explícito
        sql = (
            "SELECT "
            "ticker, "
            f"{null_date_cast} AS {cfg['presentation']['return_columns'][1]}, "
            f"{fun}({metric_col}) AS {cfg['presentation']['return_columns'][2]}, "
            f"{other_null} AS {cfg['presentation']['return_columns'][3]} "
            f"FROM {view_name}{where_sql}"
        )
        if "ticker" in params:
            sql += " GROUP BY ticker"
        return sql, params, result_key, return_cols

    # Qualquer outro agg não suportado: fallback para list
    cols_sql = base_cols_sql
    sql = f"SELECT {cols_sql} FROM {view_name}{where_sql}{order_clause} LIMIT {limit}"

    return sql, params, result_key, return_cols
