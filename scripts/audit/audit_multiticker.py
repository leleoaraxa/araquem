"""Audit script for multi-ticker/multi-intent handling.

This tool sends a fixed list of prompts to the local /ask endpoint with
`explain=true`, captures routing and gate metadata, and stores both JSONL and
Markdown summaries for reproducibility.

If the API on http://localhost:8000 is not reachable, the script exits with a
clear message so the auditor can bring the service up before re-running.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime
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

EXPLAIN_FLAG = True
OUTPUT_JSONL = Path("data/diagnostics/audit_multiticker_results.jsonl")
OUTPUT_MD = Path("docs/dev/audits/AUDIT_MULTITICKER.md")


def _build_client() -> httpx.Client:
    """Build an HTTPX client hitting the local FastAPI app.

    The audit requires a live API at http://localhost:8000. If the service is
    not reachable, the script exits with a clear instruction to start it.
    """

    base_url = "http://localhost:8000"
    health_url = f"{base_url}/healthz"

    try:
        ping = httpx.get(health_url, timeout=2.0)
        if ping.status_code == 200:
            return httpx.Client(base_url=base_url, timeout=60.0)
    except Exception:
        pass

    # Tenta uma chamada mínima ao /ask para confirmar indisponibilidade
    try:
        probe_resp = httpx.post(
            f"{base_url}/ask",
            json={"question": "ping"},
            timeout=4.0,
        )
        if probe_resp.status_code < 500:
            return httpx.Client(base_url=base_url, timeout=60.0)
    except Exception:
        pass

    raise SystemExit(
        "API local inacessível em http://localhost:8000. Inicie o serviço "
        "(ex.: `uvicorn app.api.__init__:get_app --factory --host 0.0.0.0 --port 8000`) "
        "e rode novamente."
    )


def _shorten(text: Any, limit: int = 200) -> str:
    if not isinstance(text, str):
        return ""
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _collect_fields(resp_json: Dict[str, Any]) -> Dict[str, Any]:
    status_block = resp_json.get("status") if isinstance(resp_json, dict) else {}
    if not isinstance(status_block, dict):
        status_block = {}

    meta = resp_json.get("meta") if isinstance(resp_json, dict) else {}
    if not isinstance(meta, dict):
        meta = {}

    gate = meta.get("gate") if isinstance(meta, dict) else {}
    if not isinstance(gate, dict):
        gate = {}

    planner_meta = meta.get("planner") if isinstance(meta, dict) else {}
    if not isinstance(planner_meta, dict):
        planner_meta = {}

    gate_thresholds = gate.get("thresholds_applied") if isinstance(gate, dict) else None
    planner_scoring = (planner_meta.get("explain") or {}).get("scoring", {})

    # meta.gate.planner.explain.scoring pode existir quando gate é aplicado
    gate_scoring = (gate.get("planner") or {}).get("explain", {}).get("scoring", {})
    if gate_scoring:
        planner_scoring = gate_scoring

    thresholds_applied = planner_scoring.get("thresholds_applied")
    if not thresholds_applied and isinstance(gate_thresholds, dict):
        thresholds_applied = gate_thresholds

    status_reason = status_block.get("reason")
    if status_reason is None:
        status_reason = resp_json.get("reason") if isinstance(resp_json, dict) else None

    answer_field: Optional[str] = None
    ans_value = resp_json.get("answer") if isinstance(resp_json, dict) else None
    if isinstance(ans_value, str):
        answer_field = ans_value
    elif isinstance(resp_json, dict):
        fallback_ans = resp_json.get("answer")
        if isinstance(fallback_ans, str):
            answer_field = fallback_ans

    return {
        "status_reason": status_reason,
        "meta_gate_reason": gate.get("reason"),
        "meta_gate_top2_gap": gate.get("top2_gap"),
        "meta_gate_min_gap": gate.get("min_gap"),
        "meta_gate_min_score": gate.get("min_score"),
        "meta_result_key": meta.get("result_key"),
        "meta_entity": meta.get("entity"),
        "meta_intent": meta.get("intent"),
        "intent_top2_gap_base": planner_scoring.get("intent_top2_gap_base"),
        "intent_top2_gap_final": planner_scoring.get("intent_top2_gap_final"),
        "thresholds_applied_min_score": (
            (thresholds_applied or {}).get("min_score")
            if isinstance(thresholds_applied, dict)
            else None
        ),
        "thresholds_applied_min_gap": (
            (thresholds_applied or {}).get("min_gap")
            if isinstance(thresholds_applied, dict)
            else None
        ),
        "thresholds_applied_gap": (
            (thresholds_applied or {}).get("gap")
            if isinstance(thresholds_applied, dict)
            else None
        ),
        "thresholds_applied_accepted": (
            (thresholds_applied or {}).get("accepted")
            if isinstance(thresholds_applied, dict)
            else None
        ),
        "thresholds_applied_source": (
            (thresholds_applied or {}).get("source")
            if isinstance(thresholds_applied, dict)
            else None
        ),
        "answer": _shorten(answer_field),
    }


def run_audit() -> None:
    client = _build_client()
    OUTPUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat(timespec="seconds")
    rows_md: List[str] = [
        "# Audit Multi-Ticker",
        "",
        f"Timestamp: {timestamp}",
        f"Endpoint: POST http://localhost:8000/ask (explain={EXPLAIN_FLAG})",
        "Command: python scripts/audit/audit_multiticker.py",
        "",
        "| label | question | status.reason | gate.reason | gate.top2_gap | gate.min_gap | gate.min_score | intent | entity | result_key | intent_gap_base | intent_gap_final | thr_min_score | thr_min_gap | thr_gap | thr_accepted | thr_source | answer |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
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
                resp = client.post(f"/ask{suffix}", json=payload, timeout=60.0)
            except Exception as exc:
                record = {
                    "label": q.label,
                    "question": q.text,
                    "http_status": None,
                    "status_reason": f"request_error: {exc}",
                }
                f_jsonl.write(json.dumps(record, ensure_ascii=False) + "\n")
                rows_md.append(
                    "| "
                    + " | ".join(
                        [
                            q.label,
                            q.text,
                            record["status_reason"],
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ]
                    )
                    + " |"
                )
                continue

            try:
                data = resp.json()
            except Exception:
                data = {"_parse_error": _shorten(resp.text, 200)}

            fields = _collect_fields(data)
            if not fields.get("status_reason"):
                fields["status_reason"] = resp.reason_phrase
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
                        str(record.get("meta_gate_top2_gap")),
                        str(record.get("meta_gate_min_gap")),
                        str(record.get("meta_gate_min_score")),
                        str(record.get("meta_intent")),
                        str(record.get("meta_entity")),
                        str(record.get("meta_result_key")),
                        str(record.get("intent_top2_gap_base")),
                        str(record.get("intent_top2_gap_final")),
                        str(record.get("thresholds_applied_min_score")),
                        str(record.get("thresholds_applied_min_gap")),
                        str(record.get("thresholds_applied_gap")),
                        str(record.get("thresholds_applied_accepted")),
                        str(record.get("thresholds_applied_source")),
                        _shorten(record.get("answer"), 60),
                    ]
                )
                + " |"
            )

    OUTPUT_MD.write_text("\n".join(rows_md), encoding="utf-8")
    print(
        f"Audit completed. JSONL saved to {OUTPUT_JSONL} and markdown to {OUTPUT_MD}."
    )


if __name__ == "__main__":
    run_audit()
