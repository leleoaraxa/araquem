from tests.conftest import SAMPLE_METRIC_TICKER
from app.core import context as ctx


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


def test_prom_exposes_metrics_cache_counters(client):
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
    payload = {
        "conversation_id": "metrics-obs-test",
        "nickname": "observer",
        "client_id": "obs-suite",
        "question": question,
    }

    miss_resp = client.post("/ask", json=payload)
    assert miss_resp.status_code == 200
    hit_resp = client.post("/ask", json=payload)
    assert hit_resp.status_code == 200

    metrics_text = client.get("/metrics").text
    assert f'metrics_cache_hits_total{{entity="fiis_metrics"}}' in metrics_text
    assert f'metrics_cache_misses_total{{entity="fiis_metrics"}}' in metrics_text
    assert f'cache_hits_total{{entity="fiis_metrics"}}' in metrics_text
    assert f'cache_misses_total{{entity="fiis_metrics"}}' in metrics_text

    assert _extract_metric(metrics_text, "metrics_cache_hits_total") == base_hits + 1
    assert _extract_metric(metrics_text, "metrics_cache_misses_total") == base_misses + 1
    assert _extract_metric(metrics_text, "cache_hits_total") == base_global_hits + 1
    assert _extract_metric(metrics_text, "cache_misses_total") == base_global_misses + 1
