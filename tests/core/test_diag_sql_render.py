import datetime as dt

from psycopg import adapt
import pytest

from app.executor.pg import PgExecutor
from app.main import app
from fastapi.testclient import TestClient


def _format_param(value):
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    return repr(value)


def _quote(value):
    if value is None:
        return "NULL"
    try:
        quoted = adapt(value).getquoted()
        if isinstance(quoted, (bytes, bytearray)):
            return quoted.decode()
        return str(quoted)
    except Exception:
        return repr(value)


@pytest.fixture(scope="module")
def diag_client():
    return TestClient(app)


def _run_diag(monkeypatch, diag_client, capsys, question: str, stop_after: int = 1):
    original_query = PgExecutor.query
    call_count = {"value": 0}

    def _diag_query(self, sql, params):
        rendered = sql
        for key, value in sorted(
            (params or {}).items(), key=lambda item: len(item[0]), reverse=True
        ):
            placeholder = f"%({key})s"
            rendered = rendered.replace(placeholder, _quote(value))
        print("=== RENDERED SQL ===")
        print(rendered)
        print("\n=== PARAM TYPES ===")
        for key, value in (params or {}).items():
            formatted = _format_param(value)
            type_name = type(value).__name__
            print(f"{key}: {formatted} ({type_name})")
        call_count["value"] += 1
        if call_count["value"] >= stop_after:
            raise RuntimeError("M8.DIAG-STOP")
        return []

    monkeypatch.setattr(PgExecutor, "query", _diag_query)
    try:
        payload = {
            "question": question,
            "conversation_id": "c1",
            "nickname": "n1",
            "client_id": "cli1",
        }

        with pytest.raises(RuntimeError, match="M8.DIAG-STOP"):
            diag_client.post("/ask?explain=true", json=payload)

        captured = capsys.readouterr()
        print(captured.out)
    finally:
        monkeypatch.setattr(PgExecutor, "query", original_query)


def test_diag_dy_avg(monkeypatch, diag_client, capsys):
    _run_diag(
        monkeypatch,
        diag_client,
        capsys,
        question="qual o dividend yield médio do HGRU11",
        stop_after=1,
    )


def test_diag_price_avg(monkeypatch, diag_client, capsys):
    _run_diag(
        monkeypatch,
        diag_client,
        capsys,
        question="qual o preço médio do HGRU11",
        stop_after=1,
    )
