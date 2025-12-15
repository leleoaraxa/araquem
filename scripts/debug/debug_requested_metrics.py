"""Debug helper for requested_metrics extraction and propagation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from app.core.context import orchestrator, planner
from app.narrator.narrator import Narrator
from app.orchestrator.routing import extract_requested_metrics
from app.presenter.presenter import present


def load_entity_conf(entity: str) -> Dict[str, Any]:
    path = Path("data/entities") / entity / "entity.yaml"
    if not path.exists():
        return {}
    try:
        from app.utils.filecache import load_yaml_cached

        data = load_yaml_cached(str(path))
        return data if isinstance(data, dict) else {}
    except Exception:  # pragma: no cover - debug helper
        return {}


def build_case_payload(case_id: str, question: str, entity: str) -> Dict[str, Any]:
    entity_conf = load_entity_conf(entity)
    extracted = extract_requested_metrics(question, entity_conf)

    orchestration: Dict[str, Any] = {}
    meta_requested: Any = None
    focus_meta: Any = None
    presenter_meta_requested: Any = None
    narrator_focus: Any = None
    notes: List[str] = []

    try:
        orchestration = orchestrator.route_question(
            question, client_id="debug", conversation_id="debug"
        )
    except Exception as exc:  # pragma: no cover - debug helper
        notes.append(f"orchestrator_error={exc}")
        orchestration = {}

    meta = orchestration.get("meta") if isinstance(orchestration, dict) else {}
    meta = meta or {}
    meta_requested = meta.get("requested_metrics")
    focus_meta = (meta.get("focus") or {}).get("metric_key")

    try:
        identifiers = orchestrator.extract_identifiers(question) or {}
        aggregates = meta.get("aggregates") if isinstance(meta, dict) else {}
        presenter_result = present(
            question=question,
            plan=planner.explain(question),
            orchestrator_results=orchestration.get("results") or {},
            meta=meta,
            identifiers=identifiers,
            aggregates=aggregates if isinstance(aggregates, dict) else {},
            narrator=Narrator(),
            client_id="debug",
            conversation_id="debug",
            nickname="debug",
            explain=False,
        )
        presenter_meta_requested = presenter_result.facts.requested_metrics
        narrator_focus = (presenter_result.narrator_meta or {}).get(
            "focus_metric_key"
        )
    except Exception as exc:  # pragma: no cover - debug helper
        notes.append(f"presenter_error={exc}")

    return {
        "case_id": case_id,
        "question": question,
        "entity": entity,
        "extracted_requested_metrics": extracted,
        "meta_requested_metrics_final": meta_requested,
        "meta_focus_metric_key_final": focus_meta,
        "narrator_focus_metric_key_final": narrator_focus,
        "notes": "; ".join(notes),
    }


def main() -> None:
    cases = [
        {
            "case_id": "case1",
            "question": "Qual o valor de fechamento do XPML11?",
            "entity": "fiis_precos",
        },
        {
            "case_id": "case2",
            "question": "Me dá preços do XPML11",
            "entity": "fiis_precos",
        },
        {
            "case_id": "case3",
            "question": "posição no IFIX do HGLG11",
            "entity": "fiis_rankings",
        },
    ]

    outputs = [
        build_case_payload(case["case_id"], case["question"], case["entity"])
        for case in cases
    ]

    for payload in outputs:
        print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
