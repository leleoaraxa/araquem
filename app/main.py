# app/main.py

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
import os, time
from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry import trace

from app.cache.rt_cache import RedisCache, CachePolicies, read_through
from app.planner.planner import Planner
from app.orchestrator.routing import Orchestrator
from app.executor.pg import PgExecutor
from app.observability.runtime import load_config, init_tracing, init_metrics

REGISTRY = CollectorRegistry()
REQS = Counter("api_requests_total", "Total API requests", ["path", "method", "status"], registry=REGISTRY)
LAT = Histogram("api_request_latency_seconds", "Request latency", ["path", "method"], registry=REGISTRY)
ONTO_PATH = os.getenv("ONTOLOGY_PATH", "data/ontology/entity.yaml")
CACHE_HITS = Counter("cache_hits_total", "Total cache hits", ["entity"], registry=REGISTRY)
CACHE_MISSES = Counter("cache_misses_total", "Total cache misses", ["entity"], registry=REGISTRY)
cfg = load_config()
init_tracing(service_name="api", cfg=cfg)
METRICS = init_metrics(cfg)

_cache = RedisCache(os.getenv("REDIS_URL", "redis://redis:6379/0"))
_policies = CachePolicies()
_planner = Planner(ONTO_PATH)
_executor = PgExecutor()
_orchestrator = Orchestrator(_planner, _executor)

app = FastAPI(title="Araquem API (Dev)")

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Mede tempo e conta requisições HTTP usando métricas configuradas via YAML."""
    start = time.perf_counter()
    response = await call_next(request)
    dt = time.perf_counter() - start

    route = request.url.path
    method = request.method
    status = str(response.status_code)

    if METRICS["http_hist"] is not None:
        METRICS["http_hist"].labels(route=route, method=method).observe(dt)
    if METRICS["http_counter"] is not None:
        METRICS["http_counter"].labels(route=route, method=method, code=status).inc()

    return response

@app.get("/healthz")
def healthz():
    return {"status": "ok", "build_id": os.getenv("BUILD_ID", "dev"), "services": {"db": "unknown", "redis": "unknown"}}

@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)

@app.get("/health/redis")
def health_redis():
    ok = _cache.ping()
    return {"status": "ok" if ok else "degraded"}

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

@app.get("/_debug/trace")
def debug_trace():
    tr = trace.get_tracer("api.debug")
    with tr.start_as_current_span("manual_debug_span"):
        return {"ok": True}

@app.post("/ops/cache/bust")
def cache_bust(body: dict, request: Request):
    """
    Invalida uma chave de cache específica.
    Segurança simples por token: defina CACHE_OPS_TOKEN no ambiente.
    body esperado: {"entity": "...", "identifiers": {...}}
    """
    token_env = os.getenv("CACHE_OPS_TOKEN", "")
    token_req = request.headers.get("X-OPS-TOKEN", "")
    if not token_env or token_req != token_env:
        return JSONResponse({"error": "forbidden"}, status_code=403)

    entity = (body or {}).get("entity")
    identifiers = (body or {}).get("identifiers") or {}
    policy = _policies.get(entity)
    if not (entity and policy):
        return JSONResponse({"error": "invalid entity or missing policy"}, status_code=400)

    scope = str(policy.get("scope", "pub"))
    build_id = os.getenv("BUILD_ID", "dev")
    from app.cache.rt_cache import make_cache_key
    key = make_cache_key(build_id, scope, entity, identifiers)
    deleted = _cache.delete(key)
    return {"deleted": int(deleted), "key": key}

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
    M4 — Cache read-through (Redis) por entidade, respeitando cache_policies.yaml.
    Chave: araquem:{build_id}:{scope}:{entity}:{hash(identifiers)}
    """
    t0 = time.perf_counter()

    # 1) Planejamento (YAML-driven)
    plan = _planner.explain(payload.question)
    entity = plan["chosen"]["entity"]
    intent = plan["chosen"]["intent"]
    score = plan["chosen"]["score"]

    if not entity:
        return JSONResponse({
            "status": {"reason": "unroutable", "message": "No entity matched"},
            "results": {},
            "meta": {
                "planner": plan,
                "result_key": None,
                "planner_intent": intent,
                "planner_entity": entity,
                "planner_score": score,
                "rows_total": 0,
                "elapsed_ms": int((time.perf_counter() - t0) * 1000),
            },
        })

    # 2) Identificadores na camada de ENTRADA (sem heurística)
    identifiers = _orchestrator.extract_identifiers(payload.question)

    # 3) Cache read-through
    def _fetch():
        # Orquestra pipeline completo e retorna apenas 'results' (idempotente p/ chave)
        out = _orchestrator.route_question(payload.question)
        return out["results"]

    rt = read_through(_cache, _policies, entity, identifiers, _fetch)
    if rt.get("cached"):
        CACHE_HITS.labels(entity).inc()
    else:
        CACHE_MISSES.labels(entity).inc()

    results = rt.get("value") or {}
    result_key = next(iter(results.keys()), None)
    rows = results.get(result_key, []) if isinstance(results.get(result_key), list) else []
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    return JSONResponse({
        "status": {"reason": "ok", "message": "ok"},
        "results": results,
        "meta": {
            "planner": plan,
            "result_key": result_key,
            "planner_intent": intent,
            "planner_entity": entity,
            "planner_score": score,
            "rows_total": len(rows),
            "elapsed_ms": elapsed_ms,
            "cache": {
                "hit": bool(rt.get("cached")),
                "key": rt.get("key"),
                "ttl": rt.get("ttl"),
            },
        },
    })
