# app/orchestrator/routing.py

import os
import re
import time
from typing import Any, Dict, Optional
from uuid import uuid4

from app.planner.planner import Planner
from app.builder.sql_builder import build_select_for_entity
from app.executor.pg import PgExecutor
from app.formatter.rows import format_rows
from app.observability.metrics import (
    emit_counter as counter,
    emit_histogram as histogram,
)
from app.observability.instrumentation import (
    get_trace_id,
    set_trace_attribute,
    trace as start_trace,
)
from app.analytics.explain import explain as _explain_analytics
from app.planner.param_inference import infer_params  # novo: inferência compute-on-read
from app.utils.filecache import load_yaml_cached

# Normalização de ticker na camada de ENTRADA (contrato Araquem)
TICKER_RE = re.compile(r"\b([A-Za-z]{4}11)\b")

_TH_PATH = os.getenv("PLANNER_THRESHOLDS_PATH", "data/ops/planner_thresholds.yaml")


def _load_thresholds(path: str) -> Dict[str, Any]:
    raw = load_yaml_cached(path) or {}
    return (raw.get("planner") or {}).get("thresholds") or {}


class Orchestrator:
    def __init__(
        self,
        planner: Planner,
        executor: PgExecutor,
        planner_metrics: Optional[Dict[str, Any]] = None,
    ):
        # `planner_metrics` mantido p/ compatibilidade de assinatura; métricas via façade.
        self._planner = planner
        self._exec = executor

    def extract_identifiers(self, question: str) -> Dict[str, Any]:
        m = TICKER_RE.search(question.upper())
        return {"ticker": m.group(1) if m else None}

    def route_question(self, question: str, explain: bool = False) -> Dict[str, Any]:
        t0 = time.perf_counter()
        plan = self._planner.explain(question)
        chosen = plan.get("chosen") or {}
        intent = chosen.get("intent")
        entity = chosen.get("entity")
        score = chosen.get("score")
        exp = plan.get("explain") or {}

        # top2 gap do planner (M6.5 calculado no planner)
        top2_gap = float(((exp.get("scoring") or {}).get("intent_top2_gap")) or 0.0)

        # --------- M6.6: aplicar GATES por YAML ----------
        th = _load_thresholds(_TH_PATH)
        dfl = th.get("defaults", {}) if isinstance(th, dict) else {}
        i_th = (
            (th.get("intents", {}) or {}).get(intent or "", {})
            if isinstance(th, dict)
            else {}
        )
        e_th = (
            (th.get("entities", {}) or {}).get(entity or "", {})
            if isinstance(th, dict)
            else {}
        )

        # prioridade: entity > intent > defaults
        min_score = float(
            e_th.get("min_score", i_th.get("min_score", dfl.get("min_score", 0.0)))
        )
        min_gap = float(
            e_th.get("min_gap", i_th.get("min_gap", dfl.get("min_gap", 0.0)))
        )
        gate = {
            "blocked": False,
            "reason": None,
            "min_score": min_score,
            "min_gap": min_gap,
            "top2_gap": top2_gap,
        }
        if entity:
            if score < min_score:
                gate.update({"blocked": True, "reason": "low_score"})
            elif top2_gap < min_gap:
                gate.update({"blocked": True, "reason": "low_gap"})

        if gate["blocked"]:
            counter(
                "sirios_planner_blocked_by_threshold_total",
                reason=str(gate["reason"]),
                intent=str(intent),
                entity=str(entity),
            )

        if not entity:
            return {
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
                    "gate": gate,
                },
            }

        if gate["blocked"]:
            return {
                "status": {
                    "reason": "gated",
                    "message": f"Blocked by threshold: {gate['reason']}",
                },
                "results": {},
                "meta": {
                    "planner": plan,
                    "result_key": None,
                    "planner_intent": intent,
                    "planner_entity": entity,
                    "planner_score": score,
                    "rows_total": 0,
                    "elapsed_ms": int((time.perf_counter() - t0) * 1000),
                    "gate": gate,
                    "explain": exp if explain else None,
                },
            }

        identifiers = self.extract_identifiers(question)

        # --- M7.2: inferência de parâmetros (compute-on-read) ---------------
        # Lê regras de data/ops/param_inference.yaml + entity.yaml (aggregations.*)
        try:
            agg_params = infer_params(
                question=question,
                intent=intent,
                entity=entity,
                entity_yaml_path=f"data/entities/{entity}.yaml",
                defaults_yaml_path="data/ops/param_inference.yaml",
            )  # dict: {"agg": "...", "window": "...", "limit": int, "order": "..."}
        except Exception:
            agg_params = None  # fallback seguro: SELECT básico (sem agregação)

        # estágio de planning finalizado
        histogram(
            "sirios_planner_duration_seconds", time.perf_counter() - t0, stage="plan"
        )
        counter(
            "sirios_planner_route_decisions_total",
            intent=str(intent),
            entity=str(entity),
            outcome="ok",
        )

        # --- M6.4: métricas de explain (somente quando explicitamente solicitado) ---
        if explain:
            counter("sirios_planner_explain_enabled_total")
            for n in exp.get("decision_path") or []:
                kind = n.get("type") or "unknown"
                counter("sirios_planner_explain_nodes_total", node_kind=kind)

            # Removido: tentativa de enviar somas como "counter" com _value.
            # O schema canônico exige labels exatos; sem _value. Se precisarmos
            # dessas somas no futuro, criaremos um histogram/gauge específico.
            if intent is not None:
                histogram(
                    "sirios_planner_intent_score", float(score), intent=str(intent)
                )
            if entity is not None:
                histogram(
                    "sirios_planner_entity_score", float(score), entity=str(entity)
                )

        # span do planner (atributos semânticos)
        with start_trace(
            "planner.route",
            component="planner",
            operation="route_question",
        ) as span:
            set_trace_attribute(span, "planner.intent", intent)
            set_trace_attribute(span, "planner.entity", entity)
            set_trace_attribute(
                span,
                "planner.score",
                float(score) if isinstance(score, (int, float)) else 0.0,
            )

            sql, params, result_key, return_columns = build_select_for_entity(
                entity=entity,
                identifiers=identifiers,
                agg_params=agg_params,  # <- passa inferência para o builder
            )
            if isinstance(params, dict):
                params = {**params, "entity": entity}  # etiqueta para métricas SQL
            rows = self._exec.query(sql, params)

        # elapsed consolidado para reutilização (meta e explain analytics)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        # Explain Analytics (somente quando solicitado)
        explain_analytics_payload = None
        if explain:
            # Usa o trace_id do span corrente como request_id (correlação OTEL)
            trace_id = get_trace_id(span)
            request_id = trace_id or uuid4().hex
            planner_output = {
                "route": {"intent": intent, "entity": entity, "view": result_key},
                "chosen": chosen,
            }
            metrics_snapshot = {
                "latency_ms": elapsed_ms,
                "route_source": "planner",
                # cache_hit: desconhecido neste ponto; manter None para não inferir
            }
            explain_analytics_payload = _explain_analytics(
                request_id=request_id,
                planner_output=planner_output,
                metrics=metrics_snapshot,
            )

        results = {result_key: format_rows(rows, return_columns)}

        return {
            "status": {"reason": "ok", "message": "ok"},
            "results": results,
            "meta": {
                "planner": plan,
                "explain": exp if explain else None,
                "explain_analytics": explain_analytics_payload if explain else None,
                "result_key": result_key,
                "planner_intent": intent,
                "planner_entity": entity,
                "planner_score": score,
                "rows_total": len(rows),
                "elapsed_ms": elapsed_ms,
                "gate": gate,
                "aggregates": (agg_params or {}),
            },
        }
