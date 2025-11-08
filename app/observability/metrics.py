# app/observability/metrics.py

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from prometheus_client import Gauge

from app.observability.instrumentation import counter as _counter
from app.observability.instrumentation import gauge as _gauge
from app.observability.instrumentation import histogram as _histogram

STRICT = os.getenv("SIRIOS_METRICS_STRICT", "false").strip().lower() in (
    "1",
    "true",
    "yes",
)

# Catálogo canônico: nome -> {type, labels}
_METRICS_SCHEMA: Dict[str, Dict[str, Any]] = {
    # HTTP
    "sirios_http_request_duration_seconds": {
        "type": "histogram",
        "labels": {"route", "method"},
    },
    "sirios_http_requests_total": {
        "type": "counter",
        "labels": {"route", "method", "code"},
    },
    # Planner / routing
    "sirios_planner_duration_seconds": {
        "type": "histogram",
        "labels": {"stage"},
    },  # e.g., stage=plan
    "sirios_planner_routed_total": {
        "type": "counter",
        "labels": {"outcome"},
    },  # ok | unroutable
    "sirios_planner_explain_enabled_total": {"type": "counter", "labels": set()},
    "sirios_planner_explain_latency_seconds": {"type": "histogram", "labels": set()},
    "sirios_planner_top2_gap_histogram": {"type": "histogram", "labels": set()},
    "sirios_planner_blocked_by_threshold_total": {
        "type": "counter",
        "labels": {"reason", "intent", "entity"},
    },
    "sirios_planner_route_decisions_total": {
        "type": "counter",
        "labels": {"intent", "entity", "outcome"},
    },
    "sirios_planner_explain_nodes_total": {"type": "counter", "labels": {"node_kind"}},
    "sirios_planner_intent_score": {"type": "histogram", "labels": {"intent"}},
    "sirios_planner_entity_score": {"type": "histogram", "labels": {"entity"}},
    "sirios_planner_projection_total": {
        "type": "counter",
        "labels": {"outcome", "entity"},
    },
    # Quality / routing checks (usadas no /ops/quality/push e no quality_report)
    "sirios_planner_top1_match_total": {
        "type": "counter",
        "labels": {"result"},  # result=hit|miss
    },
    "sirios_planner_confusion_total": {
        "type": "counter",
        "labels": {"expected_intent", "predicted_intent"},
    },
    # (mantém-se o restante do catálogo)
    # Cache
    "sirios_cache_ops_total": {
        "type": "counter",
        "labels": {"op", "outcome"},
    },  # op=get|set, outcome=hit|miss|ok|fail
    "cache_hits_total": {"type": "counter", "labels": {"entity"}},
    "cache_misses_total": {"type": "counter", "labels": {"entity"}},
    "metrics_cache_hits_total": {"type": "counter", "labels": {"entity"}},
    "metrics_cache_misses_total": {"type": "counter", "labels": {"entity"}},
    # Explain persistence
    "sirios_explain_events_failed_total": {"type": "counter", "labels": set()},
    # Narrator
    "sirios_narrator_render_total": {"type": "counter", "labels": {"outcome"}},
    "sirios_narrator_shadow_total": {"type": "counter", "labels": {"outcome"}},
    "sirios_narrator_latency_ms": {"type": "histogram", "labels": set()},
}

RAG_INDEX_SIZE_TOTAL = Gauge(
    "rag_index_size_total",
    "Size in bytes of the RAG embeddings index",
    labelnames=["store"],
)
RAG_INDEX_DOCS_TOTAL = Gauge(
    "rag_index_docs_total",
    "Total docs (lines) in the RAG embeddings index",
    labelnames=["store"],
)
RAG_INDEX_LAST_REFRESH_TS = Gauge(
    "rag_index_last_refresh_timestamp",
    "Epoch seconds of the last RAG index refresh",
)
RAG_INDEX_DENSITY_SCORE = Gauge(
    "rag_index_density_score",
    "Docs per MB for the RAG embeddings index",
)

RAG_EVAL_RECALL_AT_5 = Gauge("rag_eval_recall_at_5", "RAG retrieval recall@5")
RAG_EVAL_RECALL_AT_10 = Gauge("rag_eval_recall_at_10", "RAG retrieval recall@10")
RAG_EVAL_MRR = Gauge("rag_eval_mrr", "RAG retrieval mean reciprocal rank")
RAG_EVAL_NDCG_AT_10 = Gauge("rag_eval_ndcg_at_10", "RAG retrieval nDCG@10")
RAG_EVAL_LAST_RUN_TS = Gauge(
    "rag_eval_last_run_timestamp", "Epoch seconds of last retrieval QA run"
)


def _validate_and_normalize(name: str, labels: Mapping[str, Any]) -> Mapping[str, str]:
    spec = _METRICS_SCHEMA.get(name)
    if spec is None:
        if STRICT:
            raise ValueError(f"[metrics] Métrica não cadastrada: {name}")
        # Em modo não-estrito, permite qualquer label (retrocompat), mas ainda normaliza
        return {k: str(v) for k, v in labels.items() if v is not None}

    allowed = spec.get("labels", set())
    unknown = set(labels.keys()) - set(allowed)
    if unknown and STRICT:
        raise ValueError(
            f"[metrics] Labels não permitidos para {name}: {sorted(unknown)}; permitidos={sorted(allowed)}"
        )

    # filtra desconhecidos em modo brando
    return {k: str(v) for k, v in labels.items() if (k in allowed and v is not None)}


def emit_counter(name: str, **labels: Any) -> None:
    value = float(labels.pop("_value", 1.0))
    labs = _validate_and_normalize(name, labels)
    _counter(name, _value=value, **labs)


def emit_histogram(name: str, value: float, **labels: Any) -> None:
    labs = _validate_and_normalize(name, labels)
    _histogram(name, float(value), **labs)


def emit_gauge(name: str, value: float, **labels: Any) -> None:
    labs = _validate_and_normalize(name, labels)
    _gauge(name, float(value), **labs)


# Opcional: utilidade para consultar o catálogo (debug/admin)
def list_metrics_catalog() -> Dict[str, Dict[str, Any]]:
    return {
        k: {"type": v["type"], "labels": sorted(list(v["labels"]))}
        for k, v in _METRICS_SCHEMA.items()
    }


def _parse_epoch(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_iso_timestamp(raw: Any) -> Optional[int]:
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    candidates = [text]
    # Garante suporte a timestamps sem timezone explícito
    if "+" not in text and not text.endswith("Z"):
        candidates.append(text + "+00:00")
    for candidate in candidates:
        try:
            dt = datetime.fromisoformat(candidate)
        except ValueError:
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    return None


def compute_rag_index_metrics(
    base_dir: Path = Path("data/embeddings/store"),
    filename: str = "embeddings.jsonl",
    manifest_name: str = "manifest.json",
) -> Dict[str, Any]:
    store_path = base_dir / filename
    manifest_path = base_dir / manifest_name

    size_bytes = store_path.stat().st_size if store_path.exists() else 0
    docs_total = 0
    if store_path.exists():
        with store_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                except Exception:
                    continue
                docs_total += 1

    last_ts = int(time.time())
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}
        epoch = _parse_epoch(manifest.get("last_refresh_epoch"))
        if epoch is None:
            epoch = _parse_iso_timestamp(
                manifest.get("last_refresh_iso") or manifest.get("generated_at")
            )
        if epoch is None:
            try:
                epoch = int(manifest_path.stat().st_mtime)
            except FileNotFoundError:
                epoch = None
        if epoch is not None:
            last_ts = epoch

    mb = max(size_bytes / 1_000_000.0, 1e-6)
    density = float(docs_total) / mb if docs_total else 0.0

    return {
        "store": filename,
        "size_bytes": int(size_bytes),
        "docs_total": int(docs_total),
        "last_refresh_ts": int(last_ts),
        "density_score": float(density),
    }


def register_rag_index_metrics(metrics: Mapping[str, Any]) -> None:
    store = str(metrics.get("store") or "embeddings.jsonl")
    RAG_INDEX_SIZE_TOTAL.labels(store=store).set(float(metrics.get("size_bytes", 0)))
    RAG_INDEX_DOCS_TOTAL.labels(store=store).set(float(metrics.get("docs_total", 0)))
    RAG_INDEX_LAST_REFRESH_TS.set(float(metrics.get("last_refresh_ts", 0)))
    RAG_INDEX_DENSITY_SCORE.set(float(metrics.get("density_score", 0.0)))


def register_rag_eval_metrics(payload: dict) -> None:
    """
    payload = {
      "recall_at_5": float,
      "recall_at_10": float,
      "mrr": float,
      "ndcg_at_10": float,
      "ts": int (epoch)  # opcional; se ausente, usa time.time()
    }
    """

    ts = int(payload.get("ts") or time.time())
    RAG_EVAL_RECALL_AT_5.set(float(payload["recall_at_5"]))
    RAG_EVAL_RECALL_AT_10.set(float(payload["recall_at_10"]))
    RAG_EVAL_MRR.set(float(payload["mrr"]))
    RAG_EVAL_NDCG_AT_10.set(float(payload["ndcg_at_10"]))
    RAG_EVAL_LAST_RUN_TS.set(ts)
