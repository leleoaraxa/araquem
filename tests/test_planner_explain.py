from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_debug_planner_endpoint():
    r = client.get("/debug/planner", params={"q": "Qual o CNPJ do HGLG11?"})
    assert r.status_code == 200
    body = r.json()
    assert "chosen" in body
    assert "intent_scores" in body
