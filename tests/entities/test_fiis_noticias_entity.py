from app.builder.sql_builder import build_select_for_entity
from app.executor.pg import PgExecutor
from app.formatter.rows import format_rows


def test_list_returns_rows():
    agg_params = {
        "agg": None,
        "order": "desc",
        "period_start": "2024-01-01",
        "period_end": "2024-01-31",
    }
    sql, params, result_key, return_columns = build_select_for_entity(
        "fiis_noticias",
        {"ticker": "MXRF11"},
        agg_params,
    )

    assert "published_at" in sql
    assert "between %(period_start)s and %(period_end)s" in sql.lower()
    assert params["period_start"] == "2024-01-01"
    assert params["period_end"] == "2024-01-31"
    assert "order by published_at desc" in sql.lower()
    assert return_columns == [
        "ticker",
        "source",
        "title",
        "tags",
        "description",
        "url",
        "image_url",
        "published_at",
        "created_at",
        "updated_at",
    ]

    executor = PgExecutor()
    rows = executor.query(sql, {**params, "entity": "fiis_noticias"})
    formatted = format_rows(rows, return_columns)

    assert len(formatted) == 1
    row = formatted[0]
    assert set(row.keys()) == set(return_columns)
    assert row["published_at"].startswith("2024-01-08T14:30:00")
    assert row["url"].startswith("https://")
