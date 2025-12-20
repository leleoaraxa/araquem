#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# scripts/diagnostics/run_ask_suite.py

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


def _sorted_top2_from_score_map(
    score_map: Dict[Any, Any],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Recebe um dict do tipo {intent: score} e retorna (top1, top2) por score desc.
    Filtra somente (str, number).
    """
    items: List[Tuple[str, float]] = []
    for intent, score in score_map.items():
        if isinstance(intent, str) and isinstance(score, (int, float)):
            items.append((intent, float(score)))
    if not items:
        return None, None
    items.sort(key=lambda x: x[1], reverse=True)
    top1 = items[0][0]
    top2 = items[1][0] if len(items) > 1 else None
    return top1, top2


def _pick_intent_name(obj: Any) -> Optional[str]:
    if isinstance(obj, dict):
        for kk in ("intent", "name", "id", "label"):
            vv = obj.get(kk)
            if isinstance(vv, str) and vv.strip():
                return vv.strip()
    if isinstance(obj, str) and obj.strip():
        return obj.strip()
    return None


def _best_effort_topk_intents(scoring: Any) -> Tuple[Optional[str], Optional[str], str]:
    """
    Extrai top1/top2 do bloco scoring, aceitando múltiplos shapes reais do Araquem.

    Ordem de preferência (do mais “canônico” no seu explain atual):
      1) scoring["final_combined"] -> lista de {intent, score}
      2) scoring["combined"]["intent"] -> lista de {name/base/rag/combined}
      3) scoring["intent"] -> lista de {name, score}
      4) scoring["intent_scores_*"] / "intent_scores" -> dict {intent: score}
      5) fallback: listas genéricas (intents_ranked, ranked, etc.)
    """
    if scoring is None:
        return None, None, "none"

    # 1) final_combined (lista)
    if isinstance(scoring, dict):
        fc = scoring.get("final_combined")
        if isinstance(fc, list) and fc:
            top1 = _pick_intent_name(fc[0])
            top2 = _pick_intent_name(fc[1]) if len(fc) > 1 else None
            return top1, top2, "list:final_combined"

    # 2) combined.intent (lista)
    if isinstance(scoring, dict):
        cmb = scoring.get("combined")
        if isinstance(cmb, dict):
            cmb_int = cmb.get("intent")
            if isinstance(cmb_int, list) and cmb_int:
                top1 = _pick_intent_name(cmb_int[0])
                top2 = _pick_intent_name(cmb_int[1]) if len(cmb_int) > 1 else None
                return top1, top2, "list:combined.intent"

    # 3) scoring.intent (lista)
    if isinstance(scoring, dict):
        s_int = scoring.get("intent")
        if isinstance(s_int, list) and s_int:
            top1 = _pick_intent_name(s_int[0])
            top2 = _pick_intent_name(s_int[1]) if len(s_int) > 1 else None
            return top1, top2, "list:scoring.intent"

    # 4) dicts de scores
    if isinstance(scoring, dict):
        for k in (
            "intent_scores_final",
            "intent_scores_base",
            "intent_scores",
            "scores_final",
            "scores_base",
            "scores",
        ):
            v = scoring.get(k)
            if isinstance(v, dict) and v:
                top1, top2 = _sorted_top2_from_score_map(v)
                if top1:
                    return top1, top2, f"dict_scores:{k}"

    # 5) listas candidatas (fallback)
    if isinstance(scoring, dict):
        for k in ("intents_ranked", "intents", "ranked", "top_intents", "candidates"):
            v = scoring.get(k)
            if isinstance(v, list) and v:
                top1 = _pick_intent_name(v[0])
                top2 = _pick_intent_name(v[1]) if len(v) > 1 else None
                return top1, top2, f"list:{k}"

    # 6) scoring já é lista
    if isinstance(scoring, list) and scoring:
        top1 = _pick_intent_name(scoring[0])
        top2 = _pick_intent_name(scoring[1]) if len(scoring) > 1 else None
        return top1, top2, "list"

    return None, None, "unknown"


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
    status_reason = _safe_get(resp, "status.reason")
    status_message = _safe_get(resp, "status.message")

    chosen_intent = _safe_get(resp, "meta.intent") or _safe_get(
        resp, "meta.planner.chosen.intent"
    )
    chosen_entity = _safe_get(resp, "meta.entity") or _safe_get(
        resp, "meta.planner.chosen.entity"
    )
    planner_score = _safe_get(resp, "meta.planner_score") or _safe_get(
        resp, "meta.planner.chosen.score"
    )

    # gate
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

    # scoring introspection
    scoring = _safe_get(resp, "meta.planner.explain.scoring")
    intent_top1, intent_top2, scoring_mode = _best_effort_topk_intents(scoring)

    scoring_keys = ""
    if isinstance(scoring, dict):
        scoring_keys = ";".join(sorted(scoring.keys()))

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

    # total estimado (explícito como “estimate”)
    elapsed_ms_total_est = None
    try:
        if elapsed_ms_server is not None:
            elapsed_ms_total_est = float(elapsed_ms_server)
            # Só soma se vier separado; se não vier, fica só server.
            if narrator_used and narrator_latency_ms is not None:
                elapsed_ms_total_est += float(narrator_latency_ms)
    except Exception:
        elapsed_ms_total_est = None

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
        "scoring_mode": scoring_mode,
        "scoring_keys": scoring_keys,
        "rows_total": rows_total,
        "result_key": result_key,
        "cache_hit": cache_hit,
        "cache_layer": cache_layer,
        "cache_ttl": cache_ttl,
        "cache_key": cache_key,
        "rag_used": rag_used,
        "fusion_used": fusion_used,
        "elapsed_ms_server": elapsed_ms_server,
        "elapsed_ms_total_est": elapsed_ms_total_est,
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


def _print_summary(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return

    total = len(rows)
    gate_ok = sum(1 for r in rows if r.get("gate_accepted") is True)
    gate_no = sum(1 for r in rows if r.get("gate_accepted") is False)
    cache_hits = sum(1 for r in rows if r.get("cache_hit") is True)
    narrator_used = sum(1 for r in rows if r.get("narrator_used") is True)

    # Top lentas por client
    by_client = sorted(
        rows, key=lambda r: float(r.get("elapsed_ms_client") or 0.0), reverse=True
    )[:3]
    # Top lentas por narrator
    by_llm = sorted(
        rows, key=lambda r: float(r.get("narrator_latency_ms") or 0.0), reverse=True
    )[:3]

    print("\n=== RESULT COMPLETO (SUMÁRIO) ===")
    print(f"Perguntas: {total}")
    print(f"Gate: OK={gate_ok} | FAIL={gate_no}")
    print(f"Cache hit: {cache_hits}/{total} ({(cache_hits/total)*100:.1f}%)")
    print(f"Narrator usado: {narrator_used}/{total} ({(narrator_used/total)*100:.1f}%)")

    if gate_no > 0:
        print("\nFalhas de gate (gate=N):")
        for r in rows:
            if r.get("gate_accepted") is False:
                print(
                    f"- idx={r.get('idx')} | q={r.get('question')!r} | "
                    f"intent={r.get('chosen_intent')} entity={r.get('chosen_entity')} | "
                    f"reason={r.get('gate_reason')} score={r.get('score_for_gate')} "
                    f"min_score={r.get('gate_min_score')} min_gap={r.get('gate_min_gap')} gap={r.get('gate_gap')}"
                )

    print("\nTop 3 mais lentas (elapsed_ms_client):")
    for r in by_client:
        print(
            f"- idx={r.get('idx')} | {r.get('elapsed_ms_client')} ms | {r.get('question')}"
        )

    print("\nTop 3 maior latência LLM (narrator_latency_ms):")
    for r in by_llm:
        print(
            f"- idx={r.get('idx')} | {r.get('narrator_latency_ms')} ms | {r.get('question')}"
        )


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

    _print_summary(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
