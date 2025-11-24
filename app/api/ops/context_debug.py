# app/api/ops/context_debug.py
# -*- coding: utf-8 -*-

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.core.context import context_manager
from app.common.http import json_sanitize


router = APIRouter()


@router.get("/ops/context_debug")
def context_debug(
    client_id: str = Query(..., description="Client ID usado no /ask"),
    conversation_id: str = Query(..., description="Conversation ID usado no /ask"),
):
    """
    Endpoint de inspeção do contexto conversacional.

    Objetivo:
        - Mostrar turns brutos armazenados
        - Mostrar turns normalizados (wire format)
        - Mostrar políticas aplicadas (planner/narrator)
        - NÃO altera o payload nem executa planner/orchestrator
        - Guardrails v2.1.1 compliant

    Uso:
        GET /ops/context_debug?client_id=123&conversation_id=abc
    """

    try:
        enabled = context_manager.enabled
        planner_policy = context_manager.planner_policy
        narrator_policy = context_manager.narrator_policy

        turns = context_manager.load_recent(client_id, conversation_id)
        wire = context_manager.to_wire(turns) if turns else []

        out = {
            "status": {"reason": "ok", "message": "ok"},
            "context": {
                "enabled": enabled,
                "planner_policy": planner_policy,
                "narrator_policy": narrator_policy,
                "turns_count": len(turns),
                "turns": [
                    {
                        "role": t.role,
                        "content": t.content,
                        "created_at": t.created_at,
                        "meta": t.meta,
                    }
                    for t in turns
                ],
                "turns_wire": wire,
            },
        }

        return JSONResponse(json_sanitize(out))

    except Exception as e:
        return JSONResponse(
            json_sanitize(
                {
                    "status": {"reason": "error", "message": str(e)},
                    "context": None,
                }
            ),
            status_code=500,
        )
