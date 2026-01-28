from scripts.diagnostics.run_ask_suite import _evaluate_suite_status, _parse_suite_data


def test_parse_suite_dict_payloads():
    data = {
        "suite": "demo",
        "description": "demo",
        "payloads": [
            {"question": "q1", "expected_intent": "i1", "expected_entity": "e1"}
        ],
    }
    parsed = _parse_suite_data("demo_suite.json", data)

    assert parsed["suite"] == "demo"
    assert parsed["description"] == "demo"
    assert parsed["payloads"][0]["question"] == "q1"
    assert parsed["payloads"][0]["expected_intent"] == "i1"
    assert parsed["payloads"][0]["expected_entity"] == "e1"


def test_parse_suite_type_payloads():
    data = {
        "type": "routing",
        "payloads": [{"question": "q1"}],
    }
    parsed = _parse_suite_data("routing.json", data)

    assert parsed["suite"] == "routing"
    assert parsed["payloads"][0]["question"] == "q1"


def test_parse_suite_list_payloads():
    data = [{"question": "q1"}, {"question": "q2"}]
    parsed = _parse_suite_data("list_suite.json", data)

    assert parsed["suite"] == "list_suite"
    assert len(parsed["payloads"]) == 2


def test_parse_expected_from_expected_block():
    data = {
        "payloads": [
            {
                "question": "q1",
                "expected": {"route": {"intent": "i1", "entity": "e1"}},
            }
        ]
    }
    parsed = _parse_suite_data("expected.json", data)

    payload = parsed["payloads"][0]
    assert payload["expected_intent"] == "i1"
    assert payload["expected_entity"] == "e1"


def test_evaluate_suite_status_pass_fail_skip_error():
    row = {
        "http_status": 200,
        "request_error": None,
        "expected_intent": "intent",
        "expected_entity": "entity",
        "match_intent": True,
        "match_entity": True,
    }
    assert _evaluate_suite_status(row)["suite_status"] == "PASS"

    row = {
        "http_status": 200,
        "request_error": None,
        "expected_intent": "intent",
        "expected_entity": "entity",
        "match_intent": True,
        "match_entity": False,
    }
    assert _evaluate_suite_status(row)["suite_status"] == "FAIL"

    row = {
        "http_status": 200,
        "request_error": None,
        "expected_intent": None,
        "expected_entity": None,
        "match_intent": None,
        "match_entity": None,
    }
    assert _evaluate_suite_status(row)["suite_status"] == "SKIP"

    row = {
        "http_status": 500,
        "request_error": None,
        "expected_intent": "intent",
        "expected_entity": "entity",
        "match_intent": False,
        "match_entity": False,
    }
    assert _evaluate_suite_status(row)["suite_status"] == "ERROR"

    row = {
        "http_status": 200,
        "request_error": "timeout",
        "expected_intent": "intent",
        "expected_entity": "entity",
        "match_intent": False,
        "match_entity": False,
    }
    assert _evaluate_suite_status(row)["suite_status"] == "ERROR"
