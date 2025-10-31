# app/main.py

from fastapi import FastAPI, Request, Header, Query, Body
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry import trace
import os, time
import psycopg
import math

from app.cache.rt_cache import RedisCache, CachePolicies, read_through
from app.planner.planner import Planner
from app.orchestrator.routing import Orchestrator
from app.executor.pg import PgExecutor
from app.observability.runtime import (
    load_config, init_tracing, init_metrics,
    init_planner_metrics, init_sql_metrics, init_cache_metrics,
    prom_query_instant
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

@app.post("/ops/quality/push")
def quality_push(payload: Dict[str, Any] = Body(...), x_ops_token: Optional[str] = Header(default=None)):
    token_env = os.getenv("QUALITY_OPS_TOKEN", "")
    if not token_env or (x_ops_token or "") != token_env:
        return JSONResponse({"error": "forbidden"}, status_code=403)

    ptype = (payload.get("type") or "routing").strip().lower()
    # ----------------------------
    # Tipo: routing (default)
    # ----------------------------
    if ptype == "routing":
        samples_raw: List[Dict[str, Any]] = payload.get("samples", [])
        matched = 0
        missed = 0
        for s in samples_raw:
            q = s.get("question") or ""
            expected = s.get("expected_intent") or ""
            plan = _planner.explain(q)
            predicted = (plan.get("chosen") or {}).get("intent")
            # counters hit/miss
            if PLANNER_METRICS.get("top1_match_total") is not None:
                PLANNER_METRICS["top1_match_total"].labels(result="hit" if predicted == expected else "miss").inc()
            # confusion matrix
            if PLANNER_METRICS.get("confusion_total") is not None and expected and predicted:
                PLANNER_METRICS["confusion_total"].labels(expected_intent=expected, predicted_intent=predicted).inc()
            # top2 gap
            top2_gap = float(((plan.get("explain") or {}).get("scoring") or {}).get("intent_top2_gap") or 0.0)
            if PLANNER_METRICS.get("top2_gap_histogram") is not None:
                PLANNER_METRICS["top2_gap_histogram"].observe(top2_gap)
            if PLANNER_METRICS.get("quality_last_gap") is not None:
                PLANNER_METRICS["quality_last_gap"].set(top2_gap)
            matched += int(predicted == expected)
            missed  += int(predicted != expected)
        return {"accepted": len(samples_raw), "metrics": {"matched": matched, "missed": missed}}

    # ----------------------------
    # Tipo: projection
    # ----------------------------
    if ptype == "projection":
        entity = payload.get("entity")
        result_key = payload.get("result_key")
        must_have = payload.get("must_have_columns") or []
        samples_raw: List[Dict[str, Any]] = payload.get("samples", [])
        if not (entity and result_key and isinstance(must_have, list)):
            return JSONResponse({"error": "invalid projection payload"}, status_code=400)

        ok = fail = 0
        for s in samples_raw:
            q = s.get("question") or ""
            # Executa pipeline normal via orchestrator
            out = _orchestrator.route_question(q)
            results = out.get("results") or {}
            rows = results.get(result_key) or []
            passed = False
            if isinstance(rows, list) and rows:
                first = rows[0]
                if isinstance(first, dict):
                    passed = all(col in first.keys() for col in must_have)
            if passed:
                ok += 1
                if PLANNER_METRICS.get("projection_total") is not None:
                    PLANNER_METRICS["projection_total"].labels(outcome="ok", entity=entity).inc()
            else:
                fail += 1
                if PLANNER_METRICS.get("projection_total") is not None:
                    PLANNER_METRICS["projection_total"].labels(outcome="fail", entity=entity).inc()
        return {"accepted": len(samples_raw), "metrics": {"ok": ok, "fail": fail}}

    return JSONResponse({"error": f"unsupported type '{ptype}'"}, status_code=400)


# ---------------------------------------------------------------------
# M6.7 — Quality Report (compara métricas × thresholds do YAML)
# ---------------------------------------------------------------------
@app.get("/ops/quality/report")
def quality_report():
    # Carrega thresholds unificado
    thr_path = os.getenv("PLANNER_THRESHOLDS_PATH", "data/ops/planner_thresholds.yaml")
    try:
        import yaml
        with open(thr_path, "r", encoding="utf-8") as f:
            thr = yaml.safe_load(f) or {}
    except Exception as e:
        return JSONResponse({"error": f"failed to load thresholds: {e}"}, status_code=500)

    qg = ((thr.get("quality_gates") or {}).get("thresholds") or {})
    min_top1_acc  = float(qg.get("min_top1_accuracy", 0.0))
    min_routed_rt = float(qg.get("min_routed_rate", 0.0))
    min_top2_gap  = float(qg.get("min_top2_gap", 0.0))
    max_miss_abs  = float(qg.get("max_misses_absolute", 0.0))
    max_miss_ratio= float(qg.get("max_misses_ratio", 1.0))

    # PromQL (instant)
    top1_hit   = prom_query_instant('sum(sirios_planner_top1_match_total{result="hit"})')
    top1_total = prom_query_instant('sum(sirios_planner_top1_match_total)')
    routed_ok  = prom_query_instant('sum(sirios_planner_routed_total{outcome!="unroutable"})')
    routed_all = prom_query_instant('sum(sirios_planner_routed_total)')
    gap_p50    = prom_query_instant('histogram_quantile(0.50, sum(rate(sirios_planner_top2_gap_histogram_bucket[5m])) by (le))')
    proj_ok    = prom_query_instant('sum(sirios_planner_projection_total{outcome="ok"})')
    proj_total = prom_query_instant('sum(sirios_planner_projection_total)')
    miss_abs   = prom_query_instant('sum(sirios_planner_top1_match_total{result="miss"})')

    # Safeguards e coerção robusta
    def _to_float(x) -> float:
        """Converte qualquer formato Prometheus (float, int, dict com data.result[0].value[1]) em float seguro."""
        if isinstance(x, (int, float)):
            return float(x)
        if isinstance(x, dict):
            try:
                val = (x.get("data", {}).get("result") or [{}])[0].get("value")
                if isinstance(val, list) and len(val) == 2:
                    return float(val[1])
            except Exception:
                pass
            return 0.0
        try:
            return float(str(x))
        except Exception:
            return 0.0

    def _ratio(num, den) -> float:
        n, d = _to_float(num), _to_float(den)
        return (n / d) if d > 0 else 0.0

    # Normalizações coerentes
    top1_acc   = _ratio(top1_hit, top1_total)
    routed_rt  = _ratio(routed_ok, routed_all)
    proj_pass  = _ratio(proj_ok, proj_total)
    miss_abs_v = _to_float(miss_abs)
    miss_ratio = _ratio(miss_abs, top1_total)
    gap_p50_v  = _to_float(gap_p50)

    # Checagem de thresholds
    violations: List[str] = []
    if top1_acc < min_top1_acc:
        violations.append(f"top1_accuracy {top1_acc:.3f} < min {min_top1_acc:.3f}")
    if routed_rt < min_routed_rt:
        violations.append(f"routed_rate {routed_rt:.3f} < min {min_routed_rt:.3f}")
    if gap_p50_v < min_top2_gap:
        violations.append(f"top2_gap_p50 {gap_p50_v:.3f} < min {min_top2_gap:.3f}")
    if miss_abs_v > max_miss_abs:
        violations.append(f"misses_abs {miss_abs_v:.0f} > max {max_miss_abs:.0f}")
    if miss_ratio > max_miss_ratio:
        violations.append(f"misses_ratio {miss_ratio:.3f} > max {max_miss_ratio:.3f}")

    status = "pass" if not violations else "fail"

# Sanitiza NaN e infinitos antes de serializar
    def _sanitize(v: float) -> float:
        if not isinstance(v, (int, float)):
            return 0.0
        if math.isnan(v) or math.isinf(v):
            return 0.0
        return round(float(v), 6)

    metrics = {
        "top1_accuracy": _sanitize(top1_acc),
        "routed_rate": _sanitize(routed_rt),
        "top2_gap_p50": _sanitize(gap_p50_v),
        "projection_pass": _sanitize(proj_pass),
        "misses_abs": _sanitize(miss_abs_v),
        "misses_ratio": _sanitize(miss_ratio),
    }

    return {
        "status": status,
        "metrics": metrics,
        "thresholds": qg,
        "violations": violations,
    }
