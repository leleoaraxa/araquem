#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# scripts/diagnostics/run_ask_suite.py

import argparse
import csv
import glob
import json
import os
import sys
from pathlib import Path
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


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
    type_user: str
    timeout_s: float
    out_dir: str
    print_answer: bool
    explain: bool


def _ask_url(cfg: Config) -> str:
    base = cfg.base_url.rstrip("/") + "/ask"
    if cfg.explain:
        return base + "?explain=true"
    return base


def _looks_like_path(value: str) -> bool:
    if value.endswith(".json"):
        return True
    if os.path.isabs(value):
        return True
    return os.sep in value or (os.altsep and os.altsep in value)


def _resolve_suite_arg(value: str, suite_dir: str) -> str:
    if _looks_like_path(value):
        return value
    return os.path.join(suite_dir.rstrip("/"), f"{value}_suite.json")


def _resolve_suite_paths(args: argparse.Namespace) -> List[str]:
    suite_paths: List[str] = []
    base_dir = args.suite_dir.rstrip("/")
    if args.suite_path:
        suite_paths.append(args.suite_path)
    if getattr(args, "suite_name", ""):
        suite_paths.append(_resolve_suite_arg(args.suite_name, base_dir))
    for item in args.suite or []:
        suite_paths.append(_resolve_suite_arg(item, base_dir))
    if args.all_suites:
        pattern = os.path.join(base_dir, args.suite_glob)
        suite_paths.extend(sorted(glob.glob(pattern)))
    return suite_paths


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


def _parse_status(body: Dict[str, Any]) -> Tuple[bool, Any, Optional[str]]:
    status_raw = body.get("status")
    status_reason = None
    status_value = None

    if isinstance(status_raw, dict):
        status_value = status_raw.get("status")
        status_reason = status_raw.get("reason") or status_raw.get("message")
        # Back-compat: algumas respostas trazem apenas {reason:"ok", message:"ok"}
        if status_value is None:
            rr = status_raw.get("reason")
            mm = status_raw.get("message")
            if rr == "ok" and (mm == "ok" or mm is None):
                status_value = "ok"
    else:
        status_value = status_raw

    if status_reason is None and isinstance(status_value, str):
        status_reason = status_value

    status_ok = status_value == "ok"
    return status_ok, status_raw, status_reason


def _selftest_parse_status() -> None:
    cases = [
        ({"status": "ok"}, True),
        ({"status": {"reason": "ok", "message": "ok"}}, True),
    ]
    for payload, expected_ok in cases:
        ok, raw, _ = _parse_status(payload)
        assert ok is expected_ok, f"Expected status_ok {expected_ok} for {payload}"
        assert raw == payload["status"], f"Expected raw {payload['status']}"


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


def _best_effort_topk_intents(
    scoring: Any, chosen_intent: Optional[str] = None
) -> Tuple[Optional[str], Optional[str], str]:
    """
    Extrai top1/top2 do bloco de scoring sem assumir shape único.
    Prioriza listas ranqueadas e listas com {intent/name/id/label, score}.
    """
    if scoring is None:
        return None, None, "none"

    def _pick_intent(obj: Any) -> Optional[str]:
        if isinstance(obj, dict):
            for kk in ("intent", "name", "id", "label"):
                vv = obj.get(kk)
                if isinstance(vv, str) and vv.strip():
                    return vv.strip()
        if isinstance(obj, str) and obj.strip():
            return obj.strip()
        return None

    def _maybe_sort_by_score(items: List[Any]) -> List[Any]:
        # Se houver campo numérico 'score' em dict, ordena desc por score.
        scored = []
        unscored = []
        for it in items:
            if isinstance(it, dict) and isinstance(it.get("score"), (int, float)):
                scored.append(it)
            else:
                unscored.append(it)
        if scored:
            scored.sort(key=lambda x: float(x["score"]), reverse=True)
            return scored + unscored
        return items

    # 1) scoring já é lista ranqueada
    if isinstance(scoring, list) and scoring:
        items = _maybe_sort_by_score(scoring)
        top1 = _pick_intent(items[0])
        top2 = _pick_intent(items[1]) if len(items) > 1 else None
        return top1, top2, "list"

    if isinstance(scoring, dict):
        # 2) campos com listas candidatas
        for k in (
            "final_combined",
            "intents_ranked",
            "intents",
            "ranked",
            "top_intents",
            "candidates",
        ):
            v = scoring.get(k)
            if isinstance(v, list) and v:
                items = _maybe_sort_by_score(v)
                top1 = _pick_intent(items[0])
                top2 = _pick_intent(items[1]) if len(items) > 1 else None
                return top1, top2, f"list:{k}"

        # 3) campos com dict de scores por intent
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

        # 4) scoring["intent"] pode ser lista OU dict
        v_intent = scoring.get("intent")
        if isinstance(v_intent, list) and v_intent:
            items = _maybe_sort_by_score(v_intent)
            top1 = _pick_intent(items[0])
            top2 = _pick_intent(items[1]) if len(items) > 1 else None
            return top1, top2, "list:intent"
        if isinstance(v_intent, dict) and v_intent:
            top1, top2 = _sorted_top2_from_score_map(v_intent)
            if top1:
                return top1, top2, "dict_scores:intent"
    if chosen_intent:
        return chosen_intent, None, "fallback:chosen_intent"

    return None, None, "unknown"


def _compute_accuracy(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    intent_rows = [r for r in rows if r.get("expected_intent") is not None]
    entity_rows = [r for r in rows if r.get("expected_entity") is not None]
    both_rows = [r for r in rows if r.get("match_both") is not None]

    def _acc(matches: int, total: int) -> Optional[float]:
        if total == 0:
            return None
        return matches / float(total)

    matches_intent = sum(1 for r in intent_rows if r.get("match_intent") is True)
    matches_entity = sum(1 for r in entity_rows if r.get("match_entity") is True)
    matches_both = sum(1 for r in both_rows if r.get("match_both") is True)

    return {
        "intent": {
            "matches": matches_intent,
            "total": len(intent_rows),
            "accuracy": _acc(matches_intent, len(intent_rows)),
        },
        "entity": {
            "matches": matches_entity,
            "total": len(entity_rows),
            "accuracy": _acc(matches_entity, len(entity_rows)),
        },
        "both": {
            "matches": matches_both,
            "total": len(both_rows),
            "accuracy": _acc(matches_both, len(both_rows)),
        },
    }


def _print_final_summary(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return

    total = len(rows)
    status_ok = sum(1 for r in rows if r.get("status_ok") is True)
    status_not_ok = sum(1 for r in rows if r.get("status_ok") is False)
    gate_ok = sum(1 for r in rows if r.get("gate_accepted") is True)
    gate_fail = sum(1 for r in rows if r.get("gate_accepted") is False)
    cache_hits_response = sum(1 for r in rows if r.get("cache_hit_response") is True)
    cache_hits_metrics = sum(1 for r in rows if r.get("cache_hit_metrics") is True)
    narrator_used = sum(1 for r in rows if r.get("narrator_used") is True)

    acc = _compute_accuracy(rows)
    has_suite_expectations = any(
        (r.get("expected_intent") is not None) or (r.get("expected_entity") is not None)
        for r in rows
    )

    print("\n=== RESULT COMPLETO (SUMÁRIO) ===")
    print(f"Perguntas: {total}")
    print(f"Status: OK={status_ok} | NOT_OK={status_not_ok}")
    print(f"Gate: OK={gate_ok} | FAIL={gate_fail}")
    print(
        f"Cache hit (response): {cache_hits_response}/{total} "
        f"({(cache_hits_response/total*100.0 if total else 0.0):.1f}%)"
    )
    print(
        f"Cache hit (metrics): {cache_hits_metrics}/{total} "
        f"({(cache_hits_metrics/total*100.0 if total else 0.0):.1f}%)"
    )
    print(
        f"Narrator usado: {narrator_used}/{total} "
        f"({(narrator_used/total*100.0 if total else 0.0):.1f}%)"
    )

    if has_suite_expectations:
        print("\nAcurácia (modo suite):")
        print(
            f"- Intent: {acc['intent']['matches']}/{acc['intent']['total']} "
            f"({(acc['intent']['accuracy']*100.0 if acc['intent']['accuracy'] is not None else 0.0):.1f}%)"
        )
        print(
            f"- Entity: {acc['entity']['matches']}/{acc['entity']['total']} "
            f"({(acc['entity']['accuracy']*100.0 if acc['entity']['accuracy'] is not None else 0.0):.1f}%)"
        )
        print(
            f"- Ambos: {acc['both']['matches']}/{acc['both']['total']} "
            f"({(acc['both']['accuracy']*100.0 if acc['both']['accuracy'] is not None else 0.0):.1f}%)"
        )

        mismatches = [
            r
            for r in rows
            if (r.get("match_intent") is False) or (r.get("match_entity") is False)
        ]
        mismatches = sorted(mismatches, key=lambda r: r.get("idx") or 0)[:10]
        if mismatches:
            print("\nMismatches (até 10):")
            for r in mismatches:
                print(
                    f"- idx={r.get('idx')} | expected_intent={r.get('expected_intent')} "
                    f"expected_entity={r.get('expected_entity')} | "
                    f"chosen_intent={r.get('chosen_intent')} chosen_entity={r.get('chosen_entity')} | "
                    f"gate_accepted={r.get('gate_accepted')} gap_final={r.get('intent_top2_gap_final')} | "
                    f"q={r.get('question')}"
                )

    fails = [r for r in rows if r.get("gate_accepted") is False]
    if fails:
        print("\nFalhas de gate (gate=N):")
        for r in fails:
            print(
                f"- idx={r.get('idx')} | intent={r.get('chosen_intent')} entity={r.get('chosen_entity')} | "
                f"reason={r.get('gate_reason')} score={r.get('score_for_gate')} "
                f"min_score={r.get('gate_min_score')} min_gap={r.get('gate_min_gap')} gap={r.get('gate_gap')} | "
                f"q='{r.get('question')}'"
            )

    # top lentas no cliente
    slow = sorted(
        rows, key=lambda r: float(r.get("elapsed_ms_client") or 0.0), reverse=True
    )[:5]
    print("\nTop lentas (elapsed_ms_client):")
    for r in slow:
        print(
            f"- idx={r.get('idx')} | {r.get('elapsed_ms_client')} ms | {r.get('question')}"
        )

    # top LLM
    llm = [r for r in rows if r.get("narrator_used") is True]
    llm = sorted(
        llm, key=lambda r: float(r.get("narrator_latency_ms") or 0.0), reverse=True
    )[:5]
    print("\nTop LLM (narrator_latency_ms):")
    if llm:
        for r in llm:
            print(
                f"- idx={r.get('idx')} | {r.get('narrator_latency_ms')} ms | "
                f"err={r.get('narrator_error') or '-'} | {r.get('question')}"
            )
    else:
        print("- (nenhuma chamada ao narrator)")

    # “alertas” rápidos
    timeouts = [
        r
        for r in rows
        if isinstance(r.get("narrator_error"), str) and "Timeout" in r["narrator_error"]
    ]
    if timeouts:
        print("\nALERTA: timeouts de LLM detectados:")
        for r in timeouts:
            print(
                f"- idx={r.get('idx')} | {r.get('narrator_error')} | {r.get('question')}"
            )


def _post_question(
    cfg: Config, question: str
) -> Tuple[Dict[str, Any], float, Optional[str]]:
    url = _ask_url(cfg)
    payload = {
        "question": question,
        "conversation_id": cfg.conversation_id,
        "nickname": cfg.nickname,
        "client_id": cfg.client_id,
        "type_user": cfg.type_user,
    }
    t0 = time.time()
    try:
        r = requests.post(url, json=payload, timeout=cfg.timeout_s)
        if (
            r.status_code == 422
            and _is_missing_type_user(r)
            and not payload.get("type_user")
        ):
            payload["type_user"] = cfg.type_user or "diagnostics"
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


def _is_missing_type_user(response: requests.Response) -> bool:
    try:
        data = response.json()
    except Exception:
        return False
    detail = data.get("detail")
    if isinstance(detail, list):
        for item in detail:
            if not isinstance(item, dict):
                continue
            loc = item.get("loc")
            msg = item.get("msg")
            if (
                isinstance(loc, list)
                and "type_user" in loc
                and isinstance(msg, str)
                and "field required" in msg.lower()
            ):
                return True
    return False


def _extract_row(
    resp: Dict[str, Any],
    question: str,
    elapsed_ms_client: float,
    request_error: Optional[str],
    explain_enabled: bool,
    expected_intent: Optional[str] = None,
    expected_entity: Optional[str] = None,
    suite_name: Optional[str] = None,
    suite_description: Optional[str] = None,
) -> Dict[str, Any]:
    status_ok, status_raw, status_reason = _parse_status(resp)
    status_status = _safe_get(resp, "status.status") or (
        status_raw if isinstance(status_raw, str) else None
    )
    status_message = _safe_get(resp, "status.message")

    chosen_intent = _safe_get(resp, "meta.intent") or _safe_get(
        resp, "meta.planner.chosen.intent"
    )
    chosen_entity = _safe_get(resp, "meta.entity") or _safe_get(
        resp, "meta.planner.chosen.entity"
    )
    chosen_accepted = _safe_get(resp, "meta.planner.chosen.accepted")
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
    intent_top1, intent_top2, scoring_mode = _best_effort_topk_intents(
        scoring, chosen_intent
    )

    scoring_keys = ""
    if isinstance(scoring, dict):
        scoring_keys = ";".join(sorted(scoring.keys()))

    # resultado
    rows_total = _safe_get(resp, "meta.rows_total")
    result_key = _safe_get(resp, "meta.result_key")

    # cache
    cache_hit_response = _safe_get(resp, "meta.cache.hit")
    cache_key = _safe_get(resp, "meta.cache.key")
    cache_ttl = _safe_get(resp, "meta.cache.ttl")
    cache_layer = _safe_get(resp, "meta.cache.layer")
    cache_hit_metrics = _safe_get(resp, "meta.compute.metrics_cache_hit")

    # rag/fusion
    rag_used = _safe_get(resp, "meta.planner.explain.rag.used")
    fusion_used = _safe_get(resp, "meta.planner.explain.fusion.used")

    # narrator
    narrator_used = _safe_get(resp, "meta.narrator.used")
    narrator_latency_ms = _safe_get(resp, "meta.narrator.latency_ms")
    narrator_error = _safe_get(resp, "meta.narrator.error")

    # executor latency do pipeline (se existir) vs client measured
    elapsed_ms_server = _safe_get(resp, "meta.elapsed_ms")
    answer_text = _safe_get(resp, "answer")
    if not isinstance(answer_text, str):
        answer_text = None

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

    match_intent: Optional[bool] = None
    match_entity: Optional[bool] = None
    match_both: Optional[bool] = None

    if expected_intent is not None:
        match_intent = expected_intent == chosen_intent
    if expected_entity is not None:
        match_entity = expected_entity == chosen_entity
    if expected_intent is not None or expected_entity is not None:
        if (match_intent is False) or (match_entity is False):
            match_both = False
        elif (match_intent in (True, None)) and (match_entity in (True, None)):
            match_both = True
        else:
            match_both = None

    return {
        "question": question,
        "http_status": http_status,
        "request_error": request_error,
        "explain_enabled": explain_enabled,
        "status_status": status_status,
        "status_raw": status_raw,
        "status_ok": status_ok,
        "status_reason": status_reason,
        "status_message": status_message,
        "chosen_intent": chosen_intent,
        "chosen_entity": chosen_entity,
        "chosen_accepted": chosen_accepted,
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
        "cache_hit": cache_hit_response,
        "cache_hit_response": cache_hit_response,
        "cache_hit_metrics": cache_hit_metrics,
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
        "answer_text": answer_text,
        "expected_intent": expected_intent,
        "expected_entity": expected_entity,
        "match_intent": match_intent,
        "match_entity": match_entity,
        "match_both": match_both,
        "suite_name": suite_name,
        "suite_description": suite_description,
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


def _load_json_file(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_expected_from_payload(
    payload: Dict[str, Any],
) -> Tuple[Optional[str], Optional[str]]:
    expected_intent = payload.get("expected_intent")
    expected_entity = payload.get("expected_entity")
    expected_block = payload.get("expected")
    if isinstance(expected_block, dict) and (
        expected_intent is None or expected_entity is None
    ):
        route = expected_block.get("route")
        if isinstance(route, dict):
            if expected_intent is None and isinstance(route.get("intent"), str):
                expected_intent = route.get("intent")
            if expected_entity is None and isinstance(route.get("entity"), str):
                expected_entity = route.get("entity")
        if expected_intent is None and isinstance(expected_block.get("intent"), str):
            expected_intent = expected_block.get("intent")
        if expected_entity is None and isinstance(expected_block.get("entity"), str):
            expected_entity = expected_block.get("entity")
    return expected_intent, expected_entity


def _normalize_payloads(
    payloads: Sequence[Any],
    path: str,
) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for idx, payload in enumerate(payloads, start=1):
        if not isinstance(payload, dict):
            raise SystemExit(
                f"Payload #{idx} inválido em {path}: esperado objeto com question/expected_*"
            )
        question = payload.get("question")
        if not isinstance(question, str) or not question.strip():
            raise SystemExit(
                f"Payload #{idx} inválido em {path}: campo 'question' vazio"
            )
        payload_id = payload.get("id")
        if payload_id is not None and not isinstance(payload_id, str):
            raise SystemExit(
                f"Payload #{idx} inválido em {path}: campo 'id' deve ser string"
            )
        expected_intent, expected_entity = _extract_expected_from_payload(payload)
        if expected_intent is not None and not isinstance(expected_intent, str):
            raise SystemExit(
                f"Payload #{idx} inválido em {path}: expected_intent deve ser string ou null"
            )
        if expected_entity is not None and not isinstance(expected_entity, str):
            raise SystemExit(
                f"Payload #{idx} inválido em {path}: expected_entity deve ser string ou null"
            )
        normalized.append(
            {
                "id": payload_id,
                "question": question,
                "expected_intent": expected_intent,
                "expected_entity": expected_entity,
            }
        )
    return normalized


def _parse_suite_data(path: str, data: Any) -> Dict[str, Any]:
    suite_name: Optional[str] = None
    suite_description = ""
    payloads_raw: Optional[Sequence[Any]] = None

    if isinstance(data, list):
        payloads_raw = data
    elif isinstance(data, dict):
        if "payloads" in data:
            payloads_raw = data.get("payloads")
            suite_name = data.get("suite") or data.get("type")
            suite_description = data.get("description") or ""
        else:
            raise SystemExit(
                f"Formato inválido em {path}: esperado objeto com 'payloads' ou lista direta"
            )
    else:
        raise SystemExit(
            f"Formato inválido em {path}: esperado objeto com 'payloads' ou lista direta"
        )

    if not isinstance(payloads_raw, list):
        raise SystemExit(f"Suite inválida em {path}: 'payloads' deve ser uma lista")

    if suite_name is None:
        suite_name = Path(path).stem
    if not isinstance(suite_name, str):
        raise SystemExit(f"Suite inválida em {path}: 'suite' deve ser string")
    if not isinstance(suite_description, str):
        raise SystemExit(f"Suite inválida em {path}: 'description' deve ser string")

    return {
        "suite": suite_name,
        "description": suite_description,
        "payloads": _normalize_payloads(payloads_raw, path),
    }


def _load_suites(paths: List[str]) -> List[Dict[str, Any]]:
    suites: List[Dict[str, Any]] = []
    for path in paths:
        if not os.path.exists(path):
            raise SystemExit(f"Suite não encontrada: {path}")
        data = _load_json_file(path)
        suites.append(_parse_suite_data(path, data))
    return suites


def _ensure_out_dir(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)


def _write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


def _write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _collect_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(rows)
    acc = _compute_accuracy(rows)
    return {
        "total": total,
        "gate_ok": sum(1 for r in rows if r.get("gate_accepted") is True),
        "gate_fail": sum(1 for r in rows if r.get("gate_accepted") is False),
        "cache_hit_response": sum(
            1 for r in rows if r.get("cache_hit_response") is True
        ),
        "cache_hit_metrics": sum(1 for r in rows if r.get("cache_hit_metrics") is True),
        "narrator_used": sum(1 for r in rows if r.get("narrator_used") is True),
        "accuracy": acc,
    }


def _percentile(values: List[float], pct: float) -> Optional[float]:
    if not values:
        return None
    if pct <= 0:
        return values[0]
    if pct >= 100:
        return values[-1]
    values_sorted = sorted(values)
    k = (len(values_sorted) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(values_sorted) - 1)
    if f == c:
        return values_sorted[f]
    d0 = values_sorted[f] * (c - k)
    d1 = values_sorted[c] * (k - f)
    return d0 + d1


def _evaluate_suite_status(row: Dict[str, Any]) -> Dict[str, Any]:
    expected_intent = row.get("expected_intent")
    expected_entity = row.get("expected_entity")

    if row.get("request_error"):
        row["suite_status"] = "ERROR"
        row["suite_error"] = row.get("request_error")
        return row

    http_status = row.get("http_status")
    if not isinstance(http_status, int) or not (200 <= http_status < 300):
        row["suite_status"] = "ERROR"
        row["suite_error"] = f"http_status={http_status}"
        return row

    if row.get("status_ok") is not True:
        row["suite_status"] = "ERROR"
        row["suite_error"] = "status_not_ok"
        return row

    if expected_intent is None and expected_entity is None:
        row["suite_status"] = "SKIP"
        row["suite_error"] = None
        return row

    intent_ok = row.get("match_intent") if expected_intent is not None else True
    entity_ok = row.get("match_entity") if expected_entity is not None else True
    if intent_ok is False or entity_ok is False:
        row["suite_status"] = "FAIL"
    else:
        row["suite_status"] = "PASS"
    row["suite_error"] = None
    return row


def _suite_metrics(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(rows)
    pass_count = sum(1 for r in rows if r.get("suite_status") == "PASS")
    fail_count = sum(1 for r in rows if r.get("suite_status") == "FAIL")
    skip_count = sum(1 for r in rows if r.get("suite_status") == "SKIP")
    error_count = sum(1 for r in rows if r.get("suite_status") == "ERROR")

    intent_checked = [
        r
        for r in rows
        if r.get("expected_intent") is not None and r.get("suite_status") != "ERROR"
    ]
    entity_checked = [
        r
        for r in rows
        if r.get("expected_entity") is not None and r.get("suite_status") != "ERROR"
    ]
    pass_intent = sum(1 for r in intent_checked if r.get("match_intent") is True)
    pass_entity = sum(1 for r in entity_checked if r.get("match_entity") is True)

    latencies = [
        float(r.get("elapsed_ms_client"))
        for r in rows
        if isinstance(r.get("elapsed_ms_client"), (int, float))
    ]
    latencies = sorted(latencies)

    return {
        "total": total,
        "pass": pass_count,
        "fail": fail_count,
        "skip": skip_count,
        "error": error_count,
        "accuracy_intent": (
            pass_intent / len(intent_checked) if intent_checked else None
        ),
        "accuracy_entity": (
            pass_entity / len(entity_checked) if entity_checked else None
        ),
        "intent_checked": len(intent_checked),
        "entity_checked": len(entity_checked),
        "latency_ms": {
            "p50": _percentile(latencies, 50) if latencies else None,
            "p95": _percentile(latencies, 95) if latencies else None,
            "avg": (sum(latencies) / len(latencies) if latencies else None),
            "max": (max(latencies) if latencies else None),
        },
    }


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def _render_report(rows: List[Dict[str, Any]]) -> str:
    metrics = _suite_metrics(rows)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines: List[str] = [
        "# Ask Suite Report",
        "",
        f"_Generated at: {timestamp}_",
        "",
        "## Summary",
        "",
        f"- Total: **{metrics['total']}**",
        f"- Pass: **{metrics['pass']}**",
        f"- Fail: **{metrics['fail']}**",
        f"- Skip: **{metrics['skip']}**",
        f"- Error: **{metrics['error']}**",
    ]

    acc_intent = metrics["accuracy_intent"]
    acc_entity = metrics["accuracy_entity"]
    lines.extend(
        [
            "",
            "## Metrics",
            "",
            (
                f"- Accuracy (intent): **{(acc_intent * 100):.1f}%**"
                f" ({metrics['intent_checked']} checked)"
                if acc_intent is not None
                else f"- Accuracy (intent): **n/a** ({metrics['intent_checked']} checked)"
            ),
            (
                f"- Accuracy (entity): **{(acc_entity * 100):.1f}%**"
                f" ({metrics['entity_checked']} checked)"
                if acc_entity is not None
                else f"- Accuracy (entity): **n/a** ({metrics['entity_checked']} checked)"
            ),
        ]
    )

    latency = metrics["latency_ms"]
    lines.extend(
        [
            "",
            "### Latency (ms)",
            "",
            (
                f"- p50: {latency['p50']:.1f}"
                if latency["p50"] is not None
                else "- p50: n/a"
            ),
            (
                f"- p95: {latency['p95']:.1f}"
                if latency["p95"] is not None
                else "- p95: n/a"
            ),
            (
                f"- avg: {latency['avg']:.1f}"
                if latency["avg"] is not None
                else "- avg: n/a"
            ),
            (
                f"- max: {latency['max']:.1f}"
                if latency["max"] is not None
                else "- max: n/a"
            ),
        ]
    )

    lines.extend(
        [
            "",
            "## Cases",
            "",
            "| # | Question | Expected Intent | Expected Entity | Chosen Intent | Chosen Entity | Status | Latency (ms) |",
            "|---:|---|---|---|---|---|---|---:|",
        ]
    )
    for row in sorted(rows, key=lambda r: r.get("idx") or 0):
        question = row.get("question") or ""
        lines.append(
            "| {idx} | {question} | {expected_intent} | {expected_entity} | {chosen_intent} | {chosen_entity} | {status} | {latency} |".format(
                idx=row.get("idx"),
                question=_truncate(str(question), 120),
                expected_intent=row.get("expected_intent") or "-",
                expected_entity=row.get("expected_entity") or "-",
                chosen_intent=row.get("chosen_intent") or "-",
                chosen_entity=row.get("chosen_entity") or "-",
                status=row.get("suite_status") or "-",
                latency=(
                    f"{row.get('elapsed_ms_client'):.1f}"
                    if isinstance(row.get("elapsed_ms_client"), (int, float))
                    else "-"
                ),
            )
        )

    details = [
        r
        for r in sorted(rows, key=lambda r: r.get("idx") or 0)
        if r.get("suite_status") in ("FAIL", "ERROR")
    ]
    if details:
        lines.extend(["", "## Details (failures/errors)", ""])
        for row in details:
            lines.extend(
                [
                    f"### Case {row.get('idx')} ({row.get('suite_status')})",
                    "",
                    f"- Question: {row.get('question')}",
                    f"- Expected intent: {row.get('expected_intent') or '-'}",
                    f"- Expected entity: {row.get('expected_entity') or '-'}",
                    f"- Chosen intent: {row.get('chosen_intent') or '-'}",
                    f"- Chosen entity: {row.get('chosen_entity') or '-'}",
                    f"- Match intent: {row.get('match_intent')}",
                    f"- Match entity: {row.get('match_entity')}",
                    f"- HTTP status: {row.get('http_status')}",
                    f"- Error: {row.get('suite_error') or '-'}",
                    "",
                ]
            )

    return "\n".join(lines).strip() + "\n"


def _write_report(path: str, rows: List[Dict[str, Any]]) -> None:
    report = _render_report(rows)
    if path in ("", "-"):
        print(report)
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Wrote: {path}")


def _top_fail_reasons(
    rows: List[Dict[str, Any]], limit: int = 3
) -> List[Tuple[str, int]]:
    reason_counts: Dict[str, int] = {}
    for r in rows:
        if r.get("case_pass") is False:
            for reason in r.get("fail_reasons") or []:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
    return sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:limit]


def _summarize_suites(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    suites: Dict[str, Any] = {}
    for r in rows:
        suite = r.get("suite_name") or "-"
        data = suites.setdefault(
            suite,
            {
                "total": 0,
                "pass": 0,
                "fail": 0,
                "reasons": {},
                "description": r.get("suite_description"),
            },
        )
        data["total"] += 1
        if r.get("case_pass") is True:
            data["pass"] += 1
        else:
            data["fail"] += 1
            for reason in r.get("fail_reasons") or []:
                data["reasons"][reason] = data["reasons"].get(reason, 0) + 1

    for suite, data in suites.items():
        top_reasons = sorted(data["reasons"].items(), key=lambda x: x[1], reverse=True)
        suites[suite]["top_fail_reasons"] = top_reasons[:3]
    return suites


def _print_suite_summary(rows: List[Dict[str, Any]]) -> None:
    suite_summary = _summarize_suites(rows)
    if not suite_summary:
        return

    print("\n=== RESUMO POR SUITE/ENTIDADE ===")
    for suite, data in sorted(suite_summary.items()):
        top_reasons = ", ".join(
            [
                f"{reason} ({count})"
                for reason, count in data.get("top_fail_reasons", [])
            ]
        )
        print(
            f"- {suite}: total={data['total']} pass={data['pass']} fail={data['fail']} "
            f"top_fails=[{top_reasons or '-'}]"
        )


def _evaluate_case(row: Dict[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    http_status = row.get("http_status")
    if not isinstance(http_status, int) or not (200 <= http_status < 300):
        reasons.append("http_not_ok")

    if row.get("request_error"):
        reasons.append("request_error")

    if row.get("status_ok") is not True:
        reasons.append("status_not_ok")

    expected_entity = row.get("expected_entity")
    chosen_entity = row.get("chosen_entity")
    if expected_entity and expected_entity != chosen_entity:
        reasons.append("entity_mismatch")

    expected_intent = row.get("expected_intent")
    chosen_intent = row.get("chosen_intent")
    if expected_intent and expected_intent != chosen_intent:
        reasons.append("intent_mismatch")

    answer_text = row.get("answer_text")
    if isinstance(answer_text, str):
        if "{{" in answer_text or "{%" in answer_text:
            reasons.append("jinja_artifacts")
        if "None" in answer_text:
            reasons.append("none_literal")

    row["fail_reasons"] = reasons
    row["case_pass"] = len(reasons) == 0
    return row


def main() -> int:
    examples = (
        "Exemplos:\\n"
        "  python scripts/diagnostics/run_ask_suite.py --suite fiis_registrations --base-url http://localhost:8000 --conversation-id X --client-id Y\\n"
        "  python scripts/diagnostics/run_ask_suite.py --suite data/ops/quality/payloads/fiis_registrations_suite.json --base-url http://localhost:8000 --conversation-id X --client-id Y\\n"
        "  python scripts/diagnostics/run_ask_suite.py --all-suites --base-url http://localhost:8000 --conversation-id X --client-id Y\\n"
        "  python scripts/diagnostics/run_ask_suite.py --inline --questions 5 --base-url http://localhost:8000 --conversation-id X --client-id Y"
    )
    ap = argparse.ArgumentParser(
        description="Runner de diagnostics para /ask (inline, arquivo ou suites JSON).",
        epilog=examples,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
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
    ap.add_argument(
        "--suite-path",
        default="",
        help="Caminho para *_suite.json (deprecated; use --suite).",
    )
    ap.add_argument(
        "--suite-dir",
        default="data/ops/quality/payloads",
        help='Diretório onde ficam as suites (default="data/ops/quality/payloads").',
    )
    ap.add_argument(
        "--suite-glob",
        default="*_suite.json",
        help='Glob para --all-suites (default="*_suite.json").',
    )
    ap.add_argument(
        "--suite",
        action="append",
        default=[],
        help=(
            "Suite JSON (path) ou nome lógico (resolve para {suite-dir}/{suite}_suite.json). "
            "Pode repetir."
        ),
    )
    ap.add_argument(
        "--all-suites",
        action="store_true",
        help="Roda todas as suites encontradas em suite-dir que batam suite-glob.",
    )
    ap.add_argument(
        "--suite-name",
        default="",
        help="Compat: nome lógico da suite (deprecated; use --suite).",
    )
    ap.add_argument(
        "--base-url", default="http://localhost:8000", help="Ex: http://localhost:8000"
    )
    ap.add_argument("--conversation-id", default="diagnostics")
    ap.add_argument("--client-id", default="dev")
    ap.add_argument("--nickname", default="diagnostics")
    ap.add_argument("--type-user", default="paid")
    ap.add_argument("--timeout-s", type=float, default=90.0)
    ap.add_argument("--out-dir", default="out")
    ap.add_argument(
        "--out",
        default="docs/DIAGNOSTICS/ASK_SUITE_REPORT.md",
        help="Arquivo markdown para report (use '-' para stdout).",
    )
    ap.add_argument(
        "--fail-fast", action="store_true", help="Para na primeira falha/erro."
    )
    ap.add_argument(
        "--limit", type=int, default=0, help="Limita o número total de casos."
    )
    explain_group = ap.add_mutually_exclusive_group()
    explain_group.add_argument(
        "--explain",
        dest="explain",
        action="store_true",
        help="Ativa explain nas chamadas (default).",
    )
    explain_group.add_argument(
        "--no-explain",
        dest="explain",
        action="store_false",
        help="Desativa explain para medir cache real.",
    )
    ap.set_defaults(explain=True)
    ap.add_argument(
        "--print-answer",
        action="store_true",
        help="Imprime também o campo answer (útil para debug pontual).",
    )
    args = ap.parse_args()

    _selftest_parse_status()

    suite_paths = _resolve_suite_paths(args)
    suite_mode = len(suite_paths) > 0
    if args.all_suites and not suite_paths:
        raise SystemExit(
            f"Nenhuma suite encontrada em {args.suite_dir!r} com glob {args.suite_glob!r}."
        )
    if not suite_mode and not (args.inline or args.questions_file):
        raise SystemExit(
            "Informe --suite/--suite-path/--all-suites ou use --inline/--questions-file."
        )

    cfg = Config(
        base_url=args.base_url,
        conversation_id=args.conversation_id,
        client_id=args.client_id,
        nickname=args.nickname,
        type_user=args.type_user,
        timeout_s=args.timeout_s,
        out_dir=args.out_dir,
        print_answer=args.print_answer,
        explain=args.explain,
    )

    _ensure_out_dir(cfg.out_dir)

    rows: List[Dict[str, Any]] = []
    suite_rows: Dict[str, List[Dict[str, Any]]] = {}

    idx = 0
    if suite_mode:
        suites = _load_suites(suite_paths)
        for suite_data in suites:
            suite_name = suite_data.get("suite")
            suite_description = suite_data.get("description")
            payloads = suite_data.get("payloads") or []
            for payload in payloads:
                if args.limit and idx >= args.limit:
                    break
                idx += 1
                q = payload.get("question")
                expected_intent = payload.get("expected_intent")
                expected_entity = payload.get("expected_entity")

                resp, dt_ms, err = _post_question(cfg, q)
                row = _extract_row(
                    resp,
                    q,
                    dt_ms,
                    err,
                    cfg.explain,
                    expected_intent=expected_intent,
                    expected_entity=expected_entity,
                    suite_name=suite_name,
                    suite_description=suite_description,
                )
                row["payload_id"] = payload.get("id")
                row["idx"] = idx
                row = _evaluate_case(row)
                row = _evaluate_suite_status(row)
                rows.append(row)
                suite_rows.setdefault(suite_name, []).append(row)

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
                cache = "Y" if row.get("cache_hit_response") else "N"
                ms = int(
                    row.get("elapsed_ms_server") or row.get("elapsed_ms_client") or 0
                )
                llm_ms = (
                    int(row.get("narrator_latency_ms") or 0)
                    if row.get("narrator_used")
                    else 0
                )
                extras = ""
                if (expected_intent is not None) or (expected_entity is not None):
                    extras = (
                        f" expected_intent={expected_intent or '-'} "
                        f"expected_entity={expected_entity or '-'} "
                        f"match_intent={row.get('match_intent')} "
                        f"match_entity={row.get('match_entity')} "
                        f"match_both={row.get('match_both')}"
                    )
                print(
                    f"{idx:>2} | {intent:<12} | {entity:<12} | "
                    f"gate={gate} src={src:<8} gap_b={gap_b} gap_f={gap_f} "
                    f"top1={top1} top2={top2} "
                    f"rag={rag} fusion={fusion} cache={cache} ms={ms} llm_ms={llm_ms}{extras}"
                )

                if cfg.print_answer:
                    ans = _safe_get(resp, "answer")
                    if isinstance(ans, str) and ans.strip():
                        print(f"   answer: {ans.strip()[:500]}")
                if args.fail_fast and row.get("suite_status") in ("FAIL", "ERROR"):
                    break
            if args.limit and idx >= args.limit:
                break
            if (
                args.fail_fast
                and rows
                and rows[-1].get("suite_status") in ("FAIL", "ERROR")
            ):
                break
    else:
        questions = _load_questions(args)
        for q in questions:
            if args.limit and idx >= args.limit:
                break
            idx += 1
            resp, dt_ms, err = _post_question(cfg, q)
            row = _extract_row(resp, q, dt_ms, err, cfg.explain)
            row["idx"] = idx
            row = _evaluate_case(row)
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
            cache = "Y" if row.get("cache_hit_response") else "N"
            ms = int(row.get("elapsed_ms_server") or row.get("elapsed_ms_client") or 0)
            llm_ms = (
                int(row.get("narrator_latency_ms") or 0)
                if row.get("narrator_used")
                else 0
            )

            print(
                f"{idx:>2} | {intent:<12} | {entity:<12} | "
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

    if args.all_suites and suite_mode:
        all_jsonl = os.path.join(cfg.out_dir, "audit_results_all.jsonl")
        all_csv = os.path.join(cfg.out_dir, "audit_results_all.csv")
        _write_jsonl(all_jsonl, rows)
        _write_csv(all_csv, rows)
        print(f"Wrote: {all_jsonl}")
        print(f"Wrote: {all_csv}")

        summary_all: Dict[str, Any] = {
            "suites": {},
            "overall": {
                **_collect_stats(rows),
                "pass": sum(1 for r in rows if r.get("case_pass") is True),
                "fail": sum(1 for r in rows if r.get("case_pass") is False),
                "top_fail_reasons": _top_fail_reasons(rows),
            },
        }
        for suite_name, suite_rows_list in suite_rows.items():
            summary_all["suites"][suite_name] = {
                **_collect_stats(suite_rows_list),
                "pass": sum(1 for r in suite_rows_list if r.get("case_pass") is True),
                "fail": sum(1 for r in suite_rows_list if r.get("case_pass") is False),
                "top_fail_reasons": _top_fail_reasons(suite_rows_list),
            }
            if suite_rows_list:
                summary_all["suites"][suite_name]["description"] = suite_rows_list[
                    0
                ].get("suite_description")
        summary_path = os.path.join(cfg.out_dir, "audit_summary_all.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary_all, f, ensure_ascii=False, indent=2, sort_keys=True)
        print(f"Wrote: {summary_path}")

    if suite_mode:
        _write_report(args.out, rows)
        _print_suite_summary(rows)
    _print_final_summary(rows)
    if suite_mode:
        has_fail = any(r.get("suite_status") in ("FAIL", "ERROR") for r in rows)
        return 2 if has_fail else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
