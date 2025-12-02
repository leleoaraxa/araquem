import copy

import pytest

from app.context.context_manager import (
    ContextManager,
    DEFAULT_LAST_REFERENCE_POLICY,
    DEFAULT_POLICY,
)


@pytest.fixture
def base_policy():
    policy = copy.deepcopy(DEFAULT_POLICY)
    policy["enabled"] = True
    policy["last_reference"] = {
        **DEFAULT_LAST_REFERENCE_POLICY,
        "enable_last_ticker": True,
        "allowed_entities": ["alpha"],
        "max_age_turns": 2,
    }
    return policy


def test_resolve_last_reference_disabled(base_policy):
    policy = copy.deepcopy(base_policy)
    policy["last_reference"]["enable_last_ticker"] = False
    manager = ContextManager(policy=policy)

    result = manager.resolve_last_reference(
        client_id="c1",
        conversation_id="conv1",
        entity="alpha",
        identifiers={},
    )

    assert result["last_reference_used"] is False
    assert result["reason"] == "last_reference_disabled"
    assert result["identifiers_resolved"] == {}


def test_resolve_last_reference_entity_not_allowed(base_policy):
    manager = ContextManager(policy=base_policy)
    manager.update_last_reference(
        client_id="c1",
        conversation_id="conv1",
        ticker="HGLG11",
        entity="alpha",
        intent="alpha",
    )

    result = manager.resolve_last_reference(
        client_id="c1",
        conversation_id="conv1",
        entity="beta",
        identifiers={},
    )

    assert result["last_reference_used"] is False
    assert result["reason"] == "entity_not_allowed"
    assert result["identifiers_resolved"] == {}


def test_resolve_last_reference_applies_recent_value(base_policy):
    manager = ContextManager(policy=base_policy)
    manager.append_turn(
        client_id="c1",
        conversation_id="conv1",
        role="user",
        content="Pergunta",
    )
    manager.update_last_reference(
        client_id="c1",
        conversation_id="conv1",
        ticker="HGLG11",
        entity="alpha",
        intent="alpha",
    )

    result = manager.resolve_last_reference(
        client_id="c1",
        conversation_id="conv1",
        entity="alpha",
        identifiers={},
    )

    assert result["last_reference_used"] is True
    assert result["last_reference_ticker"] == "HGLG11"
    assert result["reason"] == "last_reference_applied"
    assert result["identifiers_resolved"].get("ticker") == "HGLG11"


def test_resolve_last_reference_expired(base_policy):
    policy = copy.deepcopy(base_policy)
    policy["last_reference"]["max_age_turns"] = 1
    manager = ContextManager(policy=policy)

    manager.append_turn(
        client_id="c1",
        conversation_id="conv1",
        role="user",
        content="Pergunta",
    )
    manager.update_last_reference(
        client_id="c1",
        conversation_id="conv1",
        ticker="HGLG11",
        entity="alpha",
        intent="alpha",
    )
    # avança o contador lógico de turns além do limite
    manager.append_turn(
        client_id="c1",
        conversation_id="conv1",
        role="assistant",
        content="Resposta",
    )
    manager.append_turn(
        client_id="c1",
        conversation_id="conv1",
        role="assistant",
        content="Outra resposta",
    )

    result = manager.resolve_last_reference(
        client_id="c1",
        conversation_id="conv1",
        entity="alpha",
        identifiers={},
    )

    assert result["last_reference_used"] is False
    assert result["reason"] == "expired"
    assert "ticker" not in result["identifiers_resolved"]
