import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_healthz_ok():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_metrics_exposes_prometheus_format():
    warmup = client.get("/metrics")
    assert warmup.status_code == 200

    r = client.get("/metrics")
    assert r.status_code == 200
    text = r.text
    assert any(
        metric in text
        for metric in (
            "sirios_http_requests_total",
            "sirios_http_request_duration_seconds",
            "sirios_planner_top2_gap_histogram",
        )
    )

def test_ask_contract_validation():
    payload = {
        "question": "Qual o CNPJ do HGLG11?",
        "conversation_id": "abc-123",
        "nickname": "leleo",
        "client_id": "00000000000"
    }
    r = client.post("/ask", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["status"]["reason"] in ["unroutable", "ok"]
    assert "meta" in body
