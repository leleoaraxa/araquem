#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests


DEFAULT_QUESTIONS: List[str] = [
    "Como está o KNRI11 e o XPLG11?",
    "Quais são os dividendos do HGLG11?",
    "Quais são os imóveis do HGLG11?",
    "Qual o DY do HGLG11?",
    "Qual o preço do HGLG11?",
    "Quais os riscos do KNRI11?",
    "Quais as notícias do KNRI11?",
    "Qual foi o dólar hoje?",
    "Qual a SELIC de ontem?",
    "Qual é a minha carteira hoje?",
]


@dataclass
class Config:
    base_url: str
    conversation_id: str
    client_id: str
    nickname: str
    timeout_s: float
    out_dir: str
    print_answer: bool


def _ask_url(cfg: Config) -> str:
    # IMPORTANT: use explain=true
    return cfg.base_url.rstrip("/") + "/ask?explain=true"


def _best_effort_topk_intents(scoring: Any) -> Tuple[Optional[str], Optional[str]]:
    """
    Tenta extrair os 2 primeiros intents (top1/top2) do bloco de scoring,
    sem assumir um shape único. Aceita formatos:
      - {"intents_ranked": [{"intent": "x", ...}, {"intent": "y", ...}]}
      - {"intents": [{"intent": "x", ...}, ...]}
      - {"ranked": [{"intent": "x", ...}, ...]}
      - lista direta [{"intent": "x"}, ...]
      - chaves alternativas ("name", "id", "label")
    """
    if scoring is None:
        return None, None

    candidates = None
    if isinstance(scoring, list):
        candidates = scoring
    elif isinstance(scoring, dict):
        for k in ("intents_ranked", "intents", "ranked", "top_intents", "candidates"):
            v = scoring.get(k)
            if isinstance(v, list) and v:
                candidates = v
                break

    if not isinstance(candidates, list) or not candidates:
        return None, None

    def _pick_intent(obj: Any) -> Optional[str]:
        if isinstance(obj, dict):
            for kk in ("intent", "name", "id", "label"):
                vv = obj.get(kk)
                if isinstance(vv, str) and vv.strip():
                    return vv.strip()
        if isinstance(obj, str) and obj.strip():
            return obj.strip()
        return None

    top1 = _pick_intent(candidates[0])
    top2 = _pick_intent(candidates[1]) if len(candidates) > 1 else None
    return top1, top2


def _safe_get(d: Dict[str, Any], path: str, default=None):
    cur: Any = d
    for part in path.split("."):
        if cur is None:
            return default
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return default
    return cur if cur is not None else default


def _post_question(
    cfg: Config, question: str
) -> Tuple[Dict[str, Any], float, Optional[str]]:
    url = _ask_url(cfg)
    payload = {
        "question": question,
        "conversation_id": cfg.conversation_id,
        "nickname": cfg.nickname,
        "client_id": cfg.client_id,
    }
    t0 = time.time()
    try:
        r = requests.post(url, json=payload, timeout=cfg.timeout_s)
        dt_ms = (time.time() - t0) * 1000.0
        # tenta JSON mesmo em erro (para capturar status/message)
        try:
            data = r.json()
        except Exception:
            data = {"_raw_text": r.text}
        data["_http_status"] = r.status_code
        return data, dt_ms, None
    except Exception as e:
        dt_ms = (time.time() - t0) * 1000.0
        return {}, dt_ms, str(e)


def _extract_row(
    resp: Dict[str, Any],
    question: str,
    elapsed_ms_client: float,
    request_error: Optional[str],
) -> Dict[str, Any]:
    # status base do endpoint (quando existir)
    status_reason = _safe_get(resp, "status.reason")
    status_message = _safe_get(resp, "status.message")

    # atalhos topo (o seu payload já tem intent/entity no meta)
    chosen_intent = _safe_get(resp, "meta.intent") or _safe_get(
        resp, "meta.planner.chosen.intent"
    )
    chosen_entity = _safe_get(resp, "meta.entity") or _safe_get(
        resp, "meta.planner.chosen.entity"
    )
    planner_score = _safe_get(resp, "meta.planner_score") or _safe_get(
        resp, "meta.planner.chosen.score"
    )

    # gate (FIX: thresholds_applied lives under scoring)
    gate = (
        _safe_get(resp, "meta.planner.explain.scoring.thresholds_applied")
        or _safe_get(resp, "meta.planner.explain.thresholds_applied")
        or {}
    )
    gate_accepted = gate.get("accepted")
    gate_source = gate.get("source")
    gate_reason = gate.get("reason")
    gate_min_score = gate.get("min_score")
    gate_min_gap = gate.get("min_gap")
    gate_gap = gate.get("gap")
    score_for_gate = gate.get("score_for_gate")

    # gaps
    gap_base = _safe_get(resp, "meta.planner.explain.scoring.intent_top2_gap_base")
    gap_final = _safe_get(resp, "meta.planner.explain.scoring.intent_top2_gap_final")

    # ranking (top1/top2) — ajuda muito a explicar gap=0.0 (colisão)
    scoring_blob = _safe_get(resp, "meta.planner.explain.scoring")
    intent_top1, intent_top2 = _best_effort_topk_intents(scoring_blob)

    # resultado
    rows_total = _safe_get(resp, "meta.rows_total")
    result_key = _safe_get(resp, "meta.result_key")

    # cache
    cache_hit = _safe_get(resp, "meta.cache.hit")
    cache_key = _safe_get(resp, "meta.cache.key")
    cache_ttl = _safe_get(resp, "meta.cache.ttl")
    cache_layer = _safe_get(resp, "meta.cache.layer")

    # rag/fusion
    rag_used = _safe_get(resp, "meta.planner.explain.rag.used")
    fusion_used = _safe_get(resp, "meta.planner.explain.fusion.used")

    # narrator
    narrator_used = _safe_get(resp, "meta.narrator.used")
    narrator_latency_ms = _safe_get(resp, "meta.narrator.latency_ms")
    narrator_error = _safe_get(resp, "meta.narrator.error")

    # executor latency do pipeline (se existir) vs client measured
    elapsed_ms_server = _safe_get(resp, "meta.elapsed_ms")

    http_status = resp.get("_http_status") or 0

    # total (aproximação): server + narrator quando existir
    total_ms = None
    if elapsed_ms_server is not None:
        try:
            total_ms = float(elapsed_ms_server)
            if narrator_used and narrator_latency_ms is not None:
                total_ms += float(narrator_latency_ms)
        except Exception:
            total_ms = None

    return {
        "question": question,
        "http_status": http_status,
        "request_error": request_error,
        "status_reason": status_reason,
        "status_message": status_message,
        "chosen_intent": chosen_intent,
        "chosen_entity": chosen_entity,
        "planner_score": planner_score,
        "gate_accepted": gate_accepted,
        "gate_source": gate_source,
        "gate_reason": gate_reason,
        "gate_min_score": gate_min_score,
        "gate_min_gap": gate_min_gap,
        "gate_gap": gate_gap,
        "score_for_gate": score_for_gate,
        "intent_top2_gap_base": gap_base,
        "intent_top2_gap_final": gap_final,
        "intent_top1": intent_top1,
        "intent_top2": intent_top2,
        "rows_total": rows_total,
        "result_key": result_key,
        "cache_hit": cache_hit,
        "cache_layer": cache_layer,
        "cache_ttl": cache_ttl,
        "cache_key": cache_key,
        "rag_used": rag_used,
        "fusion_used": fusion_used,
        "elapsed_ms_server": elapsed_ms_server,
        "elapsed_ms_total": total_ms,
        "elapsed_ms_client": round(elapsed_ms_client, 3),
        "narrator_used": narrator_used,
        "narrator_latency_ms": narrator_latency_ms,
        "narrator_error": narrator_error,
    }


def _load_questions(args: argparse.Namespace) -> List[str]:
    if args.questions_file:
        with open(args.questions_file, "r", encoding="utf-8") as f:
            qs = [
                ln.strip()
                for ln in f.readlines()
                if ln.strip() and not ln.strip().startswith("#")
            ]
        return qs
    if args.inline:
        n = args.questions
        return DEFAULT_QUESTIONS[:n]
    # default: inline também, mas exige --questions-file ou --inline para ser explícito
    raise SystemExit("Use --inline ou --questions-file.")


def _ensure_out_dir(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)


def _write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--inline",
        action="store_true",
        help="Usa lista embutida de perguntas (DEFAULT_QUESTIONS).",
    )
    ap.add_argument(
        "--questions",
        type=int,
        default=10,
        help="Quantas perguntas do inline usar (default=10).",
    )
    ap.add_argument(
        "--questions-file", default="", help="Arquivo txt com perguntas (1 por linha)."
    )
    ap.add_argument("--base-url", required=True, help="Ex: http://localhost:8000")
    ap.add_argument("--conversation-id", required=True)
    ap.add_argument("--client-id", default="dev")
    ap.add_argument("--nickname", default="diagnostics")
    ap.add_argument("--timeout-s", type=float, default=90.0)
    ap.add_argument("--out-dir", default="out")
    ap.add_argument(
        "--print-answer",
        action="store_true",
        help="Imprime também o campo answer (útil para debug pontual).",
    )
    args = ap.parse_args()

    cfg = Config(
        base_url=args.base_url,
        conversation_id=args.conversation_id,
        client_id=args.client_id,
        nickname=args.nickname,
        timeout_s=args.timeout_s,
        out_dir=args.out_dir,
        print_answer=args.print_answer,
    )

    questions = _load_questions(args)
    _ensure_out_dir(cfg.out_dir)

    rows: List[Dict[str, Any]] = []
    for i, q in enumerate(questions, start=1):
        resp, dt_ms, err = _post_question(cfg, q)
        row = _extract_row(resp, q, dt_ms, err)
        row["idx"] = i
        rows.append(row)

        # print curto para console
        intent = (row.get("chosen_intent") or "-")[:12]
        entity = (row.get("chosen_entity") or "-")[:12]
        top1 = (row.get("intent_top1") or "-")[:12]
        top2 = (row.get("intent_top2") or "-")[:12]
        gate = (
            "Y"
            if row.get("gate_accepted") is True
            else ("N" if row.get("gate_accepted") is False else "-")
        )
        src = (row.get("gate_source") or "-")[:8]
        gap_b = row.get("intent_top2_gap_base")
        gap_f = row.get("intent_top2_gap_final")
        rag = "Y" if row.get("rag_used") is True else "-"
        fusion = "Y" if row.get("fusion_used") is True else "-"
        cache = "Y" if row.get("cache_hit") else "N"
        ms = int(row.get("elapsed_ms_server") or row.get("elapsed_ms_client") or 0)
        llm_ms = (
            int(row.get("narrator_latency_ms") or 0) if row.get("narrator_used") else 0
        )

        print(
            f"{i:>2} | {intent:<12} | {entity:<12} | "
            f"gate={gate} src={src:<8} gap_b={gap_b} gap_f={gap_f} "
            f"top1={top1} top2={top2} "
            f"rag={rag} fusion={fusion} cache={cache} ms={ms} llm_ms={llm_ms}"
        )

        if cfg.print_answer:
            ans = _safe_get(resp, "answer")
            if isinstance(ans, str) and ans.strip():
                print(f"   answer: {ans.strip()[:500]}")

    jsonl_path = os.path.join(cfg.out_dir, "audit_results.jsonl")
    csv_path = os.path.join(cfg.out_dir, "audit_results.csv")
    _write_jsonl(jsonl_path, rows)
    _write_csv(csv_path, rows)

    print(f"\nWrote: {jsonl_path}")
    print(f"Wrote: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
