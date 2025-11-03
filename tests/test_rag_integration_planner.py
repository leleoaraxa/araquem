# tests/test_rag_integration_planner.py

import copy
import pytest

from app.planner.planner import Planner, _THRESH_DEFAULTS

ONTO_PATH = "data/ontology/entity.yaml"


def _noop_emit_counter(*args, **kwargs):
    return None


def _stub_embedder():
    class _Embedder:
        def __init__(self, *args, **kwargs):
            pass

        def embed(self, texts):
            return [[0.1] * 2]

    return _Embedder()


def _patch_rag_config(monkeypatch, **overrides):
    from app.planner import planner as planner_module

    orig_load = planner_module._load_thresholds
    existing = orig_load()
    thresholds_cfg = copy.deepcopy((existing.get("planner") or {}).get("thresholds") or {})
    rag_cfg = dict(_THRESH_DEFAULTS["planner"]["rag"])
    rag_cfg.update(overrides)
    re_rank_cfg = dict(rag_cfg.get("re_rank") or {})
    re_rank_cfg.update({
        "enabled": overrides.get("enabled", re_rank_cfg.get("enabled", False)),
        "mode": overrides.get("re_rank_mode", "blend"),
        "weight": overrides.get("weight", re_rank_cfg.get("weight", 0.25)),
    })
    rag_cfg["re_rank"] = re_rank_cfg

    monkeypatch.setitem(
        planner_module._THRESH_DEFAULTS["planner"], "rag", dict(rag_cfg)
    )

    def _fake_load():
        return {"planner": {"thresholds": thresholds_cfg, "rag": dict(rag_cfg)}}

    monkeypatch.setattr(planner_module, "_load_thresholds", _fake_load)
    return planner_module


def test_rag_disabled_keeps_base_scores(monkeypatch):
    planner_module = _patch_rag_config(monkeypatch, enabled=False)

    planner = Planner(ONTO_PATH)
    result = planner.explain("Qual o CNPJ do HGLG11?")

    rag_block = result["explain"].get("rag")
    if rag_block is not None:
        assert rag_block.get("enabled") is False

    chosen_intent = result["chosen"]["intent"]
    base_score = result["intent_scores"][chosen_intent]
    final_score = result["chosen"]["score"]

    assert pytest.approx(final_score) == base_score


def test_rag_enabled_produces_entity_hints(monkeypatch):
    planner_module = _patch_rag_config(
        monkeypatch, enabled=True, k=1, min_score=0.0, weight=0.5
    )

    class _Store:
        def search_by_vector(self, vector, k, min_score):
            assert k == 1
            assert min_score == pytest.approx(0.0)
            return [{"doc_id": "entity-fiis-cadastro", "score": 0.8}]

    monkeypatch.setattr(planner_module, "cached_embedding_store", lambda path: _Store())
    monkeypatch.setattr(planner_module, "OllamaClient", lambda *a, **kw: _stub_embedder())
    monkeypatch.setattr("app.observability.metrics.emit_counter", _noop_emit_counter)

    planner = Planner(ONTO_PATH)
    result = planner.explain("Qual o CNPJ do HGLG11?")

    rag_block = result["explain"]["rag"]
    assert rag_block["enabled"] is True
    assert isinstance(rag_block["entity_hints"], dict)


def test_rag_weight_influences_final_score(monkeypatch):
    planner_module = _patch_rag_config(
        monkeypatch, enabled=True, k=1, min_score=0.0, weight=0.5
    )

    class _BoostedStore:
        def search_by_vector(self, vector, k, min_score):
            assert k == 1
            assert min_score == pytest.approx(0.0)
            return [{"doc_id": "entity-fiis-cadastro", "score": 5.0}]

    monkeypatch.setattr(
        planner_module, "cached_embedding_store", lambda path: _BoostedStore()
    )
    monkeypatch.setattr(planner_module, "OllamaClient", lambda *a, **kw: _stub_embedder())
    monkeypatch.setattr("app.observability.metrics.emit_counter", _noop_emit_counter)

    planner = Planner(ONTO_PATH)
    result = planner.explain("Qual o CNPJ do HGLG11?")

    chosen_intent = result["chosen"]["intent"]
    base_score = result["intent_scores"][chosen_intent]
    final_score = result["chosen"]["score"]

    assert final_score > base_score
    rag_block = result["explain"]["rag"]
    assert rag_block["used"] is True
    fusion_nodes = [n for n in result["explain"]["decision_path"] if n.get("stage") == "fuse"]
    assert fusion_nodes and fusion_nodes[0]["type"] == "rag_integration"
