import json
from pathlib import Path

import pytest
import yaml

DASHBOARD_DIR = Path("grafana/dashboards")
DASHBOARD_FILES = [
    DASHBOARD_DIR / "00_sirios_overview.json",
    DASHBOARD_DIR / "10_api_slo_pipeline.json",
    DASHBOARD_DIR / "20_planner_rag_intelligence.json",
    DASHBOARD_DIR / "30_ops_reliability.json",
]

CONFIG_PATH = Path("data/ops/observability.yaml")


def load_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def flatten_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from flatten_values(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from flatten_values(item)
    else:
        yield value


def test_dashboards_exist_and_are_valid_json():
    for dashboard in DASHBOARD_FILES:
        assert dashboard.exists(), f"Missing dashboard {dashboard}"
        with dashboard.open("r", encoding="utf-8") as fh:
            json.load(fh)


def test_bindings_and_thresholds_rendered():
    config = load_config()
    texts = {dashboard: dashboard.read_text(encoding="utf-8") for dashboard in DASHBOARD_FILES}

    for placeholder in ("TODO", "RENAME_ME"):
        for dashboard, content in texts.items():
            assert placeholder not in content, f"Unexpected placeholder '{placeholder}' in {dashboard}"

    for metric in config.get("bindings", {}).values():
        assert any(metric in content for content in texts.values()), f"Binding '{metric}' not found in dashboards"

    threshold_values = [str(value) for value in flatten_values(config.get("thresholds", {}))]
    for threshold in threshold_values:
        assert any(threshold in content for content in texts.values()), f"Threshold '{threshold}' missing from dashboards"


@pytest.mark.parametrize("dashboard_path", DASHBOARD_FILES)
def test_no_unrendered_jinja(dashboard_path):
    content = dashboard_path.read_text(encoding="utf-8")
    forbidden_tokens = ["{{ bindings", "{{ thresholds", "{{ labels", "{{ variables", "{{ promql_filter"]
    for token in forbidden_tokens:
        assert token not in content, f"Template token '{token}' found in {dashboard_path}"
