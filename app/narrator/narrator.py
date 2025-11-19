# app/narrator/narrator.py
# -*- coding: utf-8 -*-
"""SIRIOS Narrator — camada de expressão determinística + LLM opcional (policy-driven)."""

from __future__ import annotations

import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable

from app.narrator.formatter import build_narrator_text
from app.narrator.prompts import build_prompt, render_narrative
from app.utils.filecache import load_yaml_cached

try:
    from app.rag.ollama_client import OllamaClient
except Exception:  # pragma: no cover - dependência opcional
    OllamaClient = None  # type: ignore


LOGGER = logging.getLogger(__name__)
_ENTITY_ROOT = Path("data/entities")
_NARRATOR_POLICY_PATH = Path("data/policies/narrator.yaml")
_TICKER_RE = re.compile(r"\b([A-Z]{4}\d{2})\b", re.IGNORECASE)
_FILTER_FIELD_NAMES = ("filters", "filter")


def _load_entity_config(entity: str) -> Dict[str, Any]:
    if not entity:
        return {}
    path = _ENTITY_ROOT / entity / "entity.yaml"
    try:
        return load_yaml_cached(str(path)) or {}
    except Exception:
        return {}


def _empty_message(entity: str) -> str | None:
    cfg = _load_entity_config(entity)
    presentation = cfg.get("presentation") if isinstance(cfg, dict) else None
    if isinstance(presentation, dict):
        message = presentation.get("empty_message")
        if isinstance(message, str) and message.strip():
            return message.strip()
    return None


def _rows_to_lines(rows: Iterable[Dict[str, Any]]) -> str:
    lines = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        parts = []
        for key, item_val in row.items():
            if key == "meta":
                continue
            if item_val is None:
                continue
            text = str(item_val)
            if not text:
                continue
            parts.append(f"**{key}**: {text}")
        if parts:
            lines.append("- " + "; ".join(parts))
    return "\n".join(lines).strip()


def _default_text(entity: str, facts: Dict[str, Any]) -> str:
    rows = list((facts or {}).get("rows") or [])
    candidates = [
        (facts or {}).get("rendered"),
        (facts or {}).get("rendered_text"),
        (facts or {}).get("text"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    if rows:
        rendered = _rows_to_lines(rows)
        if rendered:
            return rendered
    message = _empty_message(entity)
    if message:
        return message
    return "Sem dados disponíveis no momento."


def _iter_filter_payloads(source: Dict[str, Any] | None) -> Iterable[Any]:
    if not isinstance(source, dict):
        return []
    payloads = []
    for field in _FILTER_FIELD_NAMES:
        if field in source:
            payloads.append(source[field])
    nested_meta = source.get("meta")
    if isinstance(nested_meta, dict):
        payloads.extend(_iter_filter_payloads(nested_meta))
    return payloads


def _collect_filter_texts(payload: Any) -> Iterable[str]:
    texts: list[str] = []
    if isinstance(payload, str):
        texts.append(payload)
    elif isinstance(payload, dict):
        for value in payload.values():
            texts.extend(_collect_filter_texts(value))
    elif isinstance(payload, (list, tuple, set)):
        for item in payload:
            texts.extend(_collect_filter_texts(item))
    return texts


def _best_rag_chunk_text(
    rag_ctx: Dict[str, Any] | None, *, max_chars: int = 900
) -> str:
    if not isinstance(rag_ctx, dict):
        return ""
    chunks = rag_ctx.get("chunks")
    if not isinstance(chunks, list):
        return ""
    best_text = ""
    best_score = float("-inf")
    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue
        raw_text = chunk.get("text")
        if not isinstance(raw_text, str):
            continue
        text = raw_text.strip()
        if not text:
            continue
        score_raw = chunk.get("score", 0.0)
        try:
            score = float(score_raw)
        except (TypeError, ValueError):
            score = 0.0
        if score > best_score:
            best_score = score
            best_text = text
    if not best_text:
        return ""
    if max_chars > 0 and len(best_text) > max_chars:
        truncated = best_text[:max_chars].rsplit(" ", 1)[0].strip()
        if not truncated:
            truncated = best_text[:max_chars].strip()
        best_text = truncated + "..."
    return best_text


def _extract_tickers_from_question_and_filters(
    question: str,
    meta: Dict[str, Any] | None,
    facts: Dict[str, Any] | None,
) -> set[str]:
    tickers: set[str] = set()

    def _apply_regex(text: str | None) -> None:
        if not isinstance(text, str):
            return
        for match in _TICKER_RE.findall(text):
            tickers.add(match.upper())

    _apply_regex(question)

    for payload in _iter_filter_payloads(meta):
        for text in _collect_filter_texts(payload):
            _apply_regex(text)

    for payload in _iter_filter_payloads(facts):
        for text in _collect_filter_texts(payload):
            _apply_regex(text)

    return tickers


def _load_narrator_policy() -> Dict[str, Any]:
    """
    Carrega política declarativa do Narrator a partir de data/policies/narrator.yaml.

    Estrutura esperada:

    narrator:
      llm_enabled: false
      shadow: false
      model: mistral:instruct
      style: executivo
      max_llm_rows: 0
      max_prompt_tokens: 4000
      max_output_tokens: 700
    """
    try:
        data = load_yaml_cached(str(_NARRATOR_POLICY_PATH)) or {}
        policy = data.get("narrator") if isinstance(data, dict) else None
        return policy or {}
    except Exception:
        return {}


class Narrator:
    def __init__(self, model: str | None = None, style: str = "executivo"):
        # Política declarativa (fonte de verdade)
        self.policy: Dict[str, Any] = _load_narrator_policy()

        # Política específica por entidade (opcional)
        entities_cfg = (
            self.policy.get("entities") if isinstance(self.policy, dict) else {}
        )
        self.entities_policy: Dict[str, Any] = (
            entities_cfg if isinstance(entities_cfg, dict) else {}
        )

        # Modelo / estilo: prioridade → arg explícito > YAML > env > default
        self.model = (
            model
            or self.policy.get("model")
            or os.getenv("NARRATOR_MODEL")
            or "mistral:instruct"
        )
        self.style = style or self.policy.get("style") or "executivo"

        # Flags: **apenas YAML** define habilitação e shadow;
        # env é ignorado para evitar heurísticas escondidas.
        self.enabled = bool(self.policy.get("llm_enabled", False))
        self.shadow = bool(self.policy.get("shadow", False))

        # Limite de linhas para uso de LLM (0 = nunca usar LLM)
        max_rows = self.policy.get("max_llm_rows", 0)
        try:
            self.max_llm_rows = int(max_rows)
        except (TypeError, ValueError):
            self.max_llm_rows = 0

        # (Reservado) limites de tokens — ainda não usados no prompt builder,
        # mas já carregados da política para futuro hardening.
        self.max_prompt_tokens = int(self.policy.get("max_prompt_tokens", 0) or 0)
        self.max_output_tokens = int(self.policy.get("max_output_tokens", 0) or 0)

        self.client = OllamaClient() if OllamaClient else None

    # ---------------------------------------------------------------------
    # Decisão de uso de LLM — 100% baseada em policy (sem heurísticas fixas)
    # ---------------------------------------------------------------------
    def _should_use_llm(self, facts: Dict[str, Any]) -> bool:
        """
        Regras:
          - se Narrator estiver desabilitado na policy → nunca usa LLM;
          - se max_llm_rows == 0 → nunca usa LLM;
          - se len(rows) > max_llm_rows → não usa LLM;
        """
        if not self.enabled:
            return False

        rows = list((facts or {}).get("rows") or [])
        rows_count = len(rows)

        if self.max_llm_rows <= 0:
            return False

        if rows_count > self.max_llm_rows:
            return False

        return True

    # ---------------------------------------------------------------------

    def render(
        self, question: str, facts: Dict[str, Any], meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        t0_global = time.perf_counter()
        raw_meta = meta or {}
        raw_facts = facts or {}
        entity = raw_meta.get("entity") or ""
        intent = raw_meta.get("intent") or ""
        template_id = raw_meta.get("template_id") or raw_facts.get("result_key")
        render_meta: Dict[str, Any] = dict(raw_meta)

        # Política específica da entidade (se houver)
        entity_policy = (
            self.entities_policy.get(entity, {})
            if hasattr(self, "entities_policy")
            else {}
        )
        prefer_concept_when_no_ticker = bool(
            entity_policy.get("prefer_concept_when_no_ticker", False)
        )
        rag_fallback_when_no_rows = bool(
            entity_policy.get("rag_fallback_when_no_rows", False)
        )
        concept_with_data_when_rag = bool(
            entity_policy.get("concept_with_data_when_rag", False)
        )

        # Decisão de modo:
        # - concept_mode=True  -> resposta conceitual (ignora rows)
        # - concept_mode=False -> resposta baseada em rows (por fundo)
        concept_mode = False
        effective_facts: Dict[str, Any] = dict(raw_facts)
        if prefer_concept_when_no_ticker:
            detected_tickers = _extract_tickers_from_question_and_filters(
                question=question,
                meta=render_meta,
                facts=effective_facts,
            )
            if not detected_tickers:
                concept_mode = True

        if concept_mode:
            render_meta["narrator_mode"] = "concept"
            # Evita que perguntas conceituais virem "Índice de Treynor do LPLP11 = 0,00%"
            effective_facts["rows"] = []
            if "rows_sample" in effective_facts:
                effective_facts["rows_sample"] = []
            if "primary" in effective_facts:
                effective_facts["primary"] = {}

        # Contexto de RAG (opcional, injetado pelo Orchestrator em meta['rag'])
        # Regra:
        #   - se meta.rag não existir ou não for dict → rag_ctx = None
        #   - se meta.rag existir e for dict → repassado como está p/ build_prompt
        #   - se meta.rag_debug_disable=True → força rag_ctx=None (modo debug)
        rag_raw = render_meta.get("rag")
        rag_ctx = rag_raw if isinstance(rag_raw, dict) else None

        rag_debug_disable = bool(render_meta.get("rag_debug_disable"))
        if rag_debug_disable:
            rag_ctx = None

        if rag_ctx is not None:
            rag_enabled = bool(rag_ctx.get("enabled"))
            rag_chunks_count = len(rag_ctx.get("chunks") or [])
        else:
            rag_enabled = False
            rag_chunks_count = 0
        rag_best_text = _best_rag_chunk_text(rag_ctx)

        LOGGER.info(
            "narrator_render entity=%s intent=%s rows_count=%s template_id=%s "
            "enabled=%s shadow=%s model=%s rag_enabled=%s chunks=%s",
            entity,
            intent,
            len(effective_facts.get("rows") or []),
            template_id or "",
            self.enabled,
            self.shadow,
            self.model,
            rag_enabled,
            rag_chunks_count,
        )

        # 1) renderizador especializado
        deterministic_text = render_narrative(render_meta, effective_facts, self.policy)

        if concept_mode and rag_best_text:
            deterministic_text = rag_best_text
        elif (
            concept_with_data_when_rag
            and rag_best_text
            and (effective_facts.get("rows") or [])
        ):
            rows_block = _rows_to_lines(effective_facts.get("rows") or [])
            if rows_block:
                deterministic_text = (
                    f"{rag_best_text}\n\n**Dados mais recentes:**\n{rows_block}"
                )
        elif (
            rag_fallback_when_no_rows
            and not (effective_facts.get("rows") or [])
            and rag_best_text
        ):
            deterministic_text = rag_best_text

        # 2) formatter genérico
        if not deterministic_text:
            try:
                deterministic_text = build_narrator_text(
                    {"facts": effective_facts or {}}
                )
            except Exception:
                deterministic_text = ""

        # 3) fallback padrão
        baseline_text = deterministic_text or _default_text(
            entity, effective_facts
        )

        def _make_response(
            text: str,
            *,
            tokens_in: int = 0,
            tokens_out: int | None = None,
            latency_ms: float | None = None,
            error: str | None = None,
        ) -> Dict[str, Any]:
            computed_tokens_out = (
                tokens_out if tokens_out is not None else len(text.split())
            )
            elapsed_ms = (
                latency_ms
                if latency_ms is not None
                else (time.perf_counter() - t0_global) * 1000.0
            )
            return {
                "text": text,
                "score": 1.0 if text else 0.0,
                "hints": {
                    "style": self.style,
                    "mode": "concept" if concept_mode else "default",
                },
                "tokens": {"in": tokens_in, "out": computed_tokens_out},
                "latency_ms": elapsed_ms,
                "error": error,
                "enabled": self.enabled,
                "shadow": self.shadow,
            }

        # Caso global: Narrator desabilitado → só baseline
        if not self.enabled:
            return _make_response(baseline_text)

        # Cliente LLM indisponível → só baseline, com erro explícito
        if self.client is None:
            return _make_response(
                baseline_text,
                error="client_unavailable",
            )

        # Decisão policy-driven: usar ou não usar LLM
        if not self._should_use_llm(effective_facts):
            rows_count = len(effective_facts.get("rows") or [])
            return _make_response(
                baseline_text,
                error=(
                    f"llm_skipped: rows_count={rows_count} "
                    f"max_llm_rows={self.max_llm_rows}"
                ),
            )

        # A partir daqui, LLM está habilitado e será chamado
        prompt_facts = dict(effective_facts or {})
        prompt_facts.setdefault("rendered_text", baseline_text)
        if "fallback_message" not in prompt_facts:
            fallback_message = _empty_message(entity)
            if fallback_message:
                prompt_facts["fallback_message"] = fallback_message
        prompt_meta = dict(render_meta)
        if concept_mode:
            # Sinaliza explicitamente o modo para o prompt builder / debugging
            prompt_meta.setdefault("narrator_mode", "concept")

        t0 = time.perf_counter()
        prompt = build_prompt(
            question=question,
            facts=prompt_facts,
            meta=prompt_meta,
            style=self.style,
            # Passa o contexto de RAG bruto (ou None). O próprio build_prompt
            # se encarrega de normalizar/truncar quando rag for um dict válido.
            rag=rag_ctx,
        )
        tokens_in = len(prompt.split()) if prompt else 0

        text = baseline_text
        error: str | None = None
        tokens_out = 0

        try:
            # Usamos generate(), alinhado com OllamaClient
            response = self.client.generate(prompt, model=self.model, stream=False)
            candidate = (response or "").strip()
            if candidate:
                text = candidate
                tokens_out = len(candidate.split())
        except Exception as exc:  # pragma: no cover - caminho excepcional
            error = f"llm_error: {exc}"

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return _make_response(
            text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=elapsed_ms,
            error=error,
        )
