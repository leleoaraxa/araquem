"""Audit script for multi-ticker/multi-intent handling.

This tool sends a fixed list of prompts to the local /ask endpoint with
`explain=true`, captures routing and gate metadata, and stores both JSONL and
Markdown summaries for reproducibility.

The script is defensive: if the API cannot be reached, it exits with a clear
message. For hermetic runs without external services (DB/Redis), it boots an
in-process FastAPI app with minimal stubs so the planner path can be audited
without live backends.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx


@dataclass
class AuditQuestion:
    label: str
    text: str


QUESTIONS: List[AuditQuestion] = [
    AuditQuestion("mt_factual_prices", "preço de HGLG11 e KNRI11"),
    AuditQuestion("mt_factual_dividends", "dividendos de HGLG11, KNRI11 e MXRF11"),
    AuditQuestion(
        "mt_conceptual_compare",
        "compare HGLG11 e KNRI11 em setor, renda e risco",
    ),
    AuditQuestion(
        "mt_conceptual_macro",
        "como CDI versus DY 12m impacta FIIs como HGLG11 e MXRF11",
    ),
    AuditQuestion(
        "mt_conceptual_no_ticker",
        "como CDI vs DY 12m afeta FIIs (sem tickers)",
    ),
    AuditQuestion(
        "pure_conceptual_max_drawdown",
        "o que significa max drawdown alto",
    ),
    AuditQuestion(
        "pure_conceptual_sharpe",
        "o que é um sharpe ratio negativo",
    ),
    AuditQuestion(
        "multi_intent_sector_yield",
        "setor do HGLG11 e renda/dividendos esperados",
    ),
    AuditQuestion(
        "multi_intent_sector_risk",
        "setor do KNRI11 e risco de vacância",
    ),
    AuditQuestion(
        "multi_intent_rankings",
        "ranking de HGLG11 e MXRF11 por yield e por risco",
    ),
    AuditQuestion(
        "macro_multi_entity",
        "efeito do CDI e inflação no IFIX e IBOV em 2024",
    ),
    AuditQuestion(
        "macro_currency",
        "como dólar e euro variaram versus o real em 2023",
    ),
]

EXPLAIN_FLAG = False
OUTPUT_JSONL = Path("data/diagnostics/audit_multiticker_results.jsonl")
OUTPUT_MD = Path("docs/dev/audits/AUDIT_MULTITICKER.md")


def _build_client() -> httpx.Client:
    """Build an HTTPX client hitting the local FastAPI app.

    The function tries to use a running localhost API first. If it is not
    reachable, it falls back to an in-process ASGI app (with stubbed cache and
    executor) so the planner/gate path can be exercised without external
    services.
    """

    # Prefer a real localhost API if available.
    try:
        ping = httpx.get("http://localhost:8000/healthz", timeout=2.0)
        if ping.status_code == 200:
            return httpx.Client(base_url="http://localhost:8000", timeout=10.0)
    except Exception:
        pass

    # Fallback: ASGI in-process client using httpx.ASGITransport.
    try:
        from fastapi import FastAPI
        from starlette.testclient import TestClient

        from app.planner.planner import Planner
        import app.planner.planner as planner_module

        # Desliga RAG e re-rank para evitar dependências externas no modo audit.
        def _load_thresholds_stub(path: str = "data/ops/planner_thresholds.yaml"):
            return {
                "planner": {
                    "thresholds": {
                        "defaults": {"min_score": 0.8, "min_gap": 0.1},
                        "apply_on": "base",
                    },
                    "rag": {
                        "enabled": False,
                        "k": 0,
                        "min_score": 0.0,
                        "weight": 0.0,
                        "re_rank": {"enabled": False, "mode": "blend", "weight": 0.0},
                    },
                }
            }

        planner_module._load_thresholds = _load_thresholds_stub  # type: ignore
        planner = Planner("data/ontology/entity.yaml")

        app = FastAPI()

        @app.post("/ask")
        def _ask(payload: Dict[str, Any]):
            question = (payload or {}).get("question") or ""
            plan = planner.explain(question)
            chosen = plan.get("chosen") or {}
            return {
                "status": {"reason": "ok"},
                "results": {},
                "meta": {
                    "planner": plan,
                    "intent": chosen.get("intent"),
                    "entity": chosen.get("entity"),
                    "result_key": None,
                },
                "answer": "",
            }

        return TestClient(app, base_url="http://localhost")
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise SystemExit(
            f"Falha ao iniciar cliente HTTP local ou ASGI in-process: {exc}"
        )


def _shorten(text: Any, limit: int = 200) -> str:
    if not isinstance(text, str):
        return ""
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _collect_fields(resp_json: Dict[str, Any]) -> Dict[str, Any]:
    status_block = resp_json.get("status") or {}
    if not isinstance(status_block, dict):
        status_block = {}
    meta = resp_json.get("meta") or {}
    if not isinstance(meta, dict):
        meta = {}
    gate = meta.get("gate") or {}
    if not isinstance(gate, dict):
        gate = {}
    thresholds = gate.get("thresholds_applied") if isinstance(gate, dict) else None
    scoring = (gate.get("planner") or {}).get("explain", {}).get("scoring", {})
    if not thresholds and isinstance(meta.get("planner"), dict):
        scoring = (meta["planner"].get("explain") or {}).get("scoring", {})

    return {
        "status_reason": status_block.get("reason"),
        "meta_gate_reason": gate.get("reason"),
        "meta_result_key": meta.get("result_key"),
        "meta_entity": meta.get("entity"),
        "meta_intent": meta.get("intent"),
        "top2_gap": scoring.get("intent_top2_gap"),
        "min_gap": thresholds.get("min_gap") if isinstance(thresholds, dict) else None,
        "min_score": thresholds.get("min_score") if isinstance(thresholds, dict) else None,
        "answer": _shorten(resp_json.get("answer")),
    }


def run_audit() -> None:
    client = _build_client()
    OUTPUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)

    rows_md: List[str] = [
        "# Audit Multi-Ticker", "", f"Endpoint: POST /ask (explain={EXPLAIN_FLAG})", "",
        "| label | question | status.reason | gate.reason | intent | entity | result_key | top2_gap | min_gap | min_score | answer |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    with OUTPUT_JSONL.open("w", encoding="utf-8") as f_jsonl:
        for q in QUESTIONS:
            payload = {
                "question": q.text,
                "conversation_id": "audit-multiticker",
                "nickname": "audit",
                "client_id": "audit",
            }
            try:
                suffix = "?explain=true" if EXPLAIN_FLAG else ""
                resp = client.post(f"/ask{suffix}", json=payload, timeout=30.0)
            except Exception as exc:
                raise SystemExit(f"Falha ao chamar /ask: {exc}")

            try:
                data = resp.json()
            except Exception as exc:  # pragma: no cover - malformed response
                raise SystemExit(f"Resposta inválida da API: {exc}")

            fields = _collect_fields(data)
            record = {
                "label": q.label,
                "question": q.text,
                "http_status": resp.status_code,
                **fields,
            }
            f_jsonl.write(json.dumps(record, ensure_ascii=False) + "\n")

            rows_md.append(
                "| "
                + " | ".join(
                    [
                        q.label,
                        q.text,
                        str(record.get("status_reason")),
                        str(record.get("meta_gate_reason")),
                        str(record.get("meta_intent")),
                        str(record.get("meta_entity")),
                        str(record.get("meta_result_key")),
                        str(record.get("top2_gap")),
                        str(record.get("min_gap")),
                        str(record.get("min_score")),
                        _shorten(record.get("answer"), 60),
                    ]
                )
                + " |"
            )

    OUTPUT_MD.write_text("\n".join(rows_md), encoding="utf-8")
    print(f"Audit completed. JSONL saved to {OUTPUT_JSONL} and markdown to {OUTPUT_MD}.")


if __name__ == "__main__":
    run_audit()
