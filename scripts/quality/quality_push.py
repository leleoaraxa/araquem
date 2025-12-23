#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: quality_push.py
Purpose: Enviar payloads de qualidade para o endpoint /ops/quality/push.
Compliance: Guardrails Araquem v2.1.1
"""

import os
import sys
import json
from pathlib import Path
from typing import Any, Dict

import httpx

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - runtime dependency check
    yaml = None

from app.api.ops.quality_contracts import (
    RoutingPayloadValidationError,
    validate_routing_payload_contract,
)

API = os.getenv("API_URL", "http://localhost:8000")
TOKEN = os.getenv("QUALITY_OPS_TOKEN", "araquem-secret-bust-2025")


def load_payload(path: str):
    suffix = Path(path).suffix.lower()
    if suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    if suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML não instalado – instale 'pyyaml' ou use .json")
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    raise ValueError(f"formato não suportado: '{suffix}' (use .json, .yaml ou .yml)")


def _ensure_suite_v2(path: Path, payload: Dict[str, Any]) -> None:
    ptype = str(payload.get("type") or "routing").strip().lower()

    if ptype == "routing":
        try:
            validate_routing_payload_contract(payload)
        except RoutingPayloadValidationError as exc:
            raise RuntimeError(f"{path}: {exc}") from exc
        return

    is_suite_file = path.name.endswith("_suite.json") or "suite" in payload or "payloads" in payload
    if not is_suite_file:
        return
    if "samples" in payload:
        raise RuntimeError(
            f"{path}: formato inválido: use o contrato Suite v2 com 'payloads' (remova 'samples')."
        )
    payloads = payload.get("payloads")
    if not isinstance(payloads, list) or not payloads:
        raise RuntimeError(f"{path}: formato inválido: 'payloads' deve ser uma lista não vazia.")
    suite_name = payload.get("suite")
    if suite_name is None:
        raise RuntimeError(f"{path}: formato inválido: campo obrigatório 'suite' ausente.")
    if not isinstance(suite_name, str) or not suite_name.strip():
        raise RuntimeError(f"{path}: formato inválido: 'suite' deve ser string não vazia.")
    description = payload.get("description") or ""
    if not isinstance(description, str):
        raise RuntimeError(f"{path}: formato inválido: 'description' deve ser string.")


def push(path: str):
    payload_path = Path(path)
    payload = load_payload(path)
    _ensure_suite_v2(payload_path, payload)
    r = httpx.post(
        f"{API}/ops/quality/push",
        headers={"x-ops-token": TOKEN, "Content-Type": "application/json"},
        json=payload,
        timeout=30.0,
    )
    try:
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(f"[error] {path}: HTTP {r.status_code}")
        print(r.text)  # <- mostra o motivo do 422
        raise
    return r.json()


def main():
    if len(sys.argv) < 2:
        print(
            "usage: scripts/quality/quality_push.py <payload.(json|yaml|yml)> "
            "[<payload.(json|yaml|yml)> ...]",
            file=sys.stderr,
        )
        sys.exit(2)
    total = 0
    for p in sys.argv[1:]:
        out = push(p)
        total += int(out.get("accepted") or 0)
        print(f"[ok] {p}: {json.dumps(out, ensure_ascii=False)}")
    print(f"[done] total accepted={total}")


if __name__ == "__main__":
    main()
