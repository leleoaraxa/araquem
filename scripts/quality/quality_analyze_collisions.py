# scripts/quality/quality_analyze_collisions.py
# -*- coding: utf-8 -*-
"""
Ferramenta de análise de colisão de intents/entidades do planner (Araquem).

- Lê samples de roteamento (ex.: data/ops/quality/routing_samples.json).
- Para cada pergunta:
  - chama orchestrator.route_question(question)
  - extrai meta.planner.candidates
  - calcula top1, top2 e top2_gap
  - detecta colisões (top2_gap pequeno com intents/entidades diferentes)
- Gera um resumo em stdout com:
  - acurácia top1
  - taxa de colisão
  - pares de entidades/intents que mais brigam
  - piores colisões (menor top2_gap)
"""

from __future__ import annotations

import argparse
import json
import pathlib
import datetime
import statistics
from typing import Any, Dict, List, Optional, Tuple

from app.core.context import orchestrator  # contrato já usado em ops/rag_debug


Sample = Dict[str, Any]
Candidate = Dict[str, Any]


def load_samples(path: pathlib.Path) -> List[Sample]:
    """Carrega samples de um arquivo JSON com chave 'samples'."""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "samples" in data:
        samples = data["samples"]
    elif isinstance(data, list):
        # fallback: arquivo é uma lista direta de samples
        samples = data
    else:
        raise ValueError(f"Formato inesperado em {path}")

    out: List[Sample] = []
    for s in samples:
        if not isinstance(s, dict):
            continue
        question = s.get("question")
        if not question:
            continue
        out.append(
            {
                "question": question,
                "expected_intent": s.get("expected_intent"),
                "expected_entity": s.get("expected_entity"),
            }
        )
    return out


def extract_planner_candidates(
    plan: Dict[str, Any],
) -> Tuple[Optional[Candidate], Optional[Candidate], List[Candidate]]:
    """
    Extrai top1, top2 e lista de candidatos do bloco meta['planner'].

    Assumimos estrutura:
        {
          "intent": "...",
          "entity": "...",
          "candidates": [
            {"intent": "...", "entity": "...", "score": 0.92},
            ...
          ]
        }

    Se a estrutura real diferir, ajustar este ponto.
    """
    candidates = plan.get("candidates") or []
    if not isinstance(candidates, list):
        candidates = []

    # Normaliza campos esperados
    norm_candidates: List[Candidate] = []
    for c in candidates:
        if not isinstance(c, dict):
            continue
        intent = c.get("intent")
        entity = c.get("entity")
        score = c.get("score")
        try:
            score_f = float(score) if score is not None else 0.0
        except Exception:
            score_f = 0.0
        norm_candidates.append(
            {
                "intent": intent,
                "entity": entity,
                "score": score_f,
            }
        )

    # Ordena por score desc, só por garantia
    norm_candidates.sort(key=lambda x: x["score"], reverse=True)

    top1 = norm_candidates[0] if len(norm_candidates) >= 1 else None
    top2 = norm_candidates[1] if len(norm_candidates) >= 2 else None
    return top1, top2, norm_candidates


def analyze_question(question: str, top2_gap_threshold: float) -> Dict[str, Any]:
    """Chama o orchestrator para uma pergunta e calcula métricas de colisão."""
    orchestration = orchestrator.route_question(question)
    status = orchestration.get("status") or {}
    meta: Dict[str, Any] = orchestration.get("meta") or {}

    # Se nao houver status razoavel, assumimos ok=True para fins de analise de planner
    if isinstance(status, dict) and status.get("reason") is not None:
        ok = status.get("reason") == "ok"
    else:
        ok = True

    plan: Dict[str, Any] = meta.get("planner") or {}
    top1, top2, candidates = extract_planner_candidates(plan)

    if not ok or top1 is None:
        return {
            "ok": ok,
            "top1": None,
            "top2": None,
            "top2_gap": None,
            "collision": False,
            "collision_reason": "no_top1",
            "candidates": candidates,
        }

    top1_intent = top1.get("intent")
    top1_entity = top1.get("entity")

    if top2 is None:
        return {
            "ok": ok,
            "top1": top1,
            "top2": None,
            "top2_gap": None,
            "collision": False,
            "collision_reason": "single_candidate",
            "candidates": candidates,
        }

    gap = float(top1["score"]) - float(top2["score"])
    same_intent = top1.get("intent") == top2.get("intent")
    same_entity = top1.get("entity") == top2.get("entity")

    # Colisão = gap pequeno e candidatos diferentes em intent OU entity
    collision = (gap < top2_gap_threshold) and (not (same_intent and same_entity))

    reason = None
    if collision:
        reason = "low_gap_diff_entity_or_intent"
    else:
        reason = "no_collision"

    return {
        "ok": ok,
        "top1": top1,
        "top2": top2,
        "top2_gap": gap,
        "collision": collision,
        "collision_reason": reason,
        "candidates": candidates,
        "intent": top1_intent,
        "entity": top1_entity,
    }


def summarize_results(
    samples: List[Sample],
    analyses: List[Dict[str, Any]],
    top2_gap_threshold: float,
) -> None:
    """Imprime um resumo no stdout."""
    total = len(samples)
    routed = sum(1 for a in analyses if a.get("top1") is not None)
    collisions = [a for a in analyses if a.get("collision")]
    collision_count = len(collisions)

    # Acurácia top1 (se esperados estiverem presentes)
    has_expecteds = any(
        s.get("expected_intent") or s.get("expected_entity") for s in samples
    )
    correct_top1 = 0
    if has_expecteds:
        for s, a in zip(samples, analyses):
            exp_int = s.get("expected_intent")
            exp_ent = s.get("expected_entity")
            top1 = a.get("top1") or {}
            if not exp_int and not exp_ent:
                continue
            if exp_int and top1.get("intent") != exp_int:
                continue
            if exp_ent and top1.get("entity") != exp_ent:
                continue
            correct_top1 += 1

    gaps = [
        a["top2_gap"] for a in analyses if isinstance(a.get("top2_gap"), (int, float))
    ]

    print("=== QUALITY / COLLISION ANALYSIS ===")
    print(f"Total samples        : {total}")
    print(f"Routed (top1 ok)     : {routed}")
    if has_expecteds and total > 0:
        acc = correct_top1 / total * 100.0
        print(f"Top1 accuracy (vs expected): {correct_top1}/{total} = {acc:0.2f}%")
    print(f"Top2-gap threshold   : {top2_gap_threshold:0.3f}")
    print(
        f"Collisions detected  : {collision_count} ({(collision_count/total*100.0):0.2f}% dos samples)"
    )

    if gaps:
        print(f"top2_gap p50         : {statistics.median(gaps):0.4f}")
        print(f"top2_gap min / max   : {min(gaps):0.4f} / {max(gaps):0.4f}")

    # Ranking de pares (top1_entity, top2_entity) que mais colidem
    pair_counts: Dict[Tuple[str, str], int] = {}
    for a in collisions:
        t1 = a.get("top1") or {}
        t2 = a.get("top2") or {}
        e1 = str(t1.get("entity") or "")
        e2 = str(t2.get("entity") or "")
        if not e1 or not e2:
            continue
        key = (e1, e2)
        pair_counts[key] = pair_counts.get(key, 0) + 1

    if pair_counts:
        print(
            "\n--- Top pares de entidades em colisão (top1_entity -> top2_entity) ---"
        )
        for (e1, e2), cnt in sorted(
            pair_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]:
            print(f"{e1:30s} -> {e2:30s} : {cnt} colisões")

    # Listar piores casos (menor gap)
    worst = sorted(
        [
            (a.get("top2_gap"), i, a)
            for i, a in enumerate(analyses)
            if isinstance(a.get("top2_gap"), (int, float))
        ],
        key=lambda x: x[0],
    )[:10]

    if worst:
        print("\n--- Piores colisões (menor top2_gap) ---")
        for gap, idx, a in worst:
            s = samples[idx]
            q = s.get("question")
            t1 = a.get("top1") or {}
            t2 = a.get("top2") or {}
            print(f"\n[{idx}] gap={gap:0.4f}")
            print(f"  question : {q}")
            print(
                f"  top1     : intent={t1.get('intent')} entity={t1.get('entity')} score={t1.get('score')}"
            )
            print(
                f"  top2     : intent={t2.get('intent')} entity={t2.get('entity')} score={t2.get('score')}"
            )

    # Retorna estrutura consolidada (usado para export JSON)
    summary = {
        "total_samples": total,
        "routed": routed,
        "collision_count": collision_count,
        "collision_rate": collision_count / total if total else 0,
    }
    if has_expecteds and total > 0:
        summary["top1_accuracy"] = correct_top1 / total
    else:
        summary["top1_accuracy"] = None

    summary["top2_gap_stats"] = {
        "p50": statistics.median(gaps) if gaps else None,
        "min": min(gaps) if gaps else None,
        "max": max(gaps) if gaps else None,
    }

    return {
        "summary": summary,
        "collisions": collisions,
        "pair_counts": pair_counts,
        "worst": worst,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analisa colisão de intents/entidades do planner usando samples de roteamento."
    )
    parser.add_argument(
        "--samples-file",
        type=str,
        default="data/ops/quality/routing_samples.json",
        help="Caminho para o arquivo de samples (JSON). Default: data/ops/quality/routing_samples.json",
    )
    parser.add_argument(
        "--top2-gap-threshold",
        type=float,
        default=0.05,
        help="Limite de gap (top1.score - top2.score) para considerar colisão. Default: 0.05",
    )
    parser.add_argument(
        "--export-json",
        type=str,
        default=None,
        help="Caminho para exportar resultados em JSON (ex.: data/golden/m68_collisions.json)",
    )
    args = parser.parse_args()

    samples_path = pathlib.Path(args.samples_file)
    samples = load_samples(samples_path)

    analyses: List[Dict[str, Any]] = []
    for s in samples:
        q = s["question"]
        analysis = analyze_question(q, top2_gap_threshold=args.top2_gap_threshold)
        analyses.append(analysis)

    summary_data = summarize_results(samples, analyses, args.top2_gap_threshold)

    # Export JSON se solicitado
    if args.export_json:
        out_path = pathlib.Path(args.export_json)
        out = {
            "version": out_path.stem,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "top2_gap_threshold": args.top2_gap_threshold,
            "summary": summary_data["summary"],
            "pair_collisions": [
                {"pair": [e1, e2], "count": cnt}
                for (e1, e2), cnt in summary_data["pair_counts"].items()
            ],
            "worst_collisions": [
                {
                    "gap": float(gap),
                    "question": samples[idx]["question"],
                    "top1": (
                        summary_data["collisions"][0].get("top1")
                        if summary_data["collisions"]
                        else None
                    ),
                }
                for (gap, idx, _) in summary_data["worst"]
            ],
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        print(f"\nJSON exportado para: {out_path}")


if __name__ == "__main__":
    main()
