# app/api/ask.py
import json
import os
import time
from decimal import Decimal
from typing import Optional, Dict, Any

import psycopg
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.analytics.explain import explain as _explain_analytics
from app.cache.rt_cache import read_through
from app.common.http import json_sanitize, make_request_id
from app.core.context import cache, orchestrator, planner, policies
from app.observability.metrics import (
    emit_counter as counter,
    emit_histogram as histogram,
)
from app.planner.param_inference import infer_params

# ainda importamos responder/formatter aqui para retrocompatibilidade
# (o presenter usa esses módulos internamente)
from app.formatter.rows import render_rows_template
from app.responder import render_answer

# nova camada de apresentação (pós-formatter)
from app.presenter.presenter import present

# ─────────────────────────────────────────────────────────────────────────────
# Narrator (camada de apresentação M10) — totalmente opcional e sem regressão
# ─────────────────────────────────────────────────────────────────────────────
_NARRATOR_ENABLED = str(os.getenv("NARRATOR_ENABLED", "false")).lower() == "true"
_NARRATOR_SHADOW = str(os.getenv("NARRATOR_SHADOW", "false")).lower() == "true"
_NARRATOR_MODEL = os.getenv("NARRATOR_MODEL", "llama3.1:latest")

try:
    from app.narrator.narrator import Narrator  # arquivo novo (drop-in)

    # depois (deixe o Narrator ler do .env)
    _NARR: Optional[Narrator] = Narrator(model=_NARRATOR_MODEL)

except Exception:
    # Se o pacote do Narrator ainda não estiver presente, seguimos como hoje.
    _NARR = None
    _NARRATOR_ENABLED = False
    _NARRATOR_SHADOW = False

# ─────────────────────────────────────────────────────────────────────────────

router = APIRouter()


class AskPayload(BaseModel):
    question: str
    conversation_id: str
    nickname: str
    client_id: str


@router.post("/ask")
def ask(payload: AskPayload, explain: bool = Query(default=False)):
    t0 = time.perf_counter()
    request_id = make_request_id()

    t_plan0 = time.perf_counter()
    plan = planner.explain(payload.question)
    t_plan_dt = time.perf_counter() - t_plan0

    if explain:
        counter("sirios_planner_explain_enabled_total")
        histogram("sirios_planner_explain_latency_seconds", float(t_plan_dt))

    entity = plan["chosen"]["entity"]
    intent = plan["chosen"]["intent"]
    score = plan["chosen"]["score"]

    counter("sirios_planner_routed_total", outcome=("ok" if entity else "unroutable"))

    if explain:
        top2_gap = float(
            ((plan.get("explain") or {}).get("scoring") or {}).get("intent_top2_gap")
            or 0.0
        )
        histogram("sirios_planner_top2_gap_histogram", top2_gap)

    if not entity:
        elapsed_ms_unr = int((time.perf_counter() - t0) * 1000)

        explain_analytics_payload = None
        if explain:
            planner_output = {
                "route": {"intent": intent, "entity": entity, "view": None},
                "chosen": plan.get("chosen") or {},
            }
            metrics_snapshot = {
                "latency_ms": elapsed_ms_unr,
                "cache_hit": None,
                "route_source": "planner",
            }
            explain_analytics_payload = _explain_analytics(
                request_id=request_id,
                planner_output=planner_output,
                metrics=metrics_snapshot,
            )

        payload_out_unr = {
            "status": {"reason": "unroutable", "message": "No entity matched"},
            "results": {},
            "meta": {
                "planner": plan,
                "result_key": None,
                "planner_intent": intent,
                "planner_entity": entity,
                "planner_score": score,
                "rows_total": 0,
                "elapsed_ms": elapsed_ms_unr,
                "explain": (plan.get("explain") if explain else None),
                "explain_analytics": explain_analytics_payload if explain else None,
                "cache": {"hit": False, "key": None, "ttl": None},
            },
            "answer": "",
        }
        return JSONResponse(json_sanitize(payload_out_unr))

    identifiers = orchestrator.extract_identifiers(payload.question)

    try:
        agg_params = infer_params(
            question=payload.question,
            intent=intent,
            entity=entity,
            entity_yaml_path=f"data/entities/{entity}/entity.yaml",
            defaults_yaml_path="data/ops/param_inference.yaml",
        )
    except Exception:
        agg_params = {}

    def _fetch():
        return orchestrator.route_question(payload.question)

    policy = policies.get(entity) if policies else None
    strategy = str((policy or {}).get("strategy") or "read_through").lower()
    ttl_seconds = None
    if policy and "ttl_seconds" in policy:
        try:
            ttl_candidate = int(policy.get("ttl_seconds"))
        except (TypeError, ValueError):
            ttl_candidate = None
        if ttl_candidate and ttl_candidate > 0:
            ttl_seconds = ttl_candidate

    cache_identifiers = dict(identifiers)
    if isinstance(agg_params, dict):
        metric_key = agg_params.get("metric")
        window_norm = (
            orchestrator._normalize_metrics_window(agg_params) if metric_key else None
        )
        if metric_key and window_norm:
            window_info = orchestrator._split_window(window_norm)
            cache_identifiers.update(
                metric_key=metric_key,
                window_norm=window_norm,
                **window_info,
            )
    if strategy == "read_through" and ttl_seconds:
        rt = read_through(cache, policies, entity, cache_identifiers, _fetch)
        cache_outcome = "hit" if rt.get("cached") else "miss"
    else:
        value = _fetch()
        rt = {"cached": False, "value": value, "key": None, "ttl": ttl_seconds}
        cache_outcome = "miss"
    counter("sirios_cache_ops_total", op="get", outcome=cache_outcome)

    orchestration_raw = rt.get("value")
    if isinstance(orchestration_raw, dict) and "results" in orchestration_raw:
        orchestration = orchestration_raw
    else:
        legacy_results = (
            orchestration_raw if isinstance(orchestration_raw, dict) else {}
        )
        orchestration = {
            "status": {"reason": "ok", "message": "ok"},
            "results": legacy_results,
            "meta": {},
        }

    results = orchestration.get("results") or {}
    meta = orchestration.get("meta") or {}
    result_key = meta.get("result_key") or next(iter(results.keys()), None)
    rows = (
        results.get(result_key, []) if isinstance(results.get(result_key), list) else []
    )
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    # -------------------------------
    # Camada de apresentação (Presenter)
    # -------------------------------
    presenter_result = present(
        question=payload.question,
        plan=plan,
        orchestrator_results=results,
        meta=meta,
        identifiers=identifiers,
        aggregates=agg_params if isinstance(agg_params, dict) else {},
        narrator=_NARR,
        narrator_flags={
            "enabled": _NARRATOR_ENABLED,
            "shadow": _NARRATOR_SHADOW,
            "model": _NARRATOR_MODEL,
        },
        explain=explain,
    )

    explain_analytics_payload = None
    if explain:
        planner_output = {
            "route": {"intent": intent, "entity": entity, "view": result_key},
            "chosen": plan.get("chosen") or {},
        }
        metrics_snapshot = {
            "latency_ms": elapsed_ms,
            "cache_hit": bool(rt.get("cached")),
            "route_source": "cache" if rt.get("cached") else "planner",
        }
        explain_analytics_payload = _explain_analytics(
            request_id=request_id,
            planner_output=planner_output,
            metrics=metrics_snapshot,
        )

        try:
            with psycopg.connect(os.getenv("DATABASE_URL")) as conn:
                with conn.cursor() as cur:
                    # 1) Log de roteamento / explain
                    cur.execute(
                        """
                        INSERT INTO explain_events (
                            request_id, question, intent, entity,
                            route_id, features, sql_view, sql_hash,
                            cache_policy, latency_ms
                        ) VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)
                        ON CONFLICT (request_id) DO NOTHING;
                        """,
                        (
                            request_id,
                            payload.question,
                            intent or "",
                            entity or "",
                            result_key or "",
                            json.dumps(explain_analytics_payload["details"]),
                            result_key or "",
                            "",
                            "default",
                            elapsed_ms,
                        ),
                    )
                    # 2) Log do Narrator (resposta final)
                    narrator_meta = presenter_result.narrator_meta or {}
                    narrator_style = narrator_meta.get("style") or "executivo"
                    narrator_version = narrator_meta.get("version") or os.getenv(
                        "NARRATOR_VERSION", "20251117-narrator-v1"
                    )
                    answer_text = presenter_result.answer or ""

                    cur.execute(
                        """
                        INSERT INTO narrator_events (
                            request_id,
                            answer_text,
                            answer_len,
                            answer_hash,
                            narrator_version,
                            narrator_style
                        )
                        VALUES (%s, %s, %s, md5(%s), %s, %s)
                        """,
                        (
                            request_id,
                            answer_text,
                            len(answer_text),
                            answer_text,
                            narrator_version,
                            narrator_style,
                        ),
                    )
                    conn.commit()
        except Exception:
            counter("sirios_explain_events_failed_total")

    payload_out = {
        "status": {"reason": "ok", "message": "ok"},
        "results": results,
        "meta": {
            "planner": plan,
            "result_key": result_key,
            # CANÔNICOS
            "intent": intent,
            "entity": entity,
            # LEGADO / HISTÓRICO
            "planner_intent": intent,
            "planner_entity": entity,
            "planner_score": score,
            "rows_total": len(rows),
            "elapsed_ms": elapsed_ms,
            "explain": (plan.get("explain") if explain else None),
            "explain_analytics": explain_analytics_payload if explain else None,
            "cache": {
                "hit": bool(rt.get("cached")),
                "key": rt.get("key"),
                "ttl": (
                    int(rt.get("ttl"))
                    if isinstance(rt.get("ttl"), (int, float, Decimal))
                    else rt.get("ttl")
                ),
            },
            "aggregates": agg_params,
            "narrator": presenter_result.narrator_meta,
            "requested_metrics": meta.get("requested_metrics"),
        },
        "answer": presenter_result.answer,
    }

    return JSONResponse(json_sanitize(payload_out))
