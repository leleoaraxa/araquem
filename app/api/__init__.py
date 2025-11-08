# app/api/__init__.py
from fastapi import FastAPI

from app.api.ask import router as ask_router
from app.api.debug import router as debug_router
from app.api.health import router as health_router
from app.api.ops.analytics import router as ops_analytics_router
from app.api.ops.cache import router as ops_cache_router
from app.api.ops.metrics import router as ops_metrics_router
from app.api.ops.quality import router as ops_quality_router
from app.common.http import metrics_middleware
from app.api.ops.rag import router as ops_rag_router

from app.observability.runtime import (
    load_config,
    bootstrap,
    init_metrics,
    init_cache_metrics,
    init_planner_metrics,
    init_sql_metrics,
)


def get_app() -> FastAPI:

    cfg = load_config()
    bootstrap(service_name="api", cfg=cfg)
    init_metrics(cfg)
    init_cache_metrics(cfg)
    init_planner_metrics(cfg)
    init_sql_metrics(cfg)

    app = FastAPI(title="Araquem API (Dev)")
    app.middleware("http")(metrics_middleware)

    app.include_router(health_router)
    app.include_router(debug_router)
    app.include_router(ask_router)
    app.include_router(ops_cache_router)
    app.include_router(ops_analytics_router)
    app.include_router(ops_metrics_router)
    app.include_router(ops_quality_router)
    app.include_router(ops_rag_router)
    return app
