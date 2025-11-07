import pytest

from app.core import context as ctx
from tests.conftest import SAMPLE_METRIC_TICKER


def _reset_cache() -> None:
    store = getattr(ctx.cache, "_store", None)
    if isinstance(store, dict):
        store.clear()


def _extract_metric(text: str, name: str, entity: str = "fiis_metrics") -> float:
    prefix = f'{name}{{entity="{entity}"}}'
    for line in text.splitlines():
        if line.startswith(prefix):
            try:
                return float(line.split(" ", 1)[1])
            except (IndexError, ValueError):
                return 0.0
    return 0.0


@pytest.fixture
def ask_payload():
    return {
        "conversation_id": "metrics-cache-test",
        "nickname": "tester",
        "client_id": "cache-suite",
    }


def test_metrics_cache_miss_then_hit(client, ask_payload):
    _reset_cache()
    baseline = client.get("/metrics")
    assert baseline.status_code == 200
    base_text = baseline.text
    base_hits = _extract_metric(base_text, "metrics_cache_hits_total")
    base_misses = _extract_metric(base_text, "metrics_cache_misses_total")
    base_global_hits = _extract_metric(base_text, "cache_hits_total")
    base_global_misses = _extract_metric(base_text, "cache_misses_total")

    question = (
        f"soma de dividendos do {SAMPLE_METRIC_TICKER} nos ultimos 12 meses"
    )
    payload = {**ask_payload, "question": question}

    first = client.post("/ask", json=payload)
    assert first.status_code == 200
    second = client.post("/ask", json=payload)
    assert second.status_code == 200
    assert first.json()["results"] == second.json()["results"]

    metrics_text = client.get("/metrics").text
    assert _extract_metric(metrics_text, "metrics_cache_misses_total") == pytest.approx(
        base_misses + 1
    )
    assert _extract_metric(metrics_text, "metrics_cache_hits_total") == pytest.approx(
        base_hits + 1
    )
    assert _extract_metric(metrics_text, "cache_misses_total") == pytest.approx(
        base_global_misses + 1
    )
    assert _extract_metric(metrics_text, "cache_hits_total") == pytest.approx(
        base_global_hits + 1
    )


def test_metrics_cache_respects_ttl_and_key(client, ask_payload):
    _reset_cache()
    question_12m = (
        f"soma de dividendos do {SAMPLE_METRIC_TICKER} nos ultimos 12 meses"
    )
    payload_12m = {**ask_payload, "question": question_12m}

    resp_12m_first = client.post("/ask", json=payload_12m)
    assert resp_12m_first.status_code == 200
    keys_after_first = list(getattr(ctx.cache, "_store", {}).keys())
    assert len(keys_after_first) == 1
    key_12m = keys_after_first[0]

    resp_12m_second = client.post("/ask", json=payload_12m)
    assert resp_12m_second.status_code == 200
    assert list(getattr(ctx.cache, "_store", {}).keys()) == [key_12m]

    question_6m = (
        f"soma de dividendos do {SAMPLE_METRIC_TICKER} nos ultimos 6 meses"
    )
    payload_6m = {**ask_payload, "question": question_6m}
    resp_6m = client.post("/ask", json=payload_6m)
    assert resp_6m.status_code == 200

    keys_after_second_window = list(getattr(ctx.cache, "_store", {}).keys())
    assert len(keys_after_second_window) == 2
    assert key_12m in keys_after_second_window
    assert any(key != key_12m for key in keys_after_second_window)


def test_metrics_cache_does_not_cache_empty_results(client, ask_payload):
    _reset_cache()
    question = "soma de dividendos do XXXX11 nos ultimos 12 meses"
    payload = {**ask_payload, "question": question}

    resp = client.post("/ask", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"].get("fii_metrics") == []
    assert getattr(ctx.cache, "_store", {}) == {}
