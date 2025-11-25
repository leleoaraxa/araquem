# tests/narrator/test_concept_mode.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List

import pytest

import app.narrator.narrator as narrator_mod
from app.narrator.narrator import Narrator, _rows_to_lines


def _fake_concept_policy() -> Dict[str, Any]:
    return {
        "llm_enabled": False,
        "shadow": False,
        "model": "dummy-model",
        "style": "executivo",
        "max_llm_rows": 0,
        "max_prompt_tokens": 4000,
        "max_output_tokens": 700,
        "use_rag_in_prompt": True,
        "entities": {
            "fiis_financials_risk": {
                "prefer_concept_when_no_ticker": True,
                "use_rag_in_prompt": True,
            }
        },
    }


def _fake_concept_policy_with_rag() -> Dict[str, Any]:
    policy = _fake_concept_policy()
    entity_cfg = policy.setdefault("entities", {}).setdefault(
        "fiis_financials_risk", {}
    )
    entity_cfg.update(
        {
            "prefer_concept_when_no_ticker": True,
            "rag_fallback_when_no_rows": True,
            "concept_with_data_when_rag": True,
            "use_rag_in_prompt": True,
        }
    )
    return policy


def _sample_risk_rows() -> List[Dict[str, Any]]:
    return [
        {
            "ticker": "HGLG11",
            "volatility_ratio": "1,44%",
            "sharpe_ratio": "-1,08%",
            "treynor_ratio": "-0,13%",
            "jensen_alpha": "0.000",
            "beta_index": "0.403",
            "sortino_ratio": "-10,21%",
            "max_drawdown": "0.1132",
            "r_squared": "0.0781",
            "created_at": "2024-05-22 00:00:00",
            "updated_at": "2025-11-19 00:00:00",
        },
        {
            "ticker": "XPLG11",
            "volatility_ratio": "0,98%",
            "sharpe_ratio": "0,55%",
            "treynor_ratio": "0,11%",
            "jensen_alpha": "0.100",
            "beta_index": "0.290",
            "sortino_ratio": "-2,00%",
            "max_drawdown": "0.0500",
            "r_squared": "0.1200",
            "created_at": "2024-05-22 00:00:00",
            "updated_at": "2025-11-19 00:00:00",
        },
    ]


def test_concept_mode_without_ticker(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(narrator_mod, "_load_narrator_policy", _fake_concept_policy)
    narrator = Narrator(model="dummy-model", style="executivo")

    captured: Dict[str, Any] = {}

    def fake_render(meta: dict, facts: dict, policy: dict) -> str:
        captured["meta"] = meta
        captured["facts"] = facts
        return ""

    monkeypatch.setattr(narrator_mod, "render_narrative", fake_render)

    facts = {
        "rows": [{"ticker": "LPLP11", "treynor_ratio": "0%"}],
        "primary": {"ticker": "LPLP11"},
    }
    meta = {"entity": "fiis_financials_risk", "intent": "fiis_financials_risk"}

    out = narrator.render(
        question="explique o que é beta em FIIs",
        facts=facts,
        meta=meta,
    )

    assert captured["meta"].get("narrator_mode") == "concept"
    assert captured["facts"].get("rows") == []
    assert captured["facts"].get("primary") == {}
    assert out["hints"]["mode"] == "concept"
    assert "LPLP11" not in out["text"]
    assert "narrator_mode" not in meta  # meta original permanece intacto
    assert facts["rows"]  # rows originais não foram alterados


def test_entity_mode_with_question_ticker(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(narrator_mod, "_load_narrator_policy", _fake_concept_policy)
    narrator = Narrator(model="dummy-model", style="executivo")

    captured: Dict[str, Any] = {}

    def fake_render(meta: dict, facts: dict, policy: dict) -> str:
        captured["meta"] = meta
        captured["facts"] = facts
        return f"Narrativa do {facts.get('primary', {}).get('ticker', '')}"

    monkeypatch.setattr(narrator_mod, "render_narrative", fake_render)

    facts = {
        "rows": [{"ticker": "HGLG11"}],
        "primary": {"ticker": "HGLG11"},
    }
    meta = {"entity": "fiis_financials_risk", "intent": "fiis_financials_risk"}

    out = narrator.render(
        question="explique as métricas de risco do HGLG11",
        facts=facts,
        meta=meta,
    )

    assert captured["meta"].get("narrator_mode") != "concept"
    assert captured["facts"].get("rows") == facts["rows"]
    assert captured["facts"].get("primary") == facts["primary"]
    assert out["text"].startswith("Narrativa do HGLG11")
    assert out["hints"]["mode"] == "default"


def test_entity_mode_with_multiple_tickers_in_question(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(narrator_mod, "_load_narrator_policy", _fake_concept_policy)
    narrator = Narrator(model="dummy-model", style="executivo")

    captured: Dict[str, Any] = {}

    def fake_render(meta: dict, facts: dict, policy: dict) -> str:
        captured["meta"] = meta
        captured["facts"] = facts
        return "comparação"

    monkeypatch.setattr(narrator_mod, "render_narrative", fake_render)

    facts = {
        "rows": [
            {"ticker": "HGLG11"},
            {"ticker": "MXRF11"},
        ],
    }
    meta = {"entity": "fiis_financials_risk", "intent": "fiis_financials_risk"}

    out = narrator.render(
        question="compare Sharpe e Beta de HGLG11 e MXRF11",
        facts=facts,
        meta=meta,
    )

    assert captured["meta"].get("narrator_mode") != "concept"
    assert captured["facts"].get("rows") == facts["rows"]
    assert out["hints"]["mode"] == "default"


def test_entity_mode_detects_ticker_in_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(narrator_mod, "_load_narrator_policy", _fake_concept_policy)
    narrator = Narrator(model="dummy-model", style="executivo")

    captured: Dict[str, Any] = {}

    def fake_render(meta: dict, facts: dict, policy: dict) -> str:
        captured["meta"] = meta
        captured["facts"] = facts
        return "filtro detectado"

    monkeypatch.setattr(narrator_mod, "render_narrative", fake_render)

    facts = {"rows": [{"ticker": "MXRF11"}]}
    meta = {
        "entity": "fiis_financials_risk",
        "intent": "fiis_financials_risk",
        "filters": {"ticker": "MXRF11"},
    }

    out = narrator.render(
        question="quero entender risco",
        facts=facts,
        meta=meta,
    )

    assert captured["meta"].get("narrator_mode") != "concept"
    assert captured["facts"].get("rows") == facts["rows"]
    assert out["text"] == "filtro detectado"
    assert out["hints"]["mode"] == "default"


def test_concept_mode_uses_rag_chunk(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        narrator_mod, "_load_narrator_policy", _fake_concept_policy_with_rag
    )
    narrator = Narrator(model="dummy-model", style="executivo")

    monkeypatch.setattr(narrator_mod, "render_narrative", lambda *_: "")

    rag_chunk_text = "Beta em FIIs mede a sensibilidade do fundo ao mercado."
    facts = {
        "rows": [{"ticker": "LPLP11"}],
        "primary": {"ticker": "LPLP11"},
    }
    meta = {
        "entity": "fiis_financials_risk",
        "intent": "fiis_financials_risk",
        "rag": {
            "enabled": True,
            "chunks": [
                {"text": rag_chunk_text, "score": 0.9},
            ],
        },
    }

    out = narrator.render(
        question="explique o que é beta em fiis",
        facts=facts,
        meta=meta,
    )

    assert rag_chunk_text in out["text"]
    assert out["hints"]["mode"] == "concept"


def test_concept_plus_data_merges_rag_and_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        narrator_mod, "_load_narrator_policy", _fake_concept_policy_with_rag
    )
    narrator = Narrator(model="dummy-model", style="executivo")

    monkeypatch.setattr(narrator_mod, "render_narrative", lambda *_: "")

    rag_chunk_text = "Sharpe e Beta avaliam risco e retorno ajustado."
    facts = {
        "rows": [
            {"ticker": "HGLG11", "sharpe_ratio": 0.8, "beta_index": 0.9},
            {"ticker": "MXRF11", "sharpe_ratio": 0.5, "beta_index": 0.6},
        ]
    }
    meta = {
        "entity": "fiis_financials_risk",
        "intent": "fiis_financials_risk",
        "rag": {
            "enabled": True,
            "chunks": [
                {"text": rag_chunk_text, "score": 0.95},
            ],
        },
    }

    out = narrator.render(
        question="compare sharpe e beta de HGLG11 e MXRF11",
        facts=facts,
        meta=meta,
    )

    assert rag_chunk_text in out["text"]
    assert "Dados mais recentes" in out["text"]
    assert "**ticker**" in out["text"]


def test_requested_metrics_limit_rows_block(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        narrator_mod, "_load_narrator_policy", _fake_concept_policy_with_rag
    )
    narrator = Narrator(model="dummy-model", style="executivo")

    monkeypatch.setattr(narrator_mod, "render_narrative", lambda *_: "")

    rag_chunk_text = "Sharpe e Beta avaliam risco e retorno ajustado."
    facts = {
        "rows": _sample_risk_rows(),
        "requested_metrics": ["sharpe_ratio", "beta_index"],
    }
    meta = {
        "entity": "fiis_financials_risk",
        "intent": "fiis_financials_risk",
        "rag": {
            "enabled": True,
            "chunks": [
                {"text": rag_chunk_text, "score": 0.95},
            ],
        },
    }

    out = narrator.render(
        question="compare sharpe e beta de HGLG11 e XPLG11",
        facts=facts,
        meta=meta,
    )

    text = out["text"]
    assert "**sharpe_ratio**" in text
    assert "**beta_index**" in text
    assert "**sortino_ratio**" not in text
    assert "**volatility_ratio**" not in text


def test_requested_metrics_absent_lists_all(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        narrator_mod, "_load_narrator_policy", _fake_concept_policy_with_rag
    )
    narrator = Narrator(model="dummy-model", style="executivo")

    monkeypatch.setattr(narrator_mod, "render_narrative", lambda *_: "")

    rag_chunk_text = "Sharpe e Beta avaliam risco e retorno ajustado."
    facts = {"rows": _sample_risk_rows()}
    meta = {
        "entity": "fiis_financials_risk",
        "intent": "fiis_financials_risk",
        "rag": {
            "enabled": True,
            "chunks": [
                {"text": rag_chunk_text, "score": 0.95},
            ],
        },
    }

    out = narrator.render(
        question="compare sharpe e beta de HGLG11 e XPLG11",
        facts=facts,
        meta=meta,
    )

    text = out["text"]
    assert "**sortino_ratio**" in text
    assert "**max_drawdown**" in text


def test_rows_to_lines_filters_by_requested_metrics():
    rows = [
        {
            "ticker": "HGLG11",
            "volatility_ratio": "1,44%",
            "sharpe_ratio": "-1,08%",
            "treynor_ratio": "-0,13%",
            "beta_index": "0.403",
            "sortino_ratio": "-10,21%",
            "max_drawdown": "0.1132",
            "r_squared": "0.0781",
        }
    ]

    text = _rows_to_lines(
        rows,
        requested_metrics=["sharpe_ratio", "beta_index"],
    )

    # deve sempre incluir o ticker
    assert "ticker" in text
    assert "HGLG11" in text

    # deve incluir apenas as métricas pedidas
    assert "sharpe_ratio" in text
    assert "beta_index" in text

    # não deve citar outras métricas numéricas
    assert "volatility_ratio" not in text
    assert "treynor_ratio" not in text
    assert "sortino_ratio" not in text
    assert "max_drawdown" not in text
    assert "r_squared" not in text


def test_rows_to_lines_uses_all_metrics_when_requested_metrics_empty():
    rows = [
        {
            "ticker": "XPLG11",
            "volatility_ratio": "1,76%",
            "sharpe_ratio": "-59,78%",
            "treynor_ratio": "-0,10%",
            "beta_index": "0.357",
        }
    ]

    # lista vazia (ou None) deve reproduzir o comportamento antigo:
    # percorre todas as colunas, exceto 'meta'
    text = _rows_to_lines(rows, requested_metrics=[])

    assert "ticker" in text
    assert "XPLG11" in text
    assert "volatility_ratio" in text
    assert "sharpe_ratio" in text
    assert "treynor_ratio" in text
    assert "beta_index" in text
