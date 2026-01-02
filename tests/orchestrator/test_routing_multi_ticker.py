from unittest.mock import MagicMock

import pytest

from app.orchestrator import routing
from app.observability import instrumentation


class _DummyBackend:
    def inc(self, name, labels, value=1.0):
        return None

    def observe(self, name, value, labels):
        return None

    def set_gauge(self, name, value, labels):
        return None

    def start_span(self, name, attributes):
        return object()

    def end_span(self, span, exc_type=None, exc_value=None, exc_tb=None):
        return None

    def set_span_attr(self, span, key, value):
        return None

    def span_trace_id(self, span):
        return "dummy-trace"

    def current_trace_id(self):
        return "dummy-trace"


def _plan_with_bucket(bucket: str = "", entity: str = "fiis_registrations") -> dict:
    return {
        "chosen": {
            "intent": "ticker_query",
            "entity": entity,
            "score": 1.0,
            "accepted": True,
            "context_allowed": True,
        },
        "explain": {
            "bucket": {"selected": bucket},
            "scoring": {"thresholds_applied": {"gap": 1.0}},
        },
    }


def test_route_question_runs_single_select_when_multi_supported_batch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instrumentation.set_backend(_DummyBackend())

    planner = MagicMock()
    planner.explain.return_value = _plan_with_bucket(
        bucket="", entity="fiis_quota_prices"
    )

    executor = MagicMock()
    captured_identifiers = {}

    def fake_build_select_for_entity(entity, identifiers, agg_params):
        captured_identifiers.update(
            {"ticker": identifiers.get("ticker"), "tickers": identifiers.get("tickers")}
        )
        return (
            "sql",
            {
                "tickers": identifiers.get("tickers"),
                "ticker": identifiers.get("ticker"),
            },
            "result_key",
            ["ticker", "value"],
        )

    monkeypatch.setattr(
        routing, "build_select_for_entity", fake_build_select_for_entity
    )

    executor.query.return_value = [{"ticker": "HGLG11", "value": "HGLG11"}]

    orchestrator = routing.Orchestrator(planner=planner, executor=executor)

    response = orchestrator.route_question("compare HGLG11 e MXRF11")

    assert executor.query.call_count == 1
    assert captured_identifiers.get("ticker") is None
    assert captured_identifiers.get("tickers") == ["HGLG11", "MXRF11"]
    assert response["results"]["result_key"] == [
        {"ticker": "HGLG11", "value": "HGLG11"}
    ]


def test_route_question_uses_first_ticker_when_multi_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instrumentation.set_backend(_DummyBackend())

    planner = MagicMock()
    planner.explain.return_value = _plan_with_bucket(
        bucket="", entity="client_fiis_dividends_evolution"
    )

    executor = MagicMock()
    captured_identifiers = {}

    def fake_build_select_for_entity(entity, identifiers, agg_params):
        captured_identifiers.update(identifiers)
        return (
            "sql",
            {
                "ticker": identifiers.get("ticker"),
                "tickers": identifiers.get("tickers"),
            },
            "result_key",
            ["ticker"],
        )

    monkeypatch.setattr(
        routing, "build_select_for_entity", fake_build_select_for_entity
    )

    executor.query.return_value = [{"ticker": "HGLG11"}]

    orchestrator = routing.Orchestrator(planner=planner, executor=executor)

    response = orchestrator.route_question(
        "compare HGLG11 e MXRF11",
        resolved_identifiers={
            "document_number": "00000000000",
            "tickers": ["HGLG11", "MXRF11"],
        },
    )

    assert executor.query.call_count == 1
    assert captured_identifiers.get("ticker") == "HGLG11"
    assert captured_identifiers.get("tickers") == ["HGLG11", "MXRF11"]
    assert response["results"]["result_key"] == [{"ticker": "HGLG11"}]
