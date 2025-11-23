# app/narrator/narrator.py
from __future__ import annotations

import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from decimal import Decimal

from app.narrator.formatter import build_narrator_text
from app.narrator.prompts import build_prompt, render_narrative
from app.utils.filecache import load_yaml_cached

try:
    from app.rag.ollama_client import OllamaClient
except Exception:  # pragma: no cover - dependência opcional
    OllamaClient = None  # type: ignore

_FAILSAFE_TEXT = (
    "Não sei responder com segurança agora. Exemplos de perguntas válidas: "
    "'cnpj do MCCI11', 'preço do MXRF11 hoje'."
)

LOGGER = logging.getLogger(__name__)
_ENTITY_ROOT = Path("data/entities")
_NARRATOR_POLICY_PATH = Path("data/policies/narrator.yaml")
_TICKER_RE = re.compile(r"\b([A-Z]{4}\d{2})\b", re.IGNORECASE)
_FILTER_FIELD_NAMES = ("filters", "filter")


def _json_sanitise(obj: Any) -> Any:
    """
    Normaliza estruturas para algo seguro para JSON / prompts:
    - Decimal -> float
    - dict/list/tuple/set -> recursivo
    Mantém o restante inalterado.
    """
    if isinstance(obj, Decimal):
        # Se preferir preservar formatação, pode trocar para str(obj)
        return float(obj)

    if isinstance(obj, dict):
        return {k: _json_sanitise(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple, set)):
        t = type(obj)
        return t(_json_sanitise(v) for v in obj)

    return obj


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


def _rows_to_lines(
    rows: Iterable[Dict[str, Any]],
    requested_metrics: Optional[Iterable[str]] = None,
) -> str:
    lines: list[str] = []
    requested: list[str] = []
    if requested_metrics:
        requested = [
            str(metric)
            for metric in requested_metrics
            if isinstance(metric, str) and metric.strip()
        ]
        # garante ordem determinística e remove duplicatas
        seen_req: Dict[str, None] = {}
        for metric in requested:
            if metric not in seen_req:
                seen_req[metric] = None
        requested = list(seen_req.keys())

    for row in rows:
        if not isinstance(row, dict):
            continue
        parts: list[str] = []
        keys_order: list[str]
        if requested:
            keys_order = []
            if "ticker" in row:
                keys_order.append("ticker")
            keys_order.extend(
                [key for key in requested if key != "ticker" and key in row]
            )
        else:
            keys_order = [k for k in row.keys() if k != "meta"]
        for key in keys_order:
            if key == "meta":
                continue
            if key not in row:
                continue
            item_val = row.get(key)
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
    requested_metrics = (facts or {}).get("requested_metrics")
    candidates = [
        (facts or {}).get("rendered"),
        (facts or {}).get("rendered_text"),
        (facts or {}).get("text"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    if rows:
        rendered = _rows_to_lines(rows, requested_metrics=requested_metrics)
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


def _shrink_rag_for_concept(
    rag_ctx: Dict[str, Any] | None, *, max_chars: int = 900
) -> Dict[str, Any] | None:
    """
    Em modo conceitual, reduz o contexto de RAG para apenas o melhor chunk,
    com texto truncado, para evitar prompts gigantes e dispersão de foco.
    """
    if not isinstance(rag_ctx, dict):
        return None
    if not rag_ctx.get("enabled"):
        return None

    chunks = rag_ctx.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        return None

    best_chunk: Dict[str, Any] | None = None
    best_score = float("-inf")

    for ch in chunks:
        if not isinstance(ch, dict):
            continue
        raw_text = ch.get("text")
        if not isinstance(raw_text, str):
            continue
        text = raw_text.strip()
        if not text:
            continue
        score_raw = ch.get("score", 0.0)
        try:
            score = float(score_raw)
        except (TypeError, ValueError):
            score = 0.0
        if score > best_score:
            best_score = score
            best_chunk = ch

    if not best_chunk:
        return None

    new_chunk = dict(best_chunk)
    raw_text = new_chunk.get("text") or ""
    if isinstance(raw_text, str) and max_chars > 0 and len(raw_text) > max_chars:
        truncated = raw_text[:max_chars].rsplit(" ", 1)[0].strip()
        if not truncated:
            truncated = raw_text[:max_chars].strip()
        new_chunk["text"] = truncated + "..."

    policy_raw = rag_ctx.get("policy") or {}
    collections = None
    if isinstance(policy_raw, dict):
        collections = policy_raw.get("collections")
    if not collections:
        collections = rag_ctx.get("used_collections")

    new_ctx: Dict[str, Any] = {
        "enabled": True,
        "intent": rag_ctx.get("intent"),
        "entity": rag_ctx.get("entity"),
        "chunks": [new_chunk],
        "policy": {
            "max_chunks": 1,
            "collections": collections,
        },
        "used_collections": rag_ctx.get("used_collections"),
    }

    return new_ctx


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
      model: llama3.1:latest
      style: executivo
      max_llm_rows: 0
      max_prompt_tokens: 4000
      max_output_tokens: 700
    """
    try:
        data = load_yaml_cached(str(_NARRATOR_POLICY_PATH)) or {}
        if isinstance(data, dict):
            policy = (
                data.get("narrator") if isinstance(data.get("narrator"), dict) else None
            )
            return policy if policy is not None else data
        return {}
    except Exception:
        return {}


def _get_effective_policy(entity: str | None, policy: Dict[str, Any]) -> Dict[str, Any]:
    """Combina política global do Narrator com overrides específicos por entidade."""

    policy_dict = policy or {}
    default_policy = {}
    if isinstance(policy_dict, dict):
        default_policy = (
            policy_dict.get("default")
            if isinstance(policy_dict.get("default"), dict)
            else {}
        )

    effective_policy = {
        "llm_enabled": False,
        "shadow": False,
        "max_llm_rows": 0,
        "use_rag_in_prompt": False,
        "model": "llama3.1:latest",
    }

    base_overrides = {
        k: v
        for k, v in policy_dict.items()
        if k not in {"default", "entities", "terms", "version"}
    }

    if isinstance(default_policy, dict):
        effective_policy.update(default_policy)

    effective_policy.update(base_overrides)

    entities_cfg = policy_dict.get("entities") if isinstance(policy_dict, dict) else {}
    if isinstance(entities_cfg, dict):
        entity_policy_raw = entities_cfg.get(entity or "")
        if isinstance(entity_policy_raw, dict):
            effective_policy.update(entity_policy_raw)

    return effective_policy


class Narrator:
    def __init__(self, model: str | None = None, style: str = "executivo"):
        # Política declarativa (fonte de verdade)
        self.policy: Dict[str, Any] = _load_narrator_policy()

        default_policy = _get_effective_policy(None, self.policy)

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
            or default_policy.get("model")
            or self.policy.get("model")
            or os.getenv("NARRATOR_MODEL")
            or "llama3.1:latest"
        )
        self.style = style or self.policy.get("style") or "executivo"

        # Flags: **apenas YAML** define habilitação e shadow;
        # env é ignorado para evitar heurísticas escondidas.
        self.enabled = bool(default_policy.get("llm_enabled", False))
        self.shadow = bool(default_policy.get("shadow", False))

        # Limite de linhas para uso de LLM (0 = nunca usar LLM)
        max_rows = default_policy.get("max_llm_rows", 0)
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
    def _should_use_llm(
        self, facts: Dict[str, Any], effective_policy: Dict[str, Any]
    ) -> bool:
        """
        Regras:
          - se Narrator estiver desabilitado na policy → nunca usa LLM;
          - se max_llm_rows == 0 → nunca usa LLM;
          - se len(rows) > max_llm_rows → não usa LLM;
        """
        enabled = bool((effective_policy or {}).get("llm_enabled", False))
        if not enabled:
            return False

        rows = list((facts or {}).get("rows") or [])
        rows_count = len(rows)

        max_rows = (effective_policy or {}).get("max_llm_rows", 0)
        try:
            max_llm_rows = int(max_rows)
        except (TypeError, ValueError):
            max_llm_rows = 0

        if max_llm_rows <= 0:
            return False

        if rows_count > max_llm_rows:
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

        # meta.compute.mode (quando presente) é a fonte primária para o modo
        # de computação: "concept" vs "data"/"default".
        compute_mode_meta: Optional[str] = None
        compute_block = raw_meta.get("compute")
        if isinstance(compute_block, dict):
            raw_mode = compute_block.get("mode")
            if isinstance(raw_mode, str):
                m = raw_mode.strip().lower()
                if m in ("concept", "data", "default"):
                    compute_mode_meta = m

        # Política efetiva (global + overrides da entidade)
        effective_policy = _get_effective_policy(entity, self.policy)
        effective_enabled = bool(effective_policy.get("llm_enabled", self.enabled))
        effective_shadow = bool(effective_policy.get("shadow", self.shadow))
        max_rows_policy = effective_policy.get("max_llm_rows", self.max_llm_rows)
        try:
            effective_max_llm_rows = int(max_rows_policy)
        except (TypeError, ValueError):
            effective_max_llm_rows = 0

        use_rag_in_prompt = bool(effective_policy.get("use_rag_in_prompt", False))
        effective_model = effective_policy.get("model") or self.model

        narrator_meta: Dict[str, Any] = {
            "enabled": effective_enabled,
            "shadow": effective_shadow,
            "model": effective_model,
            "latency_ms": None,
            "error": None,
            "used": False,
            "strategy": "deterministic",
            "effective_policy": _json_sanitise(
                {
                    "llm_enabled": effective_enabled,
                    "shadow": effective_shadow,
                    "max_llm_rows": effective_max_llm_rows,
                    "use_rag_in_prompt": use_rag_in_prompt,
                    "model": effective_model,
                }
            ),
            "rag": None,
            "compute_mode": None,
        }

        # Política específica da entidade (se houver)
        entity_policy = effective_policy
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

        # Ordem de precedência:
        # 1) meta.compute.mode (quando definido)
        # 2) policy prefer_concept_when_no_ticker (fallback)
        if compute_mode_meta == "concept":
            concept_mode = True
        elif compute_mode_meta in ("data", "default"):
            concept_mode = False
        elif prefer_concept_when_no_ticker:
            detected_tickers = _extract_tickers_from_question_and_filters(
                question=question,
                meta=render_meta,
                facts=effective_facts,
            )
            if not detected_tickers:
                concept_mode = True

        # Normaliza render_meta.compute para refletir o modo efetivo
        if not isinstance(render_meta.get("compute"), dict):
            render_meta["compute"] = {"mode": "concept" if concept_mode else "data"}
        else:
            compute_block_rm = render_meta["compute"]
            if "mode" not in compute_block_rm:
                compute_block_rm["mode"] = "concept" if concept_mode else "data"

        compute_mode_effective = "concept" if concept_mode else "data"
        narrator_meta["compute_mode"] = compute_mode_effective

        # ------------------------------------------------------------------
        # Métrica foco (focus_metric_key) — vinda da ontologia / requested_metrics
        # ------------------------------------------------------------------
        focus_metric_key: str | None = None
        requested_metrics = effective_facts.get("requested_metrics")
        if isinstance(requested_metrics, (list, tuple)) and len(requested_metrics) == 1:
            candidate = requested_metrics[0]
            if isinstance(candidate, str) and candidate.strip():
                focus_metric_key = candidate.strip()

        narrator_meta["focus_metric_key"] = focus_metric_key

        if concept_mode:
            render_meta["narrator_mode"] = "concept"
            # Evita que perguntas conceituais virem "Índice de Treynor do LPLP11 = 0,00%"
            effective_facts["narrator_mode"] = "concept"
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

        narrator_meta["rag"] = _json_sanitise(rag_ctx)

        rag_ctx_for_prompt = rag_ctx
        if not use_rag_in_prompt:
            rag_ctx_for_prompt = None
            rag_best_text = ""
            if narrator_meta["strategy"] == "deterministic":
                narrator_meta["strategy"] = "rag_forbidden_by_policy"
        elif concept_mode and rag_ctx_for_prompt is not None:
            # Em modo conceitual, usamos apenas um chunk enxuto de RAG
            shrunk = _shrink_rag_for_concept(rag_ctx_for_prompt, max_chars=900)
            rag_ctx_for_prompt = shrunk if shrunk is not None else None

        LOGGER.info(
            "narrator_render entity=%s intent=%s rows_count=%s template_id=%s "
            "enabled=%s shadow=%s model=%s rag_enabled=%s chunks=%s",
            entity,
            intent,
            len(effective_facts.get("rows") or []),
            template_id or "",
            effective_enabled,
            effective_shadow,
            effective_model,
            rag_enabled,
            rag_chunks_count,
        )

        # 1) renderizador especializado
        deterministic_text = render_narrative(render_meta, effective_facts, self.policy)

        if (
            concept_with_data_when_rag
            and rag_best_text
            and (effective_facts.get("rows") or [])
        ):
            rows_block = _rows_to_lines(
                effective_facts.get("rows") or [],
                requested_metrics=effective_facts.get("requested_metrics"),
            )
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
        baseline_text = deterministic_text or _default_text(entity, effective_facts)
        rows_count = len(effective_facts.get("rows") or [])

        def _finalize_response(
            text: str,
            *,
            tokens_in: int = 0,
            tokens_out: int | None = None,
            latency_ms: float | None = None,
            error: str | None = None,
            strategy_override: str | None = None,
        ) -> Dict[str, Any]:
            computed_tokens_out = (
                tokens_out if tokens_out is not None else len((text or "").split())
            )
            elapsed_ms = (
                latency_ms
                if latency_ms is not None
                else (time.perf_counter() - t0_global) * 1000.0
            )

            narrator_meta["latency_ms"] = elapsed_ms
            if error is not None:
                narrator_meta["error"] = error
            if strategy_override:
                narrator_meta["strategy"] = strategy_override

            final_strategy = narrator_meta.get("strategy") or "deterministic"

            return {
                "text": text,
                "score": 1.0 if text else 0.0,
                "hints": {
                    "style": self.style,
                    "mode": "concept" if concept_mode else "default",
                    "strategy": final_strategy,
                },
                "strategy": final_strategy,
                "tokens": {"in": tokens_in, "out": computed_tokens_out},
                "latency_ms": elapsed_ms,
                "error": error,
                "enabled": narrator_meta.get("enabled", False),
                "shadow": narrator_meta.get("shadow", False),
                "meta": {"narrator": narrator_meta},
            }

        if not effective_enabled:
            return _finalize_response(
                baseline_text,
                error="llm_disabled_by_policy",
                strategy_override="llm_disabled_by_policy",
            )

        if effective_max_llm_rows <= 0:
            return _finalize_response(
                baseline_text,
                error="llm_disabled_by_policy",
                strategy_override="llm_disabled_by_policy",
            )

        if rows_count > effective_max_llm_rows:
            return _finalize_response(
                baseline_text,
                error="llm_skipped_max_rows",
                strategy_override="llm_skipped_max_rows",
            )

        if self.client is None:
            return _finalize_response(
                baseline_text,
                error="client_unavailable",
                strategy_override="llm_failed",
            )

        # ------------------------------------------------------------------
        # Fail-safe de evidência: se não há linhas nem chunks de RAG,
        # consideramos que não há contexto suficiente para o LLM trabalhar
        # sem risco de deriva. Nesses casos, não chamamos o modelo e
        # respondemos diretamente com o texto de segurança canônico.
        # ------------------------------------------------------------------
        has_rows = bool(effective_facts.get("rows") or effective_facts.get("primary"))
        rag_chunks = []
        if isinstance(rag_ctx, dict) and rag_ctx.get("enabled"):
            rag_chunks = rag_ctx.get("chunks") or []
        has_rag = bool(rag_chunks)

        if not has_rows and not has_rag:
            return _finalize_response(
                _FAILSAFE_TEXT,
                error="llm_skipped_no_evidence",
                strategy_override="llm_skipped_no_evidence",
            )

        prompt_facts = dict(effective_facts or {})
        prompt_facts.setdefault("rendered_text", baseline_text)
        if "fallback_message" not in prompt_facts:
            fallback_message = _empty_message(entity)
            if fallback_message:
                prompt_facts["fallback_message"] = fallback_message

        prompt_meta = dict(render_meta)
        if concept_mode:
            prompt_meta.setdefault("narrator_mode", "concept")

        # Injeta foco explícito no meta do prompt
        if focus_metric_key:
            focus_block = prompt_meta.get("focus")
            if not isinstance(focus_block, dict):
                focus_block = {}
            focus_block["metric_key"] = focus_metric_key
            prompt_meta["focus"] = focus_block

        prompt_facts = _json_sanitise(prompt_facts)
        prompt_meta = _json_sanitise(prompt_meta)
        rag_ctx_sanitised = (
            _json_sanitise(rag_ctx_for_prompt)
            if rag_ctx_for_prompt is not None
            else None
        )

        t0 = time.perf_counter()
        try:
            prompt = build_prompt(
                question=question,
                facts=prompt_facts,
                meta=prompt_meta,
                style=self.style,
                rag=rag_ctx_sanitised,
                effective_policy=effective_policy,
            )
        except TypeError:
            prompt = build_prompt(
                question=question,
                facts=prompt_facts,
                meta=prompt_meta,
                style=self.style,
                rag=rag_ctx_sanitised,
            )

        tokens_in = len(prompt.split()) if prompt else 0

        text = baseline_text
        error: str | None = None
        tokens_out = 0

        narrator_meta["used"] = True

        try:
            response = self.client.generate(prompt, model=effective_model, stream=False)
            candidate = (response or "").strip()
            LOGGER.info(
                "NARRATOR_LLM_RAW_RESPONSE entity=%s intent=%s model=%s "
                "tokens_in=%s candidate_len=%s",
                entity,
                intent,
                effective_model,
                tokens_in,
                len(candidate),
            )
            if candidate:
                text = candidate
                tokens_out = len(candidate.split())
        except Exception as exc:  # pragma: no cover - caminho excepcional
            error = f"llm_error: {exc}"
            LOGGER.error(
                "NARRATOR_LLM_ERROR entity=%s intent=%s model=%s error=%s",
                entity,
                intent,
                effective_model,
                exc,
            )

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        narrator_meta["latency_ms"] = elapsed_ms

        LOGGER.info(
            "NARRATOR_FINAL_TEXT entity=%s intent=%s model=%s "
            "used_llm=%s latency_ms=%.2f error=%s text_preview=%s",
            entity,
            intent,
            effective_model,
            bool(tokens_out),
            elapsed_ms,
            error,
            (text[:120] + "..." if isinstance(text, str) and len(text) > 120 else text),
        )

        if error:
            # Fail-safe alinhado ao data/policies/llm_prompts.md:
            # não tentar "salvar" a resposta com baseline potencialmente contaminado.

            return _finalize_response(
                _FAILSAFE_TEXT,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=elapsed_ms,
                error=error,
                strategy_override="llm_failed",
            )

        if effective_shadow:
            narrator_meta["strategy"] = "llm_shadow"
            return _finalize_response(
                baseline_text,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=elapsed_ms,
                strategy_override="llm_shadow",
            )

        narrator_meta["strategy"] = "llm"
        return _finalize_response(
            text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=elapsed_ms,
            strategy_override="llm",
        )
