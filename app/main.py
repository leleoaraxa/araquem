# app/main.py

from fastapi import FastAPI, Request, Header, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry import trace
import os, time
import psycopg

from app.cache.rt_cache import RedisCache, CachePolicies, read_through
from app.planner.planner import Planner
from app.orchestrator.routing import Orchestrator
from app.executor.pg import PgExecutor
from app.observability.runtime import (
    load_config, init_tracing, init_metrics,
    init_planner_metrics, init_sql_metrics, init_cache_metrics
)

REGISTRY = CollectorRegistry()
REQS = Counter("sirios_requests_total", "Total API requests", ["path", "method", "status"], registry=REGISTRY)
LAT = Histogram("sirios_request_latency_seconds", "Request latency", ["path", "method"], registry=REGISTRY)
ONTO_PATH = os.getenv("ONTOLOGY_PATH", "data/ontology/entity.yaml")
CACHE_HITS = Counter("cache_hits_total", "Total cache hits", ["entity"], registry=REGISTRY)
CACHE_MISSES = Counter("cache_misses_total", "Total cache misses", ["entity"], registry=REGISTRY)
cfg = load_config()
init_tracing(service_name="api", cfg=cfg)
METRICS = init_metrics(cfg, registry=REGISTRY)
PLANNER_METRICS = init_planner_metrics(cfg, registry=REGISTRY)
SQL_METRICS = init_sql_metrics(cfg, registry=REGISTRY)
CACHE_METRICS = init_cache_metrics(cfg, registry=REGISTRY)

_cache = RedisCache(os.getenv("REDIS_URL", "redis://redis:6379/0"))
_policies = CachePolicies()
_planner = Planner(ONTO_PATH)
_executor = PgExecutor()
_orchestrator = Orchestrator(_planner, _executor, planner_metrics=PLANNER_METRICS)
_executor.bind_metrics(SQL_METRICS)
_cache.bind_metrics(CACHE_METRICS)

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
    build_id = os.getenv("BUILD_ID", "dev")
    # Redis
    try:
        redis_ok = _cache.ping()
    except Exception:
        redis_ok = False
    # Postgres
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

class BustPayload(BaseModel):
    entity: str
    identifiers: Dict[str, Any] = Field(default_factory=dict)


@app.post("/ops/cache/bust")
def cache_bust(payload: BustPayload, x_ops_token: Optional[str] = Header(default=None)):
    """
    Invalida uma chave de cache específica.
    Segurança simples por token: defina CACHE_OPS_TOKEN no ambiente.
    body esperado: {"entity": "...", "identifiers": {...}}
    """
    token_env = os.getenv("CACHE_OPS_TOKEN", "")
    if not token_env or (x_ops_token or "") != token_env:
        return JSONResponse({"error": "forbidden"}, status_code=403)

    entity = payload.entity
    identifiers = payload.identifiers or {}
    policy = _policies.get(entity)
    if not (entity and policy):
        return JSONResponse({"error": "invalid entity or missing policy"}, status_code=400)

    scope = str(policy.get("scope", "pub"))
    build_id = os.getenv("BUILD_ID", "dev")
    from app.cache.rt_cache import make_cache_key
    key = make_cache_key(build_id, scope, entity, identifiers)
    deleted = _cache.delete(key)
    return {"deleted": int(deleted), "key": key}

class AskPayload(BaseModel):
    question: str
    conversation_id: str
    nickname: str
    client_id: str


@app.post("/ask")
def ask(payload: AskPayload, explain: bool = Query(default=False)):
    """
    M4 — Cache read-through (Redis) por entidade, respeitando cache_policies.yaml.
    Chave: araquem:{build_id}:{scope}:{entity}:{hash(identifiers)}
    """
    t0 = time.perf_counter()

    # 1) Planejamento (YAML-driven) + M6.3: métrica de explain
    t_plan0 = time.perf_counter()
    plan = _planner.explain(payload.question)
    t_plan_dt = time.perf_counter() - t_plan0
    if explain and PLANNER_METRICS.get("explain_enabled") is not None:
        PLANNER_METRICS["explain_enabled"].inc()
    if explain and PLANNER_METRICS.get("explain_latency") is not None:
        PLANNER_METRICS["explain_latency"].observe(t_plan_dt)
    entity = plan["chosen"]["entity"]
    intent = plan["chosen"]["intent"]
    score = plan["chosen"]["score"]
    # M6.5 — outcomes básicos (ok/unroutable)
    if PLANNER_METRICS.get("routed_total") is not None:
        PLANNER_METRICS["routed_total"].labels(outcome="ok" if entity else "unroutable").inc()

    # M6.3: contagem simples de nós do explain (intents avaliadas)
    if explain and PLANNER_METRICS.get("explain_nodes") is not None:
        try:
            intents_count = len(plan.get("details", {}))
            PLANNER_METRICS["explain_nodes"].labels(node_kind="intent").inc(intents_count)
        except Exception:
            pass
    # M6.5 — observar gap top1-top2 quando explain=true
    if explain:
        top2_gap = float(((plan.get("explain") or {}).get("scoring") or {}).get("intent_top2_gap") or 0.0)
        if PLANNER_METRICS.get("top2_gap_histogram") is not None:
            PLANNER_METRICS["top2_gap_histogram"].observe(top2_gap)
        if PLANNER_METRICS.get("quality_last_gap") is not None:
            PLANNER_METRICS["quality_last_gap"].set(top2_gap)

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
                # M6.4: bloco explain segue contrato (usar plan['explain'])
                "explain": (plan.get("explain") if explain else None),
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
            # M6.4: bloco explain seguindo contrato — opcional, só quando ?explain=true
            "explain": (plan.get("explain") if explain else None),
            "cache": {
                "hit": bool(rt.get("cached")),
                "key": rt.get("key"),
                "ttl": rt.get("ttl"),
            },
        },
    })



# ---------------------------------------------------------------------
# M6.5 — Quality & Confusion Telemetry endpoint (token-protected)
# ---------------------------------------------------------------------
class QualitySample(BaseModel):
    question: str
    expected_intent: str
    expected_entity: Optional[str] = None

class QualityPayload(BaseModel):
    samples: list[QualitySample]

@app.post("/ops/quality/push")
def quality_push(payload: QualityPayload, x_ops_token: Optional[str] = Header(default=None)):
    token_env = os.getenv("QUALITY_OPS_TOKEN", "")
    if not token_env or (x_ops_token or "") != token_env:
        return JSONResponse({"error": "forbidden"}, status_code=403)

    matched = 0
    missed = 0
    for s in payload.samples:
        plan = _planner.explain(s.question)
        predicted = (plan.get("chosen") or {}).get("intent")
        expected = s.expected_intent
        # counters hit/miss
        if PLANNER_METRICS.get("top1_match_total") is not None:
            PLANNER_METRICS["top1_match_total"].labels(result="hit" if predicted == expected else "miss").inc()
        # confusion matrix
        if PLANNER_METRICS.get("confusion_total") is not None and expected and predicted:
            PLANNER_METRICS["confusion_total"].labels(expected_intent=expected, predicted_intent=predicted).inc()
        # gap observation por amostra
        top2_gap = float(((plan.get("explain") or {}).get("scoring") or {}).get("intent_top2_gap") or 0.0)
        if PLANNER_METRICS.get("top2_gap_histogram") is not None:
            PLANNER_METRICS["top2_gap_histogram"].observe(top2_gap)
        if PLANNER_METRICS.get("quality_last_gap") is not None:
            PLANNER_METRICS["quality_last_gap"].set(top2_gap)
        # tally
        if predicted == expected:
            matched += 1
        else:
            missed += 1

    return {"accepted": len(payload.samples), "metrics": {"matched": matched, "missed": missed}}
