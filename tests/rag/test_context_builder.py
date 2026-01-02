# tests/rag/test_context_builder.py
# -*- coding: utf-8 -*-
import copy
from typing import Any, Dict, List

import pytest

from app.rag import context_builder


# ---------------------------------------------------------------------------
# Fixtures de política (espelham o rag.yaml atual, de forma mínima)
# ---------------------------------------------------------------------------


@pytest.fixture
def rag_policy_base() -> Dict[str, Any]:
    """Policy de RAG equivalente ao rag.yaml atual, em forma de dict.

    Observação: Não incluímos a chave 'terms' aqui porque ela não é usada
    pelo context_builder.
    """
    return {
        "version": 1,
        "profiles": {
            "default": {
                "k": 5,
                "min_score": 0.20,
                "weight": {"bm25": 0.70, "semantic": 0.30},
                "tie_break": "semantic",
                "max_context_chars": 12000,
            },
            "ambiguous": {
                "k": 8,
                "min_score": 0.15,
                "weight": {"bm25": 0.50, "semantic": 0.50},
                "tie_break": "semantic",
            },
        },
        "entities": {
            "fiis_news": {
                "k": 5,
                "min_score": 0.20,
                "collections": ["fiis_news"],
            }
        },
        "routing": {
            "deny_intents": [
                "client_fiis_positions",
                "fiis_registrations",
                "fiis_quota_prices",
                "fiis_dividends",
                "fiis_rankings",
                "fiis_real_estate",
                "fiis_legal_proceedings",
                "fiis_financials_snapshot",
                "fiis_financials_revenue_schedule",
                "fiis_financials_risk",
            ],
            "allow_intents": [
                "fiis_news",
            ],
            "notes": "RAG restrito a conteúdos textuais; dados tabulares seguem via SQL.",
        },
    }


@pytest.fixture
def rag_policy_with_entities(rag_policy_base: Dict[str, Any]) -> Dict[str, Any]:
    """Variante de policy com entities explícito, para exercitar esse ramo."""
    policy = copy.deepcopy(rag_policy_base)
    # Simula estrutura com seção "rag" + "entities"
    policy["rag"] = {
        "profiles": copy.deepcopy(policy["profiles"]),
        "entities": {
            "fiis_news": {
                # Poderia ter overrides específicos aqui (k, min_score, collections, etc.).
            }
        },
    }
    return policy


# ---------------------------------------------------------------------------
# Testes para get_rag_policy
# ---------------------------------------------------------------------------


def test_get_rag_policy_returns_disabled_when_no_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sem policy carregada (load_rag_policy retorna {})-> snapshot disabled."""

    monkeypatch.setattr(context_builder, "load_rag_policy", lambda: {})

    snapshot = context_builder.get_rag_policy(
        entity="fiis_news",
        intent="fiis_news",
        compute_mode=None,
        has_ticker=False,
        policy=None,
    )

    assert snapshot == {"enabled": False, "reason": "policy_missing"}


def test_get_rag_policy_denies_intents_in_deny_list(
    rag_policy_base: Dict[str, Any],
) -> None:
    """Intents listadas em deny_intents devem ter RAG desabilitado."""

    snapshot = context_builder.get_rag_policy(
        entity="fiis_registrations",
        intent="fiis_registrations",
        compute_mode=None,
        has_ticker=False,
        policy=rag_policy_base,
    )

    assert snapshot == {"enabled": False, "reason": "intent_denied"}


def test_get_rag_policy_denies_intents_not_in_allow_list(
    rag_policy_base: Dict[str, Any],
) -> None:
    """Se há allow_intents, intents fora dessa lista devem ser negadas."""

    snapshot = context_builder.get_rag_policy(
        entity="fiis_rankings",
        intent="alguma_coisa",
        compute_mode=None,
        has_ticker=False,
        policy=rag_policy_base,
    )

    assert snapshot == {"enabled": False, "reason": "intent_not_allowed"}


def test_get_rag_policy_allows_fiis_news_with_profiles(
    rag_policy_base: Dict[str, Any],
) -> None:
    """Com a policy atual, apenas fiis_news tem RAG habilitado."""

    snapshot = context_builder.get_rag_policy(
        entity="fiis_news",
        intent="fiis_news",
        compute_mode=None,
        has_ticker=True,
        policy=rag_policy_base,
    )

    assert snapshot["enabled"] is True
    assert snapshot["collections"] == ["fiis_news"]
    assert snapshot["has_ticker"] is True


def test_get_rag_policy_entity_not_configured_returns_reason() -> None:
    """Quando não há default nem profiles, a entity desconhecida deve ser negada."""

    minimal_policy = {
        "rag": {
            "entities": {"known": {"collections": ["known"]}},
        }
    }

    snapshot = context_builder.get_rag_policy(
        entity="unknown",
        intent="unknown",
        compute_mode=None,
        has_ticker=False,
        policy=minimal_policy,
    )

    assert snapshot == {"enabled": False, "reason": "entity_not_configured"}


# ---------------------------------------------------------------------------
# Testes para build_context
# ---------------------------------------------------------------------------


def test_build_context_returns_disabled_when_rag_not_enabled(
    rag_policy_base: Dict[str, Any],
) -> None:
    """Quando a policy desabilita RAG, build_context deve devolver enabled=False
    sem tentar acessar embeddings ou store.
    """
    ctx = context_builder.build_context(
        question="qual o administrador do HGLG11?",
        intent="fiis_registrations",  # está em deny_intents
        entity="fiis_registrations",
        policy=rag_policy_base,
    )

    assert ctx["enabled"] is False
    assert ctx["chunks"] == []
    assert ctx["total_chunks"] == 0
    assert ctx["intent"] == "fiis_registrations"
    assert ctx["entity"] == "fiis_registrations"
    assert ctx["policy"]["reason"] == "intent_denied"


class _DummyStore:
    """Store de embeddings fake para testes de build_context."""

    def __init__(self, results: List[Dict[str, Any]]) -> None:
        self._results = results
        self.last_call: Dict[str, Any] = {}

    def search_by_vector(
        self,
        vector: List[float],
        k: int,
        min_score: float | None = None,
    ) -> List[Dict[str, Any]]:
        self.last_call = {"vector": vector, "k": k, "min_score": min_score}
        return self._results


class _DummyEmbedder:
    """Cliente Ollama fake usado apenas para gerar um vetor não vazio."""

    def __init__(self) -> None:
        self.last_texts: List[str] = []

    def embed(self, texts: List[str]) -> List[List[float]]:
        self.last_texts = texts
        # Retorna um vetor simples (apenas para não cair no erro embedding-vector-empty)
        return [[0.1, 0.2, 0.3]]


def test_build_context_enabled_for_fiis_news(
    monkeypatch: pytest.MonkeyPatch, rag_policy_base: Dict[str, Any]
) -> None:
    """Quando RAG está habilitado, build_context deve consultar o store e
    retornar chunks normalizados e snapshot da policy.
    """
    # Arrange: cria resultados fake de busca
    fake_results = [
        {
            "text": "Notícia 1 sobre HGLG11",
            "score": 0.95,
            "doc_id": "doc-1",
            "chunk_id": "chunk-1",
            "collection": "fiis_news",
        },
        {
            "content": "Notícia 2 sobre FIIs logísticos",
            "score": 0.88,
            "doc_id": "doc-2",
            "chunk_id": "chunk-2",
            "collection": "fiis_news",
        },
    ]
    dummy_store = _DummyStore(fake_results)
    dummy_embedder = _DummyEmbedder()

    # Monkeypatch do cached_embedding_store e do OllamaClient no módulo context_builder
    monkeypatch.setattr(
        context_builder,
        "cached_embedding_store",
        lambda path: dummy_store,
    )
    monkeypatch.setattr(
        context_builder,
        "OllamaClient",
        lambda: dummy_embedder,
    )

    # Act
    ctx = context_builder.build_context(
        question="quais são as últimas notícias do HGLG11?",
        intent="fiis_news",
        entity="fiis_news",
        policy=rag_policy_base,
    )

    # Assert: RAG habilitado e chunks retornados
    assert ctx["enabled"] is True
    assert ctx["intent"] == "fiis_news"
    assert ctx["entity"] == "fiis_news"

    # Verifica que os chunks foram normalizados com 'text' e 'score'
    assert ctx["total_chunks"] == 2
    assert len(ctx["chunks"]) == 2
    assert all("text" in c for c in ctx["chunks"])
    assert all("score" in c for c in ctx["chunks"])

    # Policy snapshot deve refletir o profile default da policy base
    policy_snapshot = ctx["policy"]
    assert policy_snapshot["max_chunks"] == 5
    # min_score vem da policy default (0.20)
    assert pytest.approx(policy_snapshot["min_score"], rel=1e-6) == 0.20
    # max_tokens deriva de max_context_chars (12000), se parseado com sucesso
    assert policy_snapshot.get("max_tokens") in (None, 12000)
    # collections deve refletir a config da entity fiis_news
    assert policy_snapshot["collections"] == ["fiis_news"]

    # Garante que o embedder foi chamado com a pergunta
    assert dummy_embedder.last_texts == ["quais são as últimas notícias do HGLG11?"]

    # Garante que o store recebeu os parâmetros esperados
    assert dummy_store.last_call["k"] == 5
    assert pytest.approx(dummy_store.last_call["min_score"], rel=1e-6) == 0.20


def test_build_context_returns_policy_on_error(
    monkeypatch: pytest.MonkeyPatch, rag_policy_base: Dict[str, Any]
) -> None:
    """Mesmo em erros de busca, o contexto deve incluir snapshot da policy."""

    class _ErrorStore(_DummyStore):
        def search_by_vector(
            self, vector: List[float], k: int, min_score: float | None = None
        ) -> List[Dict[str, Any]]:
            raise RuntimeError("store-broke")

    monkeypatch.setattr(context_builder.Path, "exists", lambda self: True)
    monkeypatch.setattr(
        context_builder,
        "cached_embedding_store",
        lambda path: _ErrorStore([]),
    )
    monkeypatch.setattr(context_builder, "OllamaClient", lambda: _DummyEmbedder())

    ctx = context_builder.build_context(
        question="quais são as últimas notícias do HGLG11?",
        intent="fiis_news",
        entity="fiis_news",
        policy=rag_policy_base,
    )

    assert ctx["enabled"] is False
    assert ctx["policy"]["reason"] == "error"
    assert ctx["policy"]["collections"] == ["fiis_news"]
    assert ctx["policy"]["max_chunks"] == 5
    assert pytest.approx(ctx["policy"]["min_score"], rel=1e-6) == 0.20
    assert ctx["policy"].get("max_tokens") in (None, 12000)
    assert "store-broke" in (ctx["error"] or "")
