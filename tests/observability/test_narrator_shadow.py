import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

import app.observability.narrator_shadow as shadow


def _make_shadow_policy(tmp_path: Path, rate: float = 1.0) -> dict:
    base_dir = tmp_path / "shadow"
    return {
        "terms": [{"version": 1}],
        "narrator_shadow": {
            "enabled": True,
            "environment_allowlist": ["dev"],
            "private_entities": [
                "client_fiis_positions",
                "client_fiis_dividends_evolution",
                "client_fiis_performance_vs_benchmark",
            ],
            "sampling": {
                "default": {
                    "rate": rate,
                    "only_when_llm_used": True,
                    "only_when_answer_nonempty": True,
                    "always_on_llm_error": True,
                }
            },
            "redaction": {
                "mask_fields": ["document_number", "cpf", "cnpj", "email", "phone"],
                "max_rows_sample": 3,
                "max_chars": {
                    "answer_final": 1500,
                    "answer_baseline": 1500,
                    "prompt_preview": 3000,
                },
            },
            "storage": {
                "sink": "file",
                "file": {
                    "path": str(base_dir),
                    "rotation": "daily",
                    "filename_template": "narrator_shadow_%Y%m%d.jsonl",
                },
                "max_shadow_payload_kb": 64,
            },
        },
    }


def _make_narrator_policy() -> dict:
    return {
        "narrator": {
            "model": "sirios-narrator:latest",
            "llm_enabled": True,
            "shadow": True,
            "default": {"llm_enabled": True, "shadow": True, "model": "sirios"},
            "entities": {
                "fiis_noticias": {
                    "llm_enabled": True,
                    "shadow": True,
                    "rag_snippet_max_chars": 120,
                },
                "client_fiis_positions": {
                    "llm_enabled": True,
                    "shadow": True,
                    "rag_snippet_max_chars": 120,
                },
            },
        }
    }


def _shadow_file(tmp_path: Path) -> Path:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return tmp_path / "shadow" / f"narrator_shadow_{today}.jsonl"


def _base_event(entity: str) -> shadow.NarratorShadowEvent:
    return shadow.NarratorShadowEvent(
        environment="dev",
        request={
            "question": "qual o destaque de hoje?",
            "conversation_id": "c-1",
            "nickname": None,
            "client_id": "client-123",
        },
        routing={"intent": entity, "entity": entity, "planner_score": 1.0},
        facts={"entity": entity, "rows": [{"ticker": "HGLG11"}], "aggregates": {}},
        rag={
            "enabled": True,
            "collections": [entity],
            "chunks": [
                {
                    "source_id": "s1",
                    "path": "path/to/file",
                    "score": 0.5,
                    "snippet": "um trecho relevante de contexto para o narrador",
                }
            ],
        },
        narrator={
            "enabled": True,
            "shadow": True,
            "model": "sirios",
            "strategy": "llm_shadow",
            "latency_ms": 10,
            "effective_policy": {"rag_snippet_max_chars": 50, "llm_enabled": True, "shadow": True},
        },
        presenter={"answer_final": "resposta final", "answer_baseline": "baseline", "rows_used": 1, "style": "executivo"},
    )


def test_shadow_sampling_public_entity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    policy = _make_shadow_policy(tmp_path, rate=1.0)
    monkeypatch.setattr(shadow, "_load_shadow_policy", lambda path=None: policy)
    monkeypatch.setattr(shadow, "_load_narrator_policy", lambda path=None: _make_narrator_policy())
    monkeypatch.setattr(shadow.random, "random", lambda: 0.05)

    event = _base_event("fiis_noticias")
    shadow.collect_narrator_shadow(event)

    shadow_file = _shadow_file(tmp_path)
    assert shadow_file.is_file()
    content = shadow_file.read_text(encoding="utf-8").strip().splitlines()
    record = json.loads(content[0])

    assert record["request"]["question"] == event.request["question"]
    assert record["shadow"]["sampled"] is True
    assert record["shadow"]["reason"] in {"rate_hit", "llm_error_forced"}
    assert record["facts"]["rows_total"] == 1


def test_shadow_forces_on_llm_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    policy = _make_shadow_policy(tmp_path, rate=0.0)
    monkeypatch.setattr(shadow, "_load_shadow_policy", lambda path=None: policy)
    monkeypatch.setattr(shadow, "_load_narrator_policy", lambda path=None: _make_narrator_policy())
    monkeypatch.setattr(shadow.random, "random", lambda: 0.99)

    event = _base_event("fiis_noticias")
    event.narrator["error"] = "timeout"

    shadow.collect_narrator_shadow(event)

    record = json.loads(_shadow_file(tmp_path).read_text(encoding="utf-8").strip())
    assert record["shadow"]["reason"] == "llm_error_forced"
    assert record["narrator"]["error"] == "timeout"


def test_shadow_applies_redaction_for_private_entity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    policy = _make_shadow_policy(tmp_path, rate=1.0)
    monkeypatch.setattr(shadow, "_load_shadow_policy", lambda path=None: policy)
    monkeypatch.setattr(shadow, "_load_narrator_policy", lambda path=None: _make_narrator_policy())
    monkeypatch.setattr(shadow.random, "random", lambda: 0.01)

    event = _base_event("client_fiis_positions")
    event.facts["rows"] = [{"document_number": "12345678900", "ticker": "HGLG11"}]

    shadow.collect_narrator_shadow(event)

    record = json.loads(_shadow_file(tmp_path).read_text(encoding="utf-8").strip())
    masked_row = record["facts"]["rows_sample"][0]
    assert masked_row["document_number"].startswith("***")
    assert "document_number" in record["shadow"]["redaction_applied"]["masked_fields"]
