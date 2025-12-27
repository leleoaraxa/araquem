#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Valida se data/ops/quality/routing_samples.json está alinhado com as
suítes em data/ops/quality/payloads/*_suite.json.

Regras:
  - Compara chaves (expected_intent, pergunta normalizada com trim + colapso de espaços).
  - Falha (exit code != 0) se existir item apenas em routing_samples ou apenas nas suítes.
  - Exibe diffs resumidos (até 20 por categoria).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
ROUTING_PATH = ROOT / "data" / "ops" / "quality" / "routing_samples.json"
SUITES_DIR = ROOT / "data" / "ops" / "quality" / "payloads"
SUITE_GLOB = "*_suite.json"
MAX_DIFF = 20


def normalize_question(question: str) -> str:
    return " ".join(question.split()).strip()


def load_payloads(path: Path) -> List[Dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    payloads = data.get("payloads") or []
    if not isinstance(payloads, list):
        raise ValueError(f"payloads inválidos em {path}")
    return [p for p in payloads if isinstance(p, dict)]


def collect_keys(samples: Iterable[Dict]) -> Dict[Tuple[str | None, str], Dict]:
    collected: Dict[Tuple[str | None, str], Dict] = {}
    for sample in samples:
        question = sample.get("question")
        intent = sample.get("expected_intent")
        if not isinstance(question, str):
            continue
        key = (intent if isinstance(intent, str) else None, normalize_question(question))
        collected[key] = sample
    return collected


def main() -> int:
    suite_paths = sorted(SUITES_DIR.glob(SUITE_GLOB))
    suite_samples: List[Dict] = []
    for path in suite_paths:
        suite_samples.extend(load_payloads(path))

    routing_samples = load_payloads(ROUTING_PATH)

    suite_map = collect_keys(suite_samples)
    routing_map = collect_keys(routing_samples)

    missing_in_routing = sorted(
        set(suite_map.keys()) - set(routing_map.keys()),
        key=lambda k: (k[0] or "", k[1]),
    )
    extras_in_routing = sorted(
        set(routing_map.keys()) - set(suite_map.keys()),
        key=lambda k: (k[0] or "", k[1]),
    )

    if not missing_in_routing and not extras_in_routing:
        print("✅ routing_samples.json alinhado com as suítes.")
        return 0

    if missing_in_routing:
        print(f"❌ Itens ausentes em routing_samples ({len(missing_in_routing)}):")
        for key in missing_in_routing[:MAX_DIFF]:
            intent, question = key
            original = suite_map[key]
            print(f"  - [{intent}] {original.get('question')}")
        if len(missing_in_routing) > MAX_DIFF:
            print(f"  ... (+{len(missing_in_routing) - MAX_DIFF} restantes)")

    if extras_in_routing:
        print(f"❌ Itens extras em routing_samples ({len(extras_in_routing)}):")
        for key in extras_in_routing[:MAX_DIFF]:
            intent, question = key
            original = routing_map[key]
            print(f"  - [{intent}] {original.get('question')}")
        if len(extras_in_routing) > MAX_DIFF:
            print(f"  ... (+{len(extras_in_routing) - MAX_DIFF} restantes)")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
