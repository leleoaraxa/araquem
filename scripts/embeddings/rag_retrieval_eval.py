#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: rag_retrieval_eval.py
Purpose: Calcular métricas de recuperação RAG e registrar resultados operacionais.
Compliance: Guardrails Araquem v2.1.1
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Dict, List, Sequence

import requests

from app.rag.index_reader import EmbeddingStore
from app.rag.ollama_client import OllamaClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate RAG retrieval quality")
    parser.add_argument("--eval", required=True, help="Path to rag_eval_set.json")
    parser.add_argument("--k", type=int, default=10, help="Top-K for retrieval")
    parser.add_argument(
        "--index",
        default="data/embeddings/store/embeddings.jsonl",
        help="Embeddings store JSONL",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="API base URL (for metrics register)",
    )
    parser.add_argument("--timeout", type=int, default=30)
    return parser.parse_args()


# ---------- métricas ----------

def recall_at_k(expected: Sequence[str], retrieved: Sequence[str], k: int) -> float:
    if not expected:
        return 0.0
    topk = set(retrieved[:k])
    exp = set(expected)
    return float(len(exp & topk)) / float(len(exp))


def mrr_at_k(expected: Sequence[str], retrieved: Sequence[str], k: int) -> float:
    exp = set(expected)
    for rank, rid in enumerate(retrieved[:k], start=1):
        if rid in exp:
            return 1.0 / float(rank)
    return 0.0


def dcg_at_k(expected: Sequence[str], retrieved: Sequence[str], k: int) -> float:
    exp = set(expected)
    dcg = 0.0
    for i, rid in enumerate(retrieved[:k], start=1):
        rel = 1.0 if rid in exp else 0.0
        if i == 1:
            dcg += rel
        else:
            dcg += rel / math.log2(i)
    return dcg


def idcg_at_k(expected: Sequence[str], k: int) -> float:
    gains = [1.0] * min(len(expected), k)
    idcg = 0.0
    for i, rel in enumerate(gains, start=1):
        if i == 1:
            idcg += rel
        else:
            idcg += rel / math.log2(i)
    return idcg or 1.0


def ndcg_at_k(expected: Sequence[str], retrieved: Sequence[str], k: int) -> float:
    return dcg_at_k(expected, retrieved, k) / idcg_at_k(expected, k)


# ---------- runner ----------

def load_eval_set(path: str) -> List[Dict[str, object]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Eval set must be a list of {q, expected_ids}")
    return data


def retrieval(store: EmbeddingStore, embedder: OllamaClient, query: str, k: int) -> List[str]:
    results = store.search_by_text(query, embedder, k=k)
    ids: List[str] = []
    for item in results:
        rid = item.get("id") or item.get("doc_id") or item.get("chunk_id")
        if rid:
            ids.append(str(rid))
    return ids


def aggregate(metrics: List[Dict[str, float]]) -> Dict[str, float]:
    if not metrics:
        return {"recall_at_5": 0.0, "recall_at_10": 0.0, "mrr": 0.0, "ndcg_at_10": 0.0}
    agg: Dict[str, float] = {}
    for key in ("recall_at_5", "recall_at_10", "mrr", "ndcg_at_10"):
        values = [m.get(key, 0.0) for m in metrics]
        agg[key] = sum(values) / max(1, len(values))
    return agg


def main() -> None:
    args = parse_args()
    eval_set = load_eval_set(args.eval)
    store = EmbeddingStore(Path(args.index))
    embedder = OllamaClient()

    per_query: List[Dict[str, float]] = []
    for item in eval_set:
        q = str(item.get("q") or "").strip()
        expected = [str(x) for x in (item.get("expected_ids") or [])]
        if not q:
            continue
        retrieved = retrieval(store, embedder, q, k=args.k)
        per_query.append(
            {
                "recall_at_5": recall_at_k(expected, retrieved, 5),
                "recall_at_10": recall_at_k(expected, retrieved, 10),
                "mrr": mrr_at_k(expected, retrieved, args.k),
                "ndcg_at_10": ndcg_at_k(expected, retrieved, 10),
            }
        )

    agg = aggregate(per_query)
    payload = {
        "recall_at_5": round(agg["recall_at_5"], 6),
        "recall_at_10": round(agg["recall_at_10"], 6),
        "mrr": round(agg["mrr"], 6),
        "ndcg_at_10": round(agg["ndcg_at_10"], 6),
        "ts": int(time.time()),
    }

    url = f"{args.api_url}/ops/metrics/rag/eval/register"
    response = requests.post(url, json=payload, timeout=args.timeout)
    response.raise_for_status()

    out = {"per_query": per_query, "aggregate": payload}
    Path("data/ops/quality/rag_eval_last.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("[rag-eval] done:", json.dumps(payload))


if __name__ == "__main__":
    main()
