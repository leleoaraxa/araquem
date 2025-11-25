# tests/dev/test_config_guardrails.py

import logging
from pathlib import Path

import pytest

from app.api.ask import _load_narrator_flags
from app.cache.rt_cache import CachePolicies
from app.context import context_manager as cm
from app.context.context_manager import ContextManager, DEFAULT_POLICY
from app.orchestrator import routing
from app.planner import planner
from app.rag import context_builder


class TestNarratorConfig:
    def test_load_narrator_flags_missing_file_raises(self, tmp_path):
        missing_path = tmp_path / "narrator_missing.yaml"

        with pytest.raises(RuntimeError, match="Narrator policy ausente"):
            _load_narrator_flags(path=str(missing_path))

    def test_load_narrator_flags_non_mapping_yaml_raises(self, tmp_path):
        yaml_path = tmp_path / "narrator_list.yaml"
        yaml_path.write_text("- 1\n- 2\n")

        with pytest.raises(RuntimeError, match="não é um dict"):
            _load_narrator_flags(path=str(yaml_path))

    @pytest.mark.parametrize(
        "content",
        [
            {},
            {"narrator": []},
        ],
    )
    def test_load_narrator_flags_malformed_block_raises(self, tmp_path, content):
        yaml_path = tmp_path / "narrator_invalid.yaml"
        import yaml

        yaml_path.write_text(yaml.safe_dump(content))

        with pytest.raises(RuntimeError, match="policy malformada|model"):
            _load_narrator_flags(path=str(yaml_path))

    def test_load_narrator_flags_invalid_flag_types_raises(self, tmp_path):
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
            _load_narrator_flags(path=str(yaml_path))

    def test_load_narrator_flags_happy_path(self, tmp_path):
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

        result = _load_narrator_flags(path=str(yaml_path))

        assert set(result.keys()) == {"enabled", "shadow", "model"}
        assert isinstance(result["enabled"], bool)
        assert isinstance(result["shadow"], bool)
        assert isinstance(result["model"], str)
        assert result == {"enabled": True, "shadow": False, "model": "meu-modelo"}


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
