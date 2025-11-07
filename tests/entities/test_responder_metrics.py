from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_templates_render_and_fallback():
    ok = client.post(
        "/ask",
        json={
            "question": "preço médio do HGLG11 nos ultimos 3 meses",
            "conversation_id": "t",
            "nickname": "n",
            "client_id": "c",
        },
    ).json()
    assert "results" in ok
    assert isinstance(ok["answer"], str) and len(ok["answer"]) > 0

    fb = client.post(
        "/ask",
        json={
            "question": "dy médio do XXXX11 nos ultimos 3 meses",
            "conversation_id": "t",
            "nickname": "n",
            "client_id": "c",
        },
    ).json()
    assert isinstance(fb["answer"], str) and len(fb["answer"]) > 0
