# -*- coding: utf-8 -*-
"""SIRIOS Narrator — camada de expressão determinística."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Iterable

from app.narrator.prompts import build_prompt
from app.utils.filecache import load_yaml_cached

try:
    from app.rag.ollama_client import OllamaClient
except Exception:  # pragma: no cover - dependência opcional
    OllamaClient = None  # type: ignore


LOGGER = logging.getLogger(__name__)
_ENTITY_ROOT = Path("data/entities")


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


class Narrator:
    def __init__(self, model: str | None = None, style: str = "executivo"):
        self.model = model or os.getenv("NARRATOR_MODEL", "mistral:instruct")
        self.style = style
        self.enabled = os.getenv("NARRATOR_ENABLED", "false").lower() == "true"
        self.shadow = os.getenv("NARRATOR_SHADOW", "false").lower() == "true"
        self.client = OllamaClient() if OllamaClient else None

    def render(
        self, question: str, facts: Dict[str, Any], meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        entity = (meta or {}).get("entity") or ""
        rows = list((facts or {}).get("rows") or [])
        template_id = (meta or {}).get("template_id") or (facts or {}).get("result_key")
        LOGGER.info(
            "narrator_render entity=%s rows_count=%s template_id=%s enabled=%s shadow=%s",
            entity,
            len(rows),
            template_id or "",
            self.enabled,
            self.shadow,
        )

        baseline_text = _default_text(entity, facts or {})

        if not self.enabled:
            return {
                "text": baseline_text,
                "score": 1.0 if baseline_text else 0.0,
                "hints": {"style": self.style},
                "tokens": {"in": 0, "out": 0},
                "latency_ms": 0.0,
                "error": None,
                "enabled": self.enabled,
                "shadow": self.shadow,
            }

        if self.client is None:
            return {
                "text": baseline_text,
                "score": 1.0 if baseline_text else 0.0,
                "hints": {"style": self.style},
                "tokens": {"in": 0, "out": 0},
                "latency_ms": 0.0,
                "error": "client_unavailable",
                "enabled": self.enabled,
                "shadow": self.shadow,
            }

        prompt_facts = dict(facts or {})
        prompt_facts.setdefault("rendered_text", baseline_text)
        if "fallback_message" not in prompt_facts:
            fallback_message = _empty_message(entity)
            if fallback_message:
                prompt_facts["fallback_message"] = fallback_message
        prompt_meta = dict(meta or {})

        t0 = time.perf_counter()
        prompt = build_prompt(
            question=question,
            facts=prompt_facts,
            meta=prompt_meta,
            style=self.style,
        )
        tokens_in = len(prompt.split()) if prompt else 0

        text = baseline_text
        error = None
        tokens_out = 0

        try:
            response = self.client.prompt(prompt, model=self.model)
            candidate = (response or "").strip()
            if candidate:
                text = candidate
                tokens_out = len(candidate.split())
        except Exception as exc:  # pragma: no cover - caminho excepcional
            error = f"llm_error: {exc}"

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "text": text,
            "score": 1.0 if text else 0.0,
            "hints": {"style": self.style},
            "tokens": {"in": tokens_in, "out": tokens_out},
            "latency_ms": elapsed_ms,
            "error": error,
            "enabled": self.enabled,
            "shadow": self.shadow,
        }
