import yaml

from scripts.ontology import lint_entity_yaml as lint


def _write_yaml(path, data):
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def _run_lint(tmp_path, monkeypatch, intents, config):
    entity_path = tmp_path / "entity.yaml"
    config_path = tmp_path / "ontology_lint.yaml"
    report_path = tmp_path / "report.md"

    _write_yaml(entity_path, {"intents": intents})
    _write_yaml(config_path, config)

    monkeypatch.setattr(lint, "ENTITY_PATH", entity_path)
    monkeypatch.setattr(lint, "CONFIG_PATH", config_path)
    monkeypatch.setattr(lint, "REPORT_PATH", report_path)

    result = lint.lint_entity_yaml()
    return result, report_path


def test_collision_gate_forbidden_token(monkeypatch, tmp_path):
    intents = [
        {"name": "intent_a", "tokens": {"include": ["historico"]}},
        {"name": "intent_b", "tokens": {"include": ["histórico"]}},
    ]
    config = {
        "ontology_lint": {
            "collision_gate": {
                "enabled": True,
                "max_intents_per_token": 3,
                "forbidden_tokens": ["historico"],
            }
        }
    }

    result, _ = _run_lint(tmp_path, monkeypatch, intents, config)

    violations = result["violations"]["collision_gate"]
    assert any(item["type"] == "forbidden_token" for item in violations)


def test_collision_gate_numeric_token(monkeypatch, tmp_path):
    intents = [{"name": "intent_a", "tokens": {"include": ["123"]}}]
    config = {
        "ontology_lint": {
            "collision_gate": {
                "enabled": True,
                "max_intents_per_token": 1,
                "forbid_numeric_tokens": True,
            }
        }
    }

    result, _ = _run_lint(tmp_path, monkeypatch, intents, config)

    violations = result["violations"]["collision_gate"]
    assert any(item["type"] == "numeric_token" for item in violations)


def test_collision_gate_short_token(monkeypatch, tmp_path):
    intents = [{"name": "intent_a", "tokens": {"include": ["ab"]}}]
    config = {
        "ontology_lint": {
            "collision_gate": {
                "enabled": True,
                "max_intents_per_token": 2,
                "min_token_len": 3,
                "short_token_allowlist": [],
            }
        }
    }

    result, _ = _run_lint(tmp_path, monkeypatch, intents, config)

    violations = result["violations"]["collision_gate"]
    assert any(item["type"] == "short_token" for item in violations)


def test_collision_gate_too_many_intents(monkeypatch, tmp_path):
    intents = [
        {"name": "intent_a", "tokens": {"include": ["shared"]}},
        {"name": "intent_b", "tokens": {"include": ["shared"]}},
    ]
    config = {
        "ontology_lint": {
            "collision_gate": {
                "enabled": True,
                "max_intents_per_token": 1,
                "allowlist": [],
            }
        }
    }

    result, _ = _run_lint(tmp_path, monkeypatch, intents, config)

    violations = result["violations"]["collision_gate"]
    assert any(item["type"] == "too_many_intents" for item in violations)


def test_collision_gate_pass(monkeypatch, tmp_path):
    intents = [
        {"name": "intent_a", "tokens": {"include": ["alpha"]}},
        {"name": "intent_b", "tokens": {"include": ["beta"]}},
    ]
    config = {
        "ontology_lint": {
            "collision_gate": {
                "enabled": True,
                "max_intents_per_token": 2,
                "allowlist": [],
                "forbidden_tokens": [],
                "short_token_allowlist": [],
            }
        }
    }

    result, report_path = _run_lint(tmp_path, monkeypatch, intents, config)

    assert result["violations"]["collision_gate"] == []
    assert report_path.exists()
