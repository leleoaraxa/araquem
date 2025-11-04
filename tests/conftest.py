# /tests/conftest.py

import os

import pytest
from fastapi.testclient import TestClient

from app.main import app


class _InMemoryCache:
    def __init__(self):
        self._store = {}

    def ping(self):
        return True

    def get_json(self, key):
        return self._store.get(key)

    def set_json(self, key, value, ttl_seconds):
        self._store[key] = value

    def delete(self, key):
        return 1 if self._store.pop(key, None) is not None else 0


@pytest.fixture(scope="session", autouse=True)
def _test_infra():
    from app.core import context as ctx
    from app.api import ask as ask_module
    from app.api import health as health_module
    from app.api.ops import cache as ops_cache_module
    from app.executor.pg import PgExecutor
    import psycopg

    dummy = _InMemoryCache()
    original_ctx_cache = ctx.cache
    original_ask_cache = ask_module.cache
    original_health_cache = health_module.cache
    original_ops_cache = ops_cache_module.cache
    original_pg_query = PgExecutor.query
    original_psycopg_connect = psycopg.connect

    ctx.cache = dummy
    ask_module.cache = dummy
    health_module.cache = dummy
    ops_cache_module.cache = dummy

    def _fake_query(self, sql, params):
        entity = (params or {}).get("entity")
        ticker = (params or {}).get("ticker") or "MXRF11"
        if entity == "fiis_cadastro":
            return [
                {
                    "ticker": ticker,
                    "fii_cnpj": "12.345.678/0001-99",
                    "display_name": f"Fundo {ticker}",
                    "admin_name": "Admin LTDA",
                    "admin_cnpj": "11.111.111/0001-11",
                    "website_url": "https://example.com",
                }
            ]
        if entity == "fiis_precos":
            return [
                {
                    "ticker": ticker,
                    "traded_at": "2024-01-05",
                    "close_price": 98.76,
                    "adj_close_price": 98.76,
                    "open_price": 97.5,
                    "max_price": 99.9,
                    "min_price": 96.8,
                    "daily_variation_pct": 0.85,
                }
            ]
        if entity == "fiis_dividendos":
            return [
                {
                    "ticker": ticker,
                    "payment_date": "2024-01-10",
                    "dividend_amt": 1.23,
                    "traded_until_date": "2023-12-28",
                }
            ]
        if entity == "fiis_metrics":
            if ticker == "XXXX11":
                return []
            sql_lower = (sql or "").lower()
            metric = "dividends_sum"
            value = 12.34
            if "dy_avg" in sql_lower:
                metric = "dy_avg"
                value = 8.76
            elif "price_avg" in sql_lower:
                metric = "price_avg"
                value = 95.43
            elif "dividends_count" in sql_lower:
                metric = "dividends_count"
                value = 4
            return [
                {
                    "ticker": ticker,
                    "metric": metric,
                    "value": value,
                    "window_months": (params or {}).get("window_months") or 12,
                    "period_start": (params or {}).get("period_start") or "2023-01-01",
                    "period_end": (params or {}).get("period_end") or "2024-01-01",
                }
            ]
        return []

    class _DummyCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, *args, **kwargs):
            return None

        def fetchone(self):
            return ("MXRF11",)

    class _DummyConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self, *args, **kwargs):
            return _DummyCursor()

        def commit(self):
            return None

    def _connect_stub(*args, **kwargs):
        return _DummyConnection()

    PgExecutor.query = _fake_query
    psycopg.connect = _connect_stub
    os_environ = os.environ
    if "DATABASE_URL" not in os_environ:
        os_environ["DATABASE_URL"] = "postgresql://test"  # garante healthz ok

    try:
        yield dummy
    finally:
        ctx.cache = original_ctx_cache
        ask_module.cache = original_ask_cache
        health_module.cache = original_health_cache
        ops_cache_module.cache = original_ops_cache
        PgExecutor.query = original_pg_query
        psycopg.connect = original_psycopg_connect


@pytest.fixture(scope="session")
def client():
    return TestClient(app)
