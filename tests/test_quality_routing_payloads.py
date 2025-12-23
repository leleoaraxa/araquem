import json
from pathlib import Path

import pytest

from app.api.ops.quality_contracts import (
    RoutingPayloadValidationError,
    validate_routing_payload_contract,
)


ROUTING_PATH = Path("data/ops/quality/routing_samples.json")


def test_routing_samples_use_suite_v2_contract():
    data = json.loads(ROUTING_PATH.read_text(encoding="utf-8"))

    assert data.get("type") == "routing"
    assert "samples" not in data

    payloads, suite_name, description, batch = validate_routing_payload_contract(data)

    assert isinstance(payloads, list) and payloads
    assert suite_name is None or isinstance(suite_name, str)
    assert isinstance(description, str)
    assert batch is None

    for sample in payloads:
        assert isinstance(sample["question"], str) and sample["question"].strip()
        expected_intent = sample.get("expected_intent")
        if expected_intent is not None:
            assert isinstance(expected_intent, str) and expected_intent.strip()
        expected_entity = sample.get("expected_entity")
        if expected_entity is not None:
            assert isinstance(expected_entity, str) and expected_entity.strip()


def test_routing_contract_validates_batch_metadata():
    payload = {
        "type": "routing",
        "suite": "demo",
        "description": "demo batch",
        "batch": {"id": "abc", "index": 2, "total": 3},
        "payloads": [
            {"question": "q1", "expected_intent": "i1", "expected_entity": "e1"},
            {"question": "q2", "expected_intent": "i1", "expected_entity": "e1"},
        ],
    }

    payloads, suite, description, batch = validate_routing_payload_contract(payload)

    assert len(payloads) == 2
    assert suite == "demo"
    assert description == "demo batch"
    assert batch and batch.id == "abc" and batch.index == 2 and batch.total == 3


def test_routing_contract_rejects_invalid_batch():
    payload = {
        "type": "routing",
        "suite": "demo",
        "batch": {"id": "", "index": 0, "total": 1},
        "payloads": [{"question": "q1", "expected_intent": "i1"}],
    }

    with pytest.raises(RoutingPayloadValidationError):
        validate_routing_payload_contract(payload)
