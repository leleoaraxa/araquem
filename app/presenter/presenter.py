# app/presenter/presenter.py
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from app.formatter.rows import render_rows_template
from app.narrator.narrator import Narrator
from app.observability.metrics import (
    emit_counter as counter,
    emit_histogram as histogram,
)
from app.observability.narrator_shadow import (
    NarratorShadowEvent,
    collect_narrator_shadow,
)
from app.rag.context_builder import build_context, get_rag_policy, load_rag_policy
from app.templates_answer import render_answer
from app.core.context import context_manager

LOGGER = logging.getLogger(__name__)


class FactsPayload(BaseModel):
    """Pacote canônico de fatos estruturados usado pelo Presenter.

    Campos mínimos e suas origens:
    - question: pergunta original recebida pelo endpoint.
    - intent: `plan['chosen']['intent']` (Planner).
    - entity: `plan['chosen']['entity']` (Planner).
    - score: `meta['planner_score']` (ou `plan['chosen']['score']` como fallback).
    - result_key: `meta['result_key']` quando disponível; senão, a primeira chave de `results`.
    - rows: `results[result_key]` (formatação do Orchestrator).
    - primary: primeira linha de `rows` (ou `{}` quando vazio).
    - aggregates: parâmetros inferidos (`infer_params`).
    - identifiers: identificadores extraídos pelo orchestrator.
    - requested_metrics: métricas solicitadas (`meta['requested_metrics']`).

    Campos auxiliares:
    - planner_score: espelho de `score` para compatibilidade retroativa.
    - ticker/fund: atalhos convenientes extraídos de `primary` ou `identifiers`.
    """

    question: str
    intent: str
    entity: str
    score: float
    planner_score: float

    result_key: Optional[str]

    rows: List[Dict[str, Any]]
    primary: Dict[str, Any]

    aggregates: Dict[str, Any]
    identifiers: Dict[str, Any]

    requested_metrics: List[str] = Field(default_factory=list)

    ticker: Optional[str] = None
    fund: Optional[str] = None


class PresentResult(BaseModel):
    """
    Resultado da camada de apresentação (Presenter).

    É o que o /ask (ou qualquer outro canal) consome
    para montar a resposta final para o cliente.
    """

    # Texto final apresentado ao usuário
    answer: str

    # Baseline determinístico (sempre calculado)
    legacy_answer: str

    # Renderização tabular/template (Markdown)
    rendered_template: str

    # Metadados do narrador (mesmo shape do "narrator_info" atual)
    narrator_meta: Dict[str, Any]

    # Payload canônico de fatos usados na geração
    facts: FactsPayload

    # Observabilidade sobre uso de template declarativo
    template_used: bool = False
    template_kind: Optional[str] = None


def build_facts(
    *,
    question: str,
    plan: Dict[str, Any],
    orchestrator_results: Dict[str, Any],
    meta: Optional[Dict[str, Any]] = None,
    identifiers: Dict[str, Any],
    aggregates: Dict[str, Any],
) -> Tuple[FactsPayload, Optional[str], List[Dict[str, Any]]]:
    """
    Constrói o FactsPayload a partir do output das camadas de
    Planner + Orchestrator + Param Inference.

    Retorna:
    - facts: FactsPayload completo
    - result_key: chave de resultados (ex.: "dividends")
    - rows: lista de linhas usada por formatter/responder
    """
    chosen = plan.get("chosen") or {}
    intent = str(chosen.get("intent") or "")
    entity = str(chosen.get("entity") or "")

    def _coerce_float(value: Any) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    meta_dict = meta if isinstance(meta, dict) else {}
    score_from_meta = _coerce_float(meta_dict.get("planner_score"))
    score_from_plan = _coerce_float(chosen.get("score"))
    score = score_from_meta if score_from_meta is not None else (score_from_plan or 0.0)

    results = orchestrator_results or {}
    meta_result_key = (
        meta_dict.get("result_key") if isinstance(meta_dict, dict) else None
    )
    result_key: Optional[str]
    if isinstance(meta_result_key, str) and meta_result_key in results:
        result_key = meta_result_key
    else:
        result_key = next(
            iter(results.keys()),
            meta_result_key if isinstance(meta_result_key, str) else None,
        )

    rows_raw = results.get(result_key)
    rows: List[Dict[str, Any]] = rows_raw if isinstance(rows_raw, list) else []
    primary: Dict[str, Any] = rows[0] if rows else {}

    identifiers_clean = dict(identifiers or {})
    aggregates_clean = dict(aggregates or {})

    requested_metrics_raw = meta_dict.get("requested_metrics")
    requested_metrics: List[str]
    if isinstance(requested_metrics_raw, list):
        requested_metrics = [
            str(item) for item in requested_metrics_raw if isinstance(item, str)
        ]
    else:
        requested_metrics = []

    ticker = (primary or {}).get("ticker") or identifiers_clean.get("ticker")
    fund = (primary or {}).get("fund") or identifiers_clean.get("fund")

    facts = FactsPayload(
        question=question,
        intent=intent,
        entity=entity,
        score=score,
        planner_score=score,
        result_key=result_key,
        rows=rows,
        primary=primary,
        aggregates=aggregates_clean,
        identifiers=identifiers_clean,
        requested_metrics=requested_metrics,
        ticker=ticker,
        fund=fund,
    )

    return facts, result_key, rows


def present(
    *,
    question: str,
    plan: Dict[str, Any],
    orchestrator_results: Dict[str, Any],
    meta: Optional[Dict[str, Any]] = None,
    identifiers: Dict[str, Any],
    aggregates: Dict[str, Any],
    narrator: Optional[Narrator],
    narrator_meta: Optional[Dict[str, Any]] = None,
    client_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    nickname: Optional[str] = None,
    explain: bool = False,
) -> PresentResult:
    """
    Camada de apresentação do Araquem (pós-formatter).

    Responsável por:
    - Construir FactsPayload (via build_facts)
    - Gerar baseline determinístico (Responder + template tabular)
    - Acionar o Narrator (se habilitado)
    - Decidir qual texto final será retornado
    - Devolver PresentResult com answer, legacy_answer, template, narrator_meta, facts
    """
    intent = plan["chosen"]["intent"]
    entity = plan["chosen"]["entity"]
    client_id_safe = client_id or ""
    conversation_id_safe = conversation_id or ""
    has_ticker_in_question = bool(identifiers.get("ticker"))

    compute_mode_meta: Optional[str] = None
    meta_dict = meta if isinstance(meta, dict) else {}
    compute_block = meta_dict.get("compute") if isinstance(meta_dict, dict) else None
    if isinstance(compute_block, dict):
        raw_mode = compute_block.get("mode")
        if isinstance(raw_mode, str):
            m = raw_mode.strip().lower()
            if m in ("concept", "data", "default"):
                compute_mode_meta = m

    # RAG canônico: preferimos o contexto já produzido pelo Orchestrator em meta["rag"].
    rag_policy: Optional[Dict[str, Any]] = None
    meta_rag_raw = (
        meta_dict.get("rag") if isinstance(meta_dict.get("rag"), dict) else None
    )
    if isinstance(meta_rag_raw, dict):
        narrator_rag_context = dict(meta_rag_raw)
        if not isinstance(narrator_rag_context.get("policy"), dict):
            rag_policy = load_rag_policy()
            narrator_rag_context["policy"] = get_rag_policy(
                entity=entity,
                intent=intent,
                compute_mode=compute_mode_meta,
                has_ticker=has_ticker_in_question,
                policy=rag_policy,
            )
    else:
        rag_policy = load_rag_policy()
        narrator_rag_context = build_context(
            question=question,
            intent=intent,
            entity=entity,
            compute_mode=compute_mode_meta,
            has_ticker=has_ticker_in_question,
            policy=rag_policy,
        )

    # ------------------------------------------------------------------
    # CONTEXTO CONVERSACIONAL — carga best-effort para o Narrator
    # ------------------------------------------------------------------
    context_history_wire: List[Dict[str, Any]] = []
    try:
        if context_manager.enabled and context_manager.narrator_allows_entity(entity):
            turns = context_manager.load_recent(client_id_safe, conversation_id_safe)
            if turns:
                context_history_wire = context_manager.to_wire(turns)
    except Exception:
        # Contexto nunca deve quebrar a resposta principal
        context_history_wire = []

    facts, result_key, rows = build_facts(
        question=question,
        plan=plan,
        orchestrator_results=orchestrator_results,
        meta=meta,
        identifiers=identifiers,
        aggregates=aggregates,
    )

    # ------------------------------------------------------------------
    # compute.mode — decide se a pergunta é conceitual ou baseada em dados
    # ------------------------------------------------------------------
    # Regra atual (sem heurísticas mágicas):
    # - Se a entidade tiver prefer_concept_when_no_ticker=true na policy
    #   do Narrator E não houver ticker extraído da pergunta (identifiers),
    #   então compute.mode = "concept". Caso contrário, "data".
    #
    # Isso garante que perguntas como "Sharpe negativo em um FII quer dizer
    # que ele é ruim?" sejam tratadas como conceituais, mesmo que exista
    # uma view tabular por trás da entidade.
    compute_mode = "data"
    if narrator is not None and hasattr(narrator, "policy"):
        policy = getattr(narrator, "policy", {}) or {}
        entities_cfg = policy.get("entities") if isinstance(policy, dict) else {}
        entity_policy = (
            entities_cfg.get(facts.entity) if isinstance(entities_cfg, dict) else {}
        )
        if (
            isinstance(entity_policy, dict)
            and entity_policy.get("prefer_concept_when_no_ticker")
            and not has_ticker_in_question
        ):
            compute_mode = "concept"

    effective_narrator_policy: Dict[str, Any] = {}
    if narrator is not None:
        try:
            effective_narrator_policy = narrator.get_effective_policy(facts.entity)
        except Exception:
            LOGGER.warning("Falha ao obter policy efetiva do Narrator", exc_info=True)
            effective_narrator_policy = {}

    # Baseline determinístico (sempre calculado)
    # 1) Geração "antiga" (texto técnico, ainda disponível como fallback)
    legacy_answer = render_answer(
        facts.entity,
        rows,
        identifiers=facts.identifiers,
        aggregates=facts.aggregates,
    )

    # 2) Geração via template .md.j2 (modo produto)
    rendered_template = render_rows_template(
        facts.entity,
        rows,
        identifiers=facts.identifiers,
        aggregates=facts.aggregates,
    )

    # Se o template renderizou algo não-vazio, ele passa a ser o baseline
    # apresentado ao usuário final. O legacy_answer fica como backup.
    template_used = bool(
        isinstance(rendered_template, str) and rendered_template.strip()
    )
    if template_used:
        legacy_answer = rendered_template

    narrator_info: Dict[str, Any] = {
        "enabled": bool(effective_narrator_policy.get("llm_enabled")),
        "shadow": bool(effective_narrator_policy.get("shadow")),
        "model": str(
            effective_narrator_policy.get("model") or getattr(narrator, "model", "")
        ),
        "latency_ms": None,
        "error": None,
        "used": False,
        "score": None,
        "strategy": "fallback",
        "effective_policy": effective_narrator_policy or None,
    }

    final_answer = legacy_answer

    if narrator is not None:
        meta_for_narrator: Dict[str, Any] = {
            "intent": facts.intent,
            "entity": facts.entity,
            "compute": {"mode": compute_mode},
            # se explain=True, podemos expor o porquê da rota
            "explain": (plan.get("explain") if explain else None),
            "result_key": result_key,
            "rag": narrator_rag_context,
        }

        # Injeta histórico de contexto no meta consumido pelo Narrator.
        # Não altera o payload externo do /ask: é apenas meta interno.
        if context_history_wire:
            meta_for_narrator["history"] = context_history_wire

        if narrator_meta:
            meta_for_narrator.update(narrator_meta)

        try:
            t0 = time.perf_counter()
            out = narrator.render(question, facts.dict(), meta_for_narrator)
            dt_ms = (time.perf_counter() - t0) * 1000.0

            narrator_out_meta = out.get("meta", {}).get("narrator")
            if isinstance(narrator_out_meta, dict):
                narrator_info = narrator_out_meta
                narrator_info.setdefault("latency_ms", dt_ms)
            else:
                narrator_info.update(
                    latency_ms=out.get("latency_ms", dt_ms),
                    score=out.get("score"),
                    used=out.get("used", False),
                    error=out.get("error"),
                    strategy=out.get("strategy", narrator_info.get("strategy")),
                )

            strategy = narrator_info.get("strategy") or "deterministic"
            text = out.get("text") or legacy_answer
            if strategy == "llm_shadow":
                final_answer = legacy_answer
                counter("sirios_narrator_shadow_total", outcome="ok")
            else:
                final_answer = text
                counter(
                    "sirios_narrator_render_total",
                    outcome="ok" if strategy == "llm" else "skip",
                )

            latency = narrator_info.get("latency_ms") or dt_ms
            if latency is not None:
                histogram("sirios_narrator_latency_ms", float(latency))
        except Exception as e:  # noqa: BLE001
            narrator_info.update(error=str(e), strategy="fallback_error")
            counter("sirios_narrator_render_total", outcome="error")
            # fallback: mantém final_answer = legacy_answer

    narrator_info.setdefault("rag", narrator_rag_context)

    try:
        routing_thresholds = None
        if isinstance(meta_dict.get("thresholds"), dict):
            routing_thresholds = meta_dict.get("thresholds")
        elif isinstance(plan.get("chosen", {}).get("thresholds"), dict):
            routing_thresholds = plan.get("chosen", {}).get("thresholds")

        shadow_event = NarratorShadowEvent(
            environment=os.getenv("SIRIOS_ENV", os.getenv("ENVIRONMENT", "dev")),
            request={
                "question": question,
                "conversation_id": conversation_id_safe,
                "nickname": nickname,
                "client_id": client_id_safe,
            },
            routing={
                "intent": intent,
                "entity": entity,
                "planner_score": facts.score,
                "tokens": meta_dict.get("tokens"),
                "thresholds": routing_thresholds,
            },
            facts=facts.dict(),
            rag=(
                narrator_rag_context if isinstance(narrator_rag_context, dict) else None
            ),
            narrator=narrator_info,
            presenter={
                "answer_final": final_answer,
                "answer_baseline": legacy_answer,
                "rows_used": len(rows),
                "style": getattr(narrator, "style", None),
                "template_used": template_used,
                "template_kind": None,
            },
        )
        collect_narrator_shadow(shadow_event)
    except Exception:  # pragma: no cover - best-effort observability
        LOGGER.exception("Falha ao coletar Narrator Shadow", exc_info=True)

    return PresentResult(
        answer=final_answer,
        legacy_answer=legacy_answer,
        rendered_template=rendered_template,
        narrator_meta=narrator_info,
        facts=facts,
        template_used=template_used,
        template_kind=None,
    )
