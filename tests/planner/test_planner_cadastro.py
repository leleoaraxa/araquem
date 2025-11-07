import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ask_cadastro_minimum_contract():
    payload = {
        "question": "Qual o CNPJ do HGLG11?",
        "conversation_id": "conv-1",
        "nickname": "leleo",
        "client_id": "00000000000",
    }
    r = client.post("/ask", json=payload)
    assert r.status_code == 200
    body = r.json()
    # Enquanto o executor não estiver plugado, aceitamos "unroutable" ou "ok" futuramente
    assert body["status"]["reason"] in ("unroutable", "ok")
    assert "meta" in body
