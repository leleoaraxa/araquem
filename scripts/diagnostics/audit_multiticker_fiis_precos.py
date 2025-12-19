"""
Audit script for diagnosing multi-ticker queries on fiis_precos.

It runs the full planner -> orchestrator -> executor pipeline for the
question "Como está o KNRI11 e o XPLG11 hoje?" and records the SQL,
params and row-level ticker observations for each iteration.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.builder import sql_builder
from app.orchestrator import routing as orchestrator_module
from app.orchestrator.routing import Orchestrator
from app.planner.planner import Planner
from app.planner.ticker_index import extract_tickers_from_text
from app.executor.pg import PgExecutor
from app.observability import runtime as obs_runtime


QUESTION = "Como está o KNRI11 e o XPLG11 hoje?"
ONTOLOGY_PATH = Path("data/ontology/entity.yaml")
OUTPUT_PATH = Path("data/diagnostics/audit_multiticker_results.jsonl")


def _hash_sql(sql: str) -> str:
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()[:12]


def _sql_head(sql: str, length: int = 300) -> str:
    return sql.replace("\n", " ")[:length]


def _sanitize(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    if hasattr(obj, "isoformat"):
        try:
            return obj.isoformat()
        except Exception:
            pass
    if isinstance(obj, dict):
        return {str(k): _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize(v) for v in obj]
    return str(obj)


class TracingPgExecutor(PgExecutor):
    def __init__(
        self,
        *args: Any,
        calls: List[Dict[str, Any]],
        stub_rows: bool = False,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.calls = calls
        self.stub_rows = stub_rows

    def query(self, sql: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        if self.stub_rows or not self._dsn:
            safe_params = params or {}
            tickers_param = safe_params.get("tickers")
            tickers_list = (
                [safe_params.get("ticker")]
                if not isinstance(tickers_param, (list, tuple, set))
                else list(tickers_param)
            )
            rows = [{"ticker": t} for t in tickers_list if t]
            if not rows:
                rows = [{"ticker": safe_params.get("ticker")}]
        else:
            rows = super().query(sql, params)
        unique_tickers = sorted(
            {row.get("ticker") for row in rows if isinstance(row, dict)}
        )
        self.calls.append(
            {
                "sql_hash": _hash_sql(sql),
                "params": _sanitize(copy.deepcopy(params)),
                "rows_count": len(rows),
                "rows_unique_tickers": unique_tickers,
                "stubbed": bool(self.stub_rows or not self._dsn),
            }
        )
        return rows


def _rank_hypotheses(
    loop_iterations: List[Dict[str, Any]], executor_calls: List[Dict[str, Any]]
) -> List[str]:
    if len(loop_iterations) >= 2:
        iter_tickers = [it.get("ticker") for it in loop_iterations]
        if len(set(iter_tickers)) == 1:
            return ["H1", "H2", "H3", "H4", "H5"]

        param_blobs = [json.dumps(it.get("params", {}), sort_keys=True) for it in loop_iterations]
        if len(set(param_blobs)) == 1:
            return ["H2", "H3", "H4", "H5", "H1"]

    unique_per_call = [
        tuple(call.get("rows_unique_tickers") or []) for call in executor_calls
    ]
    if unique_per_call and len(set(unique_per_call)) == 1 and len(unique_per_call[0]) == 1:
        return ["H5", "H4", "H3", "H2", "H1"]

    return ["H3", "H2", "H4", "H1", "H5"]


def run_audit() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    obs_runtime.init_tracing = lambda *args, **kwargs: None
    obs_runtime.bootstrap(service_name="diagnostics")
    planner = Planner(str(ONTOLOGY_PATH))
    executor_calls: List[Dict[str, Any]] = []
    use_stub_rows = not bool(os.getenv("DATABASE_URL"))
    executor = TracingPgExecutor(calls=executor_calls, stub_rows=use_stub_rows)
    orchestrator = Orchestrator(planner=planner, executor=executor)

    loop_iterations: List[Dict[str, Any]] = []
    original_build = sql_builder.build_select_for_entity
    orchestrator_original_build = orchestrator_module.build_select_for_entity

    def wrapped_build_select_for_entity(
        entity: str, identifiers: Dict[str, Any], agg_params: Dict[str, Any] | None = None
    ):
        sql, params, result_key, columns = original_build(entity, identifiers, agg_params)
        loop_iterations.append(
            {
                "ticker": identifiers.get("ticker"),
                "identifiers": _sanitize(copy.deepcopy(identifiers)),
                "sql_hash": _hash_sql(sql),
                "sql_head": _sql_head(sql),
                "params": _sanitize(copy.deepcopy(params)),
            }
        )
        return sql, params, result_key, columns

    sql_builder.build_select_for_entity = wrapped_build_select_for_entity
    orchestrator_module.build_select_for_entity = wrapped_build_select_for_entity
    try:
        response = orchestrator.route_question(QUESTION)
    finally:
        sql_builder.build_select_for_entity = original_build
        orchestrator_module.build_select_for_entity = orchestrator_original_build

    result_key = response.get("meta", {}).get("result_key")
    rows = response.get("results", {}).get(result_key, []) if result_key else []
    final_rows_unique_tickers = sorted(
        {row.get("ticker") for row in rows if isinstance(row, dict)}
    )

    extracted_tickers = extract_tickers_from_text(QUESTION)
    expected_set = set(extracted_tickers)
    final_set = set(final_rows_unique_tickers)
    matches_expected = expected_set == final_set
    suspicion_rank = _rank_hypotheses(loop_iterations, executor_calls)

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": QUESTION,
        "extracted_tickers": extracted_tickers,
        "loop_iterations": loop_iterations,
        "executor_calls": executor_calls,
        "final_rows_unique_tickers": final_rows_unique_tickers,
        "final_rows_match_expected": matches_expected,
        "missing_tickers": sorted(expected_set - final_set),
        "unexpected_tickers": sorted(final_set - expected_set),
        "suspicion_rank": suspicion_rank,
    }
    return payload, response


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload, _ = run_audit()
    with OUTPUT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
