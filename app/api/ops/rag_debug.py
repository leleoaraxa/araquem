# app/api/ops/rag_debug.py
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api import ask as ask_api
from app.common.http import json_sanitize
from app.core.context import orchestrator
from app.presenter.presenter import present
from app.rag.context_builder import get_rag_policy

router = APIRouter(prefix="/ops/rag_debug", tags=["ops"])


class RagDebugPayload(BaseModel):
    question: str
    conversation_id: str = "rag-debug"
    nickname: str = "rag-debug"
    client_id: str = "ops"
    disable_rag: bool = False


@router.post("")
def rag_debug(payload: RagDebugPayload):
    orchestration = orchestrator.route_question(payload.question)
    status = orchestration.get("status") or {}
    results = orchestration.get("results") or {}
    meta: Dict[str, Any] = orchestration.get("meta") or {}

    if status.get("reason") != "ok":
        meta_out = dict(meta)
        meta_out["narrator"] = None
        return JSONResponse(
            json_sanitize(
                {
                    "status": status,
                    "results": results,
                    "meta": meta_out,
                    "answer": "",
                }
            )
        )

    plan = meta.get("planner") or {}
    aggregates = meta.get("aggregates") or {}
    identifiers = orchestrator.extract_identifiers(payload.question)

    compute_mode_meta = None
    compute_block = meta.get("compute") if isinstance(meta, dict) else None
    if isinstance(compute_block, dict):
        raw_mode = compute_block.get("mode")
        if isinstance(raw_mode, str) and raw_mode.strip().lower() in {
            "concept",
            "data",
            "default",
        }:
            compute_mode_meta = raw_mode.strip().lower()

    rag_policy_snapshot = get_rag_policy(
        entity=plan.get("entity") or plan.get("chosen", {}).get("entity"),
        intent=plan.get("intent") or plan.get("chosen", {}).get("intent"),
        compute_mode=compute_mode_meta,
        has_ticker=bool(identifiers.get("ticker")),
        meta=meta,
        policy=None,
    )

    narrator_meta: Dict[str, Any] = {}
    rag_ctx = meta.get("rag")
    if isinstance(rag_ctx, dict):
        rag_with_policy = dict(rag_ctx)
        rag_with_policy.setdefault("policy", rag_policy_snapshot)
        narrator_meta["rag"] = rag_with_policy

    if payload.disable_rag:
        meta["rag_debug_disable"] = True
        narrator_meta["rag_debug_disable"] = True

    presenter_result = present(
        question=payload.question,
        plan=plan,
        orchestrator_results=results,
        identifiers=identifiers,
        aggregates=aggregates if isinstance(aggregates, dict) else {},
        narrator=ask_api._NARR,
        narrator_meta=narrator_meta,
        explain=False,
    )

    meta_out = dict(meta)
    meta_out["narrator"] = presenter_result.narrator_meta
    meta_out["rag_policy"] = rag_policy_snapshot

    payload_out = {
        "status": status,
        "results": results,
        "meta": meta_out,
        "answer": presenter_result.answer,
    }

    return JSONResponse(json_sanitize(payload_out))
