import json
from pathlib import Path

from app.presenter import presenter


class DummyNarrator:
    """Narrador determinístico para testar validações de rewrite_only."""

    def __init__(self, text: str):
        self.text = text
        self.style = "test"
        self.policy = {"default": {"llm_enabled": True, "shadow": False, "max_llm_rows": 10, "rewrite_only": True}}

    def get_effective_policy(self, entity):
        return {
            "llm_enabled": True,
            "shadow": False,
            "max_llm_rows": 10,
            "rewrite_only": True,
            "model": "stub",
        }

    def render(self, question, facts, meta):
        # Simula LLM retornando texto sem âncoras
        return {
            "text": self.text,
            "strategy": "llm",
            "meta": {"narrator": {"strategy": "llm", "latency_ms": 1, "model": "stub"}},
        }


def _load_response(filename: str):
    path = Path(__file__).parent.parent / filename
    return json.loads(path.read_text())


def _present_from_response(response: dict, narrator_text: str):
    plan = {"chosen": {"intent": "fiis_processos", "entity": "fiis_processos", "score": 1.0}}
    meta = response.get("meta") or {}
    results = response.get("results") or {}
    narrator = DummyNarrator(narrator_text)

    return presenter.present(
        question="existe processos?",
        plan=plan,
        orchestrator_results=results,
        meta=meta,
        identifiers={},
        aggregates={},
        narrator=narrator,
        explain=True,
    )


def test_rewrite_only_preserves_evidence_and_fallback_absence_message():
    response = _load_response("response_A.md")
    result = _present_from_response(response, "não encontrei processos")

    # Narrator negativo deve ser ignorado; baseline precisa conter âncora factual
    assert "1000681" in result.answer
    assert result.answer == result.baseline_answer


def test_rewrite_only_fallbacks_when_answer_unanchored():
    response = _load_response("response_B.md")
    result = _present_from_response(response, "Aqui estão informações gerais.")

    # Resposta genérica sem âncoras deve cair no baseline determinístico
    assert result.answer == result.baseline_answer
    assert any(str(row.get("process_number")) in result.answer for row in result.facts.rows)
