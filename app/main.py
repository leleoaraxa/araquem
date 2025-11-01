# app/main.py

from fastapi import FastAPI, Request, Header, Query, Body
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST  # export apenas
from opentelemetry import trace
import os, time
import psycopg
import math

from app.cache.rt_cache import RedisCache, CachePolicies, read_through
from app.planner.planner import Planner
from app.orchestrator.routing import Orchestrator
from app.executor.pg import PgExecutor
from app.observability.runtime import load_config, bootstrap, prom_query_instant
from app.observability.instrumentation import counter, histogram

ONTO_PATH = os.getenv("ONTOLOGY_PATH", "data/ontology/entity.yaml")
cfg = load_config()
# inicializa tracing (se habilitado) e injeta backend de métricas na facade
bootstrap(service_name="api", cfg=cfg)

_cache = RedisCache(os.getenv("REDIS_URL", "redis://redis:6379/0"))
_policies = CachePolicies()
_planner = Planner(ONTO_PATH)
_executor = PgExecutor()
_orchestrator = Orchestrator(_planner, _executor)

app = FastAPI(title="Araquem API (Dev)")


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Mede tempo e conta requisições HTTP (centralizado na facade)."""
    start = time.perf_counter()
    response = await call_next(request)
    dt = time.perf_counter() - start

    route = request.url.path
    method = request.method
    status = str(response.status_code)

    histogram("sirios_http_request_duration_seconds", dt, route=route, method=method)
    counter("sirios_http_requests_total", route=route, method=method, code=status)
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
    status = (
        "ok"
        if (db_ok and redis_ok)
        else ("degraded" if (db_ok or redis_ok) else "down")
    )
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
    # Exporta o default registry (sem criar métricas aqui)
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health/redis")
def health_redis():
    ok = _cache.ping()
    return {"status": "ok" if ok else "degraded"}


@app.get("/debug/planner")
def debug_planner(q: str):
    """Inspeciona a decisão do planner."""
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
    Invalida uma chave de cache específica (token em CACHE_OPS_TOKEN).
    body: {"entity": "...", "identifiers": {...}}
    """
    token_env = os.getenv("CACHE_OPS_TOKEN", "")
    if not token_env or (x_ops_token or "") != token_env:
        return JSONResponse({"error": "forbidden"}, status_code=403)

    entity = payload.entity
    identifiers = payload.identifiers or {}
    policy = _policies.get(entity)
    if not (entity and policy):
        return JSONResponse(
            {"error": "invalid entity or missing policy"}, status_code=400
        )

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

    # 1) Planejamento (YAML-driven) + Explain (contadores centralizados)
    t_plan0 = time.perf_counter()
    plan = _planner.explain(payload.question)
    t_plan_dt = time.perf_counter() - t_plan0

    if explain:
        counter("sirios_planner_explain_enabled_total")
        histogram("sirios_planner_explain_latency_seconds", float(t_plan_dt))

    entity = plan["chosen"]["entity"]
    intent = plan["chosen"]["intent"]
    score = plan["chosen"]["score"]

    # M6.5 — outcomes básicos (ok/unroutable)
    counter("sirios_planner_routed_total", outcome=("ok" if entity else "unroutable"))

    # M6.5 — observar gap top1-top2 quando explain=true
    if explain:
        top2_gap = float(
            ((plan.get("explain") or {}).get("scoring") or {}).get("intent_top2_gap")
            or 0.0
        )
        histogram("sirios_planner_top2_gap_histogram", top2_gap)
        # gauge 'quality_last_gap' fica derivado no painel

    if not entity:
        return JSONResponse(
            {
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
                    "explain": (plan.get("explain") if explain else None),
                },
            }
        )

    # 2) Identificadores na camada de ENTRADA (sem heurística)
    identifiers = _orchestrator.extract_identifiers(payload.question)

    # 3) Cache read-through
    def _fetch():
        # Orquestra pipeline completo e retorna apenas 'results' (idempotente p/ chave)
        out = _orchestrator.route_question(payload.question)
        return out["results"]

    rt = read_through(_cache, _policies, entity, identifiers, _fetch)
    # padroniza em 'sirios_cache_ops_total' (get/hit|miss)
    counter(
        "sirios_cache_ops_total",
        op="get",
        outcome=("hit" if rt.get("cached") else "miss"),
    )

    results = rt.get("value") or {}
    result_key = next(iter(results.keys()), None)
    rows = (
        results.get(result_key, []) if isinstance(results.get(result_key), list) else []
    )
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    return JSONResponse(
        {
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
                "explain": (plan.get("explain") if explain else None),
                "cache": {
                    "hit": bool(rt.get("cached")),
                    "key": rt.get("key"),
                    "ttl": rt.get("ttl"),
                },
            },
        }
    )


# ---------------------------------------------------------------------
# M6.5 — Quality & Confusion Telemetry endpoint (token-protected)
# ---------------------------------------------------------------------
class QualitySample(BaseModel):
    question: str
    expected_intent: str
    expected_entity: Optional[str] = None


@app.post("/ops/quality/push")
def quality_push(
    payload: Dict[str, Any] = Body(...),
    x_ops_token: Optional[str] = Header(default=None),
):
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
            chosen = plan.get("chosen") or {}
            predicted = chosen.get("intent")
            entity = chosen.get("entity")  # outcome de roteamento

            # hit/miss
            counter(
                "sirios_planner_top1_match_total",
                result=("hit" if predicted == expected else "miss"),
            )

            # confusion matrix
            if expected and predicted:
                counter(
                    "sirios_planner_confusion_total",
                    expected_intent=str(expected),
                    predicted_intent=str(predicted),
                )

            # routed outcome (ok | unroutable)
            counter(
                "sirios_planner_routed_total",
                outcome=("ok" if entity else "unroutable"),
            )

            # top2 gap
            top2_gap = float(
                ((plan.get("explain") or {}).get("scoring") or {}).get(
                    "intent_top2_gap"
                )
                or 0.0
            )
            histogram("sirios_planner_top2_gap_histogram", top2_gap)

            matched += int(predicted == expected)
            missed += int(predicted != expected)
        return {
            "accepted": len(samples_raw),
            "metrics": {"matched": matched, "missed": missed},
        }

    # ----------------------------
    # Tipo: projection
    # ----------------------------
    if ptype == "projection":
        entity = payload.get("entity")
        result_key = payload.get("result_key")
        must_have = payload.get("must_have_columns") or []
        samples_raw: List[Dict[str, Any]] = payload.get("samples", [])
        if not (entity and result_key and isinstance(must_have, list)):
            return JSONResponse(
                {"error": "invalid projection payload"}, status_code=400
            )

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
                counter(
                    "sirios_planner_projection_total", outcome="ok", entity=str(entity)
                )
            else:
                fail += 1
                counter(
                    "sirios_planner_projection_total",
                    outcome="fail",
                    entity=str(entity),
                )
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
        return JSONResponse(
            {"error": f"failed to load thresholds: {e}"}, status_code=500
        )

    qg = (thr.get("quality_gates") or {}).get("thresholds") or {}
    min_top1_acc = float(qg.get("min_top1_accuracy", 0.0))
    min_routed_rt = float(qg.get("min_routed_rate", 0.0))
    min_top2_gap = float(qg.get("min_top2_gap", 0.0))
    max_miss_abs = float(qg.get("max_misses_absolute", 0.0))
    max_miss_ratio = float(qg.get("max_misses_ratio", 1.0))

    # PromQL (instant)
    top1_hit = prom_query_instant('sum(sirios_planner_top1_match_total{result="hit"})')
    top1_total = prom_query_instant("sum(sirios_planner_top1_match_total)")
    routed_ok = prom_query_instant(
        'sum(sirios_planner_routed_total{outcome!="unroutable"})'
    )
    routed_all = prom_query_instant("sum(sirios_planner_routed_total)")
    gap_p50 = prom_query_instant(
        "histogram_quantile(0.50, sum(rate(sirios_planner_top2_gap_histogram_bucket[5m])) by (le))"
    )
    proj_ok = prom_query_instant('sum(sirios_planner_projection_total{outcome="ok"})')
    proj_total = prom_query_instant("sum(sirios_planner_projection_total)")
    miss_abs = prom_query_instant('sum(sirios_planner_top1_match_total{result="miss"})')

    # Safeguards e coerção robusta
    def _to_float(x) -> float:
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
    top1_acc = _ratio(top1_hit, top1_total)
    routed_rt = _ratio(routed_ok, routed_all)
    proj_pass = _ratio(proj_ok, proj_total)
    miss_abs_v = _to_float(miss_abs)
    miss_ratio = _ratio(miss_abs, top1_total)
    gap_p50_v = _to_float(gap_p50)

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
