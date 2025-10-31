# tests/test_ask_cadastro_sql.py
import os
import pytest
import psycopg
from fastapi.testclient import TestClient
from app.main import app

REQUIRED_COLS = {"ticker", "fii_cnpj", "display_name", "admin_name", "admin_cnpj", "website_url"}

def _db_connect():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        pytest.skip("DATABASE_URL não definida — pulando teste M3 (SQL).")
    try:
        conn = psycopg.connect(dsn, autocommit=True)
        return conn
    except Exception as e:
        pytest.skip(f"Não foi possível conectar no Postgres ({e}) — pulando teste M3 (SQL).")

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
        # fallback: qualquer ticker existente
        try:
            cur.execute("select ticker from fiis_cadastro limit 1")
            row = cur.fetchone()
            return row[0] if row else None
        except Exception:
            return None

@pytest.mark.integration
def test_ask_returns_data_from_fiis_cadastro_when_ticker_exists():
    """
    M3 — Confere que /ask retorna dados reais da view fiis_cadastro.
    Requisitos:
      - DATABASE_URL válido
      - Pelo menos 1 linha na view fiis_cadastro
    Dica: definir TEST_FII_TICKER=VINO11 (ou outro com dado) para forçar o ticker.
    """
    conn = _db_connect()
    preferred = os.getenv("TEST_FII_TICKER", "VINO11")
    ticker = _pick_existing_ticker(conn, preferred)
    if not ticker:
        pytest.skip("Nenhum ticker encontrado em fiis_cadastro — pulando teste M3 (SQL).")

    client = TestClient(app)
    payload = {
        "question": f"Qual o CNPJ do {ticker}?",
        "conversation_id": "conv-sql-001",
        "nickname": "leleo",
        "client_id": "00000000000",
    }
    r = client.post("/ask", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()

    # Pipeline completo deve responder "ok"
    assert body["status"]["reason"] == "ok"
    assert body["meta"]["planner_entity"] == "fiis_cadastro"
    assert body["meta"]["result_key"] == "cadastro_fii"

    data = body["results"].get("cadastro_fii", [])
    assert isinstance(data, list)
    assert len(data) >= 1, "Esperava pelo menos 1 linha para o ticker testado."

    # Checa colunas essenciais (return_columns)
    row = data[0]
    assert REQUIRED_COLS.issubset(row.keys()), f"Colunas faltando. Esperado {REQUIRED_COLS}, recebi {set(row.keys())}"

    # Sanidade: ticker retorna igual ao consultado
    assert row["ticker"].upper() == ticker.upper()
