# app/api/ops/quality.py
import math
import os
import logging
from fastapi import Request
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


def _sanitize(v: float) -> float:
    if not isinstance(v, (int, float)):
        return 0.0
    if math.isnan(v) or math.isinf(v):
        return 0.0
    return round(float(v), 6)


def _first_nonzero_expr(exprs: List[str]) -> float:
    """Executa, em ordem, e retorna o primeiro valor > 0 (ou o último valor obtido)."""
    last = 0.0
    for e in exprs:
        try:
            val = _to_float(prom_query_instant(e))
            last = val
            if val > 0.0:
                return val
        except Exception:
            continue
    return last


@router.post("/ops/quality/push")
def quality_push(
    payload: Dict[str, Any] = Body(...),
    x_ops_token: Optional[str] = Header(default=None),
    authorization: Optional[str] = Header(default=None),
    request: Request = None,
):
    # --- Auth: header configurável + Bearer opcional ---
    token_env = os.getenv("QUALITY_OPS_TOKEN", "")
    if not token_env:
        return JSONResponse({"error": "forbidden"}, status_code=403)

    # Header configurável (default X-OPS-TOKEN), case-insensitive
    header_name = (os.getenv("QUALITY_TOKEN_HEADER", "X-OPS-TOKEN") or "").lower()
    provided_token = None
    if request is not None:
        provided_token = request.headers.get(header_name)
    provided_token = provided_token or x_ops_token

    # Bearer opcional controlado por env QUALITY_AUTH_BEARER
    allow_bearer = (os.getenv("QUALITY_AUTH_BEARER", "") or "").lower() in (
        "1",
        "true",
        "yes",
    )
    bearer_ok = False
    if allow_bearer and authorization and authorization.startswith("Bearer "):
        bearer_ok = authorization.replace("Bearer ", "", 1).strip() == token_env

    if not (provided_token == token_env or bearer_ok):
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
            params = payload.get("params") or {}
            try:
                out = orchestrator.route_question(q, params=params)
            except TypeError:
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
    policy_path = os.getenv("QUALITY_POLICY_PATH", "data/policies/quality.yaml")
    fallback_path = os.getenv(
        "PLANNER_THRESHOLDS_PATH", "data/ops/planner_thresholds.yaml"
    )

    try:
        import yaml
    except Exception:
        logging.exception("Failed to import yaml module in quality_report")
        return JSONResponse({"error": "failed to load quality policy"}, status_code=500)

    policy = None
    errors: List[str] = []
    used_path: Optional[str] = None
    for candidate in [policy_path, fallback_path]:
        if not candidate:
            continue
        try:
            with open(candidate, "r", encoding="utf-8") as f:
                policy = yaml.safe_load(f) or {}
            used_path = candidate  # <- corrigido (antes ficava depois do break)
            break
        except FileNotFoundError:
            error_msg = f"file not found '{candidate}'"
            errors.append(error_msg)
            logging.error(error_msg)
        except Exception as exc:
            error_msg = f"Error loading '{candidate}': {exc}"
            errors.append(error_msg)
            logging.exception(error_msg)

    if policy is None:
        return JSONResponse(
            {"error": f"failed to load quality policy: {'; '.join(errors)}"},
            status_code=500,
        )

    logging.info("quality_report: policy loaded from %s", used_path or "<unknown>")

    targets = policy.get("targets") or {}
    if not targets:
        targets = (policy.get("quality_gates") or {}).get("thresholds") or {}

    # Permite override por ENV (útil p/ testes rápidos)
    def _env_or_target(env_key: str, target_key: str, default: float) -> float:
        v = os.getenv(env_key)
        if v is not None:
            try:
                return float(v)
            except Exception:
                pass
        return float(targets.get(target_key, default))

    min_top1_acc = _env_or_target("QUALITY_MIN_TOP1_ACC", "min_top1_accuracy", 0.0)
    min_routed_rt = _env_or_target("QUALITY_MIN_ROUTED_RATE", "min_routed_rate", 0.0)
    min_top2_gap = _env_or_target("QUALITY_MIN_TOP2_GAP", "min_top2_gap", 0.0)
    max_miss_abs = _env_or_target("QUALITY_MAX_MISSES_ABS", "max_misses_absolute", 0.0)
    max_miss_ratio = _env_or_target("QUALITY_MAX_MISSES_RATIO", "max_misses_ratio", 1.0)

    # Métricas brutas
    top1_hit = prom_query_instant('sum(sirios_planner_top1_match_total{result="hit"})')
    top1_total = prom_query_instant("sum(sirios_planner_top1_match_total)")
    routed_ok = prom_query_instant(
        'sum(sirios_planner_routed_total{outcome!="unroutable"})'
    )
    routed_all = prom_query_instant("sum(sirios_planner_routed_total)")
    proj_ok = prom_query_instant('sum(sirios_planner_projection_total{outcome="ok"})')
    proj_total = prom_query_instant("sum(sirios_planner_projection_total)")
    miss_abs = prom_query_instant('sum(sirios_planner_top1_match_total{result="miss"})')

    # Gap P50 — tentar múltiplas janelas e fallback para increase()
    windows_csv = os.getenv("QUALITY_GAP_WINDOWS", "10m,1h,6h,24h")
    windows = [w.strip() for w in windows_csv.split(",") if w.strip()]
    exprs = []
    for w in windows:
        exprs.append(
            f"histogram_quantile(0.50, sum(rate(sirios_planner_top2_gap_histogram_bucket[{w}])) by (le))"
        )
    # fallback com increase (útil quando o rate é ~0 num curto período)
    for w in windows:
        exprs.append(
            f"histogram_quantile(0.50, sum(increase(sirios_planner_top2_gap_histogram_bucket[{w}])) by (le))"
        )

    gap_p50_v = _first_nonzero_expr(exprs)

    # Derivados
    top1_acc = _ratio(top1_hit, top1_total)
    routed_rt = _ratio(routed_ok, routed_all)
    proj_pass = _ratio(proj_ok, proj_total)
    miss_abs_v = _to_float(miss_abs)
    miss_ratio = _ratio(miss_abs, top1_total)

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
        "thresholds": {
            "min_top1_accuracy": min_top1_acc,
            "min_top2_gap": min_top2_gap,
            "min_routed_rate": min_routed_rt,
            "max_misses_absolute": max_miss_abs,
            "max_misses_ratio": max_miss_ratio,
        },
        "violations": violations,
    }
