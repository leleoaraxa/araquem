# app/api/ops/context_clear.py
# -*- coding: utf-8 -*-

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.core.context import context_manager
from app.common.http import json_sanitize

router = APIRouter()


@router.post("/ops/context_clear")
def context_clear(
    client_id: str = Query(..., description="Client ID usado no /ask"),
    conversation_id: str = Query(..., description="Conversation ID usado no /ask"),
):
    """
    Limpa todo o contexto de uma conversa específica (client_id + conversation_id).

    - Não causa efeitos colaterais no fluxo do /ask.
    - Best-effort: mesmo que o backend não suporte delete, não quebra.
    - Guardrails v2.1.1 compliant: sem alterar a ontologia ou payloads.
    """
    try:
        # Tentativa de carregar os turns existentes (para exibir no retorno)
        before = context_manager.load_recent(client_id, conversation_id)
        before_count = len(before)

        # Estratégia minimalista:
        # Reescreve a lista como vazia, respeitando o contrato do backend.
        context_manager._backend.save(client_id, conversation_id, [])

        out = {
            "status": {"reason": "ok", "message": "context cleared"},
            "cleared": {
                "client_id": client_id,
                "conversation_id": conversation_id,
                "removed_turns": before_count,
            },
        }

        return JSONResponse(json_sanitize(out))

    except Exception as e:
        return JSONResponse(
            json_sanitize(
                {
                    "status": {"reason": "error", "message": str(e)},
                    "cleared": None,
                }
            ),
            status_code=500,
        )
