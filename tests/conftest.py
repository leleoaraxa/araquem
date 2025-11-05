# /tests/conftest.py

import os
import calendar
import datetime as dt
from typing import Dict, List, Optional

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


SAMPLE_METRIC_TICKER = "MXRF11"


def _shift_months(date: dt.date, months: int) -> dt.date:
    year = date.year
    month = date.month - months
    while month <= 0:
        month += 12
        year -= 1
    day = min(date.day, calendar.monthrange(year, month)[1])
    return dt.date(year, month, day)


def _sample_dividends_and_prices(
    period_end: dt.date, months: int = 24
) -> tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    """Gera série sintética determinística para métricas de testes."""

    base_payment = dt.date(period_end.year, period_end.month, 15)
    dividends: List[Dict[str, object]] = []
    prices: List[Dict[str, object]] = []

    for idx in range(months):
        pay_date = _shift_months(base_payment, idx)
        traded_until = pay_date - dt.timedelta(days=5)
        # Valores crescentes para garantir diferenças entre janelas
        amount = round(0.8 + 0.02 * (months - idx), 6)
        price_value = round(12 + 0.4 * (months - idx), 6)

        dividends.append(
            {
                "ticker": SAMPLE_METRIC_TICKER,
                "payment_date": pay_date,
                "traded_until_date": traded_until,
                "dividend_amt": amount,
            }
        )
        prices.append(
            {
                "ticker": SAMPLE_METRIC_TICKER,
                "traded_at": traded_until,
                "close_price": price_value,
            }
        )

    dividends.sort(key=lambda item: item["payment_date"])  # mais antigos primeiro
    prices.sort(key=lambda item: item["traded_at"])
    return dividends, prices


def sample_metrics_expected_values(
    period_start: dt.date,
    period_end: dt.date,
    window_kind: Optional[str],
    window_value: Optional[int],
) -> Dict[str, Optional[float]]:
    """Calcula métricas esperadas para o ticker sintético usado nos testes."""

    dividends, prices = _sample_dividends_and_prices(period_end)

    if window_kind == "count" and window_value:
        ordered = sorted(
            dividends,
            key=lambda d: (d["payment_date"], d["traded_until_date"]),
            reverse=True,
        )
        selected = ordered[: int(window_value)]
    else:
        selected = [
            d
            for d in dividends
            if period_start <= d["payment_date"] <= period_end
        ]

    sum_value = sum(d["dividend_amt"] for d in selected)
    count_value = len(selected)

    price_values = [
        p["close_price"]
        for p in prices
        if period_start <= p["traded_at"] <= period_end
    ]
    price_avg = (
        sum(price_values) / len(price_values)
        if price_values
        else None
    )

    def _price_for(date: dt.date) -> Optional[float]:
        eligible = [p for p in prices if p["traded_at"] <= date]
        if not eligible:
            return None
        eligible.sort(key=lambda p: p["traded_at"], reverse=True)
        return float(eligible[0]["close_price"])

    dy_values = []
    for d in selected:
        price = _price_for(d["traded_until_date"])
        if price and price != 0:
            dy_values.append(d["dividend_amt"] / price)

    dy_avg = (
        sum(dy_values) / len(dy_values)
        if dy_values
        else None
    )

    return {
        "dividends_sum": sum_value,
        "dividends_count": float(count_value),
        "price_avg": price_avg,
        "dy_avg": dy_avg,
    }


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

            params = params or {}
            window_kind = params.get("window_kind") or "months"
            window_value = params.get("window_value")
            try:
                window_value = int(window_value) if window_value is not None else None
            except (TypeError, ValueError):
                window_value = None

            period_start_raw = params.get("period_start") or "2023-01-01"
            period_end_raw = params.get("period_end") or "2024-01-01"
            period_start_dt = dt.date.fromisoformat(str(period_start_raw))
            period_end_dt = dt.date.fromisoformat(str(period_end_raw))

            window_months = params.get("window_months") or 12

            metric_order = [
                "dividends_sum",
                "dividends_count",
                "price_avg",
                "dy_avg",
            ]

            if ticker == SAMPLE_METRIC_TICKER:
                computed = sample_metrics_expected_values(
                    period_start_dt,
                    period_end_dt,
                    window_kind,
                    window_value,
                )
                metrics = [(name, computed.get(name)) for name in metric_order]
            else:
                metrics = [
                    ("dividends_sum", 12.34),
                    ("dividends_count", 4),
                    ("price_avg", 95.43),
                    ("dy_avg", 8.76),
                ]

            sql_lower = (sql or "").lower()
            requested = next((m for m, _ in metrics if m in sql_lower), None)
            if requested:
                ordered_metrics = [pair for pair in metrics if pair[0] == requested]
                ordered_metrics.extend(pair for pair in metrics if pair[0] != requested)
            else:
                ordered_metrics = list(metrics)

            base = {
                "ticker": ticker,
                "window_months": window_months,
                "period_start": period_start_dt.isoformat(),
                "period_end": period_end_dt.isoformat(),
            }

            rows = []
            for metric, value in ordered_metrics:
                row = {
                    **base,
                    "metric": metric,
                    "value": value,
                    "meta": {"metric_key": metric},
                }
                rows.append(row)
            return rows
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
