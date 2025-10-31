# app/orchestrator/routing.py

import time
import re
from typing import Any, Dict

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

class Orchestrator:
    def __init__(self, planner: Planner, executor: PgExecutor):
        self._planner = planner
        self._exec = executor

    def extract_identifiers(self, question: str) -> Dict[str, Any]:
        m = TICKER_RE.search(question.upper())
        return {"ticker": m.group(1) if m else None}

    def route_question(self, question: str) -> Dict[str, Any]:
        t0 = time.perf_counter()
        plan = self._planner.explain(question)
        intent = plan["chosen"]["intent"]
        entity = plan["chosen"]["entity"]
        score = plan["chosen"]["score"]

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
                },
            }

        identifiers = self.extract_identifiers(question)
        # estágio de planning finalizado
        if _PM["duration"] is not None:
            _PM["duration"].labels(stage="plan").observe(time.perf_counter() - t0)

        # marca decisão do planner
        if _PM["decisions"] is not None:
            _PM["decisions"].labels(intent=intent, entity=entity, outcome="ok").inc()

        # span do planner (atributos semânticos)
        with _TR_PLANNER.start_as_current_span("planner.route") as sp:
            sp.set_attribute("planner.intent", intent)
            sp.set_attribute("planner.entity", entity)
            sp.set_attribute("planner.score", float(score) if isinstance(score, (int,float)) else 0.0)

            sql, params, result_key, return_columns = build_select_for_entity(entity, identifiers)
            rows = self._exec.query(sql, params)

        results = {result_key: format_rows(rows, return_columns)}
        return {
            "status": {"reason": "ok", "message": "ok"},
            "results": results,
            "meta": {
                "planner": plan,
                "result_key": result_key,
                "planner_intent": intent,
                "planner_entity": entity,
                "planner_score": score,
                "rows_total": len(rows),
                "elapsed_ms": int((time.perf_counter() - t0) * 1000),
            },
        }
