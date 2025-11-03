# tests/test_ask_aggregations_precos.py
def test_preco_atual_latest(client):
    payload = {
        "question": "Preço atual do MXRF11",
        "conversation_id": "t2",
        "nickname": "test",
        "client_id": "dev",
    }
    r = client.post("/ask", json=payload).json()
    ag = r["meta"]["aggregates"]
    assert ag["agg"] == "latest"
    assert ag["window"] == "count:1"
    assert len(r["results"]["precos_fii"]) == 1
