import os, time, pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def _post(question: str):
    payload = {
        "question": question,
        "conversation_id": "conv-cache",
        "nickname": "@leleo",
        "client_id": "66140994691",
    }
    r = client.post("/ask", json=payload)
    assert r.status_code == 200, r.text
    return r.json()

@pytest.mark.integration
def test_cache_miss_then_hit_for_cadastro():
    # Requer REDIS_URL válido e policies para fiis_cadastro
    red = os.getenv("REDIS_URL")
    if not red:
        pytest.skip("REDIS_URL não definido — pulando teste de cache.")
    # 1ª chamada — MISS
    body1 = _post("Qual o CNPJ do VINO11?")
    assert body1["status"]["reason"] == "ok"
    cache1 = body1["meta"].get("cache", {})
    assert cache1.get("hit") in (False, None)

    # 2ª chamada — HIT (mesma pergunta/identificadores)
    body2 = _post("Qual o CNPJ do VINO11?")
    cache2 = body2["meta"].get("cache", {})
    assert cache2.get("hit") is True
