# app/presenter/presenter.py
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

from app.formatter.rows import get_entity_presentation_kind, render_rows_template
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
from app.presenter.institutional import (
    compose_institutional_answer,
    is_institutional_intent,
)
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

    # Resposta técnica determinística (pré-template)
    technical_answer: str

    # Resposta baseline (template ou resposta técnica)
    baseline_answer: str

    # Renderização tabular/template (Markdown)
    rendered_template: str

    # Metadados do narrador (mesmo shape do "narrator_info" atual)
    narrator_meta: Dict[str, Any]

    # Payload canônico de fatos usados na geração
    facts: FactsPayload

    # Observabilidade sobre uso de template declarativo
    template_used: bool = False
    template_kind: Optional[str] = None


def _choose_result_key(
    results: Dict[str, Any], meta_result_key: Optional[str]
) -> Tuple[Optional[str], Optional[str]]:
    """Seleciona result_key de forma determinística e auditável.

    Retorna a chave escolhida e uma etiqueta de diagnóstico quando houver
    divergência (ex.: meta aponta para chave inexistente).
    """

    if not isinstance(results, dict):
        return None, "results_not_dict"

    # Preferência pelo meta.result_key quando existir na saída
    if isinstance(meta_result_key, str) and meta_result_key in results:
        return meta_result_key, None

    keys = [k for k in results.keys()]
    if len(keys) == 1:
        chosen = keys[0]
        mismatch_reason = None
    else:
        # heurística determinística: escolher a primeira chave com lista não vazia
        chosen = None
        for k in keys:
            v = results.get(k)
            if isinstance(v, list) and v:
                chosen = k
                break
        if chosen is None and keys:
            chosen = sorted(keys)[0]
        mismatch_reason = "result_key_mismatch" if meta_result_key else None

    return chosen, mismatch_reason


def _extract_rows_compact(
    rows: Iterable[Dict[str, Any]], *, max_rows: int = 3, max_fields: int = 6
) -> List[Dict[str, Any]]:
    """Extrai subconjunto de campos primitivos para wiring seguro.

    Evita campos aninhados e limita a quantidade para reduzir payload em
    rewrite_only sem perder ancoragem factual.
    """

    compact_rows: List[Dict[str, Any]] = []
    for row in list(rows)[: max_rows if max_rows > 0 else None]:
        if not isinstance(row, dict):
            continue
        compact: Dict[str, Any] = {}
        for idx, (key, value) in enumerate(row.items()):
            if key == "meta":
                continue
            if max_fields > 0 and idx >= max_fields:
                break
            if isinstance(value, (str, int, float, bool)):
                compact[key] = value
        if compact:
            compact_rows.append(compact)
    return compact_rows


def _extract_anchors_from_rows(
    rows: Iterable[Dict[str, Any]], *, max_rows: int = 5, max_fields: int = 6
) -> Set[str]:
    """Gera conjunto pequeno de âncoras textuais a partir de campos primitivos."""

    anchors: Set[str] = set()
    for row in list(rows)[: max_rows if max_rows > 0 else None]:
        if not isinstance(row, dict):
            continue
        for idx, (key, value) in enumerate(row.items()):
            if key == "meta":
                continue
            if max_fields > 0 and idx >= max_fields:
                break
            if isinstance(value, (str, int, float)):
                text = str(value).strip()
                if text:
                    anchors.add(text[:120])
    return anchors


def _ensure_baseline(baseline: str, rows: List[Dict[str, Any]]) -> str:
    """Garante baseline determinístico não vazio quando houver linhas."""

    if isinstance(baseline, str) and baseline.strip():
        return baseline

    bullets: List[str] = []
    for row in rows[:3]:
        if not isinstance(row, dict):
            continue
        parts: List[str] = []
        for idx, (k, v) in enumerate(row.items()):
            if idx >= 5:
                break
            if isinstance(v, (str, int, float, bool)):
                parts.append(f"{k}: {v}")
        if parts:
            bullets.append("- " + "; ".join(parts))
    return "\n".join(bullets).strip()


def _answer_has_anchor(answer: str, anchors: Set[str]) -> bool:
    """Valida se a resposta mantém pelo menos uma âncora factual."""

    if not anchors:
        return bool(answer and answer.strip())
    answer_low = (answer or "").lower()
    for anchor in anchors:
        if not anchor:
            continue
        if str(anchor).lower() in answer_low:
            return True
    return False


def _is_absence_text(answer: str) -> bool:
    text = (answer or "").strip().lower()
    if not text:
        return True
    absence_markers = [
        "não encontrei",
        "sem dados",
        "nenhum dado",
        "sem registros",
        "nao encontrei",
    ]
    return any(marker in text for marker in absence_markers)




def build_facts(
    *,
    question: str,
    plan: Dict[str, Any],
    orchestrator_results: Dict[str, Any],
    meta: Optional[Dict[str, Any]] = None,
    identifiers: Dict[str, Any],
    aggregates: Dict[str, Any],
) -> Tuple[FactsPayload, Optional[str], List[Dict[str, Any]], Optional[str]]:
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
    result_key, mismatch_reason = _choose_result_key(results, meta_result_key)

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

    return facts, result_key, rows, mismatch_reason


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

    # RAG canônico
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

    # CONTEXTO CONVERSACIONAL
    context_history_wire: List[Dict[str, Any]] = []
    try:
        if context_manager.enabled and context_manager.narrator_allows_entity(entity):
            turns = context_manager.load_recent(client_id_safe, conversation_id_safe)
            if turns:
                context_history_wire = context_manager.to_wire(turns)
    except Exception:
        context_history_wire = []

    facts, result_key, rows, result_key_mismatch = build_facts(
        question=question,
        plan=plan,
        orchestrator_results=orchestrator_results,
        meta=meta,
        identifiers=identifiers,
        aggregates=aggregates,
    )

    if result_key_mismatch:
        LOGGER.info(
            "result_key ajustado de forma determinística",
            extra={"meta_result_key": meta_dict.get("result_key"), "chosen": result_key},
        )

    # compute.mode
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

    template_kind = get_entity_presentation_kind(facts.entity)

    # Baseline determinístico
    technical_answer = render_answer(
        facts.entity,
        rows,
        identifiers=facts.identifiers,
        aggregates=facts.aggregates,
    )

    rendered_template = render_rows_template(
        facts.entity,
        rows,
        identifiers=facts.identifiers,
        aggregates=facts.aggregates,
    )

    template_used = bool(
        isinstance(rendered_template, str) and rendered_template.strip()
    )
    if template_used:
        baseline_answer = rendered_template
    else:
        baseline_answer = technical_answer

    baseline_answer = _ensure_baseline(baseline_answer, rows)

    # facts_md = baseline_answer
    facts_md = rendered_template if template_used else technical_answer

    legacy_answer = baseline_answer

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

    final_answer = baseline_answer
    anchors = _extract_anchors_from_rows(rows)

    is_institutional = is_institutional_intent(facts.intent)

    institutional_answer = compose_institutional_answer(
        baseline_answer=baseline_answer,
        intent=facts.intent,
    )
    if institutional_answer is not None:
        final_answer = institutional_answer
        narrator_info["used"] = False

    # Wire payload que pode ser usado pelo Narrator e/ou persistido no Shadow Event.
    facts_wire: Optional[Dict[str, Any]] = None

    # Só chama o Narrator se a policy efetiva da entidade permitir LLM.
    if (
        not is_institutional
        and narrator is not None
        and bool(effective_narrator_policy.get("llm_enabled"))
    ):
        meta_for_narrator: Dict[str, Any] = {
            "intent": facts.intent,
            "entity": facts.entity,
            "compute": {"mode": compute_mode},
            # se explain=True, podemos expor o porquê da rota
            "explain": (plan.get("explain") if explain else None),
            "result_key": result_key,
            "rag": narrator_rag_context,
            "presentation_kind": template_kind,
        }

        if context_history_wire:
            meta_for_narrator["history"] = context_history_wire

        if narrator_meta:
            meta_for_narrator.update(narrator_meta)

        try:
            t0 = time.perf_counter()
            # Wire payload para o Narrator (evita deriva quando rewrite-only estiver habilitado)
            facts_wire = facts.dict()
            # adiciona evidência compacta para manter ancoragem factual mesmo em rewrite_only
            facts_wire["rows_compact"] = _extract_rows_compact(rows)
            if anchors:
                facts_wire["anchors"] = sorted(anchors)

            # Ativa rewrite-only apenas quando explicitamente habilitado na policy efetiva
            # (sem hardcode por entidade; contrato controlado por YAML/policy)
            if bool(effective_narrator_policy.get("rewrite_only")):
                # baseline textual primário: preferir template se existir, senão technical
                facts_wire["rendered_text"] = facts_md or baseline_answer
                # optional trimming: manter apenas evidência compacta para reduzir payload
                facts_wire.pop("rows", None)
                facts_wire.pop("primary", None)
                facts_wire.pop("identifiers", None)
                facts_wire.pop("aggregates", None)

            out = narrator.render(question, facts_wire, meta_for_narrator)

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
            text = out.get("text") or baseline_answer
            if strategy == "llm_shadow":
                final_answer = baseline_answer
                counter("sirios_narrator_shadow_total", outcome="ok")
            elif strategy == "llm":
                if bool(effective_narrator_policy.get("rewrite_only")):
                    final_answer = text
                else:
                    final_answer = f"{text}\n\n{facts_md}"
                counter("sirios_narrator_render_total", outcome="ok")
            else:
                final_answer = text
                counter(
                    "sirios_narrator_render_total",
                    outcome="skip",
                )

            latency = narrator_info.get("latency_ms") or dt_ms
            if latency is not None:
                histogram("sirios_narrator_latency_ms", float(latency))

        except Exception as e:  # noqa: BLE001
            narrator_info.update(error=str(e), strategy="fallback_error")
            counter("sirios_narrator_render_total", outcome="error")

    # Validação pós-narrator: garante âncoras quando rows_total > 0
    if rows and (_is_absence_text(final_answer) or not _answer_has_anchor(final_answer, anchors)):
        LOGGER.info(
            "Narrator output descartado por falta de âncoras; usando baseline determinístico",
            extra={"result_key": result_key, "rows": len(rows)},
        )
        final_answer = baseline_answer
        narrator_info.setdefault("validation", {})[
            "result"
        ] = "fallback_baseline_missing_anchor"

    # Observabilidade: explicita se a entidade estava em rewrite-only.
    narrator_info.setdefault(
        "rewrite_only", bool(effective_narrator_policy.get("rewrite_only"))
    )

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
            facts=facts_wire or facts.dict(),
            rag=(
                narrator_rag_context if isinstance(narrator_rag_context, dict) else None
            ),
            narrator=narrator_info,
            presenter={
                "answer_final": final_answer,
                "answer_baseline": baseline_answer,
                "answer_technical": technical_answer,
                "rows_used": len(rows),
                "style": getattr(narrator, "style", None),
                "template_used": template_used,
                "template_kind": template_kind,
            },
        )
        collect_narrator_shadow(shadow_event)
    except Exception:  # pragma: no cover - best-effort observability
        LOGGER.exception("Falha ao coletar Narrator Shadow", exc_info=True)

    return PresentResult(
        answer=final_answer,
        legacy_answer=legacy_answer,
        technical_answer=technical_answer,
        baseline_answer=baseline_answer,
        rendered_template=rendered_template,
        narrator_meta=narrator_info,
        facts=facts,
        template_used=template_used,
        template_kind=template_kind,
    )
