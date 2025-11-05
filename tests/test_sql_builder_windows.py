from app.builder.sql_builder import build_select_for_entity


def test_months_window_casts_default_date_field():
    sql, params, _, _ = build_select_for_entity(
        "fiis_precos",
        identifiers={"ticker": "HGRU11"},
        agg_params={"agg": "avg", "window": "months:12"},
    )

    assert "(traded_at)::timestamp >= (CURRENT_DATE - INTERVAL '12 months')" in sql
    assert params["ticker"] == "HGRU11"
