import pytest


@pytest.fixture
def ask(client):
    def _ask(question: str):
        payload = {
            "question": question,
            "conversation_id": "t",
            "nickname": "n",
            "client_id": "c",
        }
        response = client.post("/ask", json=payload)
        response.raise_for_status()
        return response.json()

    return _ask


def _get_metric_value(response, metric_key: str):
    rows = response["results"].get("fii_metrics") or []
    for row in rows:
        if row.get("metric") == metric_key:
            return row.get("value")
    raise AssertionError(f"metric {metric_key} not found in results")


def test_dividends_sum_is_br_currency(ask):
    res = ask("soma de dividendos do HGLG11 nos ultimos 12 meses")
    value = _get_metric_value(res, "dividends_sum")
    assert value == "R$ 12,34"


def test_price_avg_is_br_currency(ask):
    res = ask("preço médio do HGLG11 nos ultimos 6 meses")
    value = _get_metric_value(res, "price_avg")
    assert value == "R$ 95,43"


def test_dividends_count_is_integer(ask):
    res = ask("soma de dividendos do HGLG11 nos ultimos 12 meses")
    value = _get_metric_value(res, "dividends_count")
    assert value == "4"


def test_dy_avg_is_percent_with_two_decimals(ask):
    res = ask("dy médio do HGLG11 nos ultimos 6 meses")
    value = _get_metric_value(res, "dy_avg")
    assert value == "8,76%"
