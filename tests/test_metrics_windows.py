import datetime as dt
from decimal import Decimal

import pytest

from app.formatter.rows import format_metric_value
from tests.conftest import SAMPLE_METRIC_TICKER, sample_metrics_expected_values


@pytest.fixture
def ask_payload():
    return {
        "conversation_id": "test-conv",
        "nickname": "tester",
        "client_id": "client",
    }


def _get_metric_row(response_json, metric_key: str) -> dict:
    rows = response_json.get("results", {}).get("fii_metrics") or []
    for row in rows:
        if row.get("metric") == metric_key:
            return row
    raise AssertionError(f"metric {metric_key} not found in results")


def _currency_to_decimal(value: str) -> Decimal:
    if value is None:
        raise AssertionError("Expected monetary value, got None")
    cleaned = value.replace("R$", "").strip()
    cleaned = cleaned.replace(".", "").replace(",", ".")
    return Decimal(cleaned)


def test_dividends_sum_3m_lt_12m(client, ask_payload):
    resp_3m = client.post(
        "/ask",
        json={
            **ask_payload,
            "question": f"soma de dividendos do {SAMPLE_METRIC_TICKER} nos ultimos 3 meses",
        },
    )
    assert resp_3m.status_code == 200
    data_3m = resp_3m.json()
    assert data_3m["meta"]["planner_entity"] == "fiis_metrics"
    assert data_3m["meta"]["planner_intent"] == "metricas"
    assert data_3m["meta"].get("rendered_response")

    resp_12m = client.post(
        "/ask",
        json={
            **ask_payload,
            "question": f"soma de dividendos do {SAMPLE_METRIC_TICKER} nos ultimos 12 meses",
        },
    )
    assert resp_12m.status_code == 200
    data_12m = resp_12m.json()

    sum_3m = _currency_to_decimal(_get_metric_row(data_3m, "dividends_sum")["value"])
    sum_12m = _currency_to_decimal(_get_metric_row(data_12m, "dividends_sum")["value"])

    assert sum_3m <= sum_12m


def test_price_avg_6m_differs_from_12m(client, ask_payload):
    resp_6m = client.post(
        "/ask",
        json={
            **ask_payload,
            "question": f"preço médio do {SAMPLE_METRIC_TICKER} nos ultimos 6 meses",
        },
    )
    assert resp_6m.status_code == 200
    data_6m = resp_6m.json()
    assert data_6m["meta"].get("rendered_response")

    resp_12m = client.post(
        "/ask",
        json={
            **ask_payload,
            "question": f"preço médio do {SAMPLE_METRIC_TICKER} nos ultimos 12 meses",
        },
    )
    assert resp_12m.status_code == 200
    data_12m = resp_12m.json()

    avg_6m = _currency_to_decimal(_get_metric_row(data_6m, "price_avg")["value"])
    avg_12m = _currency_to_decimal(_get_metric_row(data_12m, "price_avg")["value"])

    assert avg_6m != avg_12m


def test_dy_avg_respects_count_last_3_payments(client, ask_payload):
    question = f"dy médio do {SAMPLE_METRIC_TICKER} nos últimos 3 pagamentos"
    resp = client.post(
        "/ask",
        json={**ask_payload, "question": question},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["meta"]["planner_entity"] == "fiis_metrics"
    assert data["meta"]["planner_intent"] == "metricas"
    assert data["meta"]["aggregates"].get("window") == "count:3"

    row = _get_metric_row(data, "dy_avg")
    period_start = dt.date.fromisoformat(row["period_start"])
    period_end = dt.date.fromisoformat(row["period_end"])

    expected = sample_metrics_expected_values(period_start, period_end, "count", 3)
    expected_formatted = format_metric_value("dy_avg", expected["dy_avg"])

    assert row["value"] == expected_formatted


def test_count_window_overrides_months_when_both_present(client, ask_payload):
    question = (
        f"dy médio do {SAMPLE_METRIC_TICKER} nos últimos 3 pagamentos nos últimos 12 meses"
    )
    resp = client.post(
        "/ask",
        json={**ask_payload, "question": question},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["meta"]["aggregates"].get("window") == "count:3"

    row = _get_metric_row(data, "dy_avg")
    period_start = dt.date.fromisoformat(row["period_start"])
    period_end = dt.date.fromisoformat(row["period_end"])

    expected_count = sample_metrics_expected_values(period_start, period_end, "count", 3)
    expected_months = sample_metrics_expected_values(period_start, period_end, "months", 12)

    formatted_count = format_metric_value("dy_avg", expected_count["dy_avg"])
    formatted_months = format_metric_value("dy_avg", expected_months["dy_avg"])

    assert row["value"] == formatted_count
