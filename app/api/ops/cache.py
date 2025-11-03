# app/api/ops/cache.py
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.context import cache, policies

router = APIRouter()


class BustPayload(BaseModel):
    entity: str
    identifiers: Dict[str, Any] = Field(default_factory=dict)


@router.post("/ops/cache/bust")
def cache_bust(payload: BustPayload, x_ops_token: Optional[str] = Header(default=None)):
    token_env = os.getenv("CACHE_OPS_TOKEN", "")
    if not token_env or (x_ops_token or "") != token_env:
        return JSONResponse({"error": "forbidden"}, status_code=403)

    entity = payload.entity
    identifiers = payload.identifiers or {}
    policy = policies.get(entity)
    if not (entity and policy):
        return JSONResponse(
            {"error": "invalid entity or missing policy"}, status_code=400
        )

    scope = str(policy.get("scope", "pub"))
    build_id = os.getenv("BUILD_ID", "dev")
    from app.cache.rt_cache import make_cache_key

    key = make_cache_key(build_id, scope, entity, identifiers)
    deleted = cache.delete(key)
    return {"deleted": int(deleted), "key": key}
