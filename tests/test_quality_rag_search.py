from starlette.testclient import TestClient


def test_rag_search_schema_guard(client: TestClient, monkeypatch):
    monkeypatch.setenv("QUALITY_OPS_TOKEN", "dummy")
    bad = {"type": "rag_search", "samples": [{"question": "q"}]}
    response = client.post(
        "/ops/quality/push",
        json=bad,
        headers={"X-Ops-Token": "dummy"},
    )
    assert response.status_code in (400, 422)


def test_rag_search_ok_smoke(client: TestClient, monkeypatch):
    monkeypatch.setenv("QUALITY_OPS_TOKEN", "dummy")

    class FakeStore:
        def __init__(self, path):
            pass

        def search_by_vector(self, qvec, k=5):
            return [
                {
                    "doc_id": "entity-fiis_cadastro:001",
                    "score": 0.9,
                    "chunk_id": "c1",
                    "tags": ["entity"],
                },
                {
                    "doc_id": "misc:zzz",
                    "score": 0.3,
                    "chunk_id": "c2",
                    "tags": [],
                },
            ]

    class FakeEmbedder:
        def __init__(self, *args, **kwargs):
            pass

        def embed(self, texts):
            return [[0.1, 0.2, 0.3]]

    import app.rag.index_reader as index_reader
    import app.rag.ollama_client as ollama_client

    monkeypatch.setattr(index_reader, "EmbeddingStore", FakeStore)
    monkeypatch.setattr(ollama_client, "OllamaClient", FakeEmbedder)

    payload = {
        "type": "rag_search",
        "defaults": {"k": 5, "min_score": 0.2, "tags": ["entity"]},
        "samples": [
            {"question": "q", "expect": {"doc_id_prefix": "entity-fiis_cadastro"}}
        ],
    }

    response = client.post(
        "/ops/quality/push",
        json=payload,
        headers={"X-Ops-Token": "dummy"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["metrics"]["ok"] == 1
    assert data["metrics"]["fail"] == 0
    assert data["accepted"] == 1
    assert data["details"][0]["passed"] is True
