from pathlib import Path

import pytest

from app.api.ask import _load_narrator_flags
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

        with pytest.raises(ValueError, match="thresholds.defaults deve definir min_score e min_gap"):
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
    def test_load_thresholds_invalid_types_or_negative_values(self, tmp_path, override_path, match):
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
        monkeypatch.setattr(context_builder, "_RAG_INDEX_PATH", str(tmp_path / "missing_index.jsonl"))
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
