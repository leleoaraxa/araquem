import pytest

from app.planner import planner as planner_module
from app.planner import ontology_loader


def test_bucket_index_includes_catalog_entities_even_if_not_in_intents(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path
    (root / "data" / "entities" / "extra").mkdir(parents=True)
    (root / "data" / "entities" / "in_intent").mkdir(parents=True)
    (root / "data" / "ontology").mkdir(parents=True)

    (root / "data" / "entities" / "catalog.yaml").write_text(
        "entities:\n  extra:\n    paths:\n      entity_yaml: data/entities/extra/extra.yaml\n  in_intent:\n    paths:\n      entity_yaml: data/entities/in_intent/in_intent.yaml\n",
        encoding="utf-8",
    )
    (root / "data" / "entities" / "extra" / "extra.yaml").write_text(
        "id: extra\nbucket: A\n",
        encoding="utf-8",
    )
    (root / "data" / "entities" / "in_intent" / "in_intent.yaml").write_text(
        "id: in_intent\nbucket: B\n",
        encoding="utf-8",
    )
    (root / "data" / "ontology" / "entity.yaml").write_text(
        "normalize: []\n"
        "tokenization:\n  split: \"\\\\s+\"\n"
        "weights:\n  token: 1.0\n  phrase: 2.0\n"
        "intents:\n"
        "  - name: intent_in\n"
        "    tokens:\n"
        "      include: []\n"
        "      exclude: []\n"
        "    phrases:\n"
        "      include: []\n"
        "      exclude: []\n"
        "    entities:\n"
        "      - in_intent\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(ontology_loader, "ROOT", root)
    onto = ontology_loader.load_ontology(str(root / "data" / "ontology" / "entity.yaml"))

    assert "extra" in onto.bucket_index["A"]["entities"]
    assert "in_intent" in onto.bucket_index["B"]["entities"]


def test_planner_bucket_filters_intents() -> None:
    planner = planner_module.Planner("data/ontology/entity.yaml")
    plan = planner.explain("teste", bucket_hint="A")

    assert plan["explain"]["bucket"]["selected"] == ""

    bucket_gate = next(
        item
        for item in plan["explain"]["decision_path"]
        if item.get("stage") == "bucket_gate"
    )
    assert bucket_gate["applied"] is True
    assert bucket_gate["filtered_count"] < len(planner.onto.intents)
    assert plan["explain"]["bucket"]["entities"]


def test_planner_bucket_neutral_keeps_all_intents() -> None:
    planner = planner_module.Planner("data/ontology/entity.yaml")
    plan = planner.explain("teste")

    bucket_gate = next(
        item
        for item in plan["explain"]["decision_path"]
        if item.get("stage") == "bucket_gate"
    )
    assert bucket_gate["applied"] is False
    assert bucket_gate["filtered_count"] == len(planner.onto.intents)


def test_planner_never_inferrs_bucket_from_text() -> None:
    planner = planner_module.Planner("data/ontology/entity.yaml")
    plan = planner.explain("pergunta com bucket A e bucket D no texto")

    assert plan["explain"]["bucket"]["selected"] == ""

    bucket_gate = next(
        item
        for item in plan["explain"]["decision_path"]
        if item.get("stage") == "bucket_gate"
    )
    assert bucket_gate["applied"] is False
