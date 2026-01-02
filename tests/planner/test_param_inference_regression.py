import pytest

from app.planner.param_inference import infer_params


DEFAULTS_PATH = "data/ops/param_inference.yaml"
ENTITY_PATH = "data/entities/fiis_dividends/fiis_dividends.yaml"
YIELD_ENTITY_PATH = "data/entities/fiis_yield_history/fiis_yield_history.yaml"


class TestIdentifierTicker:
    def test_ticker_from_identifiers_direct_key(self):
        identifiers = {"ticker": "HGLG11"}

        result = infer_params(
            "dividendos do HGLG11",
            intent="fiis_dividends",
            entity="fiis_dividends",
            entity_yaml_path=ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers=identifiers,
        )

        assert result == {
            "agg": "list",
            "window": "months:12",
            "limit": 24,  # default limit para fiis_dividends passou a 24
            "order": "desc",
            "ticker": "HGLG11",
        }

    def test_ticker_from_identifiers_single_list(self):
        identifiers = {"tickers": ["HGLG11"]}

        result = infer_params(
            "dividendos do HGLG11",
            intent="fiis_dividends",
            entity="fiis_dividends",
            entity_yaml_path=ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers=identifiers,
        )

        assert result == {
            "agg": "list",
            "window": "months:12",
            "limit": 24,  # default limit para fiis_dividends passou a 24
            "order": "desc",
            "ticker": "HGLG11",
        }

    def test_ambiguous_tickers_clear_value(self):
        identifiers = {"tickers": ["HGLG11", "HABT11"]}

        result = infer_params(
            "dividendos do HGLG11 ou HABT11",
            intent="fiis_dividends",
            entity="fiis_dividends",
            entity_yaml_path=ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers=identifiers,
        )

        assert result == {
            "agg": "list",
            "window": "months:12",
            "limit": 24,  # default limit para fiis_dividends passou a 24
            "order": "desc",
        }

    @pytest.mark.parametrize("identifiers", [{}, None])
    def test_no_ticker_does_not_break(self, identifiers):
        result = infer_params(
            "dividendos",
            intent="fiis_dividends",
            entity="fiis_dividends",
            entity_yaml_path=ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers=identifiers,
        )

        assert result == {
            "agg": "list",
            "window": "months:12",
            "limit": 24,  # default limit para fiis_dividends passou a 24
            "order": "desc",
        }


class TestContextIsolation:
    def test_context_source_is_ignored(self):
        # Mesmo com source: ["text", "context"], ticker só aparece quando presente no texto.
        result = infer_params(
            "dividendos",
            intent="fiis_dividends",
            entity="fiis_dividends",
            entity_yaml_path=ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers={},
        )

        assert result == {
            "agg": "list",
            "window": "months:12",
            "limit": 24,  # default limit para fiis_dividends passou a 24
            "order": "desc",
        }

    def test_missing_client_and_conversation_ids_are_noop(self):
        result = infer_params(
            "dividendos",
            intent="fiis_dividends",
            entity="fiis_dividends",
            entity_yaml_path=ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers={},
            client_id=None,
            conversation_id=None,
        )

        assert result == {
            "agg": "list",
            "window": "months:12",
            "limit": 24,  # default limit para fiis_dividends passou a 24
            "order": "desc",
        }


class TestYamlDefaults:
    def test_intent_defaults_are_applied(self):
        result = infer_params(
            "dividendos do HGLG11",
            intent="fiis_dividends",
            entity="fiis_dividends",
            entity_yaml_path=ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers=None,
        )

        assert result == {
            "agg": "list",
            "window": "months:12",
            "limit": 24,  # default limit para fiis_dividends passou a 24
            "order": "desc",
            "ticker": "HGLG11",
        }

    def test_invalid_window_uses_yaml_fallback(self):
        result = infer_params(
            "qual o DY do HGLG11 na janela de 99 meses?",
            intent="fiis_dividends",
            entity="fiis_dividends",
            entity_yaml_path=ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers=None,
        )

        assert result == {
            "agg": "list",
            "window": "months:12",
            "limit": 24,  # default limit para fiis_dividends passou a 24
            "order": "desc",
            "ticker": "HGLG11",
        }

    def test_limit_and_order_only_when_allowed(self):
        result = infer_params(
            "ultimo dividendo do HGLG11",
            intent="fiis_dividends",
            entity="fiis_dividends",
            entity_yaml_path=ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers={"ticker": "HGLG11"},
        )

        assert result == {
            "agg": "latest",
            "window": "count:1",
            "ticker": "HGLG11",
        }


class TestComputeOnReadMultiTicker:
    def test_multi_ticker_compute_on_read(self):
        identifiers = {"tickers": ["HGLG11", "MXRF11"]}

        result = infer_params(
            "compare o DY medio de HGLG11 e MXRF11 nos ultimos 12 meses",
            intent="fiis_yield_history",
            entity="fiis_yield_history",
            entity_yaml_path=YIELD_ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers=identifiers,
        )

        assert result == {
            "agg": "avg",
            "window": "months:12",
        }

    def test_single_ticker_compute_on_read(self):
        identifiers = {"tickers": ["HGLG11"]}

        result = infer_params(
            "DY acumulado do HGLG11 em 24 meses",
            intent="fiis_yield_history",
            entity="fiis_yield_history",
            entity_yaml_path=YIELD_ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers=identifiers,
        )

        assert result == {
            "agg": "sum",
            "window": "months:24",
            "ticker": "HGLG11",
        }

    def test_no_ticker_compute_on_read(self):
        identifiers = {"tickers": []}

        result = infer_params(
            "DY medio dos meus FIIs nos ultimos 12 meses",
            intent="fiis_yield_history",
            entity="fiis_yield_history",
            entity_yaml_path=YIELD_ENTITY_PATH,
            defaults_yaml_path=DEFAULTS_PATH,
            identifiers=identifiers,
        )

        assert result == {
            "agg": "avg",
            "window": "months:12",
        }
