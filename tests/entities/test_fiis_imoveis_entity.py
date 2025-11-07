from app.builder.sql_builder import build_select_for_entity
from app.executor.pg import PgExecutor
from app.formatter.rows import format_rows


def test_list_returns_rows():
    sql, params, result_key, return_columns = build_select_for_entity(
        "fiis_imoveis",
        {"ticker": "HGLG11"},
        {"agg": None, "order": "desc"},
    )

    assert "SELECT ticker, asset_name, asset_class" in sql
    assert "order by updated_at desc" in sql.lower()
    assert return_columns == [
        "ticker",
        "asset_name",
        "asset_class",
        "asset_address",
        "total_area",
        "units_count",
        "vacancy_ratio",
        "non_compliant_ratio",
        "assets_status",
        "created_at",
        "updated_at",
    ]

    executor = PgExecutor()
    rows = executor.query(sql, {**params, "entity": "fiis_imoveis"})
    formatted = format_rows(rows, return_columns)

    assert len(formatted) == 1
    row = formatted[0]
    assert set(row.keys()) == set(return_columns)
    assert row["vacancy_ratio"].endswith("%")
    assert row["non_compliant_ratio"].endswith("%")
    assert row["updated_at"].startswith("2024-01-06T18:30:00")
