from app.builder.sql_builder import build_select_for_entity
from app.executor.pg import PgExecutor
from app.formatter.rows import format_rows
from app.responder import render_answer


def _fetch_rows():
    sql, params, _, return_columns = build_select_for_entity(
        "fiis_processos",
        {"ticker": "MXRF11"},
        {"agg": None, "order": "desc"},
    )
    executor = PgExecutor()
    rows = executor.query(sql, {**params, "entity": "fiis_processos"})
    return format_rows(rows, return_columns)


def test_templates_render_and_fallback():
    rows = _fetch_rows()
    rendered = render_answer("fiis_processos", rows, identifiers={"ticker": "MXRF11"})
    assert "proc" in rendered
    assert "risco" in rendered

    fallback = render_answer("fiis_processos", [{}], identifiers={"ticker": "MXRF11"})
    assert fallback.startswith("Dados de processos do MXRF11")
