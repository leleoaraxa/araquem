#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
run_ask_suite.py

Executa 10 perguntas no /ask e extrai um "audit payload" enxuto:
- winner por intent + entity vem do intent (Contrato A)
- thresholds_applied (gate)
- top2 gap base/final
- rag.used + rerank_policy + fusion.used/weight/affected
- cache hit + latência total + latência narrator
- entity_top_telemetry (apenas para inspeção; pode ser ruidoso)

Saídas:
- stdout: tabela resumida
- out/audit_results.jsonl
- out/audit_results.csv

Uso:
  python run_ask_suite.py --questions questions.txt
  python run_ask_suite.py --inline
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests


def _get(d: Dict[str, Any], path: str, default=None):
    """Safe getter for dotted paths."""
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return default
        if part not in cur:
            return default
        cur = cur[part]
    return cur


def _to_bool(v: Any) -> Optional[bool]:
    if isinstance(v, bool):
        return v
    return None


def _to_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AskConfig:
    base_url: str
    api_key: Optional[str]
    nickname: str
    client_id: str
    conversation_id: str
    timeout_s: int = 120


def call_ask(cfg: AskConfig, question: str) -> Dict[str, Any]:
    url = cfg.base_url.rstrip("/") + "/ask?explain=true"
    headers = {"Content-Type": "application/json"}
    if cfg.api_key:
        # Ajuste aqui se o seu gateway usa outro header (ex: Authorization: Bearer)
        headers["Authorization"] = f"Bearer {cfg.api_key}"

    payload = {
        "question": question,
        "conversation_id": cfg.conversation_id,
        "nickname": cfg.nickname,
        "client_id": cfg.client_id,
    }

    r = requests.post(
        url, headers=headers, data=json.dumps(payload), timeout=cfg.timeout_s
    )
    r.raise_for_status()
    return r.json()


def extract_audit(resp: Dict[str, Any], question: str) -> Dict[str, Any]:
    meta = resp.get("meta", {}) if isinstance(resp.get("meta"), dict) else {}

    chosen_intent = _get(meta, "planner.chosen.intent")
    chosen_entity = _get(meta, "planner.chosen.entity")
    chosen_score = _get(meta, "planner.chosen.score")

    # Gate / thresholds
    th = _get(meta, "planner.explain.scoring.thresholds_applied", {}) or {}
    gate_accepted = _get(th, "accepted")
    gate_source = _get(th, "source")
    gate_min_score = _get(th, "min_score")
    gate_min_gap = _get(th, "min_gap")
    gate_gap = _get(th, "gap")
    gate_score_for_gate = _get(th, "score_for_gate")
    gate_reason = _get(th, "reason")

    # top2 gaps
    gap_base = _get(meta, "planner.explain.scoring.intent_top2_gap_base")
    gap_final = _get(meta, "planner.explain.scoring.intent_top2_gap_final")

    # RAG / rerank / fusion
    rag_used = _get(meta, "planner.rag.used")
    rag_error = _get(meta, "planner.rag.error")
    rag_hints = _get(meta, "planner.rag.entity_hints", {}) or {}
    rerank_enabled = _get(meta, "planner.rag.re_rank.enabled")
    rerank_policy_enabled = _get(meta, "planner.rag.rerank_policy.enabled")
    rerank_policy_source = _get(meta, "planner.rag.rerank_policy.source")

    fusion_used = _get(meta, "planner.fusion.used")
    fusion_weight = _get(meta, "planner.fusion.weight")
    fusion_affected = _get(meta, "planner.fusion.affected_entities", []) or []

    # Telemetria "top_entity" (ruidosa quando há empate)
    entity_top_telemetry = _get(
        meta, "planner.explain.scoring.entity_top_telemetry.name"
    )

    # Context allow/deny
    context_allowed = _get(meta, "planner.chosen.context_allowed")
    context_entity_allowed = _get(meta, "planner.context.entity_allowed")
    context_entity = _get(meta, "planner.context.entity")

    # Cache
    cache_hit = _get(meta, "cache.hit")
    cache_ttl = _get(meta, "cache.ttl")

    # Latências (top-level + narrator)
    elapsed_ms = _get(meta, "elapsed_ms")
    narrator_used = _get(meta, "narrator.used")
    narrator_latency_ms = _get(meta, "narrator.latency_ms")
    narrator_error = _get(meta, "narrator.error")
    route_source = _get(meta, "explain_analytics.details.route_source")

    # Contrato A: entity vem do intent
    # details.<intent>.entities deve conter chosen_entity
    intent_entities = (
        _get(meta, f"planner.details.{chosen_intent}.entities", [])
        if chosen_intent
        else []
    )
    entity_from_intent = (
        isinstance(intent_entities, list) and (chosen_entity in intent_entities)
        if chosen_entity and chosen_intent
        else None
    )

    # Consistência "top-level" vs planner
    top_intent = _get(meta, "intent")
    top_entity = _get(meta, "entity")
    consistent_intent = (
        (top_intent == chosen_intent) if (top_intent and chosen_intent) else None
    )
    consistent_entity = (
        (top_entity == chosen_entity) if (top_entity and chosen_entity) else None
    )

    return {
        "ts_utc": _utc_now_iso(),
        "question": question,
        "chosen_intent": chosen_intent,
        "chosen_entity": chosen_entity,
        "chosen_score": _to_float(chosen_score),
        "contract_entity_from_intent": entity_from_intent,
        "contract_intent_consistent_top_level": consistent_intent,
        "contract_entity_consistent_top_level": consistent_entity,
        "gate_accepted": _to_bool(gate_accepted),
        "gate_source": gate_source,
        "gate_min_score": _to_float(gate_min_score),
        "gate_min_gap": _to_float(gate_min_gap),
        "gate_gap": _to_float(gate_gap),
        "gate_score_for_gate": _to_float(gate_score_for_gate),
        "gate_reason": gate_reason,
        "intent_top2_gap_base": _to_float(gap_base),
        "intent_top2_gap_final": _to_float(gap_final),
        "rag_used": _to_bool(rag_used),
        "rag_error": rag_error,
        "rag_hints": rag_hints,  # mantém map completo
        "rerank_enabled": _to_bool(rerank_enabled),
        "rerank_policy_enabled": _to_bool(rerank_policy_enabled),
        "rerank_policy_source": rerank_policy_source,
        "fusion_used": _to_bool(fusion_used),
        "fusion_weight": _to_float(fusion_weight),
        "fusion_affected_entities": fusion_affected,
        "context_allowed": _to_bool(context_allowed),
        "context_entity_allowed": _to_bool(context_entity_allowed),
        "context_entity": context_entity,
        "cache_hit": _to_bool(cache_hit),
        "cache_ttl": cache_ttl,
        "elapsed_ms": _to_float(elapsed_ms),
        "narrator_used": _to_bool(narrator_used),
        "narrator_latency_ms": _to_float(narrator_latency_ms),
        "narrator_error": narrator_error,
        "route_source": route_source,
        "entity_top_telemetry": entity_top_telemetry,
    }


def print_table(rows: List[Dict[str, Any]]) -> None:
    # Tabela enxuta (para terminal)
    cols = [
        ("#", "idx"),
        ("intent", "chosen_intent"),
        ("entity", "chosen_entity"),
        ("gate", "gate_accepted"),
        ("src", "gate_source"),
        ("gap_b", "intent_top2_gap_base"),
        ("gap_f", "intent_top2_gap_final"),
        ("rag", "rag_used"),
        ("fusion", "fusion_used"),
        ("cache", "cache_hit"),
        ("ms", "elapsed_ms"),
        ("llm_ms", "narrator_latency_ms"),
    ]

    def fmt(v):
        if v is None:
            return "-"
        if isinstance(v, bool):
            return "Y" if v else "N"
        if isinstance(v, float):
            # 3 casas para gaps / scores, 0 para ms
            return f"{v:.3f}" if v < 10 else f"{v:.0f}"
        return str(v)

    header = " | ".join([c[0].ljust(7) for c in cols])
    sep = "-+-".join(["-" * 7 for _ in cols])
    print(header)
    print(sep)
    for i, r in enumerate(rows, start=1):
        r2 = dict(r)
        r2["idx"] = i
        line = " | ".join([fmt(r2.get(key)).ljust(7)[:7] for _, key in cols])
        print(line)


def write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Flatten mínimo (mantém rag_hints e fusion_affected_entities como json-string)
    fieldnames = [
        "ts_utc",
        "question",
        "chosen_intent",
        "chosen_entity",
        "chosen_score",
        "contract_entity_from_intent",
        "contract_intent_consistent_top_level",
        "contract_entity_consistent_top_level",
        "gate_accepted",
        "gate_source",
        "gate_min_score",
        "gate_min_gap",
        "gate_gap",
        "gate_score_for_gate",
        "gate_reason",
        "intent_top2_gap_base",
        "intent_top2_gap_final",
        "rag_used",
        "rag_error",
        "rerank_enabled",
        "rerank_policy_enabled",
        "rerank_policy_source",
        "fusion_used",
        "fusion_weight",
        "context_allowed",
        "context_entity_allowed",
        "context_entity",
        "cache_hit",
        "cache_ttl",
        "elapsed_ms",
        "narrator_used",
        "narrator_latency_ms",
        "narrator_error",
        "route_source",
        "entity_top_telemetry",
        "rag_hints_json",
        "fusion_affected_entities_json",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            out = {k: r.get(k) for k in fieldnames if k in r}
            out["rag_hints_json"] = json.dumps(
                r.get("rag_hints", {}), ensure_ascii=False
            )
            out["fusion_affected_entities_json"] = json.dumps(
                r.get("fusion_affected_entities", []), ensure_ascii=False
            )
            w.writerow(out)


def load_questions(path: Optional[str], inline: bool) -> List[str]:
    if inline:
        # Substitua por suas 10 perguntas (ou mantenha como exemplo)
        return [
            "Como está o KNRI11 e o XPLG11?",
            "Qual foi o último dividendo do HGLG11?",
            "Quais são os imóveis do HGLG11?",
            "Qual é o DY anualizado do MXRF11?",
            "Existe algum processo judicial relevante do HGRU11?",
            "Qual o P/VP do KNRI11?",
            "Quais notícias recentes do KNRI11?",
            "Qual foi a variação do IFIX no último pregão?",
            "Qual foi o IPCA em março de 2025?",
            "Mostre minha carteira enriquecida.",
        ]

    if not path:
        raise SystemExit(
            "Você precisa passar --questions questions.txt ou usar --inline."
        )

    with open(path, "r", encoding="utf-8") as f:
        qs = [line.strip() for line in f.readlines()]
    qs = [q for q in qs if q and not q.startswith("#")]
    if len(qs) < 1:
        raise SystemExit("Arquivo de perguntas vazio.")
    if len(qs) > 10:
        qs = qs[:10]
    return qs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--base-url", default=os.getenv("ARAQUEM_BASE_URL", "http://localhost:8000")
    )
    ap.add_argument("--api-key", default=os.getenv("ARAQUEM_API_KEY"))
    ap.add_argument("--nickname", default=os.getenv("ARAQUEM_NICKNAME", "audit"))
    ap.add_argument("--client-id", default=os.getenv("ARAQUEM_CLIENT_ID", "audit"))
    ap.add_argument(
        "--conversation-id",
        default=os.getenv("ARAQUEM_CONVERSATION_ID", str(uuid.uuid4())),
    )
    ap.add_argument(
        "--questions", help="Arquivo txt com até 10 perguntas (1 por linha)."
    )
    ap.add_argument(
        "--inline",
        action="store_true",
        help="Usa a lista inline de 10 perguntas (edite no script).",
    )
    ap.add_argument("--out-dir", default="out")
    ap.add_argument(
        "--sleep-ms", type=int, default=0, help="Delay entre requests (0..)."
    )
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args()

    questions = load_questions(args.questions, args.inline)

    cfg = AskConfig(
        base_url=args.base_url,
        api_key=args.api_key,
        nickname=args.nickname,
        client_id=args.client_id,
        conversation_id=args.conversation_id,
        timeout_s=args.timeout,
    )

    results: List[Dict[str, Any]] = []
    errors: List[Tuple[str, str]] = []

    print(
        f"base_url={cfg.base_url} conversation_id={cfg.conversation_id} questions={len(questions)}"
    )
    for q in questions:
        try:
            resp = call_ask(cfg, q)
            audit = extract_audit(resp, q)
            results.append(audit)
        except Exception as e:
            errors.append((q, str(e)))
        if args.sleep_ms > 0:
            time.sleep(args.sleep_ms / 1000.0)

    print()
    print_table(results)

    out_jsonl = os.path.join(args.out_dir, "audit_results.jsonl")
    out_csv = os.path.join(args.out_dir, "audit_results.csv")
    write_jsonl(out_jsonl, results)
    write_csv(out_csv, results)

    print()
    print(f"Wrote: {out_jsonl}")
    print(f"Wrote: {out_csv}")

    if errors:
        print()
        print("Errors:")
        for q, err in errors:
            print(f"- {q}: {err}")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
