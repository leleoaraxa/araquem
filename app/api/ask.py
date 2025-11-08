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
from app.formatter.rows import render_rows_template
from app.planner.param_inference import infer_params
from app.responder import render_answer

# ─────────────────────────────────────────────────────────────────────────────
# Narrator (camada de apresentação M10) — totalmente opcional e sem regressão
# ─────────────────────────────────────────────────────────────────────────────
_NARRATOR_ENABLED = str(os.getenv("NARRATOR_ENABLED", "false")).lower() == "true"
_NARRATOR_SHADOW = str(os.getenv("NARRATOR_SHADOW", "false")).lower() == "true"
_NARRATOR_MODEL = os.getenv("NARRATOR_MODEL", "mistral:instruct")

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
        out = orchestrator.route_question(payload.question)
        return out["results"]

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

    results = rt.get("value") or {}
    result_key = next(iter(results.keys()), None)
    rows = (
        results.get(result_key, []) if isinstance(results.get(result_key), list) else []
    )
    primary = rows[0] if rows else {}
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    # -------------------------------
    # Camada de apresentação (Narrador)
    # -------------------------------
    # Fatos que o Narrador pode usar (sem inventar campos; zero alucinação)
    facts: Dict[str, Any] = {
        "result_key": result_key,
        "rows": rows,
        "primary": primary,
        "aggregates": agg_params,
        "identifiers": identifiers,
        "ticker": (primary or {}).get("ticker") or (identifiers or {}).get("ticker"),
        "fund": (primary or {}).get("fund"),
    }
    meta_for_narrator: Dict[str, Any] = {
        "intent": intent,
        "entity": entity,
        # Se você quiser narrativa “por que o Planner escolheu”, descomente:
        "explain": (plan.get("explain") if explain else None),
    }

    narrator_info = {
        "enabled": bool(_NARRATOR_ENABLED),
        "shadow": bool(_NARRATOR_SHADOW),
        "model": _NARRATOR_MODEL,
        "latency_ms": None,
        "error": None,
        "used": False,
        "score": None,
        "strategy": "fallback",
    }

    # Resposta "legada" (atual) – usada se Narrador estiver off/falhar
    legacy_answer = render_answer(
        entity, rows, identifiers=identifiers, aggregates=agg_params
    )
    rendered_response = render_rows_template(entity, rows)

    final_answer = legacy_answer

    if _NARR is not None:
        # Modo shadow: executa Narrador só para medir/registrar (não altera UX)
        if _NARRATOR_SHADOW:
            try:
                out = _NARR.render(payload.question, facts, meta_for_narrator)
                narrator_info.update(
                    latency_ms=out.get("latency_ms"),
                    score=out.get("score"),
                    used=True,
                    strategy="llm_shadow",
                )
                counter("sirios_narrator_shadow_total", outcome="ok")
                if out.get("latency_ms") is not None:
                    histogram("sirios_narrator_latency_ms", float(out["latency_ms"]))
            except Exception as e:
                narrator_info.update(error=str(e), strategy="fallback_error")
                counter("sirios_narrator_shadow_total", outcome="error")

        # Modo enabled: substitui o answer pelo texto do Narrador
        if _NARRATOR_ENABLED:
            try:
                out = _NARR.render(payload.question, facts, meta_for_narrator)
                final_answer = out.get("text") or legacy_answer
                narrator_info.update(
                    latency_ms=out.get("latency_ms"),
                    score=out.get("score"),
                    used=True,
                    strategy="llm",
                )
                counter("sirios_narrator_render_total", outcome="ok")
                if out.get("latency_ms") is not None:
                    histogram("sirios_narrator_latency_ms", float(out["latency_ms"]))
            except Exception as e:
                narrator_info.update(error=str(e), strategy="fallback_error")
                counter("sirios_narrator_render_total", outcome="error")
                # fallback: mantém final_answer = legacy_answer

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
                    conn.commit()
        except Exception as e:
            counter("sirios_explain_events_failed_total")

    payload_out = {
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
            "narrator": narrator_info,
        },
        # Se Narrador estiver habilitado e funcionar, aqui já sai “bonito”.
        # Caso contrário, mantém o render atual.
        "answer": final_answer,
    }
    return JSONResponse(json_sanitize(payload_out))
