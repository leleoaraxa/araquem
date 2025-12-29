from app.builder.sql_builder import build_select_for_entity


ENTITY = "fiis_financials_risk"


def test_build_select_single_ticker_uses_equals() -> None:
    sql, params, _, _ = build_select_for_entity(ENTITY, {"ticker": "hglg11"})

    assert "ticker = %(ticker)s" in sql
    assert "ANY(%(tickers)s)" not in sql
    assert params["ticker"] == "HGLG11"
    assert "tickers" not in params


def test_build_select_multi_ticker_uses_any() -> None:
    sql, params, _, _ = build_select_for_entity(
        ENTITY,
        {"ticker": "hglg11", "tickers": ["hglg11", "mxrf11"]},
    )

    assert "ticker = ANY(%(tickers)s)" in sql
    assert params["tickers"] == ["HGLG11", "MXRF11"]
    assert "ticker" not in params  # multi-ticker path usa apenas a lista normalizada
