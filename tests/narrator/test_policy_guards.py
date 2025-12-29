# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict

import pytest

import app.narrator.narrator as narrator_mod
from app.narrator.narrator import Narrator


def _policy_with_guards() -> Dict[str, Any]:
    return {
        "llm_enabled": True,
        "shadow": False,
        "model": "dummy-model",
        "style": "executivo",
        "rewrite_only": False,
        "max_llm_rows": 5,
        "policy_guards": {
            "timeout_seconds": 6,
            "rewrite_only_default": True,
            "invariants_prohibited": [
                "change_numbers_or_dates",
                "change_tickers",
                "change_urls",
                "emit_markdown_tables",
                "emit_pipe_tables",
            ],
            "fail_closed": {
                "on_violation": "return_baseline",
                "on_error": "return_baseline",
                "on_timeout": "return_baseline",
            },
        },
    }


class GuardClient:
    def __init__(self, *, response: str | None = None, exc: Exception | None = None):
        self.response = response
        self.exc = exc

    def generate(self, *_: Any, **__: Any) -> str:
        if self.exc:
            raise self.exc
        return self.response or ""


@pytest.fixture(autouse=True)
def _patch_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(narrator_mod, "build_prompt", lambda **__: "PROMPT")
    monkeypatch.setattr(narrator_mod, "render_narrative", lambda *_: "")
    monkeypatch.setattr(narrator_mod, "counter", lambda *_, **__: None)
    monkeypatch.setattr(narrator_mod, "histogram", lambda *_, **__: None)


def _baseline_rows() -> Dict[str, Any]:
    return {"rows": [{"valor": "10"}]}


def _baseline_meta() -> Dict[str, Any]:
    return {"entity": "fiis_financials_risk", "intent": "fiis_financials_risk"}


def test_policy_violation_returns_baseline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(narrator_mod, "_load_narrator_policy", _policy_with_guards)
    narrator = Narrator(model="dummy-model", style="executivo")
    narrator.client = GuardClient(response="Valor alterado para 20")

    out = narrator.render(
        question="qual o valor?",
        facts=_baseline_rows(),
        meta=_baseline_meta(),
    )

    assert out["text"] == "- **valor**: 10"
    narrator_meta = out["meta"]["narrator"]
    assert narrator_meta["strategy"] == "policy_violation"
    assert "policy_violation" in narrator_meta["error"]


def test_timeout_returns_baseline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(narrator_mod, "_load_narrator_policy", _policy_with_guards)
    narrator = Narrator(model="dummy-model", style="executivo")
    narrator.client = GuardClient(exc=TimeoutError("expired"))

    out = narrator.render(
        question="qual o valor?",
        facts=_baseline_rows(),
        meta=_baseline_meta(),
    )

    assert out["text"] == "- **valor**: 10"
    narrator_meta = out["meta"]["narrator"]
    assert narrator_meta["strategy"] == "llm_failed"
    assert "timeout" in (narrator_meta.get("error") or "")
