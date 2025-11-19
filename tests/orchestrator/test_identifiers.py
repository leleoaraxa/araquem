from unittest.mock import MagicMock

from app.orchestrator.routing import Orchestrator


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
