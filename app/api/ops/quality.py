import math
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.context import orchestrator, planner
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
                ((plan.get("explain") or {}).get("scoring") or {}).get("intent_top2_gap")
                or 0.0
            )
            histogram("sirios_planner_top2_gap_histogram", top2_gap)

            matched += int(predicted == expected)
            missed += int(predicted != expected)
        return {
            "accepted": len(samples_raw),
            "metrics": {"matched": matched, "missed": missed},
        }

    if ptype == "projection":
        entity = payload.get("entity")
        result_key = payload.get("result_key")
        must_have = payload.get("must_have_columns") or []
        samples_raw: List[Dict[str, Any]] = payload.get("samples", [])
        if not (entity and result_key and isinstance(must_have, list)):
            return JSONResponse({"error": "invalid projection payload"}, status_code=400)

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
                counter("sirios_planner_projection_total", outcome="ok", entity=str(entity))
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
        return JSONResponse({"error": f"failed to load thresholds: {e}"}, status_code=500)

    qg = (thr.get("quality_gates") or {}).get("thresholds") or {}
    min_top1_acc = float(qg.get("min_top1_accuracy", 0.0))
    min_routed_rt = float(qg.get("min_routed_rate", 0.0))
    min_top2_gap = float(qg.get("min_top2_gap", 0.0))
    max_miss_abs = float(qg.get("max_misses_absolute", 0.0))
    max_miss_ratio = float(qg.get("max_misses_ratio", 1.0))

    top1_hit = prom_query_instant('sum(sirios_planner_top1_match_total{result="hit"})')
    top1_total = prom_query_instant("sum(sirios_planner_top1_match_total)")
    routed_ok = prom_query_instant('sum(sirios_planner_routed_total{outcome!="unroutable"})')
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
