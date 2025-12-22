from unittest.mock import MagicMock

import pytest

from app.orchestrator import routing


def _plan(entity: str = "fiis_precos", bucket: str = "") -> dict:
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


def _orchestrator(plan: dict) -> routing.Orchestrator:
    planner = MagicMock()
    planner.explain.return_value = plan
    executor = MagicMock()
    return routing.Orchestrator(planner=planner, executor=executor)


def test_plan_hash_changes_with_inferred_params(monkeypatch: pytest.MonkeyPatch) -> None:
    plan = _plan()
    orchestrator = _orchestrator(plan)

    responses = [
        {"metric": "close_price"},
        {"metric": "close_price", "window": "30d"},
    ]
    monkeypatch.setattr(routing, "infer_params", lambda **kwargs: responses.pop(0))

    bundle_a = orchestrator.prepare_plan(
        "preço do HGLG11",
        client_id="c1",
        conversation_id="conv",
        planner_plan=plan,
    )
    bundle_b = orchestrator.prepare_plan(
        "preço do HGLG11",
        client_id="c1",
        conversation_id="conv",
        planner_plan=plan,
    )

    assert bundle_a["plan_hash"] != bundle_b["plan_hash"]


def test_plan_hash_changes_with_last_reference(monkeypatch: pytest.MonkeyPatch) -> None:
    plan = _plan()
    orchestrator = _orchestrator(plan)
    monkeypatch.setattr(routing, "infer_params", lambda **kwargs: {"metric": "close_price"})

    bundle_a = orchestrator.prepare_plan(
        "preço do fundo",
        client_id="c1",
        conversation_id="conv",
        planner_plan=plan,
        resolved_identifiers={"tickers": ["HGLG11"]},
    )
    bundle_b = orchestrator.prepare_plan(
        "preço do fundo",
        client_id="c1",
        conversation_id="conv",
        planner_plan=plan,
        resolved_identifiers={"tickers": ["MXRF11"]},
    )

    assert bundle_a["plan_hash"] != bundle_b["plan_hash"]


def test_plan_hash_changes_between_single_and_multi(monkeypatch: pytest.MonkeyPatch) -> None:
    plan = _plan()
    orchestrator = _orchestrator(plan)
    monkeypatch.setattr(routing, "infer_params", lambda **kwargs: {"metric": "close_price"})

    single = orchestrator.prepare_plan(
        "preço do HGLG11",
        client_id="c1",
        conversation_id="conv",
        planner_plan=plan,
        resolved_identifiers={"tickers": ["HGLG11"]},
    )
    multi = orchestrator.prepare_plan(
        "preço do HGLG11 e MXRF11",
        client_id="c1",
        conversation_id="conv",
        planner_plan=plan,
        resolved_identifiers={"tickers": ["HGLG11", "MXRF11"]},
    )

    assert single["plan_hash"] != multi["plan_hash"]
    assert not single["multi_ticker_enabled"]
    assert multi["multi_ticker_enabled"]


def test_bucket_disabled_does_not_enable_multi(monkeypatch: pytest.MonkeyPatch) -> None:
    plan = _plan(entity="client_fiis_dividends_evolution", bucket="A")
    orchestrator = _orchestrator(plan)
    monkeypatch.setattr(routing, "infer_params", lambda **kwargs: {})

    bundle = orchestrator.prepare_plan(
        "comparar HGLG11 e MXRF11",
        client_id="c1",
        conversation_id="conv",
        planner_plan=plan,
        resolved_identifiers={"tickers": ["HGLG11", "MXRF11"]},
    )

    assert bundle["multi_ticker_enabled"] is False
    assert bundle["multi_ticker_mode"] == "none"
