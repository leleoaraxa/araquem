#!/usr/bin/env python3
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: validate_data_contracts.py
Purpose: Validar consistência entre os contratos golden em YAML e JSON.
Compliance: Guardrails Araquem v2.1.1
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, Tuple


try:
    import yaml  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover - runtime dependency check
    print("[fail] PyYAML não instalado – instale 'pyyaml' para validar contratos.", file=sys.stderr)
    raise SystemExit(1) from exc


ROOT_DIR = Path(__file__).resolve().parents[2]
YAML_PATH = ROOT_DIR / "data" / "golden" / "m65_quality.yaml"
JSON_PATH = ROOT_DIR / "data" / "golden" / "m65_quality.json"


def _ensure_samples_from_yaml(path: Path) -> Iterable[Dict[str, object]]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} deve ser um objeto YAML na raiz")
    samples = data.get("samples")
    if not isinstance(samples, list):
        raise ValueError(f"{path} deve conter 'samples' como lista")
    normalized = []
    for idx, sample in enumerate(samples):
        if not isinstance(sample, dict):
            raise ValueError(f"{path} samples[{idx}] deve ser um objeto")
        normalized.append(sample)
    return normalized


def _ensure_samples_from_json(path: Path) -> Iterable[Dict[str, object]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} deve ser um objeto JSON na raiz")
    samples = data.get("samples")
    if not isinstance(samples, list):
        raise ValueError(f"{path} deve conter 'samples' como lista")
    normalized = []
    for idx, sample in enumerate(samples):
        if not isinstance(sample, dict):
            raise ValueError(f"{path} samples[{idx}] deve ser um objeto")
        normalized.append(sample)
    return normalized


def _canonical_sample(sample: Dict[str, object]) -> Tuple[str, Dict[str, object]]:
    canonical = json.dumps(sample, sort_keys=True, ensure_ascii=False)
    return canonical, sample


def _counter_with_lookup(
    samples: Iterable[Dict[str, object]]
) -> Tuple[Counter[str], Dict[str, Dict[str, object]]]:
    counter: Counter[str] = Counter()
    lookup: Dict[str, Dict[str, object]] = {}
    for sample in samples:
        canon, original = _canonical_sample(sample)
        counter[canon] += 1
        lookup.setdefault(canon, original)
    return counter, lookup


def _print_examples(
    prefix: str, lookup: Dict[str, Dict[str, object]], counter: Counter[str]
) -> None:
    total = sum(counter.values())
    print(f"{prefix}: {total}")
    if not total:
        return
    limit = 3
    for canon, _ in counter.most_common():
        if limit <= 0:
            break
        sample = lookup[canon]
        question = sample.get("question")
        print(
            f"  - question={question!r} sample={json.dumps(sample, ensure_ascii=False)}"
        )
        limit -= 1


def main() -> int:
    try:
        yaml_samples = list(_ensure_samples_from_yaml(YAML_PATH))
        json_samples = list(_ensure_samples_from_json(JSON_PATH))
    except ValueError as exc:
        print(f"[fail] {exc}")
        return 1

    yaml_counter, yaml_lookup = _counter_with_lookup(yaml_samples)
    json_counter, json_lookup = _counter_with_lookup(json_samples)

    missing_in_json = yaml_counter - json_counter
    missing_in_yaml = json_counter - yaml_counter

    if missing_in_json or missing_in_yaml:
        print(
            "[fail] m65 yaml!=json: "
            f"only_in_yaml={sum(missing_in_json.values())} "
            f"only_in_json={sum(missing_in_yaml.values())}"
        )
        _print_examples("[yaml] exemplos", yaml_lookup, missing_in_json)
        _print_examples("[json] exemplos", json_lookup, missing_in_yaml)
        return 1

    print("[contracts] m65 yaml==json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
