# app/api/ops/quality.py
import math
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.context import orchestrator, planner
from app.planner.planner import _load_thresholds
from app.observability.metrics import (
    emit_counter as counter,
    emit_histogram as histogram,
)
from app.observability.runtime import prom_query_instant

router = APIRouter()


class QualitySample(BaseModel):
    question: str
    expected_intent: str
    expected_entity: Optional[str] = None


@router.post("/ops/quality/push")
def quality_push(
    payload: Dict[str, Any] = Body(...),
    x_ops_token: Optional[str] = Header(default=None),
):
    token_env = os.getenv("QUALITY_OPS_TOKEN", "")
    if not token_env or (x_ops_token or "") != token_env:
        return JSONResponse({"error": "forbidden"}, status_code=403)

    ptype = (payload.get("type") or "routing").strip().lower()

    if ptype == "routing":
        samples_raw: List[Dict[str, Any]] = payload.get("samples", [])
        matched = 0
        missed = 0
        for s in samples_raw:
            q = s.get("question") or ""
            expected = s.get("expected_intent") or ""
            plan = planner.explain(q)
            chosen = plan.get("chosen") or {}
            predicted = chosen.get("intent")
            entity = chosen.get("entity")

            counter(
                "sirios_planner_top1_match_total",
                result=("hit" if predicted == expected else "miss"),
            )

            if expected and predicted:
                counter(
                    "sirios_planner_confusion_total",
                    expected_intent=str(expected),
                    predicted_intent=str(predicted),
                )

            counter(
                "sirios_planner_routed_total",
                outcome=("ok" if entity else "unroutable"),
            )

            top2_gap = float(
                ((plan.get("explain") or {}).get("scoring") or {}).get(
                    "intent_top2_gap"
                )
                or 0.0
            )
            histogram("sirios_planner_top2_gap_histogram", top2_gap)

            matched += int(predicted == expected)
            missed += int(predicted != expected)
        return {
            "accepted": len(samples_raw),
            "metrics": {"matched": matched, "missed": missed},
        }

    if ptype == "rag_search":
        defaults = payload.get("defaults") or {}
        if defaults and not isinstance(defaults, dict):
            return JSONResponse(
                {"error": "invalid rag_search payload: defaults must be an object"},
                status_code=400,
            )
        samples_raw = payload.get("samples")

        if not isinstance(samples_raw, list) or not samples_raw:
            return JSONResponse(
                {
                    "error": "invalid rag_search payload: samples must be a non-empty list"
                },
                status_code=400,
            )

        def _validate_threshold(value: Any, key: str, label: str) -> Optional[str]:
            if value is None:
                return None
            if key == "k":
                if not isinstance(value, int) or value < 1:
                    return f"{label} must be an integer >= 1"
            elif key == "min_score":
                if not isinstance(value, (int, float)):
                    return f"{label} must be a number between 0 and 1"
                value_f = float(value)
                if value_f < 0 or value_f > 1:
                    return f"{label} must be between 0 and 1"
            elif key == "tags":
                if value is None:
                    return None
                if not isinstance(value, list) or not all(
                    isinstance(tag, str) and tag.strip() for tag in value
                ):
                    return f"{label} must be a list of non-empty strings"
            return None

        for key in ("k", "min_score", "tags"):
            err = _validate_threshold(defaults.get(key), key, f"defaults.{key}")
            if err:
                return JSONResponse(
                    {"error": f"invalid rag_search payload: {err}"}, status_code=400
                )

        normalized_samples: List[Dict[str, Any]] = []
        for idx, sample in enumerate(samples_raw):
            if not isinstance(sample, dict):
                return JSONResponse(
                    {
                        "error": f"invalid rag_search payload: samples[{idx}] must be an object"
                    },
                    status_code=400,
                )
            question = sample.get("question")
            if not isinstance(question, str) or not question.strip():
                return JSONResponse(
                    {
                        "error": "invalid rag_search payload: "
                        f"samples[{idx}].question must be a non-empty string"
                    },
                    status_code=400,
                )
            expect = sample.get("expect") or {}
            if not isinstance(expect, dict):
                return JSONResponse(
                    {
                        "error": f"invalid rag_search payload: samples[{idx}].expect must be an object"
                    },
                    status_code=400,
                )
            doc_prefix = expect.get("doc_id_prefix")
            if not isinstance(doc_prefix, str) or not doc_prefix.strip():
                return JSONResponse(
                    {
                        "error": "invalid rag_search payload: "
                        f"samples[{idx}].expect.doc_id_prefix must be a non-empty string"
                    },
                    status_code=400,
                )
            for key in ("k", "min_score", "tags"):
                err = _validate_threshold(
                    expect.get(key), key, f"samples[{idx}].expect.{key}"
                )
                if err:
                    return JSONResponse(
                        {"error": f"invalid rag_search payload: {err}"}, status_code=400
                    )
            normalized_samples.append(
                {
                    "question": question,
                    "expect": expect,
                }
            )

        thr_path = os.getenv(
            "PLANNER_THRESHOLDS_PATH", "data/ops/planner_thresholds.yaml"
        )
        thresholds = _load_thresholds(thr_path)
        rag_cfg = (thresholds.get("planner") or {}).get("rag") or {}
        if not bool(rag_cfg.get("enabled", False)):
            return JSONResponse(
                {"error": "rag search disabled by thresholds"}, status_code=400
            )

        from app.rag.index_reader import EmbeddingStore
        from app.rag.ollama_client import OllamaClient

        index_path = os.getenv(
            "RAG_INDEX_PATH", "data/embeddings/store/embeddings.jsonl"
        )

        try:
            store = EmbeddingStore(index_path)
        except FileNotFoundError:
            return JSONResponse(
                {"error": f"failed to load rag index: file not found '{index_path}'"},
                status_code=500,
            )
        except Exception as exc:
            return JSONResponse(
                {"error": f"failed to load rag index: {exc}"}, status_code=500
            )

        embedder = OllamaClient()

        accepted = len(normalized_samples)
        ok = fail = 0
        details: List[Dict[str, Any]] = []

        defaults_k_raw = defaults.get("k") if isinstance(defaults, dict) else None
        defaults_k = int(defaults_k_raw) if defaults_k_raw is not None else 5
        defaults_min_score_raw = (
            defaults.get("min_score") if isinstance(defaults, dict) else None
        )
        defaults_min_score = (
            float(defaults_min_score_raw)
            if defaults_min_score_raw is not None
            else 0.20
        )
        defaults_tags_raw = defaults.get("tags") if isinstance(defaults, dict) else None
        defaults_tags = list(defaults_tags_raw or [])

        for sample in normalized_samples:
            question = sample["question"]
            expect = sample["expect"]
            if "k" in expect and expect.get("k") is not None:
                effective_k = int(expect.get("k"))
            else:
                effective_k = defaults_k

            if "min_score" in expect and expect.get("min_score") is not None:
                effective_min_score = float(expect.get("min_score"))
            else:
                effective_min_score = defaults_min_score

            if "tags" in expect:
                tags_filter_raw = expect.get("tags") or []
            else:
                tags_filter_raw = defaults_tags
            tags_filter = list(tags_filter_raw or [])

            detail: Dict[str, Any] = {
                "question": question,
                "k": effective_k,
                "min_score": effective_min_score,
                "doc_id_prefix": expect.get("doc_id_prefix"),
            }
            if tags_filter:
                detail["tags"] = list(tags_filter)

            try:
                qvec = embedder.embed([question])[0]
                hits = store.search_by_vector(qvec, k=effective_k) or []
            except Exception as exc:
                fail += 1
                counter("sirios_rag_search_total", outcome="fail")
                detail["error"] = repr(exc)
                detail["top_hits"] = []
                detail["passed"] = False
                details.append(detail)
                continue

            filtered_hits = []
            for hit in hits:
                score = float(hit.get("score") or 0.0)
                if score < effective_min_score:
                    continue
                tags = hit.get("tags") or []
                if tags_filter and not all(tag in tags for tag in tags_filter):
                    continue
                filtered_hits.append(hit)

            passed = any(
                isinstance(hit.get("doc_id"), str)
                and hit.get("doc_id", "").startswith(expect.get("doc_id_prefix"))
                for hit in filtered_hits
            )

            if filtered_hits:
                top_score = float(filtered_hits[0].get("score") or 0.0)
                histogram("sirios_rag_topscore", top_score)

            detail_hits = []
            for hit in filtered_hits[:5]:
                detail_hits.append(
                    {
                        "doc_id": hit.get("doc_id"),
                        "score": float(hit.get("score") or 0.0),
                        "chunk_id": hit.get("chunk_id"),
                    }
                )

            detail["top_hits"] = detail_hits
            detail["passed"] = bool(passed)

            if passed:
                ok += 1
                counter("sirios_rag_search_total", outcome="ok")
            else:
                fail += 1
                counter("sirios_rag_search_total", outcome="fail")

            details.append(detail)

        return {
            "accepted": accepted,
            "metrics": {"ok": ok, "fail": fail},
            "details": details,
        }

    if ptype == "projection":
        entity = payload.get("entity")
        result_key = payload.get("result_key")
        must_have = payload.get("must_have_columns") or []
        samples_raw: List[Dict[str, Any]] = payload.get("samples", [])
        if not (entity and result_key and isinstance(must_have, list)):
            return JSONResponse(
                {"error": "invalid projection payload"}, status_code=400
            )

        ok = fail = 0
        for s in samples_raw:
            q = s.get("question") or ""
            out = orchestrator.route_question(q)
            results = out.get("results") or {}
            rows = results.get(result_key) or []
            passed = False
            if isinstance(rows, list) and rows:
                first = rows[0]
                if isinstance(first, dict):
                    passed = all(col in first.keys() for col in must_have)
            if passed:
                ok += 1
                counter(
                    "sirios_planner_projection_total", outcome="ok", entity=str(entity)
                )
            else:
                fail += 1
                counter(
                    "sirios_planner_projection_total",
                    outcome="fail",
                    entity=str(entity),
                )
        return {"accepted": len(samples_raw), "metrics": {"ok": ok, "fail": fail}}

    return JSONResponse({"error": f"unsupported type '{ptype}'"}, status_code=400)


@router.get("/ops/quality/report")
def quality_report():
    thr_path = os.getenv("PLANNER_THRESHOLDS_PATH", "data/ops/planner_thresholds.yaml")
    try:
        import yaml

        with open(thr_path, "r", encoding="utf-8") as f:
            thr = yaml.safe_load(f) or {}
    except Exception as e:
        return JSONResponse(
            {"error": f"failed to load thresholds: {e}"}, status_code=500
        )

    qg = (thr.get("quality_gates") or {}).get("thresholds") or {}
    min_top1_acc = float(qg.get("min_top1_accuracy", 0.0))
    min_routed_rt = float(qg.get("min_routed_rate", 0.0))
    min_top2_gap = float(qg.get("min_top2_gap", 0.0))
    max_miss_abs = float(qg.get("max_misses_absolute", 0.0))
    max_miss_ratio = float(qg.get("max_misses_ratio", 1.0))

    top1_hit = prom_query_instant('sum(sirios_planner_top1_match_total{result="hit"})')
    top1_total = prom_query_instant("sum(sirios_planner_top1_match_total)")
    routed_ok = prom_query_instant(
        'sum(sirios_planner_routed_total{outcome!="unroutable"})'
    )
    routed_all = prom_query_instant("sum(sirios_planner_routed_total)")
    gap_p50 = prom_query_instant(
        "histogram_quantile(0.50, sum(rate(sirios_planner_top2_gap_histogram_bucket[5m])) by (le))"
    )
    proj_ok = prom_query_instant('sum(sirios_planner_projection_total{outcome="ok"})')
    proj_total = prom_query_instant("sum(sirios_planner_projection_total)")
    miss_abs = prom_query_instant('sum(sirios_planner_top1_match_total{result="miss"})')

    def _to_float(x) -> float:
        if isinstance(x, (int, float)):
            return float(x)
        if isinstance(x, dict):
            try:
                val = (x.get("data", {}).get("result") or [{}])[0].get("value")
                if isinstance(val, list) and len(val) == 2:
                    return float(val[1])
            except Exception:
                pass
            return 0.0
        try:
            return float(str(x))
        except Exception:
            return 0.0

    def _ratio(num, den) -> float:
        n, d = _to_float(num), _to_float(den)
        return (n / d) if d > 0 else 0.0

    top1_acc = _ratio(top1_hit, top1_total)
    routed_rt = _ratio(routed_ok, routed_all)
    proj_pass = _ratio(proj_ok, proj_total)
    miss_abs_v = _to_float(miss_abs)
    miss_ratio = _ratio(miss_abs, top1_total)
    gap_p50_v = _to_float(gap_p50)

    violations: List[str] = []
    if top1_acc < min_top1_acc:
        violations.append(f"top1_accuracy {top1_acc:.3f} < min {min_top1_acc:.3f}")
    if routed_rt < min_routed_rt:
        violations.append(f"routed_rate {routed_rt:.3f} < min {min_routed_rt:.3f}")
    if gap_p50_v < min_top2_gap:
        violations.append(f"top2_gap_p50 {gap_p50_v:.3f} < min {min_top2_gap:.3f}")
    if miss_abs_v > max_miss_abs:
        violations.append(f"misses_abs {miss_abs_v:.0f} > max {max_miss_abs:.0f}")
    if miss_ratio > max_miss_ratio:
        violations.append(f"misses_ratio {miss_ratio:.3f} > max {max_miss_ratio:.3f}")

    status = "pass" if not violations else "fail"

    def _sanitize(v: float) -> float:
        if not isinstance(v, (int, float)):
            return 0.0
        if math.isnan(v) or math.isinf(v):
            return 0.0
        return round(float(v), 6)

    metrics = {
        "top1_accuracy": _sanitize(top1_acc),
        "routed_rate": _sanitize(routed_rt),
        "top2_gap_p50": _sanitize(gap_p50_v),
        "projection_pass": _sanitize(proj_pass),
        "misses_abs": _sanitize(miss_abs_v),
        "misses_ratio": _sanitize(miss_ratio),
    }

    return {
        "status": status,
        "metrics": metrics,
        "thresholds": qg,
        "violations": violations,
    }
