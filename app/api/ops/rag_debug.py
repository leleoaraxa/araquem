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

    narrator_meta: Dict[str, Any] = {}
    rag_ctx = meta.get("rag")
    if isinstance(rag_ctx, dict):
        narrator_meta["rag"] = rag_ctx

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

    payload_out = {
        "status": status,
        "results": results,
        "meta": meta_out,
        "answer": presenter_result.answer,
    }

    return JSONResponse(json_sanitize(payload_out))
