# app/analytics/repository.py
from __future__ import annotations
from typing import Any, Dict, Optional, List, Tuple
import os
import psycopg


# Parser simples de janelas (guardrails: nada mágico)
def _parse_window(window: str) -> str:
    # aceita sufixos h/d; validação simples
    w = (window or "24h").strip().lower()
    if w.endswith("h") and w[:-1].isdigit():
        return f"{int(w[:-1])} hours"
    if w.endswith("d") and w[:-1].isdigit():
        return f"{int(w[:-1])} days"
    # default
    return "24 hours"


def fetch_explain_summary(
    window: str = "24h",
    intent: Optional[str] = None,
    entity: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Lê KPIs e série temporal a partir de explain_events, com janelas de tempo.
    Não altera dados; sem heurísticas; SQL real.
    """
    dsn = os.getenv("DATABASE_URL")
    interval_sql = _parse_window(window)

    where_clauses = ["ts >= now() - (%s)::interval"]
    params: List[Any] = [interval_sql]
    if intent:
        where_clauses.append("intent = %s")
        params.append(intent)
    if entity:
        where_clauses.append("entity = %s")
        params.append(entity)
    where_sql = " AND ".join(where_clauses)

    # Bucketing: escolhe 1m para janelas até 24h; caso contrário, 1h.
    bucket_sql = (
        "1 minute"
        if ("hour" in interval_sql and int(interval_sql.split()[0]) <= 24)
        else "1 hour"
    )

    sql_kpis = f"""
        WITH base AS (
          SELECT *
          FROM explain_events
          WHERE {where_sql.replace('interval %s', '(%s)::interval')}
        )
        SELECT
          COUNT(*)::bigint                                        AS requests,
          AVG(latency_ms)::float                                   AS avg_latency_ms,
          PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95_latency_ms,
          AVG(CASE WHEN (features->>'cache_hit')::bool IS TRUE THEN 1 ELSE 0 END)::float AS cache_ratio,
          AVG(CASE WHEN gold_expected_entity IS NOT NULL OR gold_expected_intent IS NOT NULL THEN 1 ELSE 0 END)::float AS gold_coverage,
          AVG(CASE WHEN gold_agree IS TRUE THEN 1 ELSE 0 END)::float AS gold_agree_ratio
        FROM base;
    """

    sql_series = f"""
        WITH base AS (
          SELECT *
          FROM explain_events
          WHERE {where_sql.replace('interval %s', '(%s)::interval')}
        )
        SELECT
          date_trunc('minute', ts) AS bucket_minute,
          COUNT(*)::bigint AS requests,
          AVG(latency_ms)::float AS avg_latency_ms,
          PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95_latency_ms,
          AVG(CASE WHEN (features->>'cache_hit')::bool IS TRUE THEN 1 ELSE 0 END)::float AS cache_ratio
        FROM base
        GROUP BY 1
        ORDER BY 1 ASC;
    """

    # Se bucketar em hora:
    if "1 hour" in bucket_sql:
        sql_series = sql_series.replace(
            "date_trunc('minute', ts)", "date_trunc('hour', ts) AS bucket_minute"
        )

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_kpis, params)
            kpis_row = cur.fetchone() or (0, None, None, None, None, None)
            kpis = {
                "requests": int(kpis_row[0]),
                "avg_latency_ms": (
                    float(kpis_row[1]) if kpis_row[1] is not None else None
                ),
                "p95_latency_ms": (
                    float(kpis_row[2]) if kpis_row[2] is not None else None
                ),
                "cache_ratio": float(kpis_row[3]) if kpis_row[3] is not None else None,
                "gold_coverage": (
                    float(kpis_row[4]) if kpis_row[4] is not None else None
                ),
                "gold_agree_ratio": (
                    float(kpis_row[5]) if kpis_row[5] is not None else None
                ),
            }

            cur.execute(sql_series, params)
            series = []
            for r in cur.fetchall() or []:
                series.append(
                    {
                        "bucket": r[0].isoformat(),
                        "requests": int(r[1]),
                        "avg_latency_ms": float(r[2]) if r[2] is not None else None,
                        "p95_latency_ms": float(r[3]) if r[3] is not None else None,
                        "cache_ratio": float(r[4]) if r[4] is not None else None,
                    }
                )

    return {
        "window": window,
        "filters": {"intent": intent, "entity": entity},
        "kpis": kpis,
        "series": series,
    }
