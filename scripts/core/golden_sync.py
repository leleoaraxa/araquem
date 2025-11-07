#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: golden_sync.py
Purpose: Normalizar datasets golden e sincronizar arquivos YAML/JSON do quality gate.
Compliance: Guardrails Araquem v2.1.1
"""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import yaml


def _load_yaml(path: Path) -> Dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping")
    return data


def _validate(samples: Sequence[Any]) -> None:
    if not isinstance(samples, Sequence) or isinstance(samples, (str, bytes)):
        raise ValueError("'samples' must be a list of mappings")

    for idx, sample in enumerate(samples):
        if not isinstance(sample, dict):
            raise ValueError(f"sample #{idx} must be a mapping")

        if "question" not in sample:
            raise ValueError(f"sample #{idx} missing required field 'question'")
        question = sample.get("question")
        if question is None or str(question).strip() == "":
            raise ValueError(f"sample #{idx} has empty 'question'")

        if "expected_intent" not in sample:
            raise ValueError(f"sample #{idx} missing required field 'expected_intent'")
        expected_intent = sample.get("expected_intent")
        if expected_intent is None or str(expected_intent).strip() == "":
            raise ValueError(f"sample #{idx} has empty 'expected_intent'")


def _normalize(samples: Iterable[Dict[str, Any]]) -> List[Dict[str, str]]:
    normalized: List[Dict[str, str]] = []

    for sample in samples:
        question = str(sample.get("question", "")).strip()
        intent = str(sample.get("expected_intent", "")).strip()

        normalized_sample: Dict[str, str] = {
            "question": question,
            "expected_intent": intent,
        }

        if "expected_entity" in sample and sample.get("expected_entity") not in (None, ""):
            normalized_sample["expected_entity"] = str(sample["expected_entity"]).strip()

        normalized.append(normalized_sample)

    return normalized


def _stable_sort(samples: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    def _key(sample: Dict[str, str]) -> tuple[str, str, str]:
        intent = sample.get("expected_intent", "").casefold()
        entity = sample.get("expected_entity", "").casefold()
        question = sample.get("question", "").casefold()
        return intent, entity, question

    return sorted(samples, key=_key)


def _render_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def _diff(a: str, b: str) -> str:
    diff = difflib.unified_diff(
        a.splitlines(keepends=True),
        b.splitlines(keepends=True),
        fromfile="current",
        tofile="generated",
    )
    return "".join(diff)


def _load_and_prepare(input_path: Path) -> Dict[str, Any]:
    data = _load_yaml(input_path)
    raw_samples = data.get("samples", [])
    _validate(raw_samples)
    normalized = _normalize(raw_samples)
    sorted_samples = _stable_sort(normalized)
    return {"type": "routing", "samples": sorted_samples}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync golden routing samples")
    parser.add_argument("--in", dest="input_path", required=True, type=Path)
    parser.add_argument("--out", dest="output_path", required=True, type=Path)
    parser.add_argument("--check", action="store_true", help="Check if output is up to date")
    parser.add_argument("--dry-run", action="store_true", help="Show diff without writing output")

    args = parser.parse_args(argv)

    if args.check and args.dry_run:
        parser.error("--check and --dry-run cannot be used together")

    try:
        payload = _load_and_prepare(args.input_path)
    except ValueError as exc:
        parser.exit(2, f"Error: {exc}\n")

    rendered = _render_json(payload)

    output_path: Path = args.output_path
    current = ""
    if output_path.exists():
        current = output_path.read_text(encoding="utf-8")

    if args.check:
        return 0 if current == rendered else 1

    if args.dry_run:
        diff = _diff(current, rendered)
        if diff:
            print(diff, end="")
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
