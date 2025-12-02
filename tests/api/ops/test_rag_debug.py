# tests/api/ops/test_rag_debug.py
import logging
from typing import Any, Dict

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.narrator.narrator as narrator_mod
from app.api.ops import rag_debug
from app.narrator.narrator import Narrator


class FakeClient:
    def __init__(self) -> None:
        self.last_prompt: str | None = None
        self.last_model: str | None = None

    def generate(
        self, prompt: str, model: str | None = None, stream: bool = False
    ) -> str:
        self.last_prompt = prompt
        self.last_model = model
        return "texto-gerado-pelo-fake-llm"


def _fake_policy_enabled() -> Dict[str, Any]:
    return {
        "llm_enabled": True,
        "shadow": False,
        "model": "dummy-model",
        "style": "executivo",
        "max_llm_rows": 10,
        "max_prompt_tokens": 4000,
        "max_output_tokens": 700,
    }


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(rag_debug.router)
    return app


def _patch_orchestrator(monkeypatch: pytest.MonkeyPatch) -> Dict[str, Any]:
    meta = {
        "planner": {
            "chosen": {
                "entity": "fiis_noticias",
                "intent": "fiis_noticias",
                "score": 1.0,
            }
        },
        "result_key": "dummy",
        "aggregates": {},
        "rag": {
            "enabled": True,
            "intent": "fiis_noticias",
            "entity": "fiis_noticias",
            "chunks": [{"text": "chunk-1"}],
        },
    }

    class DummyOrchestrator:
        def route_question(self, question: str):
            return {
                "status": {"reason": "ok", "message": "ok"},
                "results": {"dummy": [{"value": 1}]},
                "meta": meta,
            }

        def extract_identifiers(self, question: str) -> Dict[str, Any]:
            return {}

    monkeypatch.setattr(rag_debug, "orchestrator", DummyOrchestrator())
    return meta


def _patch_narrator(monkeypatch: pytest.MonkeyPatch) -> Narrator:
    monkeypatch.setattr(narrator_mod, "_load_narrator_policy", _fake_policy_enabled)
    narrator = Narrator(model="dummy-model", style="executivo")
    narrator.client = FakeClient()
    monkeypatch.setattr(rag_debug.ask_api, "_NARR", narrator)
    return narrator


def test_rag_debug_with_rag_enabled(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    meta = _patch_orchestrator(monkeypatch)
    _patch_narrator(monkeypatch)

    app = _build_app()
    client = TestClient(app)

    with caplog.at_level(logging.INFO):
        response = client.post(
            "/ops/rag_debug",
            json={"question": "quais são as últimas notícias?", "disable_rag": False},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["rag"]["enabled"] is True
    assert "rag_enabled=True" in caplog.text
    assert meta.get("rag") is not None


def test_rag_debug_with_rag_disabled(monkeypatch: pytest.MonkeyPatch):
    _patch_orchestrator(monkeypatch)
    narrator = _patch_narrator(monkeypatch)

    captured: Dict[str, Any] = {}

    def fake_build_prompt(
        question: str,
        facts: dict,
        meta: dict,
        style: str = "executivo",
        rag: dict | None = None,
    ) -> str:
        captured["rag"] = rag
        return "PROMPT-RAG-DEBUG"

    monkeypatch.setattr(narrator_mod, "build_prompt", fake_build_prompt)

    app = _build_app()
    client = TestClient(app)

    response = client.post(
        "/ops/rag_debug",
        json={"question": "quais são as últimas notícias?", "disable_rag": True},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["meta"].get("rag_debug_disable") is True
    assert payload["meta"]["rag"]["enabled"] is True
    assert captured.get("rag") is None
    assert narrator.client.last_model == "dummy-model"
