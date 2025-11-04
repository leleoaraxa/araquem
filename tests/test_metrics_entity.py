import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _ask(q: str):
    return client.post(
        "/ask",
        json={
            "question": q,
            "conversation_id": "t",
            "nickname": "n",
            "client_id": "c",
        },
    ).json()


def test_dividends_sum_returns_row():
    res = _ask("soma de dividendos do HGLG11 nos ultimos 12 meses")
    assert res["meta"]["planner_intent"] == "metricas"
    assert res["meta"]["planner_entity"] == "fiis_metrics"
    assert res["results"]["fii_metrics"] and len(res["results"]["fii_metrics"]) >= 1
    row = res["results"]["fii_metrics"][0]
    assert row["metric"] == "dividends_sum"
    assert "value" in row


def test_dy_avg_uses_prices_and_divs():
    res = _ask("dy médio do HGLG11 nos ultimos 6 meses")
    assert res["meta"]["planner_intent"] == "metricas"
    assert res["meta"]["planner_entity"] == "fiis_metrics"
    row = res["results"]["fii_metrics"][0]
    assert row["metric"] == "dy_avg"
    assert "value" in row
