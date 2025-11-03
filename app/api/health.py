import os

import psycopg
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.core.context import cache
from app.observability.runtime import render_prometheus_latest

router = APIRouter()


@router.get("/healthz")
def healthz():
    build_id = os.getenv("BUILD_ID", "dev")
    try:
        redis_ok = cache.ping()
    except Exception:
        redis_ok = False
    db_ok = False
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        try:
            with psycopg.connect(dsn, connect_timeout=2) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    _ = cur.fetchone()
                    db_ok = True
        except Exception:
            db_ok = False
    status = "ok" if (db_ok and redis_ok) else ("degraded" if (db_ok or redis_ok) else "down")
    return {
        "status": status,
        "build_id": build_id,
        "services": {
            "db": "ok" if db_ok else "down",
            "redis": "ok" if redis_ok else "down",
        },
    }


@router.get("/metrics")
def metrics():
    payload, media_type = render_prometheus_latest()
    return PlainTextResponse(payload, media_type=media_type)


@router.get("/health/redis")
def health_redis():
    ok = cache.ping()
    return {"status": "ok" if ok else "degraded"}
