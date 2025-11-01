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


def fetch_explain_events(
    window: str = "24h",
    intent: Optional[str] = None,
    entity: Optional[str] = None,
    route_id: Optional[str] = None,
    cache_hit: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
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
    if route_id:
        where_clauses.append("route_id = %s")
        params.append(route_id)
    if cache_hit is not None:
        where_clauses.append("(features->>'cache_hit')::bool = %s")
        params.append(bool(cache_hit))
    where_sql = " AND ".join(where_clauses)
    sql = f"""
      SELECT ts, request_id, question, intent, entity, route_id,
             sql_view, sql_hash, cache_policy, latency_ms,
             (features->>'cache_hit')::bool AS cache_hit
      FROM explain_events
      WHERE {where_sql}
      ORDER BY ts DESC
      LIMIT %s OFFSET %s
    """
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params + [int(limit), int(offset)])
            rows = cur.fetchall() or []
    events = []
    for r in rows:
        events.append(
            {
                "ts": r[0].isoformat(),
                "request_id": r[1],
                "question": r[2],
                "intent": r[3],
                "entity": r[4],
                "route_id": r[5],
                "sql_view": r[6],
                "sql_hash": r[7],
                "cache_policy": r[8],
                "latency_ms": float(r[9]) if r[9] is not None else None,
                "cache_hit": bool(r[10]) if r[10] is not None else None,
            }
        )
    return {
        "window": window,
        "filters": {
            "intent": intent,
            "entity": entity,
            "route_id": route_id,
            "cache_hit": cache_hit,
        },
        "events": events,
        "limit": limit,
        "offset": offset,
    }


def fetch_explain_summary(
    window: str = "24h",
    intent: Optional[str] = None,
    entity: Optional[str] = None,
    route_id: Optional[str] = None,
    cache_hit: Optional[bool] = None,
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
    if route_id:
        where_clauses.append("route_id = %s")
        params.append(route_id)
    if cache_hit is not None:
        where_clauses.append("(features->>'cache_hit')::bool = %s")
        params.append(bool(cache_hit))
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
          WHERE {where_sql}
        )
        SELECT
          COUNT(*)::bigint                                        AS requests,
          AVG(latency_ms)::float                                   AS avg_latency_ms,
          PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY latency_ms) AS p50_latency_ms,
          PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY latency_ms) AS p90_latency_ms,
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
          WHERE {where_sql}
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
            kpis_row = cur.fetchone() or (0, None, None, None, None, None, None, None)
            kpis = {
                "requests": int(kpis_row[0]),
                "avg_latency_ms": (
                    float(kpis_row[1]) if kpis_row[1] is not None else None
                ),
                "p50_latency_ms": (
                    float(kpis_row[2]) if kpis_row[2] is not None else None
                ),
                "p90_latency_ms": (
                    float(kpis_row[3]) if kpis_row[3] is not None else None
                ),
                "p95_latency_ms": (
                    float(kpis_row[4]) if kpis_row[4] is not None else None
                ),
                "cache_ratio": float(kpis_row[5]) if kpis_row[5] is not None else None,
                "gold_coverage": (
                    float(kpis_row[6]) if kpis_row[6] is not None else None
                ),
                "gold_agree_ratio": (
                    float(kpis_row[7]) if kpis_row[7] is not None else None
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

            # -------- breakdown: by_route_id --------
            cur.execute(
                f"""
                WITH base AS (
                  SELECT * FROM explain_events WHERE {where_sql}
                )
                SELECT route_id,
                       COUNT(*)::bigint                                        AS requests,
                       AVG(latency_ms)::float                                   AS avg_latency_ms,
                       PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95_latency_ms,
                       AVG(CASE WHEN (features->>'cache_hit')::bool IS TRUE THEN 1 ELSE 0 END)::float AS cache_ratio
                FROM base
                GROUP BY 1
                ORDER BY requests DESC NULLS LAST;
            """,
                params,
            )
            by_route_id = []
            for r in cur.fetchall() or []:
                by_route_id.append(
                    {
                        "route_id": r[0],
                        "requests": int(r[1]),
                        "avg_latency_ms": float(r[2]) if r[2] is not None else None,
                        "p95_latency_ms": float(r[3]) if r[3] is not None else None,
                        "cache_ratio": float(r[4]) if r[4] is not None else None,
                    }
                )

            # -------- breakdown: by_intent --------
            cur.execute(
                f"""
                WITH base AS (
                  SELECT * FROM explain_events WHERE {where_sql}
                )
                SELECT intent,
                       COUNT(*)::bigint,
                       AVG(latency_ms)::float,
                       PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms),
                       AVG(CASE WHEN (features->>'cache_hit')::bool IS TRUE THEN 1 ELSE 0 END)::float
                FROM base
                GROUP BY 1
                ORDER BY 2 DESC NULLS LAST;
            """,
                params,
            )
            by_intent = []
            for r in cur.fetchall() or []:
                by_intent.append(
                    {
                        "intent": r[0],
                        "requests": int(r[1]),
                        "avg_latency_ms": float(r[2]) if r[2] is not None else None,
                        "p95_latency_ms": float(r[3]) if r[3] is not None else None,
                        "cache_ratio": float(r[4]) if r[4] is not None else None,
                    }
                )

            # -------- breakdown: by_entity --------
            cur.execute(
                f"""
                WITH base AS (
                  SELECT * FROM explain_events WHERE {where_sql}
                )
                SELECT entity,
                       COUNT(*)::bigint,
                       AVG(latency_ms)::float,
                       PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms),
                       AVG(CASE WHEN (features->>'cache_hit')::bool IS TRUE THEN 1 ELSE 0 END)::float
                FROM base
                GROUP BY 1
                ORDER BY 2 DESC NULLS LAST;
            """,
                params,
            )
            by_entity = []
            for r in cur.fetchall() or []:
                by_entity.append(
                    {
                        "entity": r[0],
                        "requests": int(r[1]),
                        "avg_latency_ms": float(r[2]) if r[2] is not None else None,
                        "p95_latency_ms": float(r[3]) if r[3] is not None else None,
                        "cache_ratio": float(r[4]) if r[4] is not None else None,
                    }
                )

            # -------- cache quick summary by_route_id (para cards/grids rápidos) --------
            cur.execute(
                f"""
                WITH base AS (
                  SELECT * FROM explain_events WHERE {where_sql}
                )
                SELECT route_id,
                       AVG(CASE WHEN (features->>'cache_hit')::bool IS TRUE THEN 1 ELSE 0 END)::float AS cache_ratio
                FROM base
                GROUP BY 1
                ORDER BY 1;
            """,
                params,
            )
            cache_by_route_id = []
            for r in cur.fetchall() or []:
                cache_by_route_id.append(
                    {
                        "route_id": r[0],
                        "cache_ratio": float(r[1]) if r[1] is not None else None,
                    }
                )

    return {
        "window": window,
        "filters": {
            "intent": intent,
            "entity": entity,
            "route_id": route_id,
            "cache_hit": cache_hit,
        },
        "kpis": kpis,
        "series": series,
        "by_route_id": by_route_id,
        "by_intent": by_intent,
        "by_entity": by_entity,
        "cache_by_route_id": cache_by_route_id,
    }
