import time

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_rag_eval_register_and_metrics_exposed():
    payload = {
        "recall_at_5": 0.8,
        "recall_at_10": 0.9,
        "mrr": 0.75,
        "ndcg_at_10": 0.85,
        "ts": int(time.time()),
    }
    response = client.post("/ops/metrics/rag/eval/register", json=payload)
    assert response.status_code == 200
    metrics = client.get("/metrics").text
    assert "rag_eval_recall_at_5" in metrics
    assert "rag_eval_recall_at_10" in metrics
    assert "rag_eval_mrr" in metrics
    assert "rag_eval_ndcg_at_10" in metrics
    assert "rag_eval_last_run_timestamp" in metrics
