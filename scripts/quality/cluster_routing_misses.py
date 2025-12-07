#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: cluster_routing_misses.py
Purpose: Clusterizar misses de roteamento por entidades para priorizar ajustes
         de ontologia/embeddings.

Lê `data/ops/quality_experimental/routing_misses_via_ask.json`, agrupa os
misses por par (expected_entity, got_entity) e imprime um resumo agregado em
stdout. Opcionalmente exporta um JSON consolidado com os clusters.

Uso típico:

    python scripts/quality/cluster_routing_misses.py \
        --misses-file data/ops/quality_experimental/routing_misses_via_ask.json \
        --top-clusters 20 \
        --examples-per-cluster 3 \
        --export-json data/ops/quality_experimental/routing_misses_clusters.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


DEFAULT_MISSES_FILE = Path("data/ops/quality_experimental/routing_misses_via_ask.json")
DEFAULT_TOP_CLUSTERS = 20
DEFAULT_EXAMPLES_PER_CLUSTER = 3
TOP_CLUSTERS_FOR_EXAMPLES = 5


Miss = Dict[str, Any]
ClusterKey = Tuple[str, str]


def load_misses(path: Path) -> List[Miss]:
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(
            f"[error] Arquivo de misses não encontrado: {path}", file=sys.stderr
        )
        raise
    except Exception as exc:  # pragma: no cover - proteção
        print(f"[error] Falha ao ler {path}: {exc}", file=sys.stderr)
        raise

    try:
        data = json.loads(content)
    except Exception as exc:  # pragma: no cover - proteção
        print(f"[error] Falha ao parsear JSON em {path}: {exc}", file=sys.stderr)
        raise

    if not isinstance(data, list):
        raise ValueError(f"Formato inesperado em {path}: esperado lista de dicts")

    return [d for d in data if isinstance(d, dict)]


def normalize_entity(value: Optional[str]) -> str:
    return value or "<none>"


def get_status_reason(miss: Miss) -> str:
    status = miss.get("status")
    if isinstance(status, dict):
        reason = status.get("reason")
        if isinstance(reason, str):
            return reason
    return "<none>"


def get_score(miss: Miss) -> Optional[float]:
    score = miss.get("score")
    try:
        return float(score) if score is not None else None
    except Exception:
        return None


def cluster_misses(misses: Iterable[Miss]):
    clusters: Dict[ClusterKey, Dict[str, Any]] = {}
    technical_errors: Dict[str, Dict[str, Any]] = {}

    for miss in misses:
        status_reason = get_status_reason(miss)
        is_ok = status_reason == "ok"
        expected_entity = normalize_entity(miss.get("expected_entity"))
        got_entity = normalize_entity(miss.get("got_entity"))
        score = get_score(miss)

        if not is_ok:
            reason_key = status_reason or "<none>"
            bucket = technical_errors.setdefault(
                reason_key, {"count": 0, "examples": []}
            )
            bucket["count"] += 1
            bucket["examples"].append(
                {
                    "idx": miss.get("idx"),
                    "question": miss.get("question"),
                    "expected_entity": miss.get("expected_entity"),
                    "got_entity": miss.get("got_entity"),
                    "status_message": (miss.get("status") or {}).get("message"),
                }
            )
            continue

        key: ClusterKey = (expected_entity, got_entity)
        cluster = clusters.setdefault(
            key,
            {
                "expected_entity": expected_entity,
                "got_entity": got_entity,
                "count": 0,
                "scores": [],
                "examples": [],
            },
        )
        cluster["count"] += 1
        if score is not None:
            cluster["scores"].append(score)
        cluster["examples"].append(
            {
                "idx": miss.get("idx"),
                "question": miss.get("question"),
                "expected_intent": miss.get("expected_intent"),
                "expected_entity": miss.get("expected_entity"),
                "got_intent": miss.get("got_intent"),
                "got_entity": miss.get("got_entity"),
                "score": score,
                "status_reason": status_reason,
            }
        )

    return clusters, technical_errors


def score_stats(scores: List[float]) -> Tuple[str, str, str, Optional[float]]:
    if not scores:
        return "-", "-", "-", None
    avg = sum(scores) / len(scores)
    return (
        f"{avg:.3f}",
        f"{min(scores):.3f}",
        f"{max(scores):.3f}",
        avg,
    )


def print_summary(
    total: int, clusters: Dict[ClusterKey, Dict[str, Any]], technical_errors: Dict[str, Any]
) -> None:
    print("=== QUALITY / ROUTING MISSES CLUSTERS ===")
    print(f"Total misses           : {total}")
    print(f"Total clusters         : {len(clusters)}")
    tech_total = sum(v.get("count", 0) for v in technical_errors.values())
    print(f"Technical errors       : {tech_total} (status != \"ok\")")
    print()


def print_clusters_table(
    clusters: Dict[ClusterKey, Dict[str, Any]], top_n: int
) -> List[Tuple[ClusterKey, Dict[str, Any]]]:
    ordered = sorted(
        clusters.items(), key=lambda kv: kv[1].get("count", 0), reverse=True
    )
    print(f"Top {min(top_n, len(ordered))} clusters by entity pair:")
    for rank, (key, cluster) in enumerate(ordered[:top_n], start=1):
        avg_s, min_s, max_s, _ = score_stats(cluster.get("scores", []))
        print(
            f"[{rank:02d}] {key[0]} -> {key[1]} : {cluster['count']} "
            f"(avg_score={avg_s}, min_score={min_s}, max_score={max_s})"
        )
    print()
    return ordered


def print_examples(
    ordered_clusters: List[Tuple[ClusterKey, Dict[str, Any]]],
    examples_per_cluster: int,
) -> None:
    top_clusters = ordered_clusters[:TOP_CLUSTERS_FOR_EXAMPLES]
    if not top_clusters:
        return
    print("Exemplos por cluster (top):")
    for idx, (key, cluster) in enumerate(top_clusters, start=1):
        avg_s, _, _, _ = score_stats(cluster.get("scores", []))
        print(
            f"--- Cluster #{idx}: {key[0]} -> {key[1]} "
            f"(count={cluster['count']}, avg_score={avg_s}) ---"
        )
        for i, ex in enumerate(cluster.get("examples", [])[:examples_per_cluster], start=1):
            q = ex.get("question") or "<sem pergunta>"
            print(f"Exemplo {i}: \"{q}\"")
            print(f"  expected_intent: {ex.get('expected_intent')}")
            print(f"  got_intent     : {ex.get('got_intent')}")
        print()


def print_technical_errors(technical_errors: Dict[str, Any]) -> None:
    if not technical_errors:
        return
    print("Erros técnicos (status != 'ok'):")
    for reason, bucket in sorted(
        technical_errors.items(), key=lambda kv: kv[1].get("count", 0), reverse=True
    ):
        count = bucket.get("count", 0)
        print(f"- {reason}: {count}")
        for ex in bucket.get("examples", [])[:3]:
            q = ex.get("question") or "<sem pergunta>"
            print(
                f"    idx={ex.get('idx')} | {q} | expected={ex.get('expected_entity')} "
                f"| got={ex.get('got_entity')} | status_msg={ex.get('status_message')}"
            )
    print()


def build_export_payload(
    total: int,
    clusters: Dict[ClusterKey, Dict[str, Any]],
    technical_errors: Dict[str, Any],
    examples_per_cluster: int,
) -> Dict[str, Any]:
    from datetime import datetime

    ordered_clusters = sorted(
        clusters.items(), key=lambda kv: kv[1].get("count", 0), reverse=True
    )

    out_clusters = []
    for key, cluster in ordered_clusters:
        avg_s, min_s, max_s, _ = score_stats(cluster.get("scores", []))
        out_clusters.append(
            {
                "expected_entity": key[0],
                "got_entity": key[1],
                "count": cluster.get("count", 0),
                "avg_score": None if avg_s == "-" else float(avg_s),
                "min_score": None if min_s == "-" else float(min_s),
                "max_score": None if max_s == "-" else float(max_s),
                "examples": cluster.get("examples", [])[:examples_per_cluster],
            }
        )

    tech_total = sum(v.get("count", 0) for v in technical_errors.values())
    tech_out = {"total": tech_total, "by_reason": {}}
    for reason, bucket in technical_errors.items():
        tech_out["by_reason"][reason] = {
            "count": bucket.get("count", 0),
            "examples": bucket.get("examples", [])[:examples_per_cluster],
        }

    return {
        "version": "routing_misses_clusters_v1",
        "total_misses": total,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "clusters": out_clusters,
        "technical_errors": tech_out,
    }


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clusteriza misses de routing")
    parser.add_argument(
        "--misses-file",
        type=str,
        default=str(DEFAULT_MISSES_FILE),
        help="Caminho para routing_misses_via_ask.json",
    )
    parser.add_argument(
        "--top-clusters",
        type=int,
        default=DEFAULT_TOP_CLUSTERS,
        help="Número máximo de clusters a mostrar na tabela principal",
    )
    parser.add_argument(
        "--examples-per-cluster",
        type=int,
        default=DEFAULT_EXAMPLES_PER_CLUSTER,
        help="Quantidade de exemplos por cluster nos detalhes",
    )
    parser.add_argument(
        "--export-json",
        type=str,
        default=None,
        help="Se informado, caminho para salvar JSON consolidado com clusters",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    misses_path = Path(args.misses_file)
    if not misses_path.exists():
        print(
            f"[error] Arquivo de misses não encontrado: {misses_path}",
            file=sys.stderr,
        )
        return 1

    try:
        misses = load_misses(misses_path)
    except Exception as exc:  # pragma: no cover - fluxo de erro
        print(f"[error] Não foi possível carregar misses: {exc}", file=sys.stderr)
        return 1
    total_misses = len(misses)
    clusters, technical_errors = cluster_misses(misses)

    print_summary(total_misses, clusters, technical_errors)
    ordered_clusters = print_clusters_table(clusters, args.top_clusters)
    print_examples(ordered_clusters, args.examples_per_cluster)
    print_technical_errors(technical_errors)

    if args.export_json:
        export_path = Path(args.export_json)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        payload = build_export_payload(
            total_misses, clusters, technical_errors, args.examples_per_cluster
        )
        export_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"JSON consolidado salvo em {export_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
