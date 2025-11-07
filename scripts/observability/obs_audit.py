#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: obs_audit.py
Purpose: Auditar dashboards e rules contra o YAML de observabilidade para evitar drift.
Compliance: Guardrails Araquem v2.1.1

- Verifica presença de bindings/thresholds do YAML nos dashboards e rules.
- Exige que artefatos gerados sejam mais recentes que o YAML.
- Detecta placeholders não renderizados.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import yaml

YAML_PATH = Path("data/ops/observability.yaml")
DASH_DIR = Path("grafana/dashboards")
RULE_REC = Path("prometheus/recording_rules.yml")
RULE_ALT = Path("prometheus/alerting_rules.yml")
DASH_FILES = [
    "00_sirios_overview.json",
    "10_api_slo_pipeline.json",
    "20_planner_rag_intelligence.json",
    "30_ops_reliability.json",
]

PLACEHOLDER_PATTERNS = [
    r"__PLACEHOLDER__",
    r"TODO",
    r"RENAME_ME",
]


def load_yaml(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> Dict:
    return json.loads(read_text(path))


def assert_exists(paths: Iterable[Path]) -> None:
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise SystemExit(f"[audit] missing files: {missing}")


def assert_mtime_not_older(src: Path, targets: Iterable[Path]) -> None:
    src_mtime = src.stat().st_mtime
    too_old = [str(t) for t in targets if t.stat().st_mtime < src_mtime]
    if too_old:
        raise SystemExit(
            "[audit] generated artifacts older than YAML. Run generators:\n"
            f"  - python scripts/observability/gen_dashboards.py --config {YAML_PATH} --out {DASH_DIR}\n"
            f"  - python scripts/observability/gen_alerts.py --config {YAML_PATH}\n"
            f"Outdated: {too_old}"
        )


def assert_no_placeholders(texts: Iterable[Tuple[str, str]]) -> None:
    for name, content in texts:
        for pattern in PLACEHOLDER_PATTERNS:
            if re.search(pattern, content):
                raise SystemExit(f"[audit] placeholder '{pattern}' found in {name}")


def _flatten_items(data: Dict, prefix: str = "") -> List[Tuple[str, object]]:
    flattened: List[Tuple[str, object]] = []
    for key, value in data.items():
        dotted = f"{prefix}{key}"
        if isinstance(value, dict):
            flattened.extend(_flatten_items(value, dotted + "."))
        else:
            flattened.append((dotted, value))
    return flattened


def ensure_bindings_thresholds_present(cfg: Dict, dashboards: Dict[str, str], rules_text: str) -> None:
    bindings = cfg.get("bindings", {})
    thresholds = cfg.get("thresholds", {})

    missing_refs: List[str] = []

    for key, metric in bindings.items():
        needle = str(metric)
        appears = any(needle in content for content in dashboards.values()) or (needle in rules_text)
        if not appears:
            missing_refs.append(f"binding:{key} -> {needle}")

    for threshold_key, value in _flatten_items(thresholds):
        key_present = any(threshold_key in content for content in dashboards.values()) or (
            threshold_key in rules_text
        )
        if key_present:
            continue

        candidate_values = {str(value)}
        if isinstance(value, (int, float)):
            candidate_values.add(f"{value:g}")
            if float(value).is_integer():
                candidate_values.add(str(int(float(value))))

        value_present = any(
            any(candidate in content for candidate in candidate_values) for content in dashboards.values()
        ) or any(candidate in rules_text for candidate in candidate_values)

        if not value_present:
            missing_refs.append(f"threshold:{threshold_key}")

    if missing_refs:
        raise SystemExit("[audit] missing references in dashboards/rules:\n - " + "\n - ".join(missing_refs))


def main() -> None:
    assert_exists([YAML_PATH, RULE_REC, RULE_ALT, DASH_DIR])
    assert_exists([DASH_DIR / file for file in DASH_FILES])

    config = load_yaml(YAML_PATH)

    targets = [RULE_REC, RULE_ALT] + [DASH_DIR / file for file in DASH_FILES]
    assert_mtime_not_older(YAML_PATH, targets)

    dashboards_text: Dict[str, str] = {}
    for file in DASH_FILES:
        path = DASH_DIR / file
        dashboards_text[file] = read_text(path)
        load_json(path)

    recording_rules = read_text(RULE_REC)
    alerting_rules = read_text(RULE_ALT)
    rules_text = "\n".join([recording_rules, alerting_rules])

    assert_no_placeholders(
        list(dashboards_text.items())
        + [("recording_rules", recording_rules), ("alerting_rules", alerting_rules)]
    )

    ensure_bindings_thresholds_present(config, dashboards_text, rules_text)

    print("[audit] OK — dashboards and rules consistent with observability.yaml")


if __name__ == "__main__":
    main()
