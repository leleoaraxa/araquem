import json
from pathlib import Path

from app.api.ops.quality_contracts import validate_routing_payload_contract


ROUTING_PATH = Path("data/ops/quality/routing_samples.json")


def test_routing_samples_use_suite_v2_contract():
    data = json.loads(ROUTING_PATH.read_text(encoding="utf-8"))

    assert data.get("type") == "routing"
    assert "samples" not in data

    payloads, suite_name, description = validate_routing_payload_contract(data)

    assert isinstance(payloads, list) and payloads
    assert suite_name is None or isinstance(suite_name, str)
    assert isinstance(description, str)

    for sample in payloads:
        assert isinstance(sample["question"], str) and sample["question"].strip()
        expected_intent = sample.get("expected_intent")
        if expected_intent is not None:
            assert isinstance(expected_intent, str) and expected_intent.strip()
        expected_entity = sample.get("expected_entity")
        if expected_entity is not None:
            assert isinstance(expected_entity, str) and expected_entity.strip()
