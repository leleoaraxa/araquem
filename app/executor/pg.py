# app/executor/pg.py

import os
import time
from typing import List, Dict, Any, Optional
import psycopg

from app.observability.runtime import load_config, sql_sanitize
from app.observability.instrumentation import (
    set_trace_attribute,
    trace as start_trace,
)
from app.observability.metrics import emit_counter, emit_histogram


class PgExecutor:
    """
    Executor Postgres read-only. Usa DATABASE_URL do ambiente.
    """

    def __init__(self, dsn: Optional[str] = None):
        self._dsn = dsn or os.getenv("DATABASE_URL")
        # Métricas agora são reportadas via facade (sem bind de handles).

    def query(self, sql: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        _cfg = load_config()
        with psycopg.connect(self._dsn, autocommit=True) as conn:
            dbname = getattr(getattr(conn, "info", None), "dbname", "db")
            entity = (params or {}).get("entity", "unknown")
            t0 = time.perf_counter()
            try:
                stmt = sql_sanitize(
                    sql,
                    max_len=_cfg["services"]["executor"]["tracing"]
                    .get("statement", {})
                    .get("max_len", 512),
                )
                with start_trace(
                    "executor.sql.execute",
                    component="executor",
                    operation="sql.execute",
                ) as span:
                    set_trace_attribute(span, "db.system", "postgresql")
                    set_trace_attribute(span, "db.name", dbname)
                    set_trace_attribute(span, "db.sql.table", entity)
                    set_trace_attribute(span, "db.statement", stmt)
                    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                        cur.execute(sql, params or {})
                        rows = cur.fetchall()
                dt = time.perf_counter() - t0
                # Latência da query
                emit_histogram(
                    "sirios_sql_query_duration_seconds",
                    dt,
                    entity=str(entity),
                    db_name=str(dbname),
                )
                # Linhas retornadas (usa _value suportado pela facade)
                emit_counter(
                    "sirios_sql_rows_returned_total",
                    entity=str(entity),
                    _value=len(rows),
                )

                return rows
            except psycopg.Error as e:
                code = getattr(e, "pgcode", "unknown")
                emit_counter(
                    "sirios_sql_errors_total", entity=str(entity), error_code=str(code)
                )
                raise
