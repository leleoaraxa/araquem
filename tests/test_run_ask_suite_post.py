from unittest import mock

from scripts.diagnostics.run_ask_suite import Config, _post_question


def test_post_question_includes_type_user():
    cfg = Config(
        base_url="http://localhost:8000",
        conversation_id="diagnostics",
        client_id="dev",
        nickname="diagnostics",
        type_user="diagnostics",
        timeout_s=1.0,
        out_dir="out",
        print_answer=False,
        explain=False,
    )
    response = mock.Mock()
    response.status_code = 200
    response.json.return_value = {"status": "ok"}

    with mock.patch("scripts.diagnostics.run_ask_suite.requests.post", return_value=response) as post:
        _post_question(cfg, "ping")

    assert post.call_count == 1
    sent_payload = post.call_args.kwargs["json"]
    assert sent_payload["type_user"] == "diagnostics"
