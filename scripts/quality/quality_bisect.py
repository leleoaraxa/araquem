#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: quality_bisect.py
Purpose: Bisectar amostras de roteamento para isolar falhas em quality gates.
Compliance: Guardrails Araquem v2.1.1
"""

import os, json, sys
from pathlib import Path
import httpx

from app.api.ops.quality_contracts import (
    RoutingPayloadValidationError,
    validate_routing_payload_contract,
)

API = os.getenv("API_URL", "http://localhost:8000")
TOKEN = os.getenv("QUALITY_OPS_TOKEN", "araquem-secret-bust-2025")
MASTER = Path("data/ops/quality/routing_samples.json")


def run_subset(samples):
    payload = {"type": "routing", "payloads": samples}
    r = httpx.post(
        f"{API}/ops/quality/push",
        headers={"x-ops-token": TOKEN, "Content-Type": "application/json"},
        json=payload,
        timeout=30.0,
    )
    r.raise_for_status()
    j = r.json()
    # tentamos várias chaves que já vi no projeto
    metrics = j.get("metrics") or {}
    missed = metrics.get("missed") or metrics.get("misses") or 0
    matched = metrics.get("matched") or 0
    return int(matched), int(missed)


def bisect(indices, all_samples, out):
    if not indices:
        return
    subset = [all_samples[i] for i in indices]
    matched, missed = run_subset(subset)
    if missed == 0:
        return
    if len(indices) == 1:
        out.append(indices[0])
        return
    mid = len(indices) // 2
    left = indices[:mid]
    right = indices[mid:]
    bisect(left, all_samples, out)
    bisect(right, all_samples, out)


def main():
    master = json.loads(MASTER.read_text(encoding="utf-8"))
    try:
        samples, _, _ = validate_routing_payload_contract(master)
    except RoutingPayloadValidationError as exc:
        raise RuntimeError(f"Payload inválido em {MASTER}: {exc}") from exc
    idxs = list(range(len(samples)))  # 0-based
    misses = []
    bisect(idxs, samples, misses)
    if not misses:
        print("✅ Nenhum miss encontrado neste dataset.")
        return
    print(f"❌ Misses encontrados: {len(misses)} (índices 0-based). Detalhes:")
    for i in sorted(misses):
        s = samples[i]
        print(
            f"[{i+1:03d}] {s['question']}  |  exp: {s['expected_intent']} / {s['expected_entity']}"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(1)
