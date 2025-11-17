# app/presenter/presenter.py
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

from app.formatter.rows import render_rows_template
from app.narrator.narrator import Narrator
from app.observability.metrics import (
    emit_counter as counter,
    emit_histogram as histogram,
)
from app.rag.context_builder import build_context, load_rag_policy
from app.responder import render_answer


class FactsPayload(BaseModel):
    """
    Pacote canônico de fatos estruturados que alimenta
    Narrator, Responder e qualquer canal de apresentação.

    Ele é derivado de:
    - planner.explain(question)  → plan
    - orchestrator.route_question(question) → results
    - orchestrator.extract_identifiers(question) → identifiers
    - infer_params(...) → aggregates
    """

    # Pergunta original do usuário
    question: str

    # Decisão do planner
    intent: str
    entity: str
    planner_score: float

    # Chave de resultado da entidade (ex.: "dividends", "prices")
    result_key: Optional[str]

    # Dados tabulares normalizados
    rows: List[Dict[str, Any]]
    primary: Dict[str, Any]

    # Agregados inferidos (infer_params)
    aggregates: Dict[str, Any]

    # Filtros/identificadores extraídos da pergunta
    identifiers: Dict[str, Any]

    # Atalhos convenientes
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


def build_facts(
    *,
    question: str,
    plan: Dict[str, Any],
    orchestrator_results: Dict[str, Any],
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
    try:
        planner_score = float(chosen.get("score") or 0.0)
    except (TypeError, ValueError):
        planner_score = 0.0

    results = orchestrator_results or {}
    result_key: Optional[str] = next(iter(results.keys()), None)

    rows_raw = results.get(result_key)
    rows: List[Dict[str, Any]] = rows_raw if isinstance(rows_raw, list) else []
    primary: Dict[str, Any] = rows[0] if rows else {}

    identifiers = dict(identifiers or {})
    aggregates = dict(aggregates or {})

    ticker = (primary or {}).get("ticker") or identifiers.get("ticker")
    fund = (primary or {}).get("fund")

    facts = FactsPayload(
        question=question,
        intent=intent,
        entity=entity,
        planner_score=planner_score,
        result_key=result_key,
        rows=rows,
        primary=primary,
        aggregates=aggregates,
        identifiers=identifiers,
        ticker=ticker,
        fund=fund,
    )

    return facts, result_key, rows


def present(
    *,
    question: str,
    plan: Dict[str, Any],
    orchestrator_results: Dict[str, Any],
    identifiers: Dict[str, Any],
    aggregates: Dict[str, Any],
    narrator: Optional[Narrator],
    narrator_flags: Dict[str, Any],
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
    rag_policy = load_rag_policy()
    intent = plan["chosen"]["intent"]
    entity = plan["chosen"]["entity"]
    rag_context = build_context(
        question=question,
        intent=intent,
        entity=entity,
        policy=rag_policy,
    )

    facts, result_key, rows = build_facts(
        question=question,
        plan=plan,
        orchestrator_results=orchestrator_results,
        identifiers=identifiers,
        aggregates=aggregates,
    )

    # Baseline determinístico (sempre calculado)
    legacy_answer = render_answer(
        facts.entity,
        rows,
        identifiers=facts.identifiers,
        aggregates=facts.aggregates,
    )
    rendered_template = render_rows_template(facts.entity, rows)

    # Estado inicial do narrador (equivalente ao narrator_info atual)
    enabled = bool(narrator_flags.get("enabled"))
    shadow = bool(narrator_flags.get("shadow"))
    model = str(narrator_flags.get("model") or "")

    narrator_info: Dict[str, Any] = {
        "enabled": enabled,
        "shadow": shadow,
        "model": model,
        "latency_ms": None,
        "error": None,
        "used": False,
        "score": None,
        "strategy": "fallback",
    }

    final_answer = legacy_answer

    if narrator is not None:
        meta_for_narrator: Dict[str, Any] = {
            "intent": facts.intent,
            "entity": facts.entity,
            # se explain=True, podemos expor o porquê da rota
            "explain": (plan.get("explain") if explain else None),
            "result_key": result_key,
        }

        # Modo shadow: mede Narrator mas não altera o answer
        if shadow:
            try:
                t0 = time.perf_counter()
                out = narrator.render(question, facts.dict(), meta_for_narrator)
                dt_ms = (time.perf_counter() - t0) * 1000.0

                latency = out.get("latency_ms", dt_ms)
                score = out.get("score")

                narrator_info.update(
                    latency_ms=latency,
                    score=score,
                    used=True,
                    strategy="llm_shadow",
                )
                counter("sirios_narrator_shadow_total", outcome="ok")
                if latency is not None:
                    histogram("sirios_narrator_latency_ms", float(latency))
            except Exception as e:  # noqa: BLE001
                narrator_info.update(error=str(e), strategy="fallback_error")
                counter("sirios_narrator_shadow_total", outcome="error")

        # Modo enabled: substitui o answer pelo texto do Narrator
        if enabled:
            try:
                t0 = time.perf_counter()
                out = narrator.render(question, facts.dict(), meta_for_narrator)
                dt_ms = (time.perf_counter() - t0) * 1000.0

                text = out.get("text") or legacy_answer
                latency = out.get("latency_ms", dt_ms)
                score = out.get("score")

                final_answer = text
                narrator_info.update(
                    latency_ms=latency,
                    score=score,
                    used=True,
                    strategy="llm",
                )
                counter("sirios_narrator_render_total", outcome="ok")
                if latency is not None:
                    histogram("sirios_narrator_latency_ms", float(latency))
            except Exception as e:  # noqa: BLE001
                narrator_info.update(error=str(e), strategy="fallback_error")
                counter("sirios_narrator_render_total", outcome="error")
                # fallback: mantém final_answer = legacy_answer

    narrator_info["rag"] = rag_context

    return PresentResult(
        answer=final_answer,
        legacy_answer=legacy_answer,
        rendered_template=rendered_template,
        narrator_meta=narrator_info,
        facts=facts,
    )
