# app/orchestrator/routing.py

import os
import re
import time
import unicodedata
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import uuid4

from app.cache.rt_cache import make_cache_key
from app.planner.planner import Planner
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

if TYPE_CHECKING:
    from app.cache.rt_cache import CachePolicies, RedisCache

# Normalização de ticker na camada de ENTRADA (contrato Araquem)
TICKER_RE = re.compile(r"\b([A-Za-z]{4}11)\b")
_PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
_ENTITY_ROOT = Path("data/entities")


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
    path = _ENTITY_ROOT / str(entity) / "entity.yaml"
    try:
        data = load_yaml_cached(str(path)) or {}
    except Exception:
        data = {}
    return data if isinstance(data, dict) else {}


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
    normalized = (question or "").upper()
    tickers: List[str] = []
    seen = set()
    for match in TICKER_RE.finditer(normalized):
        ticker = match.group(1)
        if ticker in seen:
            continue
        seen.add(ticker)
        tickers.append(ticker)
    return tickers


_TH_PATH = os.getenv("PLANNER_THRESHOLDS_PATH", "data/ops/planner_thresholds.yaml")


def _load_thresholds(path: str) -> Dict[str, Any]:
    raw = load_yaml_cached(path) or {}
    return (raw.get("planner") or {}).get("thresholds") or {}


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
        identifiers: Dict[str, Any] = {"ticker": tickers[0] if tickers else None}
        if tickers:
            identifiers["tickers"] = tickers
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

    def _should_skip_sql_for_question(
        self,
        entity: Optional[str],
        entity_conf: Dict[str, Any],
        identifiers: Dict[str, Any],
        agg_params: Optional[Dict[str, Any]],
    ) -> bool:
        """
        Decide se devemos pular o SELECT no banco para esta combinação
        (intent/entity/pergunta), de forma 100% dirigida por YAML.

        Regra: se o bloco ask.requires_identifiers estiver definido na
        entity.yaml, e qualquer um desses identificadores estiver ausente
        em `identifiers`, não executamos SQL (modo conceitual).
        """
        ask_conf = entity_conf.get("ask") if isinstance(entity_conf, dict) else None
        if not isinstance(ask_conf, dict):
            return False

        required_ids = ask_conf.get("requires_identifiers")
        if not isinstance(required_ids, (list, tuple, set)):
            return False

        for raw_key in required_ids:
            key = str(raw_key or "").strip()
            if not key:
                continue
            value = identifiers.get(key)
            # Considera ausente se None ou coleção vazia
            if value is None or (isinstance(value, (list, tuple, set)) and not value):
                return True
        return False

    def route_question(self, question: str, explain: bool = False) -> Dict[str, Any]:
        t0 = time.perf_counter()
        plan = self._planner.explain(question)
        chosen = plan.get("chosen") or {}
        intent = chosen.get("intent")
        entity = chosen.get("entity")
        score = chosen.get("score")
        exp = plan.get("explain") or {}

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

        # --------- M6.6: aplicar GATES por YAML ----------
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

        # prioridade: entity > intent > defaults
        min_score = float(
            e_th.get("min_score", i_th.get("min_score", dfl.get("min_score", 0.0)))
        )
        min_gap = float(
            e_th.get("min_gap", i_th.get("min_gap", dfl.get("min_gap", 0.0)))
        )
        gate = {
            "blocked": False,
            "reason": None,
            "min_score": min_score,
            "min_gap": min_gap,
            "top2_gap": top2_gap,
        }
        if entity:
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
            return {
                "status": {"reason": "unroutable", "message": "No entity matched"},
                "results": {},
                "meta": {
                    "planner": plan,
                    "result_key": None,
                    "planner_intent": intent,
                    "planner_entity": entity,
                    "planner_score": score,
                    "rows_total": 0,
                    "elapsed_ms": int((time.perf_counter() - t0) * 1000),
                    "gate": gate,
                },
            }

        if gate["blocked"]:
            return {
                "status": {
                    "reason": "gated",
                    "message": f"Blocked by threshold: {gate['reason']}",
                },
                "results": {},
                "meta": {
                    "planner": plan,
                    "result_key": None,
                    "planner_intent": intent,
                    "planner_entity": entity,
                    "planner_score": score,
                    "rows_total": 0,
                    "elapsed_ms": int((time.perf_counter() - t0) * 1000),
                    "gate": gate,
                    "explain": exp if explain else None,
                },
            }

        identifiers = self.extract_identifiers(question)
        entity_conf = _load_entity_config(str(entity) if entity else None)

        # --- M7.2: inferência de parâmetros (compute-on-read) ---------------
        # Lê regras de data/ops/param_inference.yaml + entity.yaml (aggregations.*)
        try:
            agg_params = infer_params(
                question=question,
                intent=intent,
                entity=entity,
                entity_yaml_path=f"data/entities/{entity}/entity.yaml",
                defaults_yaml_path="data/ops/param_inference.yaml",
            )  # dict: {"agg": "...", "window": "...", "limit": int, "order": "..."}
        except Exception:
            agg_params = None  # fallback seguro: SELECT básico (sem agregação)

        # Decisão compute-on-read vs conceitual puro (dirigido por YAML)
        skip_sql = self._should_skip_sql_for_question(
            entity=entity,
            entity_conf=entity_conf,
            identifiers=identifiers,
            agg_params=agg_params,
        )

        cache_ctx = self._prepare_metrics_cache_context(entity, identifiers, agg_params)
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
                sql, params, result_key, return_columns = build_select_for_entity(
                    entity=entity,
                    identifiers=identifiers,
                    agg_params=agg_params,  # <- passa inferência para o builder
                )
                if isinstance(params, dict):
                    params = {**params, "entity": entity}  # etiqueta para métricas SQL
                rows_raw = self._exec.query(sql, params)
                set_trace_attribute(span, "cache.hit", False)
                set_trace_attribute(span, "sql.skipped", False)

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
                        pass
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

        final_rows = rows_formatted or []
        requested_metrics = extract_requested_metrics(question, entity_conf)
        results = {result_key: final_rows}

        meta: Dict[str, Any] = {
            "planner": plan,
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
            "rows_total": len(final_rows),
            "elapsed_ms": elapsed_ms,
            "gate": gate,
            "aggregates": (agg_params or {}),
            "requested_metrics": requested_metrics,
            "compute": {
                "mode": ("conceptual" if skip_sql else "sql"),
                "metrics_cache_hit": bool(metrics_cache_hit),
                "cache_key": metrics_cache_key,
                "cache_ttl": metrics_cache_ttl,
            },
        }

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

        return {
            "status": {"reason": "ok", "message": "ok"},
            "results": results,
            "meta": meta,
        }
