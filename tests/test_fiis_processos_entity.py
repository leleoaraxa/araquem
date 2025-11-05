from app.builder.sql_builder import build_select_for_entity
from app.executor.pg import PgExecutor
from app.formatter.rows import format_rows


def test_list_returns_rows():
    sql, params, result_key, return_columns = build_select_for_entity(
        "fiis_processos",
        {"ticker": "VISC11"},
        {"agg": None, "order": "desc"},
    )

    assert "order by updated_at desc" in sql.lower()
    assert return_columns == [
        "ticker",
        "process_number",
        "judgment",
        "instance",
        "initiation_date",
        "cause_amt",
        "process_parts",
        "loss_risk_pct",
        "main_facts",
        "loss_impact_analysis",
        "created_at",
        "updated_at",
    ]

    executor = PgExecutor()
    rows = executor.query(sql, {**params, "entity": "fiis_processos"})
    formatted = format_rows(rows, return_columns)

    assert len(formatted) == 1
    row = formatted[0]
    assert set(row.keys()) == set(return_columns)
    assert row["cause_amt"].startswith("R$")
    assert row["loss_risk_pct"].endswith("%")
    assert row["initiation_date"] == "2023-06-01"
