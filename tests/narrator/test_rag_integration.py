# tests/narrator/test_rag_integration.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict

import pytest

import app.narrator.narrator as narrator_mod
from app.narrator.narrator import Narrator


def _fake_policy_enabled() -> Dict[str, Any]:
    """Policy fake para habilitar o uso de LLM no Narrator durante o teste."""
    return {
        "llm_enabled": True,
        "shadow": False,
        "model": "dummy-model",
        "style": "executivo",
        "max_llm_rows": 10,
        "max_prompt_tokens": 4000,
        "max_output_tokens": 700,
        "use_rag_in_prompt": True,
    }


class FakeClient:
    """Cliente LLM fake para evitar chamadas reais ao Ollama."""

    def __init__(self) -> None:
        self.last_prompt: str | None = None
        self.last_model: str | None = None

    def generate(
        self, prompt: str, model: str | None = None, stream: bool = False
    ) -> str:
        self.last_prompt = prompt
        self.last_model = model
        # Retornamos um texto simples para o Narrator usar como resposta.
        return "texto-gerado-pelo-fake-llm"


def test_narrator_passes_rag_context_to_build_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Quando meta.rag estiver habilitado, o Narrator deve repassar esse
    contexto para o build_prompt (parâmetro rag).
    """

    # 1) Força policy com LLM habilitado
    monkeypatch.setattr(narrator_mod, "_load_narrator_policy", _fake_policy_enabled)

    # 2) Cria Narrator com cliente fake (sem dependência de Ollama real)
    narrator = Narrator(model="dummy-model", style="executivo")
    fake_client = FakeClient()
    narrator.client = fake_client

    captured: Dict[str, Any] = {}

    def fake_build_prompt(
        question: str,
        facts: dict,
        meta: dict,
        style: str = "executivo",
        rag: dict | None = None,
    ) -> str:
        captured["question"] = question
        captured["facts"] = facts
        captured["meta"] = meta
        captured["style"] = style
        captured["rag"] = rag
        return "PROMPT-DE-TESTE"

    # Patch do símbolo build_prompt dentro do módulo narrator (não em prompts.py)
    monkeypatch.setattr(narrator_mod, "build_prompt", fake_build_prompt)

    question = "quais são as últimas notícias do HGLG11?"
    facts = {"rows": [{"dummy": 1}]}
    meta = {
        "entity": "fiis_noticias",
        "intent": "fiis_noticias",
        "rag": {
            "enabled": True,
            "intent": "fiis_noticias",
            "entity": "fiis_noticias",
            "chunks": [
                {
                    "text": "Primeira notícia sobre HGLG11",
                    "score": 0.9,
                    "doc_id": "doc-1",
                },
                {
                    "text": "Segunda notícia sobre HGLG11",
                    "score": 0.8,
                    "doc_id": "doc-2",
                },
            ],
            "policy": {"max_chunks": 5, "collections": ["fiis_noticias"]},
        },
    }

    out = narrator.render(question=question, facts=facts, meta=meta)

    # 3) Saída básica do Narrator
    assert isinstance(out, dict)
    assert isinstance(out.get("text"), str)
    assert out["text"] != ""  # recebeu algo do fake LLM

    # 4) build_prompt foi chamado com o rag bruto vindo do meta
    assert captured["question"] == question
    assert captured["meta"].get("entity") == "fiis_noticias"
    assert captured["meta"].get("intent") == "fiis_noticias"

    rag = captured.get("rag")
    assert isinstance(rag, dict)
    assert rag.get("enabled") is True
    assert rag.get("intent") == "fiis_noticias"
    assert rag.get("entity") == "fiis_noticias"
    assert len(rag.get("chunks") or []) == 2


def test_narrator_handles_absent_rag_gracefully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mesmo sem meta.rag, o Narrator deve funcionar normalmente e
    chamar build_prompt com rag=None.
    """

    # 1) Policy com LLM habilitado
    monkeypatch.setattr(narrator_mod, "_load_narrator_policy", _fake_policy_enabled)

    narrator = Narrator(model="dummy-model", style="executivo")
    narrator.client = FakeClient()

    captured: Dict[str, Any] = {}

    def fake_build_prompt(
        question: str,
        facts: dict,
        meta: dict,
        style: str = "executivo",
        rag: dict | None = None,
    ) -> str:
        captured["question"] = question
        captured["facts"] = facts
        captured["meta"] = meta
        captured["style"] = style
        captured["rag"] = rag
        return "PROMPT-DE-TESTE-SEM-RAG"

    monkeypatch.setattr(narrator_mod, "build_prompt", fake_build_prompt)

    question = "resuma a situação de risco do HGLG11"
    facts = {"rows": [{"dummy": 1}]}
    meta = {
        "entity": "fiis_financials_risk",
        "intent": "fiis_financials_risk",
        # sem campo "rag"
    }

    out = narrator.render(question=question, facts=facts, meta=meta)

    # 2) Saída básica
    assert isinstance(out, dict)
    assert isinstance(out.get("text"), str)
    assert out["text"] != ""

    # 3) build_prompt foi chamado, mas sem rag
    assert captured["question"] == question
    assert captured["meta"].get("entity") == "fiis_financials_risk"
    assert captured["rag"] is None
