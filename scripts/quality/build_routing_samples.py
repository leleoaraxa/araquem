#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera data/ops/quality/routing_samples.json a partir das suítes canônicas
em data/ops/quality/payloads/*_suite.json.

Regras:
  - Dedupe por (expected_intent, pergunta normalizada com trim + colapso de espaços).
  - Ordena por expected_intent e depois por question (texto original preservado).
  - Não cria dependências novas; usa apenas stdlib.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
SUITES_DIR = ROOT / "data" / "ops" / "quality" / "payloads"
SUITE_GLOB = "*_suite.json"
OUT_PATH = ROOT / "data" / "ops" / "quality" / "routing_samples.json"


def normalize_question(question: str) -> str:
    """Normaliza pergunta apenas para deduplicação."""
    return " ".join(question.split()).strip()


def load_suite(path: Path) -> Iterable[Dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    payloads = data.get("payloads") or []
    if not isinstance(payloads, list):
        raise ValueError(f"payloads inválidos em {path}")
    for sample in payloads:
        if not isinstance(sample, dict):
            raise ValueError(f"payload malformado em {path}: {sample!r}")
        question = sample.get("question")
        expected_intent = sample.get("expected_intent")
        if not isinstance(question, str):
            raise ValueError(f"payload incompleto em {path}: {sample!r}")
        if expected_intent is not None and not isinstance(expected_intent, str):
            raise ValueError(f"expected_intent inválido em {path}: {sample!r}")
        yield sample


def dedupe_samples(samples: Iterable[Dict]) -> List[Dict]:
    seen: Dict[Tuple[str, str], Dict] = {}
    for sample in samples:
        question = sample["question"]
        intent = sample.get("expected_intent")
        key = (intent, normalize_question(question))
        if key not in seen:
            seen[key] = sample
    return sorted(
        seen.values(),
        key=lambda s: (s.get("expected_intent") or "", s.get("question") or ""),
    )


def build_routing_samples() -> List[Dict]:
    suite_paths = sorted(SUITES_DIR.glob(SUITE_GLOB))
    merged: List[Dict] = []
    for path in suite_paths:
        merged.extend(load_suite(path))
    return dedupe_samples(merged)


def main() -> int:
    samples = build_routing_samples()
    payload = {"type": "routing", "payloads": samples}
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[build_routing_samples] {len(samples)} amostras gravadas em {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
