import time
import re
from typing import Any, Dict

from app.planner.planner import Planner
from app.builder.sql_builder import build_select_for_entity
from app.executor.pg import PgExecutor
from app.formatter.rows import format_rows

# Normalização de ticker na camada de ENTRADA (contrato Araquem)
TICKER_RE = re.compile(r"\b([A-Za-z]{4}11)\b")

class Orchestrator:
    def __init__(self, planner: Planner, executor: PgExecutor):
        self._planner = planner
        self._exec = executor

    def _extract_identifiers(self, question: str) -> Dict[str, Any]:
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

        identifiers = self._extract_identifiers(question)
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
