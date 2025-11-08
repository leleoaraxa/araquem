# -*- coding: utf-8 -*-
"""SIRIOS Narrator — drop-in, sem alterar o pipeline existente.
Generated: 2025-11-08T18:03:21
"""

from __future__ import annotations
import os, time, traceback
from typing import Any, Dict
from app.narrator.prompts import build_prompt

try:
    from app.rag.ollama_client import OllamaClient
except Exception:
    OllamaClient = None

def _fmt_number_br(x: Any) -> str:
    try:
        if isinstance(x, (int, float)):
            s = f"{x:,.2f}"
            return s.replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        pass
    return str(x)

def _fallback_text(facts: Dict[str, Any], meta: Dict[str, Any]) -> str:
    tck = (facts or {}).get("ticker") or (facts or {}).get("fund") or ""
    linhas = [f"**{tck}** — resposta baseada em fatos disponíveis:"]
    medidas = (facts or {}).get("medidas") or []
    for m in medidas:
        nome = m.get("nome")
        val = m.get("valor")
        un = m.get("unidade","")
        if isinstance(val, (int, float)) and un == "ratio":
            linhas.append(f"- {nome}: **{_fmt_number_br(val*100)}%**")
        elif isinstance(val, (int, float)):
            linhas.append(f"- {nome}: **{_fmt_number_br(val)} {un}**".rstrip())
        else:
            linhas.append(f"- {nome}: **{val}**".rstrip())
    faixas = (facts or {}).get("faixas") or []
    for fx in faixas:
        nome = fx.get("nome")
        val = fx.get("valor")
        un = fx.get("unidade","")
        if isinstance(val, (int, float)) and un == "ratio":
            linhas.append(f"- {nome.replace('_','→')}: **{_fmt_number_br(val*100)}%**")
    if len(linhas) == 1:
        linhas.append("(Sem campos detalhados disponíveis para narração.)")
    linhas.append("Fonte: SIRIOS.")
    return "\n".join(linhas)

class Narrator:
    def __init__(self, model: str | None = None, style: str = "executivo"):
        self.model = model or os.getenv("NARRATOR_MODEL", "mistral:instruct")
        self.style = style
        self.enabled = os.getenv("NARRATOR_ENABLED", "false").lower() == "true"
        self.shadow = os.getenv("NARRATOR_SHADOW", "false").lower() == "true"
        self.client = OllamaClient() if OllamaClient else None

    def render(self, question: str, facts: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        t0 = time.perf_counter()
        prompt = build_prompt(question=question, facts=facts, meta=meta, style=self.style)
        text = None
        error = None
        tokens_in = len(prompt.split())
        tokens_out = 0

        if self.client is not None:
            try:
                resp = self.client.prompt(prompt, model=self.model)
                text = (resp or "").strip()
                tokens_out = len(text.split())
            except Exception as e:
                error = f"llm_error: {e}\n{traceback.format_exc()}"
        else:
            error = "OllamaClient indisponível; usando fallback."

        if not text:
            text = _fallback_text(facts, meta)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        score = 1.0 if ((facts or {}).get("ticker","") and (facts.get("ticker","") in text)) else 0.9

        return {
            "text": text,
            "score": score,
            "hints": {"style": self.style},
            "tokens": {"in": tokens_in, "out": tokens_out},
            "latency_ms": elapsed_ms,
            "error": error,
            "enabled": self.enabled,
            "shadow": self.shadow
        }
