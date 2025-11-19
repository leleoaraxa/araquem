# tests/orchestrator/test_rag_integration_orchestrator.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, List

import pytest

from app.orchestrator import routing


class FakePlanner:
    """Planner fake que sempre retorna fiis_noticias com score alto."""

    def explain(self, question: str) -> Dict[str, Any]:
        return {
            "chosen": {
                "intent": "fiis_noticias",
                "entity": "fiis_noticias",
                "score": 1.0,
            },
            "explain": {},
        }


class FakeExecutor:
    """Executor fake que não bate no banco."""

    def query(
        self,
        sql: str,
        params: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        # Não precisamos de dados reais aqui; o foco é integrar RAG.
        return []


def test_route_question_attaches_rag_context(monkeypatch: pytest.MonkeyPatch) -> None:
    """Quando o planner escolhe fiis_noticias, o Orchestrator deve
    chamar build_rag_context e anexar meta.rag.
    """

    # 1) Neutraliza thresholds: sem gates bloqueando o fluxo
    monkeypatch.setattr(routing, "_load_thresholds", lambda path: {})

    # 2) Neutraliza métricas/observability (counters/histograms)
    monkeypatch.setattr(routing, "counter", lambda *a, **k: None)
    monkeypatch.setattr(routing, "histogram", lambda *a, **k: None)

    # 3) Neutraliza tracing (span OTEL)
    @contextmanager
    def dummy_trace(*args: Any, **kwargs: Any):
        class DummySpan:
            pass

        span = DummySpan()
        yield span

    monkeypatch.setattr(routing, "start_trace", dummy_trace)
    monkeypatch.setattr(routing, "set_trace_attribute", lambda *a, **k: None)
    monkeypatch.setattr(routing, "get_trace_id", lambda span: None)

    planner = FakePlanner()
    executor = FakeExecutor()
    orch = routing.Orchestrator(planner=planner, executor=executor)

    # 4) Evita bater no builder real / DB
    def fake_build_select_for_entity(
        entity: str,
        identifiers: Dict[str, Any],
        agg_params: Dict[str, Any] | None = None,
    ):
        # sql, params, result_key, return_columns
        return "SELECT 1", {}, "fiis_noticias_view", []

    monkeypatch.setattr(
        routing,
        "build_select_for_entity",
        fake_build_select_for_entity,
    )
    monkeypatch.setattr(routing, "format_rows", lambda rows, cols: [])

    # 5) Captura chamada ao builder de RAG
    captured: Dict[str, Any] = {}

    def fake_build_rag_context(
        question: str,
        intent: str,
        entity: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        captured["question"] = question
        captured["intent"] = intent
        captured["entity"] = entity
        return {
            "enabled": True,
            "question": question,
            "intent": intent,
            "entity": entity,
            "chunks": [],
            "total_chunks": 0,
            "policy": {"max_chunks": 5, "collections": ["fiis_noticias"]},
        }

    # Patch do alias importado no routing.py (build_rag_context)
    monkeypatch.setattr(routing, "build_rag_context", fake_build_rag_context)

    # 6) Executa o fluxo
    out = orch.route_question("quais são as últimas notícias do HGLG11?", explain=False)

    meta = out.get("meta") or {}
    rag = meta.get("rag")

    # 7) Verifica que meta.rag existe e segue o contrato mínimo
    assert isinstance(rag, dict)
    assert rag.get("enabled") is True
    assert rag.get("intent") == "fiis_noticias"
    assert rag.get("entity") == "fiis_noticias"

    # Garante que o Orchestrator passou os parâmetros corretos para o builder de RAG
    assert captured["question"] == "quais são as últimas notícias do HGLG11?"
    assert captured["intent"] == "fiis_noticias"
    assert captured["entity"] == "fiis_noticias"
