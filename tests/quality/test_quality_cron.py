from scripts.quality.quality_push_cron import (
    validate_projection_payload,
    validate_routing_payload,
)


def test_validate_routing_ok():
    ok, err = validate_routing_payload(
        {
            "type": "routing",
            "samples": [
                {
                    "question": "q",
                    "expected_intent": "cadastro",
                }
            ],
        }
    )
    assert ok and err is None


def test_validate_routing_bad():
    ok, err = validate_routing_payload(
        {
            "type": "routing",
            "samples": [
                {
                    "expected_intent": "x",
                }
            ],
        }
    )
    assert not ok and err


def test_validate_projection_ok():
    ok, err = validate_projection_payload(
        {
            "type": "projection",
            "entity": "fiis_cadastro",
            "result_key": "view_fiis_cadastro",
            "must_have_columns": ["ticker"],
            "samples": [{"question": "q"}],
        }
    )
    assert ok and err is None


def test_validate_projection_bad():
    ok, err = validate_projection_payload(
        {
            "type": "projection",
            "samples": [{"question": "q"}],
        }
    )
    assert not ok and err
