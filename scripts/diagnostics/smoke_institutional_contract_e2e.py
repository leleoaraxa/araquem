#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: smoke_institutional_contract_e2e.py
Purpose: End-to-end smoke check para o contrato institucional via /ask?explain=true.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.presenter.institutional import load_institutional_policy
from app.utils.filecache import load_yaml_cached

API_DEFAULT = os.getenv("API_URL", "http://localhost:8000")
TIMEOUT_DEFAULT = float(os.getenv("INSTITUTIONAL_E2E_TIMEOUT_SECONDS", "30.0"))


def _get_intent_prefix(policy: Dict[str, Any]) -> str:
    apply_when = policy.get("apply_when") if isinstance(policy, dict) else {}
    intent_prefix = (
        apply_when.get("intent_prefix")
        if isinstance(apply_when, dict)
        else "institutional_"
    )
    if not isinstance(intent_prefix, str) or not intent_prefix.strip():
        return "institutional_"
    return intent_prefix


def _extract_intent(payload: Dict[str, Any]) -> Optional[str]:
    meta = payload.get("meta") if isinstance(payload, dict) else {}
    intent = meta.get("intent") if isinstance(meta, dict) else None
    if isinstance(intent, str):
        return intent
    planner = meta.get("planner") if isinstance(meta, dict) else {}
    chosen = planner.get("chosen") if isinstance(planner, dict) else {}
    if isinstance(chosen, dict):
        intent = chosen.get("intent")
    return intent if isinstance(intent, str) else None


def _extract_narrator_used(payload: Dict[str, Any]) -> Optional[bool]:
    meta = payload.get("meta") if isinstance(payload, dict) else {}
    narrator = meta.get("narrator") if isinstance(meta, dict) else None
    if isinstance(narrator, dict):
        used = narrator.get("used")
        if isinstance(used, bool):
            return used
    return None


def _get_layer_3_heading(policy: Dict[str, Any]) -> str:
    paths = policy.get("paths") if isinstance(policy, dict) else {}
    response_contract_path = (
        paths.get("response_contract") if isinstance(paths, dict) else None
    )
    if isinstance(response_contract_path, str) and response_contract_path.strip():
        contract = load_yaml_cached(str(response_contract_path))
    else:
        contract = {}

    composition = contract.get("composition") if isinstance(contract, dict) else {}
    presentation = (
        composition.get("presentation") if isinstance(composition, dict) else {}
    )
    headings = presentation.get("headings") if isinstance(presentation, dict) else {}
    heading = headings.get("layer_3_default_title") or "Conceito"
    return heading if isinstance(heading, str) and heading.strip() else "Conceito"


def main() -> int:
    policy = load_institutional_policy()
    intent_prefix = _get_intent_prefix(policy if isinstance(policy, dict) else {})

    payload = {
        "question": "O que é a SIRIOS?",
        "conversation_id": "diag-institutional-e2e",
        "nickname": "diag",
        "client_id": "diag",
    }

    try:
        response = httpx.post(
            f"{API_DEFAULT}/ask?explain=true",
            json=payload,
            timeout=TIMEOUT_DEFAULT,
        )
        response.raise_for_status()
    except httpx.RequestError as exc:
        print(f"FAIL: request_error ({exc})")
        return 1
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response else "unknown"
        print(f"FAIL: http_status_error ({status})")
        return 1

    try:
        data = response.json()
    except ValueError as exc:
        print(f"FAIL: json_decode_error ({exc})")
        return 1

    intent = _extract_intent(data)
    if not isinstance(intent, str) or not intent.startswith(intent_prefix):
        print("FAIL: intent_not_institutional")
        return 1

    narrator_used = _extract_narrator_used(data)
    if narrator_used is not False:
        meta = data.get("meta") if isinstance(data, dict) else {}
        narrator = meta.get("narrator") if isinstance(meta, dict) else None
        if isinstance(narrator, dict):
            print(f"DEBUG: meta.narrator = {narrator}")
        else:
            print("DEBUG: meta.narrator = missing")
        print("FAIL: narrator_used")
        return 1

    answer_text = data.get("answer") if isinstance(data, dict) else None
    if not isinstance(answer_text, str) or not answer_text.strip():
        print("FAIL: empty_answer")
        return 1

    layer_3_heading = _get_layer_3_heading(policy)
    if layer_3_heading not in answer_text:
        print("FAIL: missing_concept_heading")
        return 1

    print("PASS: institutional intent, narrator blocked, and concept heading present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
