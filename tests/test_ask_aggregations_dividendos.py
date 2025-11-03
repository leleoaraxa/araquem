# tests/test_ask_aggregations_dividendos.py


def test_latest_dividendo_meta(client):
    payload = {
        "question": "Qual o último dividendo do XPLG11?",
        "conversation_id": "t1",
        "nickname": "test",
        "client_id": "dev",
    }
    r = client.post("/ask", json=payload).json()
    ag = r["meta"]["aggregates"]
    assert ag["agg"] == "latest"
    assert ag["window"] == "count:1"
    # deve retornar 1 linha no results.dividendos_fii
    assert len(r["results"]["dividendos_fii"]) == 1
