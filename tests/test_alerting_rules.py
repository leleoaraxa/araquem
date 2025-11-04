from pathlib import Path
import yaml


def _load(path: str):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def test_rules_exist():
    assert Path("prometheus/recording_rules.yml").exists()
    assert Path("prometheus/alerting_rules.yml").exists()


def test_recording_uses_bindings_and_thresholds():
    cfg = yaml.safe_load(Path("data/ops/observability.yaml").read_text(encoding="utf-8"))
    recording = Path("prometheus/recording_rules.yml").read_text(encoding="utf-8")
    for key in (
        "api_requests_total",
        "api_latency_bucket",
        "cache_hits_total",
        "cache_misses_total",
        "rag_index_last_refresh_timestamp",
        "rag_index_density_score",
    ):
        assert cfg["bindings"][key] in recording


def test_alerts_reference_recordings():
    alerting = _load("prometheus/alerting_rules.yml")
    expressions = [
        rule["expr"]
        for group in alerting["groups"]
        for rule in group["rules"]
    ]
    assert any("job:api_latency_ms:p95" in expr for expr in expressions)
    assert any("job:api_error_rate:ratio" in expr for expr in expressions)
    assert any("job:cache_hit_ratio:pct" in expr for expr in expressions)
    assert any("job:rag_last_refresh_age_seconds" in expr for expr in expressions)
    assert any("job:rag_density_score" in expr for expr in expressions)


def test_yaml_is_valid():
    for path in ("prometheus/recording_rules.yml", "prometheus/alerting_rules.yml"):
        yaml.safe_load(Path(path).read_text(encoding="utf-8"))
