#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: quality_diff_routing.py
Purpose: Comparar roteamento atual com amostras de qualidade para detectar divergências.
Compliance: Guardrails Araquem v2.1.1
"""

import argparse
import datetime
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

import httpx

from app.api.ops.quality_contracts import (
    RoutingPayloadValidationError,
    validate_routing_payload_contract,
)

CID = os.getenv("QUALITY_CONVERSATION_ID", "ops-quality")
NICK = os.getenv("QUALITY_NICK", "ops")
CLIENT = os.getenv("QUALITY_CLIENT", "ops")
SRC = Path("data/ops/quality/routing_samples.json")
OUT = Path("data/ops/quality_experimental/routing_misses_via_ask.json")
API_DEFAULT = os.getenv("API_URL", "http://localhost:8000")
TIMEOUT_DEFAULT = float(os.getenv("QUALITY_TIMEOUT_SECONDS", "300.0"))
DISABLE_RAG_DEFAULT = bool(int(os.getenv("QUALITY_DISABLE_RAG", "0")))


def pick(d: Dict[str, Any], *paths: Sequence[str], default: Any = None) -> Any:
    """pega o primeiro caminho existente em dicts aninhados"""
    for path in paths:
        cur = d
        ok = True
        for k in path:
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                ok = False
                break
        if ok:
            return cur
    return default


def preview(text: str, max_len: int = 300) -> str:
    return text if len(text) <= max_len else text[:max_len] + "…"


def find_intent_entity_anywhere(obj):
    if isinstance(obj, dict):
        intent = obj.get("intent")
        entity = obj.get("entity")
        if isinstance(intent, str) and isinstance(entity, str):
            score = obj.get("score", None)
            return intent, entity, score
        for v in obj.values():
            r = find_intent_entity_anywhere(v)
            if r:
                return r
    elif isinstance(obj, list):
        for it in obj:
            r = find_intent_entity_anywhere(it)
            if r:
                return r
    return None


def extract_routing(resp: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Any]:
    intent_paths: Iterable[Sequence[str]] = (
        ("meta", "planner", "chosen", "intent"),
        ("meta", "planner", "chosen_intent"),
        ("meta", "routing", "chosen", "intent"),
        ("meta", "route", "intent"),
        ("meta", "orchestrator", "route", "intent"),
        ("route", "intent"),
        ("planner_intent",),
    )
    entity_paths: Iterable[Sequence[str]] = (
        ("meta", "planner", "chosen", "entity"),
        ("meta", "route", "entity"),
        ("meta", "routing", "chosen", "entity"),
        ("planner_entity",),
    )
    score_paths: Iterable[Sequence[str]] = (
        ("meta", "planner", "chosen", "score"),
        ("planner_score",),
    )

    intent = pick(resp, *intent_paths, default=None)
    entity = pick(resp, *entity_paths, default=None)
    score = pick(resp, *score_paths, default=None)
    if intent is None or entity is None:
        meta = resp.get("meta")
        r = find_intent_entity_anywhere(meta) if meta is not None else None
        if r:
            return r[0], r[1], r[2]
    return intent, entity, score


def ask(q: str, api_url: str, timeout: float, disable_rag: bool) -> Dict[str, Any]:
    payload = {
        "question": q,
        "conversation_id": CID,
        "nickname": NICK,
        "client_id": CLIENT,
    }

    # Header interno para o /ask entrar em modo "routing-only"
    headers: dict = {}
    if disable_rag:
        headers["X-Quality-Routing-Only"] = "1"

    try:
        r = httpx.post(
            f"{api_url}/ask?explain=true",
            json=payload,
            timeout=timeout,
            headers=headers or None,
        )
        r.raise_for_status()
    except httpx.ReadTimeout as exc:
        return {
            "ok": False,
            "error_kind": "timeout",
            "error_message": str(exc),
            "status_code": None,
            "body_preview": None,
        }
    except httpx.HTTPStatusError as exc:
        response = exc.response
        return {
            "ok": False,
            "error_kind": "http_status_error",
            "error_message": str(exc),
            "status_code": response.status_code if response else None,
            "body_preview": preview(response.text) if response else None,
        }
    except httpx.RequestError as exc:
        response = getattr(exc, "response", None)
        return {
            "ok": False,
            "error_kind": "request_error",
            "error_message": str(exc),
            "status_code": response.status_code if response else None,
            "body_preview": (
                preview(response.text) if response and response.text else None
            ),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error_kind": "unexpected_error",
            "error_message": repr(exc),
            "status_code": None,
            "body_preview": None,
        }

    try:
        j = r.json()
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "error_kind": "json_decode_error",
            "error_message": str(exc),
            "status_code": r.status_code,
            "body_preview": preview(r.text),
        }

    intent, entity, score = extract_routing(j)
    if intent is None or entity is None:
        return {
            "ok": False,
            "error_kind": "parse_error_semantic",
            "error_message": "intent/entity ausentes no payload",
            "status_code": r.status_code,
            "body_preview": preview(json.dumps(j, ensure_ascii=False)),
            "raw": j,
        }

    return {
        "ok": True,
        "intent": intent,
        "entity": entity,
        "score": score,
        "raw": j,
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diferenças de roteamento contra golden set"
    )
    parser.add_argument(
        "--api-url",
        default=API_DEFAULT,
        help="URL base da API (/ask). Default: env API_URL ou http://localhost:8000",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=TIMEOUT_DEFAULT,
        help=f"Timeout em segundos para /ask. Default: {TIMEOUT_DEFAULT}",
    )
    parser.add_argument(
        "--disable-rag",
        action="store_true",
        default=DISABLE_RAG_DEFAULT,
        help="Força modo routing-only (ou usa QUALITY_DISABLE_RAG=1)",
    )
    parser.add_argument(
        "--enable-rag",
        action="store_false",
        dest="disable_rag",
        help="Desativa o modo routing-only mesmo se QUALITY_DISABLE_RAG=1",
    )
    return parser.parse_args(argv)


def main():
    args = parse_args()
    data = json.loads(SRC.read_text(encoding="utf-8"))
    try:
        samples, _, _, _ = validate_routing_payload_contract(data)
    except RoutingPayloadValidationError as exc:
        raise RuntimeError(f"payload de routing inválido em {SRC}: {exc}") from exc
    misses = []
    errors = []
    for i, s in enumerate(samples, start=1):
        result = ask(
            s["question"],
            api_url=args.api_url,
            timeout=args.timeout,
            disable_rag=args.disable_rag,
        )
        if not result.get("ok"):
            errors.append(
                {
                    "idx": i,
                    "question": s["question"],
                    "expected_intent": s["expected_intent"],
                    "expected_entity": s["expected_entity"],
                    "error_kind": result.get("error_kind"),
                    "error_message": result.get("error_message"),
                    "status_code": result.get("status_code"),
                    "body_preview": result.get("body_preview"),
                }
            )
            continue

        intent = result["intent"]
        entity = result["entity"]
        score = result.get("score")
        resp = result["raw"]
        ok = (intent == s["expected_intent"]) and (entity == s["expected_entity"])
        if not ok:
            misses.append(
                {
                    "idx": i,
                    "question": s["question"],
                    "expected_intent": s["expected_intent"],
                    "expected_entity": s["expected_entity"],
                    "got_intent": intent,
                    "got_entity": entity,
                    "score": score,
                    "status": resp.get("status", {}),
                    "normalized": pick(
                        resp, ("meta", "planner", "normalized"), default=None
                    ),
                    "tokens": pick(resp, ("meta", "planner", "tokens"), default=None),
                    "intent_scores": pick(
                        resp, ("meta", "planner", "intent_scores"), default=None
                    ),
                    "thresholds": pick(
                        resp,
                        ("meta", "planner", "explain", "scoring", "thresholds_applied"),
                        default=None,
                    ),
                }
            )
    errors_summary: Dict[str, int] = {}
    for err in errors:
        errors_summary[err["error_kind"]] = errors_summary.get(err["error_kind"], 0) + 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "api_url": args.api_url,
        "totals": {
            "samples": len(samples),
            "misses": len(misses),
            "errors": len(errors),
        },
        "errors_summary": errors_summary,
        "misses": misses,
        "errors": errors,
    }

    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    if errors:
        summary_parts = [f"{k}={v}" for k, v in sorted(errors_summary.items())]
        summary = ", ".join(summary_parts) if summary_parts else "n/a"
        print(
            f"❌ Errors: {len(errors)} (por tipo {summary}). "
            f"Misses reais: {len(misses)}. Arquivo salvo em {OUT}."
        )
        return 2

    if misses:
        print(f"❌ Misses: {len(misses)}  → salvos em {OUT}")
        for m in misses:
            print(
                f"[#{m['idx']:03d}] {m['question']}\n"
                f"    exp : {m['expected_intent']} / {m['expected_entity']}\n"
                f"    got : {m['got_intent']} / {m['got_entity']} (score={m['score']})\n"
            )
        return 1

    print("✅ Sem misses.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
