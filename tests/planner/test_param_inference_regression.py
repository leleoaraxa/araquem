import pytest

from app.planner.param_inference import infer_params


DEFAULTS_PATH = "data/ops/param_inference.yaml"
ENTITY_PATH = "data/entities/fiis_dividendos/entity.yaml"


class TestIdentifierTicker:
    def test_ticker_from_identifiers_direct_key(self):
        identifiers = {"ticker": "HGLG11"}

        result = infer_params(
            "dividendos do HGLG11",
            intent="fiis_dividendos",
            entity="fiis_dividendos",
            entity_yaml_path=ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers=identifiers,
        )

        assert result == {
            "agg": "list",
            "window": "months:12",
            "limit": 10,
            "order": "desc",
            "ticker": "HGLG11",
        }

    def test_ticker_from_identifiers_single_list(self):
        identifiers = {"tickers": ["HGLG11"]}

        result = infer_params(
            "dividendos do HGLG11",
            intent="fiis_dividendos",
            entity="fiis_dividendos",
            entity_yaml_path=ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers=identifiers,
        )

        assert result == {
            "agg": "list",
            "window": "months:12",
            "limit": 10,
            "order": "desc",
            "ticker": "HGLG11",
        }

    def test_ambiguous_tickers_clear_value(self):
        identifiers = {"tickers": ["HGLG11", "HABT11"]}

        result = infer_params(
            "dividendos do HGLG11 ou HABT11",
            intent="fiis_dividendos",
            entity="fiis_dividendos",
            entity_yaml_path=ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers=identifiers,
        )

        assert result == {
            "agg": "list",
            "window": "months:12",
            "limit": 10,
            "order": "desc",
        }

    @pytest.mark.parametrize("identifiers", [{}, None])
    def test_no_ticker_does_not_break(self, identifiers):
        result = infer_params(
            "dividendos",
            intent="fiis_dividendos",
            entity="fiis_dividendos",
            entity_yaml_path=ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers=identifiers,
        )

        assert result == {
            "agg": "list",
            "window": "months:12",
            "limit": 10,
            "order": "desc",
        }


class TestContextIsolation:
    def test_context_source_is_ignored(self):
        # Mesmo com source: ["text", "context"], ticker só vem dos identifiers.
        result = infer_params(
            "dividendos",
            intent="fiis_dividendos",
            entity="fiis_dividendos",
            entity_yaml_path=ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers={},
        )

        assert result == {
            "agg": "list",
            "window": "months:12",
            "limit": 10,
            "order": "desc",
        }

    def test_missing_client_and_conversation_ids_are_noop(self):
        result = infer_params(
            "dividendos",
            intent="fiis_dividendos",
            entity="fiis_dividendos",
            entity_yaml_path=ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers={},
            client_id=None,
            conversation_id=None,
        )

        assert result == {
            "agg": "list",
            "window": "months:12",
            "limit": 10,
            "order": "desc",
        }


class TestYamlDefaults:
    def test_intent_defaults_are_applied(self):
        result = infer_params(
            "dividendos do HGLG11",
            intent="fiis_dividendos",
            entity="fiis_dividendos",
            entity_yaml_path=ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers=None,
        )

        assert result == {
            "agg": "list",
            "window": "months:12",
            "limit": 10,
            "order": "desc",
        }

    def test_invalid_window_uses_yaml_fallback(self):
        result = infer_params(
            "qual o DY do HGLG11 na janela de 99 meses?",
            intent="fiis_dividendos",
            entity="fiis_dividendos",
            entity_yaml_path=ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers=None,
        )

        assert result == {
            "agg": "list",
            "window": "months:12",
            "limit": 10,
            "order": "desc",
        }

    def test_limit_and_order_only_when_allowed(self):
        result = infer_params(
            "ultimo dividendo do HGLG11",
            intent="fiis_dividendos",
            entity="fiis_dividendos",
            entity_yaml_path=ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers={"ticker": "HGLG11"},
        )

        assert result == {
            "agg": "latest",
            "window": "count:1",
            "ticker": "HGLG11",
        }

