import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_healthz_ok():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_metrics_exposes_prometheus_format():
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "sirios_requests_total" in r.text

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
