# tests/dev/test_config_guardrails.py

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import List

import pytest
from app.cache.rt_cache import CachePolicies
from app.context import context_manager as cm
from app.context.context_manager import ContextManager, DEFAULT_POLICY
from app.orchestrator import routing
from app.narrator import narrator as narrator_module
from app.planner import planner
from app.planner.ontology_loader import load_ontology
from app.rag import context_builder
from app.observability import runtime


@pytest.fixture
def quality_module(monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "quality_module_for_test", Path("app/api/ops/quality.py")
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "_QUALITY_LOADER_ERRORS", [])
    return module


@pytest.fixture
def ask_module(monkeypatch, tmp_path):
    import yaml

    policy_path = tmp_path / "narrator_fixture.yaml"
    policy_path.write_text(
        yaml.safe_dump(
            {
                "narrator": {
                    "model": "sirios-narrator:latest",
                    "llm_enabled": False,
                    "shadow": False,
                }
            }
        )
    )
    monkeypatch.setattr(narrator_module, "_NARRATOR_POLICY_PATH", policy_path)

    original_loader = narrator_module._load_narrator_policy

    def _patched_loader(path: str = str(policy_path)):
        return original_loader(path=str(policy_path))

    monkeypatch.setattr(narrator_module, "_load_narrator_policy", _patched_loader)
    module = importlib.import_module("app.api.ask")
    return importlib.reload(module)


class TestNarratorConfig:
    def test_load_narrator_flags_missing_file_raises(self, tmp_path, ask_module):
        missing_path = tmp_path / "narrator_missing.yaml"

        with pytest.raises(RuntimeError, match="Narrator policy ausente"):
            ask_module._load_narrator_flags(path=str(missing_path))

    def test_load_narrator_flags_non_mapping_yaml_raises(self, tmp_path, ask_module):
        yaml_path = tmp_path / "narrator_list.yaml"
        yaml_path.write_text("- 1\n- 2\n")

        with pytest.raises(RuntimeError, match="não é um dict"):
            ask_module._load_narrator_flags(path=str(yaml_path))

    @pytest.mark.parametrize(
        "content",
        [
            {},
            {"narrator": []},
        ],
    )
    def test_load_narrator_flags_malformed_block_raises(self, tmp_path, content, ask_module):
        yaml_path = tmp_path / "narrator_invalid.yaml"
        import yaml

        yaml_path.write_text(yaml.safe_dump(content))

        with pytest.raises(RuntimeError, match="policy malformada|model"):
            ask_module._load_narrator_flags(path=str(yaml_path))

    def test_load_narrator_flags_invalid_flag_types_raises(self, tmp_path, ask_module):
        yaml_path = tmp_path / "narrator_flags.yaml"
        import yaml

        yaml_path.write_text(
            yaml.safe_dump(
                {
                    "narrator": {
                        "model": "meu-modelo",
                        "llm_enabled": "true",
                        "shadow": "false",
                    }
                }
            )
        )

        with pytest.raises(RuntimeError, match="booleano"):
            ask_module._load_narrator_flags(path=str(yaml_path))

    def test_load_narrator_flags_happy_path(self, tmp_path, ask_module):
        yaml_path = tmp_path / "narrator_valid.yaml"
        import yaml

        yaml_path.write_text(
            yaml.safe_dump(
                {
                    "narrator": {
                        "model": "meu-modelo",
                        "llm_enabled": True,
                        "shadow": False,
                    }
                }
            )
        )

        result = ask_module._load_narrator_flags(path=str(yaml_path))

        assert set(result.keys()) == {"enabled", "shadow", "model"}
        assert isinstance(result["enabled"], bool)
        assert isinstance(result["shadow"], bool)
        assert isinstance(result["model"], str)
        assert result == {"enabled": True, "shadow": False, "model": "meu-modelo"}


class TestNarratorPolicyLoader:
    def _set_policy_path(self, monkeypatch, yaml_path: Path) -> None:
        monkeypatch.setattr(narrator_module, "_NARRATOR_POLICY_PATH", yaml_path)
        original_loader = narrator_module._load_narrator_policy

        def _patched_loader(path: str = str(yaml_path)):
            return original_loader(path=str(yaml_path))

        monkeypatch.setattr(narrator_module, "_load_narrator_policy", _patched_loader)

    def test_load_narrator_policy_missing_file_raises(self, tmp_path, caplog, monkeypatch):
        caplog.set_level(logging.ERROR)
        missing_path = tmp_path / "narrator_missing.yaml"
        self._set_policy_path(monkeypatch, missing_path)

        with pytest.raises(RuntimeError, match="Narrator policy ausente"):
            narrator_module._load_narrator_policy()

        assert any("Narrator policy ausente" in rec.getMessage() for rec in caplog.records)

    def test_load_narrator_policy_non_mapping_yaml_raises(self, tmp_path, caplog, monkeypatch):
        caplog.set_level(logging.ERROR)
        yaml_path = tmp_path / "narrator_list.yaml"
        yaml_path.write_text("- 1\n- 2\n")
        self._set_policy_path(monkeypatch, yaml_path)

        with pytest.raises(ValueError, match="mapeamento|inválida"):
            narrator_module._load_narrator_policy()

        assert any("esperado mapeamento" in rec.getMessage() for rec in caplog.records)

    @pytest.mark.parametrize(
        "content,match",
        [
            ({}, "ausente|mapeamento"),
            ({"narrator": []}, "mapeamento"),
            ({"narrator": "foo"}, "mapeamento"),
        ],
    )
    def test_load_narrator_policy_missing_or_invalid_block(
        self, tmp_path, caplog, content, match, monkeypatch
    ):
        caplog.set_level(logging.ERROR)
        yaml_path = tmp_path / "narrator_invalid.yaml"
        import yaml

        yaml_path.write_text(yaml.safe_dump(content))
        self._set_policy_path(monkeypatch, yaml_path)

        with pytest.raises((RuntimeError, ValueError), match=match):
            narrator_module._load_narrator_policy()

        assert any("narrator" in rec.getMessage() for rec in caplog.records)

    @pytest.mark.parametrize(
        "content,match",
        [
            ({"narrator": {"llm_enabled": True, "shadow": False}}, "model"),
            ({"narrator": {"model": "modelo", "shadow": False}}, "llm_enabled"),
            ({"narrator": {"model": "modelo", "llm_enabled": True}}, "shadow"),
        ],
    )
    def test_load_narrator_policy_missing_required_fields(
        self, tmp_path, caplog, content, match, monkeypatch
    ):
        caplog.set_level(logging.ERROR)
        yaml_path = tmp_path / "narrator_missing_fields.yaml"
        import yaml

        yaml_path.write_text(yaml.safe_dump(content))
        self._set_policy_path(monkeypatch, yaml_path)

        with pytest.raises(ValueError, match="obrigatório|malformada"):
            narrator_module._load_narrator_policy()

        assert any(match in rec.getMessage() for rec in caplog.records)

    @pytest.mark.parametrize(
        "key,value,match",
        [
            ("model", 123, "string"),
            ("model", "", "string"),
            ("llm_enabled", "true", "booleano"),
            ("shadow", "false", "booleano"),
        ],
    )
    def test_load_narrator_policy_invalid_required_fields(
        self, tmp_path, caplog, key, value, match, monkeypatch
    ):
        caplog.set_level(logging.ERROR)
        import yaml

        yaml_path = tmp_path / "narrator_required.yaml"
        yaml_path.write_text(
            yaml.safe_dump(
                {
                    "narrator": {
                        "model": "modelo",
                        "llm_enabled": True,
                        "shadow": False,
                    }
                }
            )
        )

        data = yaml.safe_load(yaml_path.read_text())
        data["narrator"][key] = value
        yaml_path.write_text(yaml.safe_dump(data))
        self._set_policy_path(monkeypatch, yaml_path)

        with pytest.raises(ValueError, match=match):
            narrator_module._load_narrator_policy()

        assert any(key in rec.getMessage() for rec in caplog.records)

    def test_load_narrator_policy_happy_path(self, tmp_path, monkeypatch):
        yaml_path = tmp_path / "narrator_valid.yaml"
        import yaml

        yaml_path.write_text(
            yaml.safe_dump(
                {
                    "narrator": {
                        "model": "mistral:instruct",
                        "llm_enabled": True,
                        "shadow": False,
                    }
                }
            )
        )
        self._set_policy_path(monkeypatch, yaml_path)

        result = narrator_module._load_narrator_policy()

        assert result == {
            "model": "mistral:instruct",
            "llm_enabled": True,
            "shadow": False,
        }


class TestOntologyLoader:
    def test_load_ontology_missing_file_raises(self, tmp_path: Path):
        missing_path = tmp_path / "missing_ontology.yaml"

        with pytest.raises(ValueError, match="ontologia ausente"):
            load_ontology(str(missing_path))

    def test_load_ontology_invalid_yaml_raises(self, tmp_path: Path):
        yaml_path = tmp_path / "ontology_list.yaml"
        yaml_path.write_text("- 1\n- 2\n")

        with pytest.raises(ValueError, match="ontologia inválido"):
            load_ontology(str(yaml_path))

    def test_load_ontology_happy_path(self, tmp_path: Path):
        yaml_path = tmp_path / "ontology_valid.yaml"
        import yaml

        yaml_path.write_text(
            yaml.safe_dump(
                {
                    "normalize": ["lower"],
                    "tokenization": {"split": r"\b"},
                    "weights": {"token": 1.0, "phrase": 2.5},
                    "intents": [
                        {
                            "name": "foo",
                            "tokens": {"include": ["a"], "exclude": ["b"]},
                            "phrases": {"include": ["ola"], "exclude": ["tchau"]},
                            "entities": ["fiis_precos"],
                        }
                    ],
                    "anti_tokens": {"foo": ["bar"]},
                }
            )
        )

        ontology = load_ontology(str(yaml_path))

        assert ontology.normalize == ["lower"]
        assert ontology.token_split == r"\b"
        assert ontology.weights == {"token": 1.0, "phrase": 2.5}
        assert ontology.anti_tokens == {"foo": ["bar"]}
        assert len(ontology.intents) == 1
        intent = ontology.intents[0]
        assert intent.name == "foo"
        assert intent.tokens_include == ["a"]
        assert intent.tokens_exclude == ["b"]
        assert intent.phrases_include == ["ola"]
        assert intent.phrases_exclude == ["tchau"]
        assert intent.entities == ["fiis_precos"]


class TestPlannerThresholds:
    @pytest.fixture(autouse=True)
    def _reset_cache(self, monkeypatch):
        monkeypatch.setattr(planner, "_THRESHOLDS_CACHE", None)

    def _write_thresholds(self, tmp_path: Path, config: dict) -> str:
        import yaml

        yaml_path = tmp_path / "thresholds.yaml"
        yaml_path.write_text(yaml.safe_dump(config))
        return str(yaml_path)

    def _base_thresholds(self) -> dict:
        return {
            "planner": {
                "thresholds": {
                    "defaults": {"min_score": 1.0, "min_gap": 0.5},
                    "apply_on": "base",
                },
                "rag": {
                    "enabled": False,
                    "k": 5,
                    "min_score": 0.2,
                    "weight": 0.3,
                    "re_rank": {"enabled": False, "mode": "blend", "weight": 0.25},
                },
            }
        }

    def test_load_thresholds_missing_file_raises(self, tmp_path):
        missing_path = tmp_path / "missing_thresholds.yaml"

        with pytest.raises(ValueError, match="Arquivo de thresholds ausente"):
            planner._load_thresholds(path=str(missing_path))

    def test_load_thresholds_invalid_yaml_raises(self, tmp_path):
        yaml_path = tmp_path / "thresholds_list.yaml"
        yaml_path.write_text("- 1\n- 2\n")

        with pytest.raises(ValueError, match="inválido"):
            planner._load_thresholds(path=str(yaml_path))

    @pytest.mark.parametrize(
        "config,expected",
        [
            ({"foo": "bar"}, "Bloco 'planner' obrigatório"),
            ({"planner": {}}, "obrigatórios"),
            ({"planner": {"thresholds": {}}}, "obrigatórios"),
        ],
    )
    def test_load_thresholds_missing_required_blocks(self, tmp_path, config, expected):
        yaml_path = self._write_thresholds(tmp_path, config)

        with pytest.raises(ValueError, match=expected):
            planner._load_thresholds(path=yaml_path)

    def test_load_thresholds_defaults_missing_min_values(self, tmp_path):
        config = self._base_thresholds()
        config["planner"]["thresholds"]["defaults"].pop("min_gap")
        yaml_path = self._write_thresholds(tmp_path, config)

        with pytest.raises(
            ValueError, match="thresholds.defaults deve definir min_score e min_gap"
        ):
            planner._load_thresholds(path=yaml_path)

    @pytest.mark.parametrize(
        "override_path,match",
        [
            (("planner", "rag", "k"), "inteiro positivo"),
            (("planner", "rag", "min_score"), "não pode ser negativo"),
            (("planner", "rag", "weight"), "não pode ser negativo"),
            (("planner", "rag", "re_rank", "weight"), "numérico"),
        ],
    )
    def test_load_thresholds_invalid_types_or_negative_values(
        self, tmp_path, override_path, match
    ):
        config = self._base_thresholds()
        target = config
        for key in override_path[:-1]:
            target = target[key]
        last_key = override_path[-1]
        if "k" in override_path:
            target[last_key] = "five"
        elif override_path[-2:] == ("re_rank", "weight"):
            target[last_key] = "bad"
        elif "min_score" in override_path or "weight" in override_path:
            target[last_key] = -1
        yaml_path = self._write_thresholds(tmp_path, config)

        with pytest.raises(ValueError, match=match):
            planner._load_thresholds(path=yaml_path)

    def test_load_thresholds_happy_path_and_cache(self, tmp_path):
        yaml_path = self._write_thresholds(tmp_path, self._base_thresholds())

        first = planner._load_thresholds(path=yaml_path)

        assert first["planner"]["thresholds"]["defaults"]["min_score"] == 1.0
        assert first["planner"]["thresholds"]["defaults"]["min_gap"] == 0.5
        assert first["planner"]["rag"]["k"] == 5
        assert first["planner"]["rag"]["re_rank"]["weight"] == 0.25

        second = planner._load_thresholds(path=yaml_path)

        assert first is second


class TestOrchestratorThresholds:
    @pytest.fixture(autouse=True)
    def _reset_cache(self, monkeypatch):
        monkeypatch.setattr(planner, "_THRESHOLDS_CACHE", None)

    def _write_thresholds(self, tmp_path: Path, config: dict) -> str:
        import yaml

        yaml_path = tmp_path / "orchestrator_thresholds.yaml"
        yaml_path.write_text(yaml.safe_dump(config))
        return str(yaml_path)

    def _base_thresholds(self) -> dict:
        return {
            "planner": {
                "thresholds": {
                    "defaults": {"min_score": 0.2, "min_gap": 0.1},
                    "apply_on": "base",
                },
                "rag": {
                    "enabled": False,
                    "k": 3,
                    "min_score": 0.1,
                    "weight": 0.2,
                    "re_rank": {"enabled": False, "mode": "blend", "weight": 0.1},
                },
            }
        }

    def test_orchestrator_thresholds_missing_file_logs_warning(self, tmp_path, caplog):
        missing_path = tmp_path / "missing_thresholds.yaml"
        caplog.set_level(logging.WARNING)

        result = routing._load_thresholds(str(missing_path))

        assert result == {}
        assert any("ausente" in rec.message for rec in caplog.records)

    def test_orchestrator_thresholds_invalid_yaml_logs_error(self, tmp_path, caplog):
        yaml_path = tmp_path / "invalid_thresholds.yaml"
        yaml_path.write_text("- 1\n- 2\n")
        caplog.set_level(logging.ERROR)

        result = routing._load_thresholds(str(yaml_path))

        assert result == {}
        assert any("inválido" in rec.message for rec in caplog.records)

    def test_orchestrator_thresholds_happy_path(self, tmp_path, caplog):
        yaml_path = self._write_thresholds(tmp_path, self._base_thresholds())
        caplog.set_level(logging.ERROR)

        result = routing._load_thresholds(str(yaml_path))

        assert result["defaults"]["min_score"] == 0.2
        assert result["defaults"]["min_gap"] == 0.1
        assert not any(rec.levelno >= logging.ERROR for rec in caplog.records)


class TestQualityConfigLoader:
    def _set_error_sink(self, module, monkeypatch) -> List[str]:
        errors: List[str] = []
        monkeypatch.setattr(module, "_QUALITY_LOADER_ERRORS", errors)
        return errors

    def test_load_candidate_missing_file_logs_warning(
        self, tmp_path, caplog, quality_module, monkeypatch
    ):
        caplog.set_level(logging.WARNING)
        errors = self._set_error_sink(quality_module, monkeypatch)

        missing_path = tmp_path / "missing_quality.yaml"
        result = quality_module._load_candidate(str(missing_path))

        assert result is None
        assert any("ausente" in rec.message for rec in caplog.records)
        assert any("ausente" in err for err in errors)

    def test_load_candidate_non_mapping_yaml_logs_error(
        self, tmp_path, caplog, quality_module, monkeypatch
    ):
        caplog.set_level(logging.ERROR)
        errors = self._set_error_sink(quality_module, monkeypatch)

        yaml_path = tmp_path / "quality_list.yaml"
        yaml_path.write_text("- 1\n- 2\n")

        result = quality_module._load_candidate(str(yaml_path))

        assert result is None
        assert any("mapeamento" in rec.message for rec in caplog.records)
        assert any("mapeamento" in err for err in errors)

    def test_load_candidate_malformed_schema(self, tmp_path, caplog, quality_module, monkeypatch):
        caplog.set_level(logging.ERROR)
        errors = self._set_error_sink(quality_module, monkeypatch)

        import yaml

        yaml_path = tmp_path / "quality_invalid.yaml"
        yaml_path.write_text(
            yaml.safe_dump(
                {
                    "targets": ["should", "be", "dict"],
                    "quality_gates": {"thresholds": []},
                }
            )
        )

        result = quality_module._load_candidate(str(yaml_path))

        assert result is None
        assert any("malformada" in err for err in errors)
        assert any("malformada" in rec.message for rec in caplog.records)

    def test_load_candidate_happy_path(self, tmp_path, caplog, quality_module, monkeypatch):
        caplog.set_level(logging.ERROR)
        errors = self._set_error_sink(quality_module, monkeypatch)

        import yaml

        yaml_path = tmp_path / "quality_valid.yaml"
        yaml_path.write_text(
            yaml.safe_dump(
                {
                    "targets": {
                        "min_top1_accuracy": 0.9,
                        "min_routed_rate": 0.8,
                        "min_top2_gap": 0.1,
                        "max_misses_absolute": 10,
                        "max_misses_ratio": 0.2,
                    }
                }
            )
        )

        result = quality_module._load_candidate(str(yaml_path))

        assert isinstance(result, dict)
        assert result.get("targets", {}).get("min_top1_accuracy") == 0.9
        assert errors == []
        assert not any(rec.levelno >= logging.ERROR for rec in caplog.records)


class TestContextPolicy:
    def test_load_context_policy_missing_file(self, tmp_path):
        missing_path = tmp_path / "context_missing.yaml"

        result = planner._load_context_policy(path=str(missing_path))

        assert result["context"] == {}
        assert result["planner"] == {}
        assert result["status"] == "missing"

    def test_load_context_policy_invalid_yaml(self, tmp_path):
        yaml_path = tmp_path / "context_invalid.yaml"
        yaml_path.write_text("- 1\n- 2\n")

        result = planner._load_context_policy(path=str(yaml_path))

        assert result["context"] == {}
        assert result["planner"] == {}
        assert result["status"] == "invalid"
        assert result.get("error")

    def test_load_context_policy_happy_path(self, tmp_path):
        yaml_path = tmp_path / "context_valid.yaml"
        import yaml

        yaml_path.write_text(
            yaml.safe_dump(
                {
                    "context": {
                        "planner": {
                            "enabled": True,
                            "allowed_entities": ["fiis_cadastro"],
                            "denied_entities": [],
                        }
                    }
                }
            )
        )

        result = planner._load_context_policy(path=str(yaml_path))

        assert result["status"] == "ok"
        assert isinstance(result["context"], dict)
        assert isinstance(result["planner"], dict)


class TestEntityConfigLoader:
    def test_load_entity_config_missing_logs_warning(self, tmp_path, caplog, monkeypatch):
        monkeypatch.setattr(routing, "_ENTITY_ROOT", tmp_path)
        caplog.set_level(logging.WARNING)

        result = routing._load_entity_config("foo")

        assert result == {}
        assert any("entity.yaml ausente" in rec.message for rec in caplog.records)

    def test_load_entity_config_invalid_yaml_logs_error(self, tmp_path, caplog, monkeypatch):
        entity_dir = tmp_path / "bar"
        entity_dir.mkdir(parents=True)
        yaml_path = entity_dir / "entity.yaml"
        yaml_path.write_text("- 1\n- 2\n")
        monkeypatch.setattr(routing, "_ENTITY_ROOT", tmp_path)
        caplog.set_level(logging.ERROR)

        result = routing._load_entity_config("bar")

        assert result == {}
        assert any("inválido" in rec.message for rec in caplog.records)

    def test_load_entity_config_happy_path(self, tmp_path, caplog, monkeypatch):
        entity_dir = tmp_path / "baz"
        entity_dir.mkdir(parents=True)
        yaml_path = entity_dir / "entity.yaml"
        yaml_path.write_text("foo: bar\n")
        monkeypatch.setattr(routing, "_ENTITY_ROOT", tmp_path)
        caplog.set_level(logging.ERROR)

        result = routing._load_entity_config("baz")

        assert result == {"foo": "bar"}
        assert not any(rec.levelno >= logging.ERROR for rec in caplog.records)


class TestCachePoliciesConfig:
    def test_cache_policies_missing_file(self, tmp_path, caplog):
        missing_path = tmp_path / "cache_missing.yaml"
        caplog.set_level(logging.WARNING)

        policies = CachePolicies(path=missing_path)

        assert policies._policies == {}
        assert policies._status == "missing"
        assert policies._error
        assert any("ausente" in rec.message for rec in caplog.records)

    def test_cache_policies_invalid_yaml(self, tmp_path, caplog):
        yaml_path = tmp_path / "cache_invalid.yaml"
        yaml_path.write_text("- 1\n- 2\n")
        caplog.set_level(logging.ERROR)

        policies = CachePolicies(path=yaml_path)

        assert policies._policies == {}
        assert policies._status == "invalid"
        assert policies._error
        assert any("Falha ao carregar" in rec.message for rec in caplog.records)

    def test_cache_policies_happy_path(self, tmp_path, caplog):
        import yaml

        yaml_path = tmp_path / "cache_valid.yaml"
        yaml_path.write_text(
            yaml.safe_dump({"policies": {"foo": {"ttl_seconds": 10, "scope": "pub"}}})
        )
        caplog.set_level(logging.WARNING)

        policies = CachePolicies(path=yaml_path)

        assert policies._status == "ok"
        assert policies._error is None
        assert policies.get("foo") == {"ttl_seconds": 10, "scope": "pub"}
        assert not any(rec.levelno >= logging.ERROR for rec in caplog.records)


class TestContextManagerPolicy:
    def _patch_loader(self, monkeypatch, path: Path):
        original = cm._load_policy

        def _override(path_override: str = str(path)):
            return original(path=path_override)

        monkeypatch.setattr(cm, "_load_policy", _override)

    def test_context_policy_missing_file(self, tmp_path, caplog, monkeypatch):
        missing_path = tmp_path / "context_missing.yaml"
        self._patch_loader(monkeypatch, missing_path)
        caplog.set_level(logging.WARNING)

        manager = ContextManager()

        assert manager._policy == DEFAULT_POLICY
        assert manager.policy_status == "missing"
        assert manager.policy_error
        assert any("DEFAULT_POLICY" in rec.message for rec in caplog.records)

    def test_context_policy_invalid_yaml(self, tmp_path, caplog, monkeypatch):
        yaml_path = tmp_path / "context_invalid.yaml"
        yaml_path.write_text("- 1\n- 2\n")
        self._patch_loader(monkeypatch, yaml_path)
        caplog.set_level(logging.ERROR)

        manager = ContextManager()

        assert manager._policy == DEFAULT_POLICY
        assert manager.policy_status == "invalid"
        assert manager.policy_error
        assert any("Falha ao carregar" in rec.message for rec in caplog.records)

    def test_context_policy_happy_path(self, tmp_path, caplog, monkeypatch):
        import yaml

        yaml_path = tmp_path / "context_valid.yaml"
        yaml_path.write_text(
            yaml.safe_dump(
                {
                    "context": {
                        "enabled": True,
                        "planner": {"enabled": False},
                        "narrator": {"max_turns": 5},
                    }
                }
            )
        )
        self._patch_loader(monkeypatch, yaml_path)
        caplog.set_level(logging.ERROR)

        manager = ContextManager()

        assert manager.enabled is True
        assert manager.policy_status == "ok"
        assert manager.policy_error is None
        assert manager.planner_policy.get("enabled") is False
        assert manager.narrator_policy.get("max_turns") == 5
        assert manager.narrator_policy.get("max_chars") == DEFAULT_POLICY["narrator"]["max_chars"]


class TestRagPolicyAndIndex:
    def test_load_rag_policy_missing_returns_empty(self, tmp_path, monkeypatch):
        missing_path = tmp_path / "missing_rag.yaml"
        monkeypatch.setattr(context_builder, "_RAG_POLICY_PATH", str(missing_path))

        result = context_builder.load_rag_policy()

        assert result == {}

    def test_load_rag_policy_invalid_raises(self, tmp_path, monkeypatch):
        yaml_path = tmp_path / "rag_invalid.yaml"
        yaml_path.write_text("- 1\n- 2\n")
        monkeypatch.setattr(context_builder, "_RAG_POLICY_PATH", str(yaml_path))

        with pytest.raises(RuntimeError, match="inválida"):
            context_builder.load_rag_policy()

    def test_build_context_missing_index(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            context_builder, "_RAG_INDEX_PATH", str(tmp_path / "missing_index.jsonl")
        )
        monkeypatch.setattr(
            context_builder,
            "load_rag_policy",
            lambda: {"rag": {"default": {"enabled": True}}},
        )

        result = context_builder.build_context(
            question="Pergunta?", intent="consulta", entity="entidade"
        )

        assert result["enabled"] is False
        assert "RAG index não encontrado" in (result.get("error") or "")


class TestObservabilityConfig:
    def test_env_missing_file_raises(self, tmp_path, monkeypatch, caplog):
        missing_path = tmp_path / "missing_observability.yaml"
        monkeypatch.setenv("OBSERVABILITY_CONFIG", str(missing_path))
        caplog.set_level(logging.ERROR)

        with pytest.raises(ValueError, match="observabilidade|ausente"):
            runtime.load_config()

        assert any("observabilidade" in rec.getMessage() for rec in caplog.records)

    def test_invalid_yaml_logs_and_raises(self, tmp_path, monkeypatch, caplog):
        invalid_path = tmp_path / "observability_invalid.yaml"
        invalid_path.write_text("- 1\n- 2\n")
        monkeypatch.setenv("OBSERVABILITY_CONFIG", str(invalid_path))
        caplog.set_level(logging.ERROR)

        with pytest.raises(ValueError, match="inválido|observabilidade"):
            runtime.load_config()

        assert any(rec.levelno >= logging.ERROR for rec in caplog.records)
        assert any(rec.exc_info for rec in caplog.records)

    def test_valid_minimal_config(self, tmp_path, monkeypatch):
        import yaml

        valid_path = tmp_path / "observability_valid.yaml"
        valid_path.write_text(
            yaml.safe_dump(
                {
                    "services": {
                        "gateway": {
                            "tracing": {"enabled": True},
                            "metrics": {},
                        }
                    },
                    "global": {"exporters": {"otlp_endpoint": "http://otel:4317"}},
                }
            )
        )
        monkeypatch.setenv("OBSERVABILITY_CONFIG", str(valid_path))

        cfg = runtime.load_config()

        assert isinstance(cfg, dict)
        assert set(cfg.keys()) >= {"services", "global"}
        assert cfg["services"]["gateway"]["tracing"]["enabled"] is True
