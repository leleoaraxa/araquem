# app/orchestrator/routing.py

import time
import re
import os, yaml
from typing import Any, Dict, Optional

from app.planner.planner import Planner
from app.builder.sql_builder import build_select_for_entity
from app.executor.pg import PgExecutor
from app.formatter.rows import format_rows
from opentelemetry import trace
from app.observability.runtime import load_config, init_planner_metrics

# Normalização de ticker na camada de ENTRADA (contrato Araquem)
TICKER_RE = re.compile(r"\b([A-Za-z]{4}11)\b")

_CFG = load_config()
_PM = init_planner_metrics(_CFG)
_TR_PLANNER = trace.get_tracer("planner")
_TH_PATH = os.getenv("PLANNER_THRESHOLDS_PATH", "data/ops/planner_thresholds.yaml")

def _load_thresholds(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        return (raw.get("planner") or {}).get("thresholds") or {}
    except Exception:
        return {}



class Orchestrator:
    def __init__(self, planner: Planner, executor: PgExecutor, planner_metrics: Optional[Dict[str, Any]] = None):
        self._planner = planner
        self._exec = executor
        self._pm = planner_metrics or {"decisions": None, "duration": None}

    def extract_identifiers(self, question: str) -> Dict[str, Any]:
        m = TICKER_RE.search(question.upper())
        return {"ticker": m.group(1) if m else None}

    def route_question(self, question: str, explain: bool = False) -> Dict[str, Any]:
        t0 = time.perf_counter()
        plan = self._planner.explain(question)
        intent = plan["chosen"]["intent"]
        entity = plan["chosen"]["entity"]
        score = plan["chosen"]["score"]
        exp = plan.get("explain") or {}
        # top2 gap do planner (M6.5 calculado no planner)
        top2_gap = float(((exp.get("scoring") or {}).get("intent_top2_gap")) or 0.0)

        # --------- M6.6: aplicar GATES por YAML ----------
        th = _load_thresholds(_TH_PATH)
        dfl = th.get("defaults", {}) if isinstance(th, dict) else {}
        i_th = (th.get("intents", {}) or {}).get(intent or "", {}) if isinstance(th, dict) else {}
        e_th = (th.get("entities", {}) or {}).get(entity or "", {}) if isinstance(th, dict) else {}
        # prioridade: entity > intent > defaults
        min_score = float(
            e_th.get("min_score", i_th.get("min_score", dfl.get("min_score", 0.0)))
        )
        min_gap = float(
            e_th.get("min_gap", i_th.get("min_gap", dfl.get("min_gap", 0.0)))
        )
        gate = {"blocked": False, "reason": None, "min_score": min_score, "min_gap": min_gap, "top2_gap": top2_gap}
        if entity:
            if score < min_score:
                gate.update({"blocked": True, "reason": "low_score"})
            elif top2_gap < min_gap:
                gate.update({"blocked": True, "reason": "low_gap"})
        # métrica de bloqueio (se bloqueou)
        if gate["blocked"] and self._pm.get("blocked_by_threshold"):
            self._pm["blocked_by_threshold"].labels(
                reason=str(gate["reason"]), intent=str(intent), entity=str(entity)
            ).inc()

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

        # Se gate bloqueou, devolve sem executar SQL, com meta.gate
        if gate["blocked"]:
            return {
                "status": {"reason": "gated", "message": f"Blocked by threshold: {gate['reason']}"},
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
        # estágio de planning finalizado
        if self._pm["duration"] is not None:
            self._pm["duration"].labels(stage="plan").observe(time.perf_counter() - t0)

        # marca decisão do planner
        if self._pm["decisions"] is not None:
            self._pm["decisions"].labels(intent=intent, entity=entity, outcome="ok").inc()

        # --- M6.4: métricas de explain (somente quando explicitamente solicitado) ---
        if explain and self._pm.get("explain_enabled"):
            self._pm["explain_enabled"].inc()
            # nós por tipo (aproximação: contamos pelos stages)
            nodes = exp.get("decision_path", [])
            if self._pm.get("explain_nodes"):
                for n in nodes:
                    kind = n.get("type") or "unknown"
                    self._pm["explain_nodes"].labels(node_kind=kind).inc()
            # somatórios de pesos
            ws = (exp.get("signals") or {}).get("weights_summary") or {}
            if self._pm.get("explain_weight_sum"):
                # registramos por tipo, mantendo cardinalidade baixa
                for k in ("token_sum", "phrase_sum", "anti_sum"):
                    v = float(ws.get(k, 0.0) or 0.0)
                    self._pm["explain_weight_sum"].labels(type=k.replace("_sum","")).inc(v)
            # profundidade (gauge) e histogramas de score
            if self._pm.get("explain_depth"):
                self._pm["explain_depth"].set(float(len(nodes)))
            if self._pm.get("intent_score_hist") and intent is not None:
                self._pm["intent_score_hist"].labels(intent=intent).observe(float(score))
            if self._pm.get("entity_score_hist") and entity is not None:
                self._pm["entity_score_hist"].labels(entity=entity).observe(float(score))

        # span do planner (atributos semânticos)
        with _TR_PLANNER.start_as_current_span("planner.route") as sp:
            sp.set_attribute("planner.intent", intent)
            sp.set_attribute("planner.entity", entity)
            sp.set_attribute("planner.score", float(score) if isinstance(score, (int,float)) else 0.0)

            sql, params, result_key, return_columns = build_select_for_entity(entity, identifiers)
            # garante etiqueta da entidade no executor para métricas SQL
            if isinstance(params, dict):
                params = {**params, "entity": entity}
            rows = self._exec.query(sql, params)

        results = {result_key: format_rows(rows, return_columns)}
        return {
            "status": {"reason": "ok", "message": "ok"},
            "results": results,
            "meta": {
                "planner": plan,
                "explain": exp if explain else None,
                "result_key": result_key,
                "planner_intent": intent,
                "planner_entity": entity,
                "planner_score": score,
                "rows_total": len(rows),
                "elapsed_ms": int((time.perf_counter() - t0) * 1000),
                "gate": gate,
            },
        }
