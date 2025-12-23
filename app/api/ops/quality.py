# app/api/ops/quality.py
import math
import os
import logging
from threading import Lock
from fastapi import Request
from typing import Any, Dict, List, Optional, Set, Tuple
import yaml

from fastapi import APIRouter, Body, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.ops.quality_contracts import (
    RoutingBatchMetadata,
    RoutingPayloadValidationError,
    validate_routing_payload_contract,
)
from app.core.context import orchestrator, planner
from app.planner.planner import _load_thresholds
from app.observability.metrics import (
    emit_counter as counter,
    emit_histogram as histogram,
)
from app.observability.runtime import prom_query_instant

router = APIRouter()
LOGGER = logging.getLogger(__name__)
_QUALITY_LOADER_ERRORS: List[str] | None = None
_ROUTING_BATCH_LOCK = Lock()
_PROCESSED_ROUTING_BATCHES: Dict[str, Set[int]] = {}
_ROUTING_BATCH_MAX_KEYS = 512


class QualitySample(BaseModel):
    question: str
    expected_intent: str
    expected_entity: Optional[str] = None


def _routing_batch_to_dict(batch: RoutingBatchMetadata) -> Dict[str, Any]:
    return {"id": batch.id, "index": batch.index, "total": batch.total}


def _is_duplicate_routing_batch(batch: RoutingBatchMetadata) -> bool:
    """
    Controla idempotência básica por (batch.id, batch.index).
    Mantém um cache em memória com tamanho máximo para evitar crescimento indefinido.
    """
    with _ROUTING_BATCH_LOCK:
        if batch.id not in _PROCESSED_ROUTING_BATCHES and len(_PROCESSED_ROUTING_BATCHES) >= _ROUTING_BATCH_MAX_KEYS:
            # Remove uma chave antiga para evitar crescimento infinito.
            _PROCESSED_ROUTING_BATCHES.pop(next(iter(_PROCESSED_ROUTING_BATCHES)))

        seen = _PROCESSED_ROUTING_BATCHES.setdefault(batch.id, set())
        if batch.index in seen:
            return True

        seen.add(batch.index)
        return False


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


def _append_quality_error(msg: str, sink: Optional[List[str]]) -> None:
    if sink is not None:
        sink.append(msg)

    global _QUALITY_LOADER_ERRORS
    if _QUALITY_LOADER_ERRORS is not None and _QUALITY_LOADER_ERRORS is not sink:
        _QUALITY_LOADER_ERRORS.append(msg)


def _load_candidate(path: str) -> Optional[Dict[str, Any]]:
    errors_sink = _QUALITY_LOADER_ERRORS

    if not path:
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            try:
                loaded = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                LOGGER.error(
                    "Falha ao carregar configuração de qualidade de %s", path, exc_info=True
                )
                _append_quality_error(f"YAML inválido em {path}", errors_sink)
                return None
    except FileNotFoundError:
        msg = f"arquivo de qualidade ausente: {path}"
        LOGGER.warning(msg)
        _append_quality_error(msg, errors_sink)
        return None
    except Exception:
        LOGGER.error(
            "Falha ao carregar configuração de qualidade de %s", path, exc_info=True
        )
        _append_quality_error(f"falha ao ler arquivo: {path}", errors_sink)
        return None

    if not isinstance(loaded, dict):
        msg = f"Configuração de qualidade inválida (esperado mapeamento): {path}"
        LOGGER.error(msg)
        _append_quality_error(msg, errors_sink)
        return None

    targets = loaded.get("targets") if isinstance(loaded, dict) else None
    quality_gates = loaded.get("quality_gates") if isinstance(loaded, dict) else None
    thresholds = None

    schema_errors: List[str] = []
    if targets is not None and not isinstance(targets, dict):
        schema_errors.append("targets deve ser um mapeamento")
    if quality_gates is not None and not isinstance(quality_gates, dict):
        schema_errors.append("quality_gates deve ser um mapeamento")
    if isinstance(quality_gates, dict):
        thresholds = quality_gates.get("thresholds")
        if thresholds is not None and not isinstance(thresholds, dict):
            schema_errors.append("quality_gates.thresholds deve ser um mapeamento")

    if schema_errors:
        msg = f"Configuração de qualidade malformada em {path}: {'; '.join(schema_errors)}"
        LOGGER.error(msg)
        _append_quality_error(msg, errors_sink)
        return None

    if targets is None and thresholds is None:
        msg = f"Configuração de qualidade vazia ou sem thresholds em {path}"
        LOGGER.error(msg)
        _append_quality_error(msg, errors_sink)
        return None

    return loaded


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


def _samples_for_window(w: str) -> float:
    """
    Número de amostras observadas no histograma para a janela w.
    Usa increase(count) como proxy de volume.
    """
    expr = f"sum(increase(sirios_planner_top2_gap_histogram_count[{w}]))"
    try:
        return _to_float(prom_query_instant(expr))
    except Exception:
        return 0.0


def _prom_gap_p50_choose_window(
    windows: List[str], min_samples: float
) -> Tuple[float, bool, str, float]:
    """
    Seleciona p50 considerando presença e volume:
      1) Percorre janelas (menor→maior); ignora as com samples < min_samples.
      2) Entre as elegíveis, retorna a primeira cujo p50 > 0 (rate()→increase()).
      3) Se nenhuma elegível tiver p50>0, usa a MAIOR janela com samples >= min_samples (fallback).
      4) Se nenhuma janela tiver samples suficientes, calcula um 'last_val' informativo e marca had_samples=False.

    Retorna (valor_p50, had_samples, expr_usada, samples_da_janela_escolhida).
    """
    chosen_val, chosen_expr, chosen_samples = float("nan"), "", 0.0
    any_enough = False

    # 1) tenta janelas com volume suficiente
    for w in windows:
        s = _samples_for_window(w)
        if s >= min_samples:
            any_enough = True
            # rate() primeiro
            expr_rate = f"histogram_quantile(0.50, sum(rate(sirios_planner_top2_gap_histogram_bucket[{w}])) by (le))"
            try:
                v = _to_float(prom_query_instant(expr_rate))
                if v > 0.0:
                    return (v, True, expr_rate, s)
                # guarda como possível fallback
                chosen_val, chosen_expr, chosen_samples = v, expr_rate, s
            except Exception:
                pass
            # increase() como alternativa
            expr_inc = f"histogram_quantile(0.50, sum(increase(sirios_planner_top2_gap_histogram_bucket[{w}])) by (le))"
            try:
                v = _to_float(prom_query_instant(expr_inc))
                if v > 0.0:
                    return (v, True, expr_inc, s)
                if math.isnan(chosen_val):
                    chosen_val, chosen_expr, chosen_samples = v, expr_inc, s
            except Exception:
                pass

    # 2) Sem p50>0 mas com volume em alguma janela: retorna o melhor fallback
    if any_enough and not math.isnan(chosen_val):
        return (chosen_val, True, chosen_expr, chosen_samples)

    # 3) Sem volume suficiente: calcula algo informativo (had_samples=False)
    last_val, last_expr = float("nan"), ""
    for w in windows:
        expr_rate = f"histogram_quantile(0.50, sum(rate(sirios_planner_top2_gap_histogram_bucket[{w}])) by (le))"
        try:
            last_val = _to_float(prom_query_instant(expr_rate))
            last_expr = expr_rate
        except Exception:
            pass
        expr_inc = f"histogram_quantile(0.50, sum(increase(sirios_planner_top2_gap_histogram_bucket[{w}])) by (le))"
        try:
            last_val = _to_float(prom_query_instant(expr_inc))
            last_expr = expr_inc
        except Exception:
            pass
    return (last_val, False, last_expr, 0.0)


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
        try:
            normalized_payloads, suite_name, description, batch_meta = validate_routing_payload_contract(
                payload
            )
        except RoutingPayloadValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)

        batch_dict = _routing_batch_to_dict(batch_meta) if batch_meta else None
        if batch_meta and _is_duplicate_routing_batch(batch_meta):
            return {
                "accepted": 0,
                "suite": suite_name,
                "description": description,
                "batch": batch_dict,
                "duplicate": True,
                "metrics": {"matched": 0, "missed": 0},
            }

        samples_raw = normalized_payloads
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

        response: Dict[str, Any] = {
            "accepted": len(samples_raw),
            "suite": suite_name,
            "description": description,
            "metrics": {"matched": matched, "missed": missed},
        }
        if batch_dict:
            response["batch"] = batch_dict
        return response

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
            try:
                out = orchestrator.route_question(q)
            except Exception:
                LOGGER.error(
                    "quality projection failed to route question", exc_info=True
                )
                fail += 1
                counter(
                    "sirios_planner_projection_total",
                    outcome="fail",
                    entity=str(entity),
                )
                continue
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

    policy: Optional[Dict[str, Any]] = None
    errors: List[str] = []
    used_path: Optional[str] = None

    global _QUALITY_LOADER_ERRORS
    _QUALITY_LOADER_ERRORS = errors

    def _extract_targets(policy_dict: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not policy_dict:
            return {}
        return policy_dict.get("targets") or (policy_dict.get("quality_gates") or {}).get(
            "thresholds", {}
        )

    policy = _load_candidate(policy_path)
    if policy is not None:
        used_path = policy_path
    else:
        policy = _load_candidate(fallback_path)
        if policy is not None:
            used_path = fallback_path

    targets = _extract_targets(policy)
    if not targets and used_path != fallback_path:
        fallback_policy = _load_candidate(fallback_path)
        fallback_targets = _extract_targets(fallback_policy)
        if fallback_targets:
            policy = fallback_policy
            targets = fallback_targets
            used_path = fallback_path

    if policy is None:
        _QUALITY_LOADER_ERRORS = None
        return JSONResponse(
            {"error": f"failed to load quality policy: {'; '.join(errors)}"},
            status_code=500,
        )

    logging.info("quality_report: policy loaded from %s", used_path or "<unknown>")

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

    # Gap P50 — escolha de janela com amostras mínimas e fallback controlado
    windows_csv = os.getenv("QUALITY_GAP_WINDOWS", "10m,1h,6h,24h")
    windows = [w.strip() for w in windows_csv.split(",") if w.strip()]
    min_samples = _to_float(os.getenv("QUALITY_GAP_MIN_SAMPLES", "10"))
    gap_p50_raw, gap_has_data, gap_expr, gap_samples = _prom_gap_p50_choose_window(
        windows, min_samples
    )

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
    if gap_has_data and gap_samples >= min_samples:
        if gap_p50_raw < min_top2_gap:
            violations.append(
                f"top2_gap_p50 {gap_p50_raw:.3f} < min {min_top2_gap:.3f}"
            )
    if miss_abs_v > max_miss_abs:
        violations.append(f"misses_abs {miss_abs_v:.0f} > max {max_miss_abs:.0f}")
    if miss_ratio > max_miss_ratio:
        violations.append(f"misses_ratio {miss_ratio:.3f} > max {max_miss_ratio:.3f}")

    status = "pass" if not violations else "fail"

    metrics = {
        "top1_accuracy": _sanitize(top1_acc),
        "routed_rate": _sanitize(routed_rt),
        "top2_gap_p50": _sanitize(gap_p50_raw),
        "projection_pass": _sanitize(proj_pass),
        "misses_abs": _sanitize(miss_abs_v),
        "misses_ratio": _sanitize(miss_ratio),
    }

    _QUALITY_LOADER_ERRORS = None

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
        "meta": {
            "no_data": {"top2_gap_p50": (not gap_has_data)},
            "debug": {
                "gap_expr": gap_expr,
                "gap_samples": gap_samples,
                "gap_min_samples": min_samples,
                "gap_windows": windows,
            },
        },
    }
