from fastapi import FastAPI

from app.api.ask import router as ask_router
from app.api.debug import router as debug_router
from app.api.health import router as health_router
from app.api.ops.analytics import router as ops_analytics_router
from app.api.ops.cache import router as ops_cache_router
from app.api.ops.metrics import router as ops_metrics_router
from app.api.ops.quality import router as ops_quality_router
from app.common.http import metrics_middleware


def get_app() -> FastAPI:
    app = FastAPI(title="Araquem API (Dev)")
    app.middleware("http")(metrics_middleware)
    app.include_router(health_router)
    app.include_router(debug_router)
    app.include_router(ask_router)
    app.include_router(ops_cache_router)
    app.include_router(ops_analytics_router)
    app.include_router(ops_metrics_router)
    app.include_router(ops_quality_router)
    return app
