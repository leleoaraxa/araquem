from app.builder.sql_builder import build_select_for_entity
from app.executor.pg import PgExecutor
from app.formatter.rows import format_rows
from app.responder import render_answer


def _fetch_rows():
    sql, params, _, return_columns = build_select_for_entity(
        "fiis_imoveis",
        {"ticker": "HGLG11"},
        {"agg": None, "order": "desc"},
    )
    executor = PgExecutor()
    rows = executor.query(sql, {**params, "entity": "fiis_imoveis"})
    return format_rows(rows, return_columns)


def test_templates_render_and_fallback():
    rows = _fetch_rows()
    rendered = render_answer("fiis_imoveis", rows, identifiers={"ticker": "HGLG11"})
    assert "Galpão Alpha" in rendered
    assert "vacância" in rendered

    fallback = render_answer("fiis_imoveis", [{}], identifiers={"ticker": "HGLG11"})
    assert fallback.startswith("Dados de imóveis do HGLG11")
