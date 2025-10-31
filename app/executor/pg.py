# app/executor/pg.py

import os
import time
from typing import List, Dict, Any, Optional
import psycopg

from opentelemetry import trace
from app.observability.runtime import load_config, sql_sanitize

class PgExecutor:
    """
    Executor Postgres read-only. Usa DATABASE_URL do ambiente.
    """
    def __init__(self, dsn: Optional[str] = None):
        self._dsn = dsn or os.getenv("DATABASE_URL")
        self._metrics = {"qhist": None, "rows": None, "errors": None}

    def bind_metrics(self, metrics: Dict[str, Any]):
        """Injeta handles de métricas (qhist/rows/errors) já criados no REGISTRY correto."""
        self._metrics = metrics or self._metrics

    def query(self, sql: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        _cfg = load_config()
        _tr = trace.get_tracer("executor")
        with psycopg.connect(self._dsn, autocommit=True) as conn:
            dbname = getattr(getattr(conn, "info", None), "dbname", "db")
            entity = (params or {}).get("entity", "unknown")
            t0 = time.perf_counter()
            try:
                stmt = sql_sanitize(sql, max_len=_cfg["services"]["executor"]["tracing"].get("statement", {}).get("max_len", 512))
                with _tr.start_as_current_span("sql.execute") as sp:
                    sp.set_attribute("db.system", "postgresql")
                    sp.set_attribute("db.name", dbname)
                    sp.set_attribute("db.sql.table", entity)
                    sp.set_attribute("db.statement", stmt)
                    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                        cur.execute(sql, params or {})
                        rows = cur.fetchall()
                dt = time.perf_counter() - t0
                if self._metrics["qhist"] is not None:
                    self._metrics["qhist"].labels(entity=entity, db_name=dbname).observe(dt)
                if self._metrics["rows"] is not None:
                    self._metrics["rows"].labels(entity=entity).inc(len(rows))
                return rows
            except psycopg.Error as e:
                if self._metrics["errors"] is not None:
                    code = getattr(e, "pgcode", "unknown")
                    self._metrics["errors"].labels(entity=entity, error_code=str(code)).inc(1)
                raise
