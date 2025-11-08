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
    # tenta pegar a linha principal
    primary = (facts or {}).get("primary")
    if not primary:
        rows = (facts or {}).get("rows") or []
        primary = rows[0] if rows else {}

    # ticker no topo
    tck = (
        (primary or {}).get("ticker")
        or (facts or {}).get("ticker")
        or (facts or {}).get("fund")
        or ""
    )
    header = (
        f"**{tck}** — resposta baseada em fatos disponíveis:"
        if tck
        else "Resposta baseada em fatos disponíveis:"
    )
    linhas = [header]

    # mapeamento de campos do seu dataset de processos
    campos = [
        ("Processo", primary.get("process_number")),
        ("Juízo", primary.get("judgment")),
        ("Instância", primary.get("instance")),
        ("Início", primary.get("initiation_date")),
        ("Valor da causa", primary.get("cause_amt")),
        ("Partes", primary.get("process_parts")),
        ("Risco de perda", primary.get("loss_risk_pct")),
        ("Fatos", primary.get("main_facts")),
        ("Impacto", primary.get("loss_impact_analysis")),
    ]
    for nome, val in campos:
        if val:
            linhas.append(f"- {nome}: **{val}**")

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

    def render(
        self, question: str, facts: Dict[str, Any], meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        t0 = time.perf_counter()
        prompt = build_prompt(
            question=question, facts=facts, meta=meta, style=self.style
        )
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
        score = (
            1.0
            if ((facts or {}).get("ticker", "") and (facts.get("ticker", "") in text))
            else 0.9
        )

        return {
            "text": text,
            "score": score,
            "hints": {"style": self.style},
            "tokens": {"in": tokens_in, "out": tokens_out},
            "latency_ms": elapsed_ms,
            "error": error,
            "enabled": self.enabled,
            "shadow": self.shadow,
        }
