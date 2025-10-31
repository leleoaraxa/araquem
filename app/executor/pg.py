# app/executor/pg.py

import os
import time
from typing import List, Dict, Any, Optional
import psycopg

from opentelemetry import trace
from app.observability.runtime import load_config, init_sql_metrics, sql_sanitize

class PgExecutor:
    """
    Executor Postgres read-only. Usa DATABASE_URL do ambiente.
    """
    def __init__(self, dsn: Optional[str] = None):
        self._dsn = dsn or os.getenv("DATABASE_URL")

    def query(self, sql: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        _cfg = load_config()
        _sm = init_sql_metrics(_cfg)
        _tr = trace.get_tracer("executor")
        with psycopg.connect(self._dsn, autocommit=True) as conn:
            dbname = getattr(getattr(conn, "info", None), "dbname", "db")
            t0 = time.perf_counter()
            try:
                stmt = sql_sanitize(sql, max_len=_cfg["services"]["executor"]["tracing"].get("statement", {}).get("max_len", 512))
                with _tr.start_as_current_span("sql.execute") as sp:
                    sp.set_attribute("db.system", "postgresql")
                    sp.set_attribute("db.name", dbname)
                    sp.set_attribute("db.sql.table", params.get("entity", ""))  # opcional, se existir
                    sp.set_attribute("db.statement", stmt)
                    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                        cur.execute(sql, params or {})
                        rows = cur.fetchall()
                dt = time.perf_counter() - t0
                if _sm["qhist"] is not None:
                    _sm["qhist"].labels(entity=params.get("entity", "unknown"), db_name=dbname).observe(dt)
                if _sm["rows"] is not None:
                    _sm["rows"].labels(entity=params.get("entity", "unknown")).inc(len(rows))
                return rows
            except psycopg.Error as e:
                if _sm["errors"] is not None:
                    code = getattr(e, "pgcode", "unknown")
                    _sm["errors"].labels(entity=params.get("entity", "unknown"), error_code=str(code)).inc(1)
                raise
