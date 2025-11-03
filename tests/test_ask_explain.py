# /tests/test_ask_explain.py
import os
import pytest
import psycopg
from fastapi.testclient import TestClient
from app.main import app

def _db_connect():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        pytest.skip("DATABASE_URL não definida — pulando teste M6.3 (/ask?explain).")
    try:
        conn = psycopg.connect(dsn, autocommit=True)
        return conn
    except Exception as e:
        pytest.skip(f"Não foi possível conectar no Postgres ({e}) — pulando teste M6.3.")

def _pick_existing_ticker(conn, preferred: str | None) -> str | None:
    with conn.cursor() as cur:
        if preferred:
            try:
                cur.execute("select ticker from fiis_cadastro where ticker = %s limit 1", (preferred.upper(),))
                row = cur.fetchone()
                if row:
                    return row[0]
            except Exception:
                pass
        try:
            cur.execute("select ticker from fiis_cadastro limit 1")
            row = cur.fetchone()
            return row[0] if row else None
        except Exception:
            return None

@pytest.mark.integration
def test_ask_with_explain_includes_explain_block():
    """
    M6.3 — Quando ?explain=true, a resposta de /ask inclui meta.explain (planner.explain()).
    Requisitos:
      - DATABASE_URL válido
      - Pelo menos 1 linha na view fiis_cadastro
    """
    conn = _db_connect()
    preferred = os.getenv("TEST_FII_TICKER", "VINO11")
    ticker = _pick_existing_ticker(conn, preferred)
    if not ticker:
        pytest.skip("Nenhum ticker encontrado em fiis_cadastro — pulando teste M6.3 (/ask?explain).")

    client = TestClient(app)
    payload = {
        "question": f"Qual o CNPJ do {ticker}?",
        "conversation_id": "conv-explain-001",
        "nickname": "leleo",
        "client_id": "00000000000",
    }
    r = client.post("/ask?explain=true", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["status"]["reason"] == "ok"
    assert body["meta"]["planner_entity"] == "fiis_cadastro"
    assert "explain" in body["meta"]
    exp = body["meta"]["explain"]
    assert isinstance(exp, dict)

    for key in ("decision_path", "scoring", "signals", "rag"):
        assert key in exp

    ea = body["meta"].get("explain_analytics")
    assert isinstance(ea, dict) and "summary" in ea and "details" in ea
