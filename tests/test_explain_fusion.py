import copy
import textwrap

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.planner.planner import Planner, _THRESH_DEFAULTS


class _DummyEmbedder:
    def __init__(self, *args, **kwargs):
        pass

    def embed(self, texts):
        return [[0.1] * 2]


def _configure_rag(monkeypatch, *, enabled=True, weight=0.5, hints=None, k=3, min_score=0.0):
    from app.planner import planner as planner_module

    existing = planner_module._load_thresholds()
    thresholds_cfg = copy.deepcopy((existing.get("planner") or {}).get("thresholds") or {})

    rag_cfg = dict(_THRESH_DEFAULTS["planner"]["rag"])
    rag_cfg.update({
        "enabled": enabled,
        "weight": weight,
        "k": k,
        "min_score": min_score,
    })

    def _fake_load():
        return {"planner": {"thresholds": thresholds_cfg, "rag": dict(rag_cfg)}}

    monkeypatch.setattr(planner_module, "_load_thresholds", _fake_load)
    monkeypatch.setitem(planner_module._THRESH_DEFAULTS["planner"], "rag", dict(rag_cfg))

    class _Store:
        def search_by_vector(self, vector, k, min_score):
            return [
                {"doc_id": f"entity-{key}", "score": value}
                for key, value in (hints or {}).items()
            ]

    monkeypatch.setattr(planner_module, "cached_embedding_store", lambda path: _Store())
    monkeypatch.setattr(planner_module, "OllamaClient", lambda *a, **kw: _DummyEmbedder())

    def _fake_hints(results):
        return dict(hints or {})

    monkeypatch.setattr(planner_module, "entity_hints_from_rag", _fake_hints)
    monkeypatch.setattr("app.observability.metrics.emit_counter", lambda *a, **k: None)

    return rag_cfg


@pytest.fixture
def simple_ontology(tmp_path):
    yaml_text = textwrap.dedent(
        """
        normalize: []
        tokenization:
          split: "\\\\b"
        weights:
          token: 1.0
          phrase: 1.0
        intents:
          - name: alpha
            tokens:
              include: [alpha]
              exclude: []
            phrases:
              include: []
              exclude: []
            entities: [entity_a]
          - name: beta
            tokens:
              include: [beta]
              exclude: []
            phrases:
              include: []
              exclude: []
            entities: [entity_b]
        anti_tokens: {}
        """
    ).strip()
    path = tmp_path / "ontology.yaml"
    path.write_text(yaml_text, encoding="utf-8")
    return str(path)


def _run_planner(monkeypatch, simple_ontology, *, hints=None, weight=0.5, enabled=True, question="alpha beta"):
    _configure_rag(monkeypatch, enabled=enabled, weight=weight, hints=hints)
    planner = Planner(simple_ontology)
    return planner.explain(question)


def test_explain_combined_block_structure(monkeypatch, simple_ontology):
    result = _run_planner(monkeypatch, simple_ontology, hints={"entity_b": 0.9}, weight=0.5)
    combined = result["explain"]["scoring"]["combined"]

    assert set(combined.keys()) == {"intent", "entity", "weight", "notes"}
    assert "linear_fusion" in combined["notes"]

    for bucket in ("intent", "entity"):
        entries = combined[bucket]
        assert isinstance(entries, list)
        for item in entries:
            assert set(item.keys()) == {"name", "base", "rag", "combined", "winner"}
            assert isinstance(item["name"], str)
            assert isinstance(item["winner"], bool)
            for key in ("base", "rag", "combined"):
                assert isinstance(item[key], (int, float))


def test_combined_equals_linear_formula(monkeypatch, simple_ontology):
    weight = 0.4
    result = _run_planner(monkeypatch, simple_ontology, hints={"entity_b": 0.8}, weight=weight)
    combined = result["explain"]["scoring"]["combined"]
    assert combined["weight"] == pytest.approx(weight)

    for item in combined["intent"]:
        expected = item["base"] * (1 - weight) + item["rag"] * weight
        assert abs(item["combined"] - expected) < 1e-9

    for item in combined["entity"]:
        expected = item["base"] * (1 - weight) + item["rag"] * weight
        assert abs(item["combined"] - expected) < 1e-9


def test_top2_gap_updates_after_fusion(monkeypatch, simple_ontology):
    result = _run_planner(monkeypatch, simple_ontology, hints={"entity_b": 1.0}, weight=0.6)
    combined = result["explain"]["scoring"]["combined"]
    ordered = sorted(combined["intent"], key=lambda item: item["combined"], reverse=True)
    assert len(ordered) >= 2
    expected_gap = ordered[0]["combined"] - ordered[1]["combined"]
    assert result["explain"]["scoring"]["intent_top2_gap"] == pytest.approx(expected_gap)
    assert ordered[0]["winner"] is True
    assert ordered[1]["winner"] is False


def test_fusion_summary_and_decision_path(monkeypatch, simple_ontology):
    weight = 0.55
    result = _run_planner(monkeypatch, simple_ontology, hints={"entity_b": 0.9}, weight=weight)
    explain = result["explain"]
    fusion = explain["fusion"]

    assert fusion["enabled"] is True
    assert fusion["used"] is True
    assert fusion["weight"] == pytest.approx(weight)
    assert fusion["affected_entities"]

    fusion_nodes = [
        node for node in explain["decision_path"] if node.get("stage") == "fuse"
    ]
    assert any(node.get("type") == "rag_fusion" for node in fusion_nodes)
    fusion_node = next(node for node in fusion_nodes if node.get("type") == "rag_fusion")
    assert fusion_node["weight"] == pytest.approx(weight)
    assert fusion_node["affected"] == len(fusion["affected_entities"])

    result_off = _run_planner(
        monkeypatch,
        simple_ontology,
        hints=None,
        weight=weight,
        enabled=False,
    )
    explain_off = result_off["explain"]
    fusion_off = explain_off["fusion"]
    assert fusion_off["enabled"] is False or (
        fusion_off["weight"] == pytest.approx(0.0) and fusion_off["used"] is False
    )

    combined_off = explain_off["scoring"]["combined"]
    assert combined_off["weight"] == pytest.approx(0.0)
    for bucket in ("intent", "entity"):
        for item in combined_off[bucket]:
            assert item["rag"] == pytest.approx(0.0)
            assert item["combined"] == pytest.approx(item["base"])


def test_no_contract_change_for_results(monkeypatch):
    class DummyPlanner:
        def explain(self, question):
            return {
                "normalized": question,
                "tokens": [],
                "intent_scores": {"alpha": 1.0},
                "details": {},
                "chosen": {
                    "intent": "alpha",
                    "entity": "entity_a",
                    "score": 1.0,
                    "accepted": True,
                },
                "explain": {"scoring": {"intent_top2_gap": 0.0}},
            }

    class DummyOrchestrator:
        def extract_identifiers(self, question):
            return {}

        def route_question(self, question):
            return {"results": {"table": [{"value": 1}]}}

    def fake_read_through(cache, policies, entity, identifiers, fetch):
        return {"value": {"table": [{"value": 1}]}, "cached": False, "key": "table", "ttl": None}

    monkeypatch.setattr("app.api.ask.planner", DummyPlanner())
    monkeypatch.setattr("app.api.ask.orchestrator", DummyOrchestrator())
    monkeypatch.setattr("app.api.ask.read_through", fake_read_through)
    monkeypatch.setattr("app.api.ask.infer_params", lambda **kwargs: {})
    monkeypatch.setattr("app.api.ask.counter", lambda *a, **k: None)
    monkeypatch.setattr("app.api.ask.histogram", lambda *a, **k: None)
    monkeypatch.setattr("app.api.ask._explain_analytics", lambda **kwargs: {"summary": {}, "details": {}})
    monkeypatch.setattr("app.api.ask.psycopg.connect", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))

    client = TestClient(app)
    payload = {
        "question": "teste",
        "conversation_id": "conv",
        "nickname": "tester",
        "client_id": "00000000000",
    }

    resp_no = client.post("/ask", json=payload)
    resp_yes = client.post("/ask?explain=true", json=payload)

    assert resp_no.status_code == 200
    assert resp_yes.status_code == 200

    body_no = resp_no.json()
    body_yes = resp_yes.json()

    assert body_no["results"] == body_yes["results"]
    assert body_no["results"] == {"table": [{"value": 1}]}
    assert body_no["meta"]["result_key"] == body_yes["meta"]["result_key"] == "table"
    assert set(body_no["meta"].keys()) == set(body_yes["meta"].keys())
