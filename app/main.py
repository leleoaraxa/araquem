# app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
import os, time
from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

from app.planner.planner import Planner
from app.orchestrator.routing import Orchestrator
from app.executor.pg import PgExecutor

REGISTRY = CollectorRegistry()
REQS = Counter("api_requests_total", "Total API requests", ["path", "method", "status"], registry=REGISTRY)
LAT = Histogram("api_request_latency_seconds", "Request latency", ["path", "method"], registry=REGISTRY)
ONTO_PATH = os.getenv("ONTOLOGY_PATH", "data/ontology/entity.yaml")
_planner = Planner(ONTO_PATH)
_executor = PgExecutor()
_orchestrator = Orchestrator(_planner, _executor)

app = FastAPI(title="Araquem API (Dev)")

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    LAT.labels(request.url.path, request.method).observe(time.perf_counter() - start)
    REQS.labels(request.url.path, request.method, str(response.status_code)).inc()
    return response

@app.get("/healthz")
def healthz():
    return {"status": "ok", "build_id": os.getenv("BUILD_ID", "dev"), "services": {"db": "unknown", "redis": "unknown"}}

@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@app.get("/debug/planner")
def debug_planner(q: str):
    """
    Inspeciona a decisão do planner.
    Ex.: /debug/planner?q=Qual%20o%20CNPJ%20do%20HGLG11
    """
    try:
        return _planner.explain(q)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# Guardrails: immutable payload contract for /ask (validation only for now)
from pydantic import BaseModel

class AskPayload(BaseModel):
    question: str
    conversation_id: str
    nickname: str
    client_id: str


@app.post("/ask")
def ask(payload: AskPayload):
    """
    M3 — Orquestração: planner → builder → executor → formatter
    """
    out = _orchestrator.route_question(payload.question)
    return JSONResponse(out)

