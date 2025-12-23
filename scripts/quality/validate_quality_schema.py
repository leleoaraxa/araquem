#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Valida consistência dos payloads de qualidade (Suite v2).

Checa:
- Todos os *_suite.json possuem {suite, payloads} e não usam "samples".
- Nenhum routing payload usa "samples".
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
SUITES_DIR = REPO_ROOT / "data" / "ops" / "quality" / "payloads"
QUALITY_DIR = REPO_ROOT / "data" / "ops" / "quality"


def _expected_suite_name(path: Path) -> str:
    stem = path.stem
    if stem.endswith("_suite"):
        return stem[: -len("_suite")]
    return stem


def _load_json(path: Path) -> Tuple[Dict[str, Any], List[str]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return {}, [f"{path}: payload must be a JSON object"]
        return data, []
    except Exception as exc:
        return {}, [f"{path}: failed to read JSON ({exc})"]


def validate_suite_file(path: Path) -> List[str]:
    errors: List[str] = []
    data, load_errors = _load_json(path)
    errors.extend(load_errors)
    if load_errors:
        return errors

    if "samples" in data:
        errors.append(f"{path}: remove legacy 'samples', use 'payloads'")

    suite = data.get("suite")
    expected = _expected_suite_name(path)
    if not isinstance(suite, str) or not suite.strip():
        errors.append(f"{path}: 'suite' must be a non-empty string (expected '{expected}')")
    elif suite.strip() != expected:
        errors.append(f"{path}: suite '{suite}' must match filename '{expected}'")

    payloads = data.get("payloads")
    if not isinstance(payloads, list) or not payloads:
        errors.append(f"{path}: 'payloads' must be a non-empty list")
        return errors

    for idx, payload in enumerate(payloads, start=1):
        if not isinstance(payload, dict):
            errors.append(f"{path}: payload #{idx} must be an object")
            continue
        question = payload.get("question")
        if not isinstance(question, str) or not question.strip():
            errors.append(f"{path}: payload #{idx} question must be a non-empty string")
        for key in ("expected_intent", "expected_entity"):
            if key in payload and payload[key] is not None and not (
                isinstance(payload[key], str) and payload[key].strip()
            ):
                errors.append(f"{path}: payload #{idx} {key} must be a string or null")

    return errors


def validate_routing_payloads() -> List[str]:
    errors: List[str] = []
    for path in QUALITY_DIR.glob("*.json"):
        data, load_errors = _load_json(path)
        errors.extend(load_errors)
        if load_errors:
            continue
        if data.get("type") != "routing":
            continue
        if "samples" in data:
            errors.append(f"{path}: routing must use 'payloads', not 'samples'")
        payloads = data.get("payloads")
        if not isinstance(payloads, list) or not payloads:
            errors.append(f"{path}: routing payloads must be a non-empty list")
    return errors


def main() -> int:
    errors: List[str] = []
    suite_files = sorted(SUITES_DIR.glob("*_suite.json"))
    if not suite_files:
        errors.append(f"Nenhuma suite encontrada em {SUITES_DIR}")
    for path in suite_files:
        errors.extend(validate_suite_file(path))

    errors.extend(validate_routing_payloads())

    if errors:
        print("❌ Falhas de validação:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("✅ Schemas de qualidade OK (Suite v2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
