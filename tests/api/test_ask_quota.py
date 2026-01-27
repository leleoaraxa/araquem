import json

from fastapi.responses import JSONResponse

from app.api import ask as ask_module
from app.quota.ask_quota import QuotaDecision


def test_ask_returns_blocked_message_before_planner(monkeypatch):
    blocked_message = "Mensagem anon"

    def fake_enforce(*_args, **_kwargs):
        return QuotaDecision(allowed=False, remaining=0)

    def fake_policy():
        return {"enabled": True, "blocked_messages": {"anon": blocked_message}}

    def fail_planner(*_args, **_kwargs):
        raise AssertionError("planner should not be called")

    monkeypatch.setattr(ask_module, "enforce_ask_quota", fake_enforce)
    monkeypatch.setattr(ask_module, "load_ask_quota_policy", fake_policy)
    monkeypatch.setattr(ask_module.planner, "explain", fail_planner)

    payload = ask_module.AskPayload(
        question="Ola?",
        conversation_id="conv-1",
        nickname="Tester",
        client_id="",
        type_user="anon",
    )

    response = ask_module.ask(payload, explain=False)
    assert isinstance(response, JSONResponse)

    body = json.loads(response.body)
    assert body["answer"] == blocked_message
    assert body["status"] == "ok"
