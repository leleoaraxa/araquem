from unittest.mock import MagicMock

from app.orchestrator.routing import Orchestrator, extract_requested_metrics


def _make_orchestrator() -> Orchestrator:
    return Orchestrator(planner=MagicMock(), executor=MagicMock())


def test_extract_identifiers_single_ticker() -> None:
    orchestrator = _make_orchestrator()

    identifiers = orchestrator.extract_identifiers("como está o hglg11?")

    assert identifiers["ticker"] == "HGLG11"
    assert identifiers["tickers"] == ["HGLG11"]


def test_extract_identifiers_multiple_tickers() -> None:
    orchestrator = _make_orchestrator()

    identifiers = orchestrator.extract_identifiers(
        "compare HGLG11, mxrf11 e hglg11 ao mesmo tempo"
    )

    assert identifiers["ticker"] == "HGLG11"
    assert identifiers["tickers"] == ["HGLG11", "MXRF11"]


def test_extract_identifiers_without_ticker() -> None:
    orchestrator = _make_orchestrator()

    identifiers = orchestrator.extract_identifiers("explique beta")

    assert identifiers["ticker"] is None
    assert "tickers" not in identifiers


def test_extract_requested_metrics_multiple_matches() -> None:
    entity_conf = {
        "ask": {
            "metrics_synonyms": {
                "sharpe_ratio": ["sharpe", "indice de sharpe"],
                "beta_index": ["beta", "beta em relacao ao ifix"],
                "treynor_ratio": ["treynor", "indice de treynor"],
            }
        }
    }

    out = extract_requested_metrics(
        "compare Sharpe e Beta de HGLG11 e MXRF11", entity_conf
    )

    assert out == ["sharpe_ratio", "beta_index"]


def test_extract_requested_metrics_single_match() -> None:
    entity_conf = {
        "ask": {
            "metrics_synonyms": {
                "sharpe_ratio": ["sharpe", "indice de sharpe"],
                "beta_index": ["beta", "beta em relacao ao ifix"],
                "treynor_ratio": ["treynor", "indice de treynor"],
            }
        }
    }

    out = extract_requested_metrics("Indice de Treynor do HGLG11", entity_conf)

    assert out == ["treynor_ratio"]


def test_extract_requested_metrics_beta_only() -> None:
    entity_conf = {
        "ask": {
            "metrics_synonyms": {
                "sharpe_ratio": ["sharpe", "indice de sharpe"],
                "beta_index": ["beta", "beta em relacao ao ifix"],
                "treynor_ratio": ["treynor", "indice de treynor"],
            }
        }
    }

    out = extract_requested_metrics("beta do HGLG11", entity_conf)

    assert out == ["beta_index"]


def test_extract_requested_metrics_no_config() -> None:
    out = extract_requested_metrics("beta do HGLG11", {"ask": {}})

    assert out == []
