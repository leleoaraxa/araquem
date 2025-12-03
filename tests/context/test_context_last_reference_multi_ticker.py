import copy

import pytest

from app.context.context_manager import (
    ContextManager,
    DEFAULT_LAST_REFERENCE_POLICY,
    DEFAULT_POLICY,
)


@pytest.fixture
def bucket_policy():
    policy = copy.deepcopy(DEFAULT_POLICY)
    policy["enabled"] = True
    policy["last_reference"] = {
        **DEFAULT_LAST_REFERENCE_POLICY,
        "enable_last_ticker": True,
        "allowed_entities": ["alpha"],
        "max_age_turns": 4,
        "bucket_ttl": {"A": 4, "B": 2, "C": 3, "D": 1},
    }
    return policy


def test_inherit_multi_ticker_same_bucket(bucket_policy):
    manager = ContextManager(policy=bucket_policy)
    manager.append_turn(
        client_id="c1",
        conversation_id="conv1",
        role="user",
        content="Pergunta A",
        meta={"bucket": "A"},
    )
    manager.append_turn(
        client_id="c1",
        conversation_id="conv1",
        role="assistant",
        content="Resposta",
        meta={"bucket": "A"},
    )
    manager.update_last_reference(
        client_id="c1",
        conversation_id="conv1",
        tickers=["HGLG11", "MXRF11"],
        entity="alpha",
        intent="alpha",
        bucket="A",
    )

    manager.append_turn(
        client_id="c1",
        conversation_id="conv1",
        role="user",
        content="E o overview deles?",
        meta={"bucket": "A"},
    )

    result = manager.resolve_last_reference(
        client_id="c1",
        conversation_id="conv1",
        entity="alpha",
        bucket="A",
        identifiers={},
    )

    assert result["last_reference_used"] is True
    assert result["identifiers_resolved"].get("tickers") == ["HGLG11", "MXRF11"]


def test_ttl_expired_per_bucket(bucket_policy):
    policy = copy.deepcopy(bucket_policy)
    policy["last_reference"]["bucket_ttl"] = {"A": 1}
    manager = ContextManager(policy=policy)

    manager.append_turn(
        client_id="c1",
        conversation_id="conv1",
        role="user",
        content="Pergunta",
        meta={"bucket": "A"},
    )
    manager.append_turn(
        client_id="c1",
        conversation_id="conv1",
        role="assistant",
        content="Resposta",
        meta={"bucket": "A"},
    )
    manager.update_last_reference(
        client_id="c1",
        conversation_id="conv1",
        tickers=["HGLG11"],
        entity="alpha",
        intent="alpha",
        bucket="A",
    )
    manager.append_turn(
        client_id="c1",
        conversation_id="conv1",
        role="assistant",
        content="Passou um turno",
        meta={"bucket": "A"},
    )
    manager.append_turn(
        client_id="c1",
        conversation_id="conv1",
        role="user",
        content="Nova pergunta sem ticker",
        meta={"bucket": "A"},
    )

    result = manager.resolve_last_reference(
        client_id="c1",
        conversation_id="conv1",
        entity="alpha",
        bucket="A",
        identifiers={},
    )

    assert result["last_reference_used"] is False
    assert result["reason"] == "expired"
    assert "tickers" not in result["identifiers_resolved"]


def test_different_bucket_no_inheritance(bucket_policy):
    manager = ContextManager(policy=bucket_policy)
    manager.append_turn(
        client_id="c1",
        conversation_id="conv1",
        role="user",
        content="Pergunta A",
        meta={"bucket": "A"},
    )
    manager.append_turn(
        client_id="c1",
        conversation_id="conv1",
        role="assistant",
        content="Resposta",
        meta={"bucket": "A"},
    )
    manager.update_last_reference(
        client_id="c1",
        conversation_id="conv1",
        tickers=["HGLG11"],
        entity="alpha",
        intent="alpha",
        bucket="A",
    )
    manager.append_turn(
        client_id="c1",
        conversation_id="conv1",
        role="user",
        content="Pergunta bucket C",
        meta={"bucket": "C"},
    )

    result = manager.resolve_last_reference(
        client_id="c1",
        conversation_id="conv1",
        entity="alpha",
        bucket="C",
        identifiers={},
    )

    assert result["last_reference_used"] is False
    assert "tickers" not in result["identifiers_resolved"]


def test_explicit_ticker_wins(bucket_policy):
    manager = ContextManager(policy=bucket_policy)
    manager.append_turn(
        client_id="c1",
        conversation_id="conv1",
        role="user",
        content="Pergunta A",
        meta={"bucket": "A"},
    )
    manager.append_turn(
        client_id="c1",
        conversation_id="conv1",
        role="assistant",
        content="Resposta",
        meta={"bucket": "A"},
    )
    manager.update_last_reference(
        client_id="c1",
        conversation_id="conv1",
        tickers=["HGLG11"],
        entity="alpha",
        intent="alpha",
        bucket="A",
    )
    manager.append_turn(
        client_id="c1",
        conversation_id="conv1",
        role="user",
        content="E o MXRF11?",
        meta={"bucket": "A"},
    )

    result = manager.resolve_last_reference(
        client_id="c1",
        conversation_id="conv1",
        entity="alpha",
        bucket="A",
        identifiers={"tickers": ["MXRF11"]},
    )

    assert result["last_reference_used"] is False
    assert result["identifiers_resolved"].get("tickers") == ["MXRF11"]
