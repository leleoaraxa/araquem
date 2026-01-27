#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api import get_app


def _safe_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _top2_from_scoring(scoring: Dict[str, Any]) -> List[Dict[str, Any]]:
    candidates = scoring.get("final_combined") or scoring.get("combined") or scoring.get("intent") or []
    if not isinstance(candidates, list):
        return []
    normalized: List[Tuple[str, float]] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        name = item.get("intent") or item.get("name")
        score = item.get("score") or item.get("combined") or item.get("value")
        if not isinstance(name, str) or not name:
            continue
        score_val = _safe_float(score)
        if score_val is None:
            continue
        normalized.append((name, score_val))
    normalized.sort(key=lambda x: x[1], reverse=True)
    return [{"intent": name, "score": score} for name, score in normalized[:2]]


def _summarize_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    chosen = plan.get("chosen") if isinstance(plan, dict) else {}
    if not isinstance(chosen, dict):
        chosen = {}
    explain = plan.get("explain") if isinstance(plan, dict) else {}
    if not isinstance(explain, dict):
        explain = {}
    scoring = explain.get("scoring") if isinstance(explain, dict) else {}
    return {
        "chosen_intent": chosen.get("intent"),
        "chosen_entity": chosen.get("entity"),
        "chosen_score": chosen.get("score"),
        "top2": _top2_from_scoring(scoring) if isinstance(scoring, dict) else [],
        "top2_gap": _safe_float(scoring.get("intent_top2_gap")) if isinstance(scoring, dict) else None,
        "thresholds": scoring.get("thresholds_applied") if isinstance(scoring, dict) else None,
        "gate_source": explain.get("planner_gate_source") if isinstance(explain, dict) else None,
    }


def _summarize_rag(meta: Dict[str, Any]) -> Dict[str, Any]:
    rag = meta.get("rag") if isinstance(meta, dict) else None
    if not isinstance(rag, dict):
        return {"enabled": False, "reason": "missing"}
    policy = rag.get("policy") if isinstance(rag.get("policy"), dict) else {}
    chunks = rag.get("chunks") if isinstance(rag.get("chunks"), list) else []
    return {
        "enabled": bool(rag.get("enabled")),
        "policy": {
            "enabled": policy.get("enabled"),
            "reason": policy.get("reason"),
            "mode": policy.get("mode"),
            "collections": policy.get("collections"),
            "max_chunks": policy.get("max_chunks"),
            "min_score": policy.get("min_score"),
        },
        "chunks_total": len(chunks),
        "chunks": [
            {
                "doc_id": chunk.get("doc_id"),
                "chunk_id": chunk.get("chunk_id"),
                "score": chunk.get("score"),
                "tags": chunk.get("tags"),
                "entity": chunk.get("entity"),
                "collection": chunk.get("collection"),
            }
            for chunk in chunks
            if isinstance(chunk, dict)
        ],
    }


def _classify_path(meta: Dict[str, Any]) -> str:
    rows_total = meta.get("rows_total") if isinstance(meta, dict) else 0
    rag = meta.get("rag") if isinstance(meta, dict) else None
    rag_chunks = 0
    if isinstance(rag, dict):
        rag_chunks = len(rag.get("chunks") or [])
    if rows_total and rag_chunks:
        return "mixed_sql_rag"
    if rows_total:
        return "sql_only"
    if rag_chunks:
        return "rag_only"
    return "no_data"


def trace_question(client: TestClient, question: str) -> Dict[str, Any]:
    payload = {
        "question": question,
        "conversation_id": "diag-concepts",
        "nickname": "diag",
        "client_id": "diag",
    }
    try:
        response = client.post("/ask?explain=true", json=payload)
    except Exception as exc:  # pragma: no cover - runtime dependency
        return {"error": str(exc), "question": question}

    try:
        data = response.json()
    except Exception:
        return {"error": f"non-json response (status={response.status_code})", "question": question}

    meta = data.get("meta") if isinstance(data, dict) else {}
    if not isinstance(meta, dict):
        meta = {}
    plan = meta.get("planner") if isinstance(meta, dict) else {}
    if not isinstance(plan, dict):
        plan = {}

    return {
        "question": question,
        "status": data.get("status"),
        "planner": _summarize_plan(plan if isinstance(plan, dict) else {}),
        "rag": _summarize_rag(meta if isinstance(meta, dict) else {}),
        "filters_applied": {
            "required_entity_doc": None,
            "hint_filters_allowlist": None,
            "hint_filters_denylist": None,
        },
        "context_final": {
            "rows_total": meta.get("rows_total") if isinstance(meta, dict) else None,
            "rag_chunks": len((meta.get("rag") or {}).get("chunks") or [])
            if isinstance(meta, dict)
            else None,
        },
        "path": _classify_path(meta if isinstance(meta, dict) else {}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Trace concepts flow via /ask.")
    parser.add_argument(
        "--questions",
        nargs="*",
        default=[
            "o que é dividend yield em fiis?",
            "como funciona vacancia fisica e vacancia financeira?",
            "o que significa p/vp em fundos imobiliarios?",
            "quais foram os dividendos do HGLG11 no ultimo ano?",
        ],
    )
    args = parser.parse_args()

    os.environ.setdefault("RAG_TRACE", "1")
    app = get_app()
    client = TestClient(app)

    for question in args.questions:
        report = trace_question(client, question)
        print("# Trace Report")
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
