import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from prometheus_client.parser import text_string_to_metric_families


def _count_valid_docs(store_path: Path) -> int:
    count = 0
    if not store_path.exists():
        return 0
    with store_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                json.loads(line)
            except Exception:
                continue
            count += 1
    return count


def _manifest_epoch(manifest_path: Path) -> int:
    if not manifest_path.exists():
        return 0
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        manifest = {}
    epoch = manifest.get("last_refresh_epoch")
    if epoch is not None:
        try:
            return int(epoch)
        except (TypeError, ValueError):
            pass
    iso_value = manifest.get("last_refresh_iso") or manifest.get("generated_at")
    if isinstance(iso_value, str) and iso_value.strip():
        text = iso_value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            dt = None
        if dt is not None:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
    return int(manifest_path.stat().st_mtime)


def _extract_metric(metrics_body: str, name: str, labels: dict | None = None) -> float:
    for family in text_string_to_metric_families(metrics_body):
        if family.name != name:
            continue
        for sample in family.samples:
            sample_labels = dict(sample.labels)
            if labels is not None:
                if sample_labels == labels:
                    return float(sample.value)
            elif not sample_labels:
                return float(sample.value)
    raise AssertionError(f"Metric {name} with labels {labels} not found")


def test_rag_index_metrics_registration(client):
    store_path = Path("data/embeddings/store/embeddings.jsonl")
    manifest_path = Path("data/embeddings/store/manifest.json")

    response = client.post("/ops/metrics/rag/register")
    assert response.status_code == 200
    payload = response.json()
    metrics = payload["metrics"]

    assert metrics["store"] == store_path.name

    size_bytes = store_path.stat().st_size if store_path.exists() else 0
    docs_total = _count_valid_docs(store_path)
    density_expected = 0.0
    if docs_total:
        density_expected = docs_total / max(size_bytes / 1_000_000.0, 1e-6)

    last_refresh = _manifest_epoch(manifest_path)

    assert metrics["size_bytes"] == size_bytes
    assert metrics["docs_total"] == docs_total
    assert metrics["last_refresh_ts"] == last_refresh
    assert metrics["density_score"] == pytest.approx(density_expected)

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    body = metrics_response.text

    exposed_size = _extract_metric(
        body, "rag_index_size_total", labels={"store": store_path.name}
    )
    exposed_docs = _extract_metric(
        body, "rag_index_docs_total", labels={"store": store_path.name}
    )
    exposed_last_refresh = _extract_metric(body, "rag_index_last_refresh_timestamp", labels=None)
    exposed_density = _extract_metric(body, "rag_index_density_score", labels=None)

    assert exposed_size == pytest.approx(size_bytes)
    assert exposed_docs == pytest.approx(docs_total)
    assert exposed_last_refresh == pytest.approx(last_refresh)
    assert exposed_density == pytest.approx(density_expected)

    assert size_bytes > 0
    assert docs_total > 0
    assert exposed_density > 0
