import os
from typing import List, Dict, Any, Optional
import psycopg

class PgExecutor:
    """
    Executor Postgres read-only. Usa DATABASE_URL do ambiente.
    """
    def __init__(self, dsn: Optional[str] = None):
        self._dsn = dsn or os.getenv("DATABASE_URL")

    def query(self, sql: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        with psycopg.connect(self._dsn, autocommit=True) as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(sql, params or {})
                return cur.fetchall()
