# app/api/ask.py
import json
import logging
import os
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any, List

import psycopg
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.analytics.explain import explain as _explain_analytics
from app.cache.rt_cache import read_through
from app.common.http import json_sanitize, make_request_id
from app.core.context import cache, orchestrator, planner, policies, context_manager
from app.observability.metrics import (
    emit_counter as counter,
    emit_histogram as histogram,
)

# from app.planner.param_inference import infer_params

# ainda importamos responder/formatter aqui para retrocompatibilidade
# (o presenter usa esses módulos internamente)
from app.formatter.rows import render_rows_template
from app.templates_answer import render_answer

# nova camada de apresentação (pós-formatter)
from app.presenter.presenter import present, _choose_result_key

# ─────────────────────────────────────────────────────────────────────────────
# Narrator (camada de apresentação M10)
# ─────────────────────────────────────────────────────────────────────────────
from app.narrator.narrator import Narrator  # arquivo novo (drop-in)


LOGGER = logging.getLogger(__name__)


_NARR: Optional[Narrator] = Narrator()

# ─────────────────────────────────────────────────────────────────────────────

router = APIRouter()


class AskPayload(BaseModel):
    question: str
    conversation_id: str
    nickname: str
    client_id: str


@router.post("/ask")
def ask(
    payload: AskPayload,
    explain: bool = Query(default=False),
):
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
    exp_safe = plan.get("explain") if isinstance(plan, dict) else {}
    bucket_info = exp_safe.get("bucket") if isinstance(exp_safe, dict) else {}
    if not isinstance(bucket_info, dict):
        bucket_info = {}
    bucket_selected = str(bucket_info.get("selected") or "")

    # ------------------------------------------------------------------
    # CONTEXTO CONVERSACIONAL (M12) — registro do turno do usuário
    # ------------------------------------------------------------------
    try:
        context_manager.append_turn(
            client_id=payload.client_id,
            conversation_id=payload.conversation_id,
            role="user",
            content=payload.question,
            meta={
                "request_id": request_id,
                "intent": intent,
                "entity": entity,
                "bucket": bucket_selected,
            },
        )
    except Exception:
        LOGGER.warning("Falha ao registrar turno do usuário no contexto", exc_info=True)

    counter("sirios_planner_routed_total", outcome=("ok" if entity else "unroutable"))

    if explain:
        top2_gap = float(
            ((plan.get("explain") or {}).get("scoring") or {}).get("intent_top2_gap")
            or 0.0
        )
        histogram("sirios_planner_top2_gap_histogram", top2_gap)

    if not entity:
        elapsed_ms_unr = int((time.perf_counter() - t0) * 1000)
        response_timestamp = (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )

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

        unroutable_answer = (
            "Desculpe, não consegui encontrar dados relevantes para a sua pergunta. "
            "Tente reformular em outras palavras ou mencionar um fundo específico."
        )

        payload_out_unr = {
            "status": {"reason": "unroutable", "message": "No entity matched"},
            "results": {},
            "meta": {
                "planner": plan,
                "result_key": None,
                "intent": intent,
                "entity": entity,
                "planner_intent": intent,
                "planner_entity": entity,
                "planner_score": score,
                "rows_total": 0,
                "elapsed_ms": elapsed_ms_unr,
                "explain": (plan.get("explain") if explain else None),
                "explain_analytics": explain_analytics_payload if explain else None,
                "cache": {"hit": False, "key": None, "ttl": None},
            },
            "answer": unroutable_answer,
        }

        # Registro do turno do "assistant" (resposta unroutable)
        try:
            context_manager.append_turn(
                client_id=payload.client_id,
                conversation_id=payload.conversation_id,
                role="assistant",
                content=unroutable_answer,
                meta={
                    "request_id": request_id,
                    "intent": intent,
                    "entity": entity,
                    "bucket": bucket_selected,
                    "status_reason": "unroutable",
                },
            )
        except Exception:
            LOGGER.warning(
                "Falha ao registrar turno unroutable no contexto",
                exc_info=True,
                extra={"request_id": request_id, "entity": entity, "intent": intent},
            )

        if explain:
            body = payload_out_unr
        else:
            body = {
                "question": payload.question,
                "conversation_id": payload.conversation_id,
                "answer": unroutable_answer,
                "timestamp": response_timestamp,
                "elapsed_ms": elapsed_ms_unr,
                "status": "error",
                "error": {
                    "code": "unroutable",
                    "message": "No entity matched",
                    "retryable": False,
                },
            }

        return JSONResponse(json_sanitize(body))

    identifiers = orchestrator.extract_identifiers(payload.question) or {}
    last_reference_resolution: Optional[Dict[str, Any]] = None
    try:
        last_reference_resolution = context_manager.resolve_last_reference(
            client_id=payload.client_id,
            conversation_id=payload.conversation_id,
            entity=entity,
            bucket=bucket_selected,
            identifiers=identifiers,
        )
        identifiers = (
            last_reference_resolution.get("identifiers_resolved")
            if isinstance(last_reference_resolution, dict)
            else identifiers
        ) or identifiers
    except Exception:
        LOGGER.exception(
            "Falha ao resolver last_reference; seguindo sem herança",
            extra={"entity": entity, "intent": intent, "request_id": request_id},
        )

    # try:
    #     agg_params = infer_params(
    #         question=payload.question,
    #         intent=intent,
    #         entity=entity,
    #         entity_yaml_path=f"data/entities/{entity}/entity.yaml",
    #         defaults_yaml_path="data/ops/param_inference.yaml",
    #         identifiers=identifiers,
    #         client_id=payload.client_id,
    #         conversation_id=payload.conversation_id,
    #     )
    # except Exception:
    #     LOGGER.warning(
    #         "Inferência de parâmetros falhou; seguindo sem agregados",
    #         extra={"entity": entity, "intent": intent, "request_id": request_id},
    #         exc_info=True,
    #     )
    #     agg_params = {}

    def _fetch():
        return orchestrator.route_question(
            payload.question,
            client_id=payload.client_id,
            conversation_id=payload.conversation_id,
        )

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
    # if isinstance(agg_params, dict):
    #     metric_key = agg_params.get("metric")
    #     window_norm = (
    #         orchestrator._normalize_metrics_window(agg_params) if metric_key else None
    #     )
    #     if metric_key and window_norm:
    #         window_info = orchestrator._split_window(window_norm)
    #         cache_identifiers.update(
    #             metric_key=metric_key,
    #             window_norm=window_norm,
    #             **window_info,
    #         )
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
    result_key, rk_diag = _choose_result_key(results, meta.get("result_key"))
    if rk_diag:
        meta.setdefault("diagnostics", {})["result_key_mismatch"] = rk_diag
    rows = (
        results.get(result_key, []) if isinstance(results.get(result_key), list) else []
    )

    agg_params = (meta.get("aggregates") or {}) if isinstance(meta, dict) else {}

    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    response_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

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
        client_id=payload.client_id,
        conversation_id=payload.conversation_id,
        nickname=payload.nickname,
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
            LOGGER.error(
                "Falha ao registrar explain/narrator events no banco", exc_info=True
            )
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

    if isinstance(last_reference_resolution, dict):
        meta.setdefault("context", {})["last_reference"] = {
            "used": bool(last_reference_resolution.get("last_reference_used")),
            "ticker": last_reference_resolution.get("last_reference_ticker"),
            "reason": last_reference_resolution.get("reason"),
        }

    # ------------------------------------------------------------------
    # CONTEXTO CONVERSACIONAL — registro do turno do "assistant"
    # ------------------------------------------------------------------
    try:
        context_manager.append_turn(
            client_id=payload.client_id,
            conversation_id=payload.conversation_id,
            role="assistant",
            content=presenter_result.answer or "",
            meta={
                "request_id": request_id,
                "intent": intent,
                "entity": entity,
                "bucket": bucket_selected,
                "status_reason": "ok",
            },
        )

        # ------------------------------------------------------------------
        # last_reference: grava apenas quando existe UM ticker não ambíguo
        # e já resolvido pelas camadas canônicas (param_inference / orchestrator).
        # Nada de regex local; sem heurística nova.
        tickers_for_context: List[str] = []

        # 1) Se o Planner/param_inference já resolveu um ticker explícito,
        #    usamos ele como referência principal.
        if isinstance(agg_params, dict):
            candidate = agg_params.get("ticker")
            if isinstance(candidate, str) and candidate:
                tickers_for_context.append(candidate)

        # 2) Inclui tickers presentes nos identifiers (já resolvidos/normatizados).
        if isinstance(identifiers, dict):
            t = identifiers.get("ticker")
            if isinstance(t, str) and t:
                tickers_for_context.append(t)
            tickers = identifiers.get("tickers")
            if isinstance(tickers, list):
                tickers_for_context.extend(
                    [tk for tk in tickers if isinstance(tk, str) and tk]
                )

        deduped: List[str] = []
        seen = set()
        for tk in tickers_for_context:
            if tk not in seen:
                deduped.append(tk)
                seen.add(tk)

        if deduped:
            context_manager.update_last_reference(
                client_id=payload.client_id,
                conversation_id=payload.conversation_id,
                ticker=deduped[0],
                tickers=deduped,
                entity=entity,
                intent=intent,
                bucket=bucket_selected,
            )
    except Exception:
        LOGGER.warning(
            "Falha ao registrar turno final do assistant no contexto",
            exc_info=True,
            extra={"request_id": request_id, "entity": entity, "intent": intent},
        )

    # Escolha do payload conforme modo:
    # - explain=True  -> payload rico (core), usado para debug/QA.
    # - explain=False -> AskResponse v1 (client), slim e estável.
    if explain:
        body = payload_out
    else:
        body = {
            "question": payload.question,
            "conversation_id": payload.conversation_id,
            "answer": presenter_result.answer or "",
            "timestamp": response_timestamp,
            "elapsed_ms": elapsed_ms,
            "status": "ok",
        }

    return JSONResponse(json_sanitize(body))
