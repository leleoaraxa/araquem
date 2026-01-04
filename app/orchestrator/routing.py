# app/orchestrator/routing.py

import logging
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import uuid4

from app.cache.rt_cache import (
    build_plan_hash,
    is_cacheable_payload,
    make_cache_key,
    make_plan_cache_key,
)
from app.planner import planner as planner_module
from app.planner.planner import Planner
from app.planner.ticker_index import extract_tickers_from_text
from app.builder.sql_builder import build_select_for_entity
from app.executor.pg import PgExecutor
from app.formatter.rows import format_rows
from app.observability.metrics import (
    emit_counter as counter,
    emit_histogram as histogram,
)
from app.observability.instrumentation import (
    get_trace_id,
    set_trace_attribute,
    trace as start_trace,
)
from app.analytics.explain import explain as _explain_analytics
from app.planner.param_inference import infer_params  # novo: inferência compute-on-read
from app.utils.filecache import load_yaml_cached
from app.rag.context_builder import build_context as build_rag_context

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.cache.rt_cache import CachePolicies, RedisCache

_PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
_ENTITY_ROOT = Path("data/entities")


def _entity_yaml_path(entity: str) -> Path:
    base_dir = _ENTITY_ROOT / str(entity)
    new_path = base_dir / f"{entity}.yaml"
    legacy_path = base_dir / "entity.yaml"
    if new_path.exists():
        return new_path
    if legacy_path.exists():
        return legacy_path
    return new_path


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def _normalize_for_metrics(text: str) -> str:
    lowered = (text or "").lower()
    no_accents = _strip_accents(lowered)
    no_punct = _PUNCT_RE.sub(" ", no_accents)
    return re.sub(r"\s+", " ", no_punct).strip()


def _load_entity_config(entity: Optional[str]) -> Dict[str, Any]:
    if not entity:
        return {}
    path = _entity_yaml_path(str(entity))
    if not path.exists():
        LOGGER.warning(
            "entity.yaml ausente para %s em %s; usando config vazia", entity, path
        )
        return {}

    try:
        data = load_yaml_cached(str(path))
    except Exception:
        LOGGER.error(
            "Falha ao carregar entity.yaml para %s em %s; usando config vazia",
            entity,
            path,
            exc_info=True,
        )
        return {}

    if not isinstance(data, dict):
        LOGGER.error(
            "entity.yaml inválido para %s em %s (esperado mapeamento); usando config vazia",
            entity,
            path,
        )
        return {}

    return data


def extract_requested_metrics(question: str, entity_conf: Dict[str, Any]) -> List[str]:
    """Retorna métricas solicitadas com base em ask.metrics_synonyms."""

    ask_conf = entity_conf.get("ask") if isinstance(entity_conf, dict) else None
    metrics_synonyms = (
        ask_conf.get("metrics_synonyms") if isinstance(ask_conf, dict) else None
    )
    if not isinstance(metrics_synonyms, dict):
        return []

    normalized_question = _normalize_for_metrics(question)
    if not normalized_question:
        return []

    requested: List[str] = []
    seen = set()
    for metric_name, synonyms in metrics_synonyms.items():
        if not isinstance(metric_name, str) or not metric_name:
            continue
        candidates: List[str]
        if isinstance(synonyms, (list, tuple, set)):
            candidates = [str(s) for s in synonyms if isinstance(s, str)]
        elif isinstance(synonyms, str):
            candidates = [synonyms]
        else:
            continue
        for synonym in candidates:
            synonym_norm = _normalize_for_metrics(synonym)
            if not synonym_norm:
                continue
            if synonym_norm in normalized_question and metric_name not in seen:
                requested.append(metric_name)
                seen.add(metric_name)
                break
    return requested


def _extract_ticker_identifiers(question: str) -> List[str]:
    """Extrai todos os tickers normalizados a partir da pergunta."""
    return extract_tickers_from_text(question)


_TH_PATH = os.getenv("PLANNER_THRESHOLDS_PATH", "data/ops/planner_thresholds.yaml")

def _env_int(var_name: str, default: int) -> int:
    try:
        return int(os.getenv(var_name, default))
    except (TypeError, ValueError):
        return default


def _load_thresholds(path: str) -> Dict[str, Any]:
    policy_path = Path(path)
    if not policy_path.exists():
        LOGGER.warning(
            "Arquivo de thresholds do Orchestrator ausente em %s; usando fallback vazio",
            policy_path,
        )
        return {}

    try:
        planner_cfg = planner_module._load_thresholds(path=path)
    except ValueError:
        LOGGER.error(
            "YAML de thresholds do Orchestrator inválido em %s; usando fallback vazio",
            policy_path,
            exc_info=True,
        )
        return {}
    except Exception:
        LOGGER.error(
            "Erro inesperado ao carregar thresholds do Orchestrator em %s; usando fallback vazio",
            policy_path,
            exc_info=True,
        )
        return {}

    planner_block = planner_cfg.get("planner") if isinstance(planner_cfg, dict) else {}
    thresholds = (
        planner_block.get("thresholds") if isinstance(planner_block, dict) else {}
    )
    if not isinstance(thresholds, dict):
        LOGGER.error(
            "Configuração de thresholds do Orchestrator não é um mapeamento em %s; usando fallback vazio",
            policy_path,
        )
        return {}
    return thresholds


class Orchestrator:
    def __init__(
        self,
        planner: Planner,
        executor: PgExecutor,
        planner_metrics: Optional[Dict[str, Any]] = None,
        cache: Optional["RedisCache"] = None,
        cache_policies: Optional["CachePolicies"] = None,
    ):
        # `planner_metrics` mantido p/ compatibilidade de assinatura; métricas via façade.
        self._planner = planner
        self._exec = executor
        self._cache: Optional["RedisCache"] = None
        self._cache_policies: Optional["CachePolicies"] = None
        self.set_cache_backend(cache, cache_policies)

    def set_cache_backend(
        self,
        cache: Optional["RedisCache"],
        policies: Optional["CachePolicies"],
    ) -> None:
        self._cache = cache
        self._cache_policies = policies

    def extract_identifiers(self, question: str) -> Dict[str, Any]:
        tickers = _extract_ticker_identifiers(question)
        # Contrato canônico:
        # - ticker: apenas quando há exatamente 1 ticker na pergunta
        # - tickers: lista quando há 1+ tickers
        identifiers: Dict[str, Any] = {"ticker": None}
        if tickers:
            identifiers["tickers"] = tickers
            if len(tickers) == 1:
                identifiers["ticker"] = tickers[0]
        return identifiers

    def _normalize_metrics_window(
        self, agg_params: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        if not agg_params:
            return None
        window = agg_params.get("window")
        if isinstance(window, str) and window:
            return window
        window_months = agg_params.get("window_months")
        try:
            window_months_int = int(window_months)
        except (TypeError, ValueError):
            window_months_int = None
        if window_months_int and window_months_int > 0:
            return f"months:{window_months_int}"
        period_start = agg_params.get("period_start")
        period_end = agg_params.get("period_end")
        if period_start and period_end:
            return f"range:{period_start}:{period_end}"
        return None

    def _split_window(self, window_norm: Optional[str]) -> Dict[str, Any]:
        if not window_norm:
            return {"window_type": None, "window_value": None}
        raw = str(window_norm)
        if ":" not in raw:
            return {"window_type": raw, "window_value": None}
        kind, remainder = raw.split(":", 1)
        try:
            value_int = int(remainder)
        except (TypeError, ValueError):
            value_int = None
        window_value = value_int if value_int is not None else remainder
        return {"window_type": kind, "window_value": window_value}

    def _metrics_cache_denied(
        self, policy: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        for rule in policy.get("deny_if") or []:
            if not isinstance(rule, dict):
                continue
            field = str(rule.get("field") or "").strip()
            if not field:
                continue
            actual = context.get(field)
            expected = rule.get("equals")
            if expected is not None and actual != expected:
                continue
            if expected is None and rule.get("value") is None and actual is None:
                continue
            if "value" in rule:
                target_field = rule.get("value_field") or (
                    "window_value" if field == "window_type" else field
                )
                if context.get(target_field) != rule.get("value"):
                    continue
            return True
        return False

    def _prepare_metrics_cache_context(
        self,
        entity: Optional[str],
        identifiers: Dict[str, Any],
        agg_params: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if self._cache is None or self._cache_policies is None:
            return None
        policy = self._cache_policies.get(entity) if self._cache_policies else None
        if not policy:
            return None
        identifiers = identifiers or {}
        agg_params = agg_params or {}
        ticker_raw = identifiers.get("ticker")
        ticker = str(ticker_raw).upper() if ticker_raw else ""
        if not ticker:
            return None
        metric_key = agg_params.get("metric")
        if not metric_key:
            return None
        window_norm = self._normalize_metrics_window(agg_params)
        if not window_norm:
            return None
        window_info = self._split_window(window_norm)
        context = {
            "ticker": ticker,
            "metric_key": metric_key,
            "window_norm": window_norm,
            **window_info,
        }
        if self._metrics_cache_denied(policy, context):
            return None
        ttl = int(policy.get("ttl_seconds") or 0)
        if ttl <= 0:
            return None
        scope = str(policy.get("scope") or "pub")
        cache_identifiers = {
            **identifiers,
            "metric_key": metric_key,
            "window_norm": window_norm,
            **window_info,
        }
        key = make_cache_key(
            os.getenv("BUILD_ID", "dev"),
            scope,
            entity,
            cache_identifiers,
        )
        return {"key": key, "ttl": ttl, "entity": entity, "context": context}

    def prepare_plan(
        self,
        question: str,
        *,
        client_id: Optional[str],
        conversation_id: Optional[str],
        planner_plan: Optional[Dict[str, Any]] = None,
        resolved_identifiers: Optional[Dict[str, Any]] = None,
        agg_params_override: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        plan_resolved = (
            planner_plan if isinstance(planner_plan, dict) else self._planner.explain(question)
        )
        chosen = plan_resolved.get("chosen") or {}
        intent = chosen.get("intent")
        entity = chosen.get("entity")
        score = chosen.get("score")
        exp = plan_resolved.get("explain") or {}

        exp_safe = exp if isinstance(exp, dict) else {}
        bucket_info = exp_safe.get("bucket") if isinstance(exp_safe, dict) else {}
        if not isinstance(bucket_info, dict):
            bucket_info = {}
        bucket_selected = str(bucket_info.get("selected") or "")

        entity_conf = _load_entity_config(str(entity) if entity else None)
        requested_metrics = extract_requested_metrics(question, entity_conf)

        identifiers = (
            dict(resolved_identifiers)
            if isinstance(resolved_identifiers, dict)
            else self.extract_identifiers(question)
        )
        provided_tickers = identifiers.get("tickers")
        tickers_list = (
            provided_tickers
            if isinstance(provided_tickers, list) and provided_tickers
            else extract_tickers_from_text(question)
        )
        if tickers_list:
            identifiers = {**identifiers, "tickers": tickers_list}
            if len(tickers_list) == 1:
                identifiers["ticker"] = identifiers.get("ticker") or tickers_list[0]
            else:
                identifiers["ticker"] = None

        opts = entity_conf.get("options") if isinstance(entity_conf, dict) else None
        supports_multi = bool(opts.get("supports_multi_ticker")) if isinstance(opts, dict) else False
        raw_multi_mode = (
            str(opts.get("multi_ticker_mode")).strip().lower()
            if isinstance(opts, dict) and "multi_ticker_mode" in opts
            else None
        )
        multi_ticker_mode = None
        if supports_multi:
            multi_ticker_mode = raw_multi_mode or "loop"
        else:
            multi_ticker_mode = "none"

        multi_ticker_enabled = supports_multi and len(tickers_list) > 1
        if tickers_list and len(tickers_list) > 1 and not multi_ticker_enabled:
            identifiers["ticker"] = tickers_list[0]

        agg_params = None
        if entity:
            if agg_params_override is not None:
                agg_params = dict(agg_params_override)
            else:
                try:
                    agg_params = infer_params(
                        question=question,
                        intent=intent,
                        entity=entity,
                        entity_yaml_path=str(_entity_yaml_path(str(entity))),
                        defaults_yaml_path="data/ops/param_inference.yaml",
                        identifiers=identifiers,
                        client_id=client_id,
                        conversation_id=conversation_id,
                    )
                except Exception:
                    LOGGER.warning(
                        "Inferência de parâmetros falhou; usando SELECT básico",
                        exc_info=True,
                        extra={"entity": entity, "intent": intent},
                    )
                    agg_params = None

        skip_sql = self._should_skip_sql_for_question(
            entity=entity,
            entity_conf=entity_conf,
            identifiers=identifiers,
            agg_params=agg_params,
        )

        compute_mode = "conceptual" if skip_sql else "sql"
        flags = {
            "multi_ticker_enabled": multi_ticker_enabled,
            "multi_ticker_mode": multi_ticker_mode,
            "compute_mode": compute_mode,
        }

        scope = ""
        policy = self._cache_policies.get(entity) if self._cache_policies else None
        if policy and isinstance(policy, dict):
            scope = str(policy.get("scope", ""))

        plan_hash, plan_fingerprint = build_plan_hash(
            entity=str(entity or ""),
            intent=str(intent or ""),
            bucket=bucket_selected,
            scope=scope,
            identifiers=identifiers,
            agg_params=agg_params,
            flags=flags,
            requested_metrics=requested_metrics,
        )

        return {
            "planner_plan": plan_resolved,
            "entity": entity,
            "intent": intent,
            "score": score,
            "bucket_selected": bucket_selected,
            "scope": scope,
            "identifiers": identifiers,
            "agg_params": agg_params,
            "skip_sql": skip_sql,
            "requested_metrics": requested_metrics,
            "multi_ticker_enabled": multi_ticker_enabled,
            "multi_ticker_mode": multi_ticker_mode,
            "compute_mode": compute_mode,
            "plan_hash": plan_hash,
            "plan_fingerprint": plan_fingerprint,
        }

    def _should_skip_sql_for_question(
        self,
        entity: Optional[str],
        entity_conf: Dict[str, Any],
        identifiers: Dict[str, Any],
        agg_params: Optional[Dict[str, Any]],
    ) -> bool:
        ask_conf = entity_conf.get("ask") if isinstance(entity_conf, dict) else None
        if not isinstance(ask_conf, dict):
            return False

        required_ids = ask_conf.get("requires_identifiers")
        if not isinstance(required_ids, (list, tuple, set)):
            return False

        # suporta multi? (YAML-driven)
        opts = entity_conf.get("options") if isinstance(entity_conf, dict) else None
        supports_multi = (
            bool(opts.get("supports_multi_ticker")) if isinstance(opts, dict) else False
        )
        has_tickers = (
            isinstance(identifiers.get("tickers"), list)
            and len(identifiers["tickers"]) > 0
        )
        is_multi_question = has_tickers and len(identifiers["tickers"]) > 1

        for raw_key in required_ids:
            key = str(raw_key or "").strip()
            if not key:
                continue

            # Se a entidade suporta multi e a pergunta tem 2+ tickers,
            # aceitar "ticker" como satisfeito via "tickers" (sem violar contrato).
            if key == "ticker" and supports_multi and is_multi_question:
                continue

            value = identifiers.get(key)
            missing = (
                value is None
                or (isinstance(value, (list, tuple, set)) and not value)
                or (isinstance(value, str) and not value.strip())
            )

            if missing:
                if isinstance(agg_params, dict):
                    alt = agg_params.get(key)
                    alt_missing = (
                        alt is None
                        or (isinstance(alt, (list, tuple, set)) and not alt)
                        or (isinstance(alt, str) and not alt.strip())
                    )
                    if not alt_missing:
                        continue
                return True

        return False

    def route_question(
        self,
        question: str,
        explain: bool = False,
        *,
        client_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        plan: Optional[Dict[str, Any]] = None,
        resolved_identifiers: Optional[Dict[str, Any]] = None,
        agg_params_override: Optional[Dict[str, Any]] = None,
        prepared_plan: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        t0 = time.perf_counter()
        prepared = (
            prepared_plan
            if isinstance(prepared_plan, dict)
            else self.prepare_plan(
                question,
                client_id=client_id,
                conversation_id=conversation_id,
                planner_plan=plan,
                resolved_identifiers=resolved_identifiers,
                agg_params_override=agg_params_override,
            )
        )

        plan_resolved = prepared.get("planner_plan") or (
            plan if isinstance(plan, dict) else self._planner.explain(question)
        )
        chosen = plan_resolved.get("chosen") or {}
        intent = chosen.get("intent")
        entity = chosen.get("entity")
        score = chosen.get("score")
        exp = plan_resolved.get("explain") or {}

        # top2 gap do planner (M7.4: usa gap consolidado do planner)
        scoring_block = exp.get("scoring") or {}
        thr_info = scoring_block.get("thresholds_applied") or {}
        top2_gap = float(
            thr_info.get(
                "gap",
                scoring_block.get(
                    "intent_top2_gap_final",
                    scoring_block.get("intent_top2_gap_base", 0.0),
                ),
            )
            or 0.0
        )

        entity_conf = _load_entity_config(str(entity) if entity else None)
        requested_metrics = prepared.get("requested_metrics") or extract_requested_metrics(
            question, entity_conf
        )
        focus_metric = None
        if isinstance(requested_metrics, (list, tuple)) and len(requested_metrics) == 1:
            candidate = requested_metrics[0]
            if isinstance(candidate, str):
                focus_metric = candidate.strip() or None

        # --------- M6.6: aplicar GATES por YAML (fonte única = Planner) ----------
        th = _load_thresholds(_TH_PATH)
        dfl = th.get("defaults", {}) if isinstance(th, dict) else {}
        i_th = (
            (th.get("intents", {}) or {}).get(intent or "", {})
            if isinstance(th, dict)
            else {}
        )
        e_th = (
            (th.get("entities", {}) or {}).get(entity or "", {})
            if isinstance(th, dict)
            else {}
        )

        # prioridade: entity > intent > defaults (usado apenas como fallback)
        min_score = float(
            e_th.get("min_score", i_th.get("min_score", dfl.get("min_score", 0.0)))
        )
        min_gap = float(
            e_th.get("min_gap", i_th.get("min_gap", dfl.get("min_gap", 0.0)))
        )
        gate_source = None
        gate_score_for_planner = score
        planner_gate_reason = None
        if thr_info:
            try:
                min_score = float(thr_info.get("min_score", min_score))
                min_gap = float(thr_info.get("min_gap", min_gap))
                gate_source = thr_info.get("source", gate_source)
                top2_gap = float(thr_info.get("gap", top2_gap))
                gate_score_for_planner = float(
                    thr_info.get("score_for_gate", gate_score_for_planner or 0.0)
                )
                planner_gate_reason = thr_info.get("reason")
            except Exception:
                pass
        gate = {
            "blocked": False,
            "reason": None,
            "min_score": min_score,
            "min_gap": min_gap,
            "top2_gap": top2_gap,
            "source": gate_source,
            "score_for_gate": gate_score_for_planner,
        }
        if entity:
            if thr_info:
                gate["blocked"] = not bool(thr_info.get("accepted", True))
                if gate["blocked"]:
                    gate["reason"] = (
                        planner_gate_reason
                        or ("low_score" if gate_score_for_planner < min_score else None)
                        or ("low_gap" if top2_gap < min_gap else None)
                    )
            else:
                if score < min_score:
                    gate.update({"blocked": True, "reason": "low_score"})
                elif top2_gap < min_gap:
                    gate.update({"blocked": True, "reason": "low_gap"})

        if gate["blocked"]:
            counter(
                "sirios_planner_blocked_by_threshold_total",
                reason=str(gate["reason"]),
                intent=str(intent),
                entity=str(entity),
            )

        if not entity:
            meta_payload = {
                "planner": plan_resolved,
                "result_key": None,
                "planner_intent": intent,
                "planner_entity": entity,
                "planner_score": score,
                "rows_total": 0,
                "elapsed_ms": int((time.perf_counter() - t0) * 1000),
                "requested_metrics": requested_metrics,
                "gate": gate,
                "planner_gate_source": gate.get("source"),
            }
            if focus_metric:
                meta_payload["focus"] = {"metric_key": focus_metric}
            return {
                "status": {"reason": "unroutable", "message": "No entity matched"},
                "results": {},
                "meta": meta_payload,
            }

        if gate["blocked"]:
            meta_payload = {
                "planner": plan_resolved,
                "result_key": None,
                "planner_intent": intent,
                "planner_entity": entity,
                "planner_score": score,
                "rows_total": 0,
                "elapsed_ms": int((time.perf_counter() - t0) * 1000),
                "requested_metrics": requested_metrics,
                "gate": gate,
                "planner_gate_source": gate.get("source"),
                "explain": exp if explain else None,
            }
            if focus_metric:
                meta_payload["focus"] = {"metric_key": focus_metric}
            return {
                "status": {
                    "reason": "gated",
                    "message": f"Blocked by threshold: {gate['reason']}",
                },
                "results": {},
                "meta": meta_payload,
            }

        identifiers = prepared.get("identifiers") or {}
        tickers_list = (
            identifiers.get("tickers")
            if isinstance(identifiers.get("tickers"), list)
            else []
        )
        bucket_selected = prepared.get("bucket_selected") or ""

        multi_ticker_enabled = bool(prepared.get("multi_ticker_enabled"))
        multi_ticker_mode = prepared.get("multi_ticker_mode") or (
            "loop"
            if bool(
                (entity_conf.get("options") or {}).get("supports_multi_ticker")
                if isinstance(entity_conf, dict)
                else False
            )
            else "none"
        )
        multi_ticker_batch_supported = multi_ticker_enabled and multi_ticker_mode == "batch"

        # --- M7.2: inferência de parâmetros (compute-on-read) ---------------
        # Lê regras de data/ops/param_inference.yaml + entity.yaml (aggregations.*)
        agg_params = prepared.get("agg_params")

        # Decisão compute-on-read vs conceitual puro (dirigido por YAML)
        skip_sql = bool(prepared.get("skip_sql"))
        compute_mode = prepared.get("compute_mode") or ("conceptual" if skip_sql else "sql")

        plan_cache_key: Optional[str] = None
        plan_cache_hit = False
        plan_cache_written = False
        plan_cache_ttl: Optional[int] = None
        plan_cache_enabled = False
        plan_lock_key: Optional[str] = None
        plan_lock_acquired: bool = False
        plan_hash = prepared.get("plan_hash")
        scope = prepared.get("scope") or ""
        plan_cache_policy = self._cache_policies.get(entity) if self._cache_policies else None
        is_private_entity = (
            self._cache_policies.is_private_entity(entity) if self._cache_policies else False
        )
        namespace = None
        if is_private_entity:
            if client_id:
                namespace = f"client:{client_id}"
            else:
                namespace = None

        if (
            self._cache is not None
            and plan_cache_policy
            and not skip_sql
            and plan_hash
            and plan_cache_policy.get("ttl_seconds")
        ):
            try:
                plan_cache_ttl = int(plan_cache_policy.get("ttl_seconds", 0) or 0)
            except (TypeError, ValueError):
                plan_cache_ttl = 0

            if plan_cache_ttl and plan_cache_ttl > 0:
                if not is_private_entity or namespace:
                    plan_cache_enabled = True
                    build_id = os.getenv("BUILD_ID", "dev")
                    plan_cache_key = make_plan_cache_key(
                        build_id,
                        scope,
                        entity,
                        plan_hash,
                        namespace=namespace,
                    )
                    try:
                        cached_plan_payload = self._cache.get_json(plan_cache_key)
                    except Exception:
                        LOGGER.warning("Falha ao consultar cache de plano", exc_info=True)
                        cached_plan_payload = None

                    if isinstance(cached_plan_payload, dict):
                        plan_cache_hit = True
                        meta_payload = cached_plan_payload.get("meta") or {}
                        compute_meta = meta_payload.get("compute") or {}
                        compute_meta.update(
                            {
                                "plan_cache_hit": True,
                                "plan_cache_written": False,
                                "cache_key": plan_cache_key,
                            }
                        )
                        meta_payload["compute"] = compute_meta
                        cached_plan_payload["meta"] = meta_payload
                        return cached_plan_payload

                    lock_key = f"{plan_cache_key}:lock"
                    lock_ttl_ms = _env_int("CACHE_SINGLEFLIGHT_LOCK_TTL_MS", 15000)
                    lock_acquired = self._cache.acquire_lock(lock_key, lock_ttl_ms)
                    if lock_acquired:
                        plan_lock_key = lock_key
                        plan_lock_acquired = True
                    if not lock_acquired:
                        waited_payload = self._cache.wait_for_key(
                            plan_cache_key,
                            _env_int("CACHE_SINGLEFLIGHT_MAX_WAIT_MS", 2000),
                            _env_int("CACHE_SINGLEFLIGHT_STEP_MS", 100),
                        )
                        if isinstance(waited_payload, dict):
                            meta_payload = waited_payload.get("meta") or {}
                            compute_meta = meta_payload.get("compute") or {}
                            compute_meta.update(
                                {
                                    "plan_cache_hit": True,
                                    "plan_cache_written": False,
                                    "cache_key": plan_cache_key,
                                }
                            )
                            meta_payload["compute"] = compute_meta
                            waited_payload["meta"] = meta_payload
                            return waited_payload

        cache_ctx = None
        if not multi_ticker_enabled:
            cache_ctx = self._prepare_metrics_cache_context(
                entity, identifiers, agg_params
            )
        metrics_cache_hit = False
        metrics_cache_key: Optional[str] = None
        metrics_cache_ttl: Optional[int] = None
        cached_rows_formatted = None
        cached_result_key = None
        cache_lookup_error = False
        if cache_ctx and not skip_sql:
            metrics_cache_key = cache_ctx.get("key")
            metrics_cache_ttl = cache_ctx.get("ttl")
            try:
                cached_payload = self._cache.get_json(metrics_cache_key)
            except Exception:
                LOGGER.warning("Falha ao consultar cache de métricas", exc_info=True)
                cache_lookup_error = True
                cached_payload = None
            if not cache_lookup_error and isinstance(cached_payload, dict):
                cached_result_key = cached_payload.get("result_key")
                cached_rows_formatted = cached_payload.get("rows")
                if cached_result_key is not None and isinstance(
                    cached_rows_formatted, list
                ):
                    metrics_cache_hit = True
                else:
                    cached_rows_formatted = None
                    cached_result_key = None

        # estágio de planning finalizado
        histogram(
            "sirios_planner_duration_seconds", time.perf_counter() - t0, stage="plan"
        )
        counter(
            "sirios_planner_route_decisions_total",
            intent=str(intent),
            entity=str(entity),
            outcome="ok",
        )

        # --- M6.4: métricas de explain (somente quando explicitamente solicitado) ---
        if explain:
            counter("sirios_planner_explain_enabled_total")
            for n in exp.get("decision_path") or []:
                kind = n.get("type") or "unknown"
                counter("sirios_planner_explain_nodes_total", node_kind=kind)

            # Removido: tentativa de enviar somas como "counter" com _value.
            # O schema canônico exige labels exatos; sem _value. Se precisarmos
            # dessas somas no futuro, criaremos um histogram/gauge específico.
            if intent is not None:
                histogram(
                    "sirios_planner_intent_score", float(score), intent=str(intent)
                )
            if entity is not None:
                histogram(
                    "sirios_planner_entity_score", float(score), entity=str(entity)
                )

        rows_raw = []
        rows_formatted = cached_rows_formatted if metrics_cache_hit else None
        result_key = cached_result_key if metrics_cache_hit else None
        return_columns = None

        # span do planner (atributos semânticos)
        with start_trace(
            "planner.route",
            component="planner",
            operation="route_question",
        ) as span:
            set_trace_attribute(span, "planner.intent", intent)
            set_trace_attribute(span, "planner.entity", entity)
            set_trace_attribute(
                span,
                "planner.score",
                float(score) if isinstance(score, (int, float)) else 0.0,
            )
            if metrics_cache_hit:
                # Leitura direta de cache de métricas
                set_trace_attribute(span, "cache.hit", True)
                set_trace_attribute(span, "sql.skipped", False)
            elif skip_sql:
                # Modo conceitual: não executa SQL nem usa cache de métricas
                set_trace_attribute(span, "cache.hit", False)
                set_trace_attribute(span, "sql.skipped", True)
            else:

                # Caminho determinístico normal: gera SELECT + executa no Postgres
                if multi_ticker_enabled and not multi_ticker_batch_supported:
                    rows_raw = []
                    result_key = None
                    return_columns = None
                    for ticker in tickers_list:
                        ticker_identifiers = {**identifiers, "ticker": ticker}
                        sql, params, rk, columns = build_select_for_entity(
                            entity=entity,
                            identifiers=ticker_identifiers,
                            agg_params=agg_params,
                        )
                        if isinstance(params, dict):
                            params = {**params, "entity": entity}

                        rows_raw.extend(self._exec.query(sql, params))
                        result_key = result_key or rk
                        return_columns = return_columns or columns
                    set_trace_attribute(span, "cache.hit", False)
                    set_trace_attribute(span, "sql.skipped", False)
                else:
                    sql, params, result_key, return_columns = build_select_for_entity(
                        entity=entity,
                        identifiers=identifiers,
                        agg_params=agg_params,  # <- passa inferência para o builder
                    )
                    if isinstance(params, dict):
                        params = {
                            **params,
                            "entity": entity,
                        }  # etiqueta para métricas SQL

                    rows_raw = self._exec.query(sql, params)
                    set_trace_attribute(span, "cache.hit", False)
                    set_trace_attribute(span, "sql.skipped", False)

            set_trace_attribute(span, "multi_ticker.enabled", multi_ticker_enabled)
            set_trace_attribute(
                span,
                "multi_ticker.count",
                len(tickers_list) if multi_ticker_enabled else 0,
            )

        # elapsed consolidado para reutilização (meta e explain analytics)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        if not metrics_cache_hit:
            if not skip_sql:
                # Caminho normal: formatar linhas e potencialmente popular cache
                rows_formatted = format_rows(rows_raw, return_columns)
                if (
                    cache_ctx
                    and self._cache is not None
                    and metrics_cache_key
                    and isinstance(metrics_cache_ttl, int)
                    and metrics_cache_ttl > 0
                    and rows_formatted
                    and result_key
                ):
                    try:
                        self._cache.set_json(
                            metrics_cache_key,
                            {"result_key": result_key, "rows": rows_formatted},
                            ttl_seconds=metrics_cache_ttl,
                        )
                    except Exception:
                        LOGGER.warning(
                            "Falha ao gravar payload no cache de métricas",
                            exc_info=True,
                        )
            else:
                # Modo conceitual: sem linhas formatadas (deixamos Narrator/RAG trabalhar)
                rows_formatted = []

        else:
            rows_formatted = list(rows_formatted or [])

        # Explain Analytics (somente quando solicitado)
        explain_analytics_payload = None
        if explain:
            # Usa o trace_id do span corrente como request_id (correlação OTEL)
            trace_id = get_trace_id(span)
            request_id = trace_id or uuid4().hex
            # Defina explicitamente route_id = result_key (com fallback para entity)
            route_id = result_key or entity or ""
            planner_output = {
                "route": {
                    "intent": intent,
                    "entity": entity,
                    "view": result_key,
                    "route_id": route_id,
                },
                "chosen": chosen,
            }
            metrics_snapshot = {
                "latency_ms": elapsed_ms,
                "route_source": "cache" if metrics_cache_hit else "planner",
                "cache_hit": metrics_cache_hit,
            }
            explain_analytics_payload = _explain_analytics(
                request_id=request_id,
                planner_output=planner_output,
                metrics=metrics_snapshot,
            )

        if not result_key:
            result_key = (
                entity_conf.get("result_key") if isinstance(entity_conf, dict) else None
            ) or entity

        final_rows = rows_formatted or []
        results = {result_key: final_rows}

        meta: Dict[str, Any] = {
            "planner": plan_resolved,
            "explain": exp if explain else None,
            "explain_analytics": explain_analytics_payload if explain else None,
            "result_key": result_key,
            # CANÔNICOS (para debug / narrator / rag_debug)
            "intent": intent,
            "entity": entity,
            # HISTÓRICO / CAMPO LEGADO
            "planner_intent": intent,
            "planner_entity": entity,
            "planner_score": score,
            "planner_gate_source": gate.get("source"),
            "rows_total": len(final_rows),
            "elapsed_ms": elapsed_ms,
            "gate": gate,
            "aggregates": (agg_params or {}),
            "requested_metrics": requested_metrics,
            "compute": {
                "mode": compute_mode,
                "metrics_cache_hit": bool(metrics_cache_hit),
                "cache_key": metrics_cache_key,
                "cache_ttl": metrics_cache_ttl,
            },
        }

        if "focus" not in meta:
            if focus_metric:
                meta["focus"] = {"metric_key": focus_metric}

        # ------------------- M12: contexto de RAG -------------------
        # O contexto canônico de RAG é sempre produzido aqui no
        # orchestrator. O build_rag_context aplica as políticas
        # (rag.yaml) e só aciona embeddings quando habilitado.
        try:
            meta["rag"] = build_rag_context(
                question=question,
                intent=str(intent or ""),
                entity=str(entity or ""),
            )
        except Exception as exc:
            LOGGER.warning("Erro ao montar contexto de RAG", exc_info=True)
            meta["rag"] = {
                "enabled": False,
                "question": question,
                "intent": intent,
                "entity": entity,
                "used_collections": [],
                "chunks": [],
                "total_chunks": 0,
                "policy": None,
                "error": str(exc),
            }

        payload = {
            "status": {"reason": "ok", "message": "ok"},
            "results": results,
            "meta": meta,
        }

        if (
            self._cache is not None
            and plan_cache_enabled
            and plan_cache_key
            and isinstance(plan_cache_ttl, int)
            and plan_cache_ttl > 0
            and not plan_cache_hit
            and is_cacheable_payload(payload)
        ):
            try:
                self._cache.set_json(plan_cache_key, payload, ttl_seconds=plan_cache_ttl)
                plan_cache_written = True
            except Exception:
                LOGGER.warning("Falha ao gravar payload no plan-cache", exc_info=True)

        if plan_lock_acquired and plan_lock_key:
            self._cache.release_lock(plan_lock_key, self._cache.lock_token)

        compute_meta = meta.get("compute") or {}
        if plan_cache_key:
            compute_meta.setdefault("plan_cache_key", plan_cache_key)
        compute_meta["plan_cache_hit"] = bool(plan_cache_hit)
        compute_meta["plan_cache_written"] = bool(plan_cache_written)
        if metrics_cache_key:
            compute_meta.setdefault("metrics_cache_key", metrics_cache_key)
        meta["compute"] = compute_meta
        payload["meta"] = meta

        return payload
