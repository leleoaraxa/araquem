-- =====================================================================
-- DROP VIEW
-- =====================================================================
DROP VIEW IF EXISTS client_fiis_dividends_evolution;
DROP VIEW IF EXISTS client_fiis_performance_vs_benchmark;
DROP VIEW IF EXISTS fii_overview;
DROP VIEW IF EXISTS fiis_yield_history;
DROP VIEW IF EXISTS fiis_markowitz_universe;
DROP VIEW IF EXISTS fiis_cadastro;
DROP VIEW IF EXISTS fiis_dividendos;
DROP VIEW IF EXISTS fiis_precos;
DROP VIEW IF EXISTS fiis_rankings;
DROP VIEW IF EXISTS fiis_imoveis;
DROP VIEW IF EXISTS fiis_processos;
DROP VIEW IF EXISTS fiis_noticias;
DROP VIEW IF EXISTS fiis_financials_snapshot;
DROP VIEW IF EXISTS fiis_financials_risk;
DROP VIEW IF EXISTS fiis_financials_revenue_schedule;
DROP VIEW IF EXISTS fiis_financials;
DROP VIEW IF EXISTS financials_tickers_typed;
DROP VIEW IF EXISTS view_markowitz_sirios_portfolios_latest;
DROP VIEW IF EXISTS view_markowitz_sirios_portfolios;
DROP VIEW IF EXISTS view_markowitz_frontier_best_sharpe;
DROP VIEW IF EXISTS view_markowitz_universe_stats;
DROP VIEW IF EXISTS view_markowitz_frontier_plot;
-- =====================================================================
-- DROP MATERIALIZED VIEW
-- =====================================================================
DROP MATERIALIZED VIEW IF EXISTS client_fiis_positions;
DROP MATERIALIZED VIEW IF EXISTS view_fiis_info;
DROP MATERIALIZED VIEW IF EXISTS view_fiis_history_dividends;
DROP MATERIALIZED VIEW IF EXISTS view_fiis_history_assets;
DROP MATERIALIZED VIEW IF EXISTS view_fiis_history_judicial;
DROP MATERIALIZED VIEW IF EXISTS view_fiis_history_prices;
DROP MATERIALIZED VIEW IF EXISTS view_fiis_history_news;
DROP MATERIALIZED VIEW IF EXISTS history_market_indicators;
DROP MATERIALIZED VIEW IF EXISTS view_history_indexes;
DROP MATERIALIZED VIEW IF EXISTS view_market_indicators;
DROP MATERIALIZED VIEW IF EXISTS history_b3_indexes;
DROP MATERIALIZED VIEW IF EXISTS history_currency_rates;
DROP MATERIALIZED VIEW IF EXISTS rf_daily_series_mat;
DROP MATERIALIZED VIEW IF EXISTS market_index_series;
DROP MATERIALIZED VIEW IF EXISTS fiis_rankings_quant;
-- =====================================================================
-- DROP INDEX
-- =====================================================================
DROP INDEX idx_client_position_filter;
-- =====================================================================
-- EXTENSION: unaccent / pg_stat_statements
-- =====================================================================
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
-- =====================================================================
-- FUNCTION: unaccent_ci
-- =====================================================================
CREATE OR REPLACE FUNCTION unaccent_ci(text)
RETURNS text
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT unaccent('unaccent', lower($1))
$$;
-- =====================================================================
-- VIEW: view_fiis_info
-- =====================================================================
CREATE MATERIALIZED VIEW view_fiis_info AS
SELECT
    bt.ticker AS ticker,
    bt.document AS fii_cnpj,
    bt.ticker_name AS ticker_full_name,
    bt.bovespa_name AS b3_name,
    INITCAP(bt.classification) AS classification,
    bt.sector AS sector,
    bt.industry_type AS sub_sector,
    bt.management_type AS management_type,
    INITCAP(bt.target_market) AS target_market,
    CASE
        WHEN bt.exclusive_fund = 'S' THEN true
        WHEN bt.exclusive_fund = 'N' THEN false
        ELSE NULL
    END AS is_exclusive,
    bt.isin_code AS isin,
    TO_CHAR(TO_DATE(bt.ipo_date, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS ipo_date,
    bt.website AS website_url,
    INITCAP(bt.administrator_name) AS admin_name,
    REGEXP_REPLACE(bt.administrator_document, '(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})', '\1.\2.\3/\4-\5') AS admin_cnpj,
    INITCAP(bt.custodian_name) AS custodian_name,

    COALESCE(itl.percent_ifil, 0) AS ifil_weight_pct,
    COALESCE(itx.percent_ifix, 0) AS ifix_weight_pct,

    ROUND(sd.dividend_yield_m::numeric, 2) AS dy_monthly_pct,
    ROUND(sd.dividend_yield_12m::numeric, 2) AS dy_pct,
    ROUND(COALESCE(sd.dividends_sum_12m::numeric, 0), 2) AS sum_anual_dy_amt,
    ROUND(COALESCE(sd.last_dividend::numeric, 0), 2) AS last_dividend_amt,
    TO_CHAR(TO_DATE(sd.payment_date::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS last_payment_date,

    ROUND(cf.market_cap::numeric, 2) AS market_cap_value,
    ROUND(cf.enterprise_value::numeric, 2) AS enterprise_value,
    ROUND(cf.price_to_book_ratio::numeric, 4) AS price_book_ratio,
    ROUND(cf.equity_per_share::numeric, 3) AS equity_per_share,
    ROUND(cf.revenue_per_share::numeric, 3) AS revenue_per_share,
    ROUND(cf.dividend_payout_ratio::numeric, 2) AS dividend_payout_pct,
    ROUND(cf.growth_rate::numeric, 3) AS growth_rate,
    ROUND(cf.cap_rate::numeric, 3) AS cap_rate,
    ROUND(cf.volatility::numeric, 4) AS volatility_ratio,
    ROUND(cf.sharpe_ratio::numeric, 4) AS sharpe_ratio,
    ROUND(cf.treynor_ratio::numeric, 4) AS treynor_ratio,
    ROUND(cf.jensen_alpha::numeric, 3) AS jensen_alpha,
    ROUND(cf.beta_index::numeric, 3) AS beta_index,

    -- 🆕 Novos indicadores
    ROUND(cf.sortino_ratio::numeric, 4) AS sortino_ratio,
    ROUND(cf.max_drawdown::numeric, 4) AS max_drawdown,
    ROUND(cf.r_squared::numeric, 4) AS r_squared,

    ROUND(cf.leverage::numeric, 4) AS leverage_ratio,
    ROUND(f.equity::numeric, 2) AS equity_value,
    ROUND(f.shares_count::numeric, 0) AS shares_count,
    ROUND(COALESCE(f.effective_variation_year, 0), 4) AS variation_year_ratio,

    CASE
        WHEN f.effective_variation_month ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.effective_variation_month, '999999999D9999'), 0), 4)
        ELSE 0
    END AS variation_month_ratio,
    CASE
        WHEN f.equity_variation_month ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.equity_variation_month, '999999999D9999'), 0), 4)
        ELSE 0
    END AS equity_month_ratio,
    CASE
        WHEN f.dividend_to_distribute ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.dividend_to_distribute, '999999999999D99'), 0), 2)
        ELSE 0
    END AS shareholders_count,
    CASE
        WHEN f.shareholders_count ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.shareholders_count, '999999999999D99'), 0), 2)
        ELSE 0
    END AS dividend_reserve_amt,
    CASE
        WHEN f.administration_fee_to_pay ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.administration_fee_to_pay, '999999999999D99'), 0), 2)
        ELSE 0
    END AS admin_fee_due_amt,
    CASE
        WHEN f.performance_fee_to_pay ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.performance_fee_to_pay, '999999999999D99'), 0), 2)
        ELSE 0
    END AS perf_fee_due_amt,
    CASE
        WHEN f.total_cash ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.total_cash, '999999999999D99'), 0), 2)
        ELSE 0
    END AS total_cash_amt,
    CASE
        WHEN f.expected_revenue ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.expected_revenue, '999999999999D99'), 0), 2)
        ELSE 0
    END AS expected_revenue_amt,
    CASE
        WHEN f.total_liabilities ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.total_liabilities, '999999999999D99'), 0), 2)
        ELSE 0
    END AS liabilities_total_amt,

    CASE
        WHEN f.percent_total_revenue_due_upto3months ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.percent_total_revenue_due_upto3months, '999999999D9999'), 0), 4)
        ELSE 0
    END AS revenue_due_0_3m_pct,
    CASE
        WHEN f.percent_total_revenue_due_3to6months ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.percent_total_revenue_due_3to6months, '999999999D9999'), 0), 4)
        ELSE 0
    END AS revenue_due_3_6m_pct,
    CASE
        WHEN f.percent_total_revenue_due_6to9months ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.percent_total_revenue_due_6to9months, '999999999D9999'), 0), 4)
        ELSE 0
    END AS revenue_due_6_9m_pct,
    CASE
        WHEN f.percent_total_revenue_due_9to12months ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.percent_total_revenue_due_9to12months, '999999999D9999'), 0), 4)
        ELSE 0
    END AS revenue_due_9_12m_pct,
    CASE
        WHEN f.percent_total_revenue_due_12to15months ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.percent_total_revenue_due_12to15months, '999999999D9999'), 0), 4)
        ELSE 0
    END AS revenue_due_12_15m_pct,
    CASE
        WHEN f.percent_total_revenue_due_15to18months ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.percent_total_revenue_due_15to18months, '999999999D9999'), 0), 4)
        ELSE 0
    END AS revenue_due_15_18m_pct,
    CASE
        WHEN f.percent_total_revenue_due_18to21months ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.percent_total_revenue_due_18to21months, '999999999D9999'), 0), 4)
        ELSE 0
    END AS revenue_due_18_21m_pct,
    CASE
        WHEN f.percent_total_revenue_due_21to24months ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.percent_total_revenue_due_21to24months, '999999999D9999'), 0), 4)
        ELSE 0
    END AS revenue_due_21_24m_pct,
    CASE
        WHEN f.percent_total_revenue_due_24to27months ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.percent_total_revenue_due_24to27months, '999999999D9999'), 0), 4)
        ELSE 0
    END AS revenue_due_24_27m_pct,
    CASE
        WHEN f.percent_total_revenue_due_27to30months ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.percent_total_revenue_due_27to30months, '999999999D9999'), 0), 4)
        ELSE 0
    END AS revenue_due_27_30m_pct,
    CASE
        WHEN f.percent_total_revenue_due_30to33months ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.percent_total_revenue_due_30to33months, '999999999D9999'), 0), 4)
        ELSE 0
    END AS revenue_due_30_33m_pct,
    CASE
        WHEN f.percent_total_revenue_due_33to36months ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.percent_total_revenue_due_33to36months, '999999999D9999'), 0), 4)
        ELSE 0
    END AS revenue_due_33_36m_pct,
    CASE
        WHEN f.percent_total_revenue_due_above36months ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.percent_total_revenue_due_above36months, '999999999D9999'), 0), 4)
        ELSE 0
    END AS revenue_due_over_36m_pct,
    CASE
        WHEN f.percent_total_revenue_due_undetermined ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.percent_total_revenue_due_undetermined, '999999999D9999'), 0), 4)
        ELSE 0
    END AS revenue_due_undetermined_pct,

    CASE
        WHEN f.percent_total_revenue_igpm_index ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.percent_total_revenue_igpm_index, '999999999D9999'), 0), 4)
        ELSE 0
    END AS revenue_igpm_pct,
    CASE
        WHEN f.percent_total_revenue_inpc_index ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.percent_total_revenue_inpc_index, '999999999D9999'), 0), 4)
        ELSE 0
    END AS revenue_inpc_pct,
    CASE
        WHEN f.percent_total_revenue_ipca_index ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.percent_total_revenue_ipca_index, '999999999D9999'), 0), 4)
        ELSE 0
    END AS revenue_ipca_pct,
    CASE
        WHEN f.percent_total_revenue_incc_index ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(f.percent_total_revenue_incc_index, '999999999D9999'), 0), 4)
        ELSE 0
    END AS revenue_incc_pct,

    ROUND(r.users_ranking::numeric, 0) AS users_ranking_count,
    ROUND(r.users_ranking_positions_moved::numeric, 0) AS users_rank_movement_count,
    ROUND(r.sirios_ranking::numeric, 0) AS sirios_ranking_count,
    ROUND(r.sirios_ranking_positions_moved::numeric, 0) AS sirios_rank_movement_count,
    ROUND(r.ifix_ranking::numeric, 0) AS ifix_ranking_count,
    ROUND(r.ifix_ranking_positions_moved::numeric, 0) AS ifix_rank_movement_count,
    ROUND(r.ifil_ranking::numeric, 0) AS ifil_ranking_count,
    ROUND(r.ifil_ranking_positions_moved::numeric, 0) AS ifil_rank_movement_count,

    TO_CHAR(TO_DATE(bt.created_at::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS created_at,
    TO_CHAR(TO_DATE(bt.updated_at::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS updated_at

FROM basics_tickers bt
LEFT JOIN ifil_tickers itl   ON bt.ticker = itl.ticker
LEFT JOIN ifix_tickers itx   ON bt.ticker = itx.ticker
LEFT JOIN dividends_tickers sd ON bt.ticker = sd.ticker
LEFT JOIN calc_financials_tickers cf ON bt.ticker = cf.ticker
LEFT JOIN financials_tickers f ON bt.ticker = f.ticker
LEFT JOIN ranking_fiis r      ON bt.ticker = r.ticker
ORDER BY bt.ticker ASC
WITH DATA;
-- =====================================================================
-- INDEX VIEW: view_fiis_info
-- =====================================================================
CREATE UNIQUE INDEX IF NOT EXISTS idx_fiis_info_ticker ON view_fiis_info(ticker);
-- =====================================================================
-- VIEW: view_history_indexes
-- =====================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS view_history_indexes
TABLESPACE pg_default
AS
 SELECT to_char(to_date(date_taxes::text, 'YYYY-MM-DD'::text)::timestamp with time zone, 'YYYY-MM-DD HH24:MI:SS'::text) AS index_date,
    round(ibovespa_taxes::numeric, 0) AS ibov_points_count,
    round(ibovespa_variation::numeric, 2) AS ibov_var_pct,
    round(ifix_taxes::numeric, 0) AS ifix_points_count,
    round(ifix_variation::numeric, 2) AS ifix_var_pct,
    round(ifil_taxes::numeric, 0) AS ifil_points_count,
    round(ifil_variation::numeric, 2) AS ifil_var_pct,
    round(usd_buy::numeric, 2) AS usd_buy_amt,
    round(usd_sell::numeric, 2) AS usd_sell_amt,
    round(usd_variation::numeric, 2) AS usd_var_pct,
    round(eur_buy::numeric, 2) AS eur_buy_amt,
    round(eur_sell::numeric, 2) AS eur_sell_amt,
    round(eur_variation::numeric, 2) AS eur_var_pct,
    to_char(to_date(created_at::text, 'YYYY-MM-DD'::text)::timestamp with time zone, 'YYYY-MM-DD HH24:MI:SS'::text) AS created_at,
    to_char(to_date(updated_at::text, 'YYYY-MM-DD'::text)::timestamp with time zone, 'YYYY-MM-DD HH24:MI:SS'::text) AS updated_at
   FROM hist_taxes ht
  ORDER BY date_taxes DESC
WITH DATA;
-- =====================================================================
-- INDEX VIEW: view_history_indexes
-- =====================================================================
CREATE UNIQUE INDEX idx_history_indexes ON view_history_indexes USING btree     (index_date COLLATE pg_catalog."default") TABLESPACE pg_default;
-- =====================================================================
-- VIEW: view_market_indicators
-- =====================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS view_market_indicators
TABLESPACE pg_default
AS
 SELECT to_char(to_date(date_indicators::text, 'YYYY-MM-DD'::text)::timestamp with time zone, 'YYYY-MM-DD HH24:MI:SS'::text) AS indicator_date,
    upper(slug_indicators::text) AS indicator_name,
    value_indicators AS indicator_amt,
    to_char(to_date(created_at::text, 'YYYY-MM-DD'::text)::timestamp with time zone, 'YYYY-MM-DD HH24:MI:SS'::text) AS created_at,
    to_char(to_date(updated_at::text, 'YYYY-MM-DD'::text)::timestamp with time zone, 'YYYY-MM-DD HH24:MI:SS'::text) AS updated_at
   FROM hist_indicators hi
  ORDER BY date_indicators DESC, slug_indicators
WITH DATA;
-- =====================================================================
-- INDEX VIEW: view_market_indicators
-- =====================================================================
CREATE UNIQUE INDEX idx_market_indicators ON view_market_indicators USING btree (indicator_date COLLATE pg_catalog."default", indicator_name COLLATE pg_catalog."default") TABLESPACE pg_default;
-- =====================================================================
-- VIEW: view_fiis_history_dividends
-- =====================================================================
CREATE MATERIALIZED VIEW view_fiis_history_dividends AS
SELECT
    bt.ticker AS ticker,
    DATE_TRUNC('day', hd.traded_until) AS traded_until_date,
    DATE_TRUNC('day', hd.payment_date) AS payment_date,
    hd.amount AS dividend_amt,
	TO_CHAR(TO_DATE(hd.created_at::text,
		'YYYY-MM-DD'),
	    'YYYY-MM-DD HH24:MI:SS') 				AS created_at,
	TO_CHAR(TO_DATE(hd.updated_at::text,
		'YYYY-MM-DD'),
	    'YYYY-MM-DD HH24:MI:SS') 				AS updated_at
FROM basics_tickers bt
JOIN hist_dividends hd ON bt.ticker = hd.ticker
ORDER BY bt.ticker ASC, hd.traded_until DESC, hd.payment_date DESC;
-- =====================================================================
-- INDEX VIEW: view_fiis_history_dividends
-- =====================================================================
CREATE UNIQUE INDEX idx_fiis_hist_dividends ON view_fiis_history_dividends(ticker, traded_until_date, payment_date);
-- =====================================================================
-- VIEW: view_fiis_history_assets
-- =====================================================================
CREATE MATERIALIZED VIEW view_fiis_history_assets AS
SELECT
    bt.ticker AS ticker,
    at.asset AS asset_name,
    at.asset_class AS asset_class,
    at.address AS asset_address,
    CASE
        WHEN at.total_area ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(at.total_area, '999999999D9999'), 0), 2)
        ELSE 0
    END AS total_area,
    CASE
        WHEN at.number_units ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(at.number_units, '999999999D9999'), 0), 0)
        ELSE 0
    END AS units_count,
    CASE
        WHEN at.space_vacancy ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(at.space_vacancy, '999999999D9999'), 0), 4)
        ELSE 0
    END AS vacancy_ratio,
    CASE
        WHEN at.non_compliance ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(at.non_compliance, '999999999D9999'), 0), 4)
        ELSE 0
    END AS non_compliant_ratio,
    CASE
        WHEN at.asset_status = '1' THEN 'Ativo'
        WHEN at.asset_status = '0' THEN 'Inativo'
        ELSE NULL
    END AS assets_status,
    TO_CHAR(TO_DATE(at.created_at::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS created_at,
    TO_CHAR(TO_DATE(at.updated_at::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS updated_at
FROM basics_tickers bt
JOIN assets_tickers at ON bt.ticker = at.ticker
ORDER BY bt.ticker ASC;
-- =====================================================================
-- INDEX VIEW: view_fiis_history_assets
-- =====================================================================
CREATE UNIQUE INDEX idx_fiis_assets ON view_fiis_history_assets(ticker, asset_class, asset_name, asset_address, assets_status);
-- =====================================================================
-- VIEW: view_fiis_history_judicial
-- =====================================================================
CREATE MATERIALIZED VIEW view_fiis_history_judicial AS
SELECT
    bt.ticker          AS ticker,
    pt.process_number  AS process_number,
    pt.judgment        AS judgment,
    pt.instance        AS instance,
	TO_CHAR(TO_DATE(pt.initiation_date::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS initiation_date,
	CASE
        WHEN pt.value_of_cause ~ '^-?\d+(\.\d+)?$'
        THEN ROUND(COALESCE(TO_NUMBER(pt.value_of_cause, '999999999999D99'), 0), 2)
        ELSE 0
    END AS cause_amt,
    INITCAP(pt.process_parts)   AS process_parts,
    INITCAP(pt.chance_of_loss)  AS loss_risk_pct,
    pt.main_facts      AS main_facts,
    pt.analysis_impact_loss AS loss_impact_analysis,
    TO_CHAR(TO_DATE(pt.created_at::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS created_at,
    TO_CHAR(TO_DATE(pt.updated_at::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS updated_at
FROM basics_tickers bt
JOIN process_tickers pt ON bt.ticker = pt.ticker
ORDER BY bt.ticker ASC;
-- =====================================================================
-- INDEX VIEW: view_fiis_history_judicial
-- =====================================================================
CREATE UNIQUE INDEX idx_fiis_judicial ON view_fiis_history_judicial(ticker, process_number);
-- =====================================================================
-- VIEW: view_fiis_history_prices
-- =====================================================================
CREATE MATERIALIZED VIEW view_fiis_history_prices AS
SELECT
    bt.ticker          AS ticker,
	TO_CHAR(TO_DATE(p.price_ref_date::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS price_date,
    p.close_price      AS close_price,
    p.adj_close_price  AS adj_close_price,
    p.open_price       AS open_price,
	ROUND(p.daily_range::numeric, 2) AS daily_range_pct,
    p.max_price        AS max_price,
    p.min_price        AS min_price,
	TO_CHAR(TO_DATE(p.created_at::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS created_at,
    TO_CHAR(TO_DATE(p.updated_at::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS updated_at
FROM basics_tickers bt
JOIN price_tickers p ON bt.ticker = p.ticker
ORDER BY bt.ticker ASC, p.price_ref_date DESC;
-- =====================================================================
-- INDEX VIEW: view_fiis_history_prices
-- =====================================================================
CREATE UNIQUE INDEX idx_fiis_history_prices ON view_fiis_history_prices(ticker, price_date);
-- =====================================================================
-- VIEW: view_fiis_history_news
-- =====================================================================
CREATE MATERIALIZED VIEW view_fiis_history_news AS
SELECT
    bt.ticker           AS ticker,
    mn.news_topic       AS source,
    mn.news_title       AS title,
    mn.news_tags        AS tags,
    mn.news_description AS description,
    mn.news_url         AS url,
	mn.news_image		AS image_url,
	TO_CHAR(TO_DATE(mn.news_date::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS published_at,
	TO_CHAR(TO_DATE(mn.created_at::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS created_at,
    TO_CHAR(TO_DATE(mn.updated_at::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS updated_at
FROM basics_tickers bt
JOIN market_news mn
  ON (mn.news_title ILIKE '%' || bt.ticker || '%' OR
      mn.news_description ILIKE '%' || bt.ticker || '%')
ORDER BY bt.ticker;
-- =====================================================================
-- VIEW: view_fiis_history_news
-- =====================================================================
CREATE UNIQUE INDEX idx_fiis_history_news ON view_fiis_history_news(ticker, url);
CREATE INDEX IF NOT EXISTS idx_news_ticker_date ON view_fiis_history_news (ticker, published_at DESC);
-- =====================================================================
-- VIEW: history_market_indicators
-- =====================================================================
CREATE MATERIALIZED VIEW history_market_indicators AS
SELECT
	TO_CHAR(TO_DATE(hi.date_indicators::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS indicator_date,
    UPPER(hi.slug_indicators)   AS indicator_name,
    hi.value_indicators  AS indicator_amt,
	TO_CHAR(TO_DATE(hi.created_at::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS created_at,
    TO_CHAR(TO_DATE(hi.updated_at::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS updated_at
FROM hist_indicators hi
ORDER BY hi.date_indicators DESC, hi.slug_indicators ASC;
-- =====================================================================
-- INDEX VIEW: history_market_indicators
-- =====================================================================
CREATE UNIQUE INDEX idx_history_market_indicators ON history_market_indicators(indicator_date, indicator_name);
-- =====================================================================
-- VIEW: history_b3_indexes
-- =====================================================================
CREATE MATERIALIZED VIEW history_b3_indexes AS
SELECT
    TO_CHAR(TO_DATE(ht.date_taxes::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS index_date,
    ROUND(ht.ibovespa_taxes::numeric, 0)       AS ibov_points_count,
    ROUND(ht.ibovespa_variation::numeric, 2)   AS ibov_var_pct,
    ROUND(ht.ifix_taxes::numeric, 0)           AS ifix_points_count,
    ROUND(ht.ifix_variation::numeric, 2)       AS ifix_var_pct,
    ROUND(ht.ifil_taxes::numeric, 0)           AS ifil_points_count,
    ROUND(ht.ifil_variation::numeric, 2)       AS ifil_var_pct,
    TO_CHAR(TO_DATE(ht.created_at::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS created_at,
    TO_CHAR(TO_DATE(ht.updated_at::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS updated_at
FROM hist_taxes ht
ORDER BY ht.date_taxes DESC;
-- =====================================================================
-- INDEX VIEW: history_b3_indexes
-- =====================================================================
CREATE UNIQUE INDEX idx_history_b3_indexes ON history_b3_indexes(index_date);
-- =====================================================================
-- VIEW: history_currency_rates
-- =====================================================================
CREATE MATERIALIZED VIEW history_currency_rates AS
SELECT
    TO_CHAR(TO_DATE(ht.date_taxes::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS rate_date,
    ROUND(ht.usd_buy::numeric, 2)     AS usd_buy_amt,
    ROUND(ht.usd_sell::numeric, 2)    AS usd_sell_amt,
    ROUND(ht.usd_variation::numeric, 2) AS usd_var_pct,
    ROUND(ht.eur_buy::numeric, 2)     AS eur_buy_amt,
    ROUND(ht.eur_sell::numeric, 2)    AS eur_sell_amt,
    ROUND(ht.eur_variation::numeric, 2) AS eur_var_pct,
    TO_CHAR(TO_DATE(ht.created_at::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS created_at,
    TO_CHAR(TO_DATE(ht.updated_at::text, 'YYYY-MM-DD'), 'YYYY-MM-DD HH24:MI:SS') AS updated_at
FROM hist_taxes ht
ORDER BY ht.date_taxes DESC;
-- =====================================================================
-- INDEX VIEW: history_currency_rates
-- =====================================================================
CREATE UNIQUE INDEX idx_history_currency_rates ON history_currency_rates(rate_date);
-- =====================================================================
-- VIEW: fiis_cadastro
-- =====================================================================
CREATE OR REPLACE VIEW fiis_cadastro AS
SELECT ticker, fii_cnpj, ticker_full_name as display_name, b3_name, classification, sector, sub_sector, management_type,
	target_market, is_exclusive, isin, ipo_date, website_url, admin_name, admin_cnpj, custodian_name,
	ifil_weight_pct, ifix_weight_pct, shares_count, shareholders_count, created_at, updated_at
FROM view_fiis_info;
-- =====================================================================
-- VIEW: fiis_precos
-- =====================================================================
CREATE OR REPLACE VIEW fiis_precos AS
SELECT ticker, price_date as traded_at, close_price, adj_close_price,
open_price, max_price, min_price, daily_range_pct as daily_variation_pct, created_at, updated_at
FROM view_fiis_history_prices;
-- =====================================================================
-- VIEW: fiis_dividendos
-- =====================================================================
CREATE OR REPLACE VIEW fiis_dividendos AS
SELECT ticker, traded_until_date, payment_date, dividend_amt, created_at, updated_at
FROM view_fiis_history_dividends;
-- =====================================================================
-- VIEW: fiis_imoveis
-- =====================================================================
CREATE OR REPLACE VIEW fiis_imoveis AS
SELECT
    ticker,
    asset_name,
    asset_class,
    asset_address,
    total_area,
    units_count,
    vacancy_ratio,
    non_compliant_ratio,
    assets_status,
    created_at,
    updated_at
FROM view_fiis_history_assets;
-- =====================================================================
-- VIEW: fiis_processos
-- =====================================================================
CREATE OR REPLACE VIEW fiis_processos AS
SELECT
    ticker,
    process_number,
    judgment,
    instance,
	initiation_date,
	cause_amt,
    process_parts,
    loss_risk_pct,
    main_facts,
    loss_impact_analysis,
    created_at,
    updated_at
FROM view_fiis_history_judicial;
-- =====================================================================
-- VIEW: fiis_noticias
-- =====================================================================
CREATE OR REPLACE VIEW fiis_noticias AS
SELECT
    ticker,
    source,
    title,
    tags,
    description,
    url,
	image_url,
	published_at,
	created_at,
    updated_at
FROM view_fiis_history_news;
-- =====================================================================
-- VIEW: fiis_financials
-- =====================================================================
CREATE OR REPLACE VIEW fiis_financials AS
SELECT ticker, dy_monthly_pct, dy_pct, sum_anual_dy_amt, last_dividend_amt, last_payment_date, market_cap_value,
	enterprise_value, price_book_ratio, equity_per_share, revenue_per_share, dividend_payout_pct, growth_rate,
	cap_rate, volatility_ratio, sharpe_ratio, treynor_ratio, jensen_alpha, beta_index, sortino_ratio, max_drawdown, r_squared, leverage_ratio, equity_value,
	variation_month_ratio, variation_year_ratio, equity_month_ratio, dividend_reserve_amt, admin_fee_due_amt, perf_fee_due_amt, total_cash_amt,
	expected_revenue_amt, liabilities_total_amt, revenue_due_0_3m_pct, revenue_due_3_6m_pct, revenue_due_6_9m_pct,
	revenue_due_9_12m_pct, revenue_due_12_15m_pct, revenue_due_15_18m_pct, revenue_due_18_21m_pct, revenue_due_21_24m_pct,
	revenue_due_24_27m_pct, revenue_due_27_30m_pct, revenue_due_30_33m_pct, revenue_due_33_36m_pct, revenue_due_over_36m_pct,
	revenue_due_undetermined_pct, revenue_igpm_pct, revenue_inpc_pct, revenue_ipca_pct, revenue_incc_pct, created_at,
	updated_at
FROM view_fiis_info;
-- =====================================================================
-- VIEW MATERIALIZED: client_fiis_positions
-- =====================================================================
CREATE MATERIALIZED VIEW client_fiis_positions AS
WITH docs AS (
    SELECT DISTINCT document_number
    FROM equities_positions
)
SELECT
    f.document_number,
    f.reference_date      AS position_date,
    f.ticker_symbol       AS ticker,
    f.corporation_name    AS fii_name,
    f.participant_name,
    f.equities_quantity   AS qty,
    f.closing_price,
    f.update_value,
    f.available_quantity,
    f.average_price,
    f.profitability_percentage,
    f.percentage,
    f.reference_date      AS created_at,
    f.reference_date      AS updated_at
FROM docs d
CROSS JOIN LATERAL fc_fiis_portfolio(d.document_number) AS f
WITH NO DATA;
-- =====================================================================
-- INDEX VIEW: client_fiis_positions
-- =====================================================================
CREATE UNIQUE INDEX CONCURRENTLY idx_client_fiis_positions_uq
    ON client_fiis_positions (document_number, ticker, participant_name, position_date);

CREATE INDEX CONCURRENTLY idx_client_fiis_positions_doc_ticker
    ON client_fiis_positions (document_number, ticker);
-- =====================================================================
-- VIEW: fiis_financials_snapshot
-- =====================================================================
CREATE OR REPLACE VIEW fiis_financials_snapshot AS
SELECT
  ticker,
  dy_monthly_pct, dy_pct, sum_anual_dy_amt,
  last_dividend_amt, last_payment_date,
  market_cap_value, enterprise_value, price_book_ratio,
  equity_per_share, revenue_per_share, dividend_payout_pct,
  growth_rate, cap_rate,
  leverage_ratio, equity_value,
  variation_month_ratio, variation_year_ratio, equity_month_ratio,
  dividend_reserve_amt, admin_fee_due_amt, perf_fee_due_amt,
  total_cash_amt, expected_revenue_amt, liabilities_total_amt,
  created_at, updated_at
FROM fiis_financials;
-- =====================================================================
-- VIEW: fiis_financials_revenue_schedule
-- =====================================================================
CREATE OR REPLACE VIEW fiis_financials_revenue_schedule AS
SELECT
  ticker,
  revenue_due_0_3m_pct,
  revenue_due_3_6m_pct,
  revenue_due_6_9m_pct,
  revenue_due_9_12m_pct,
  revenue_due_12_15m_pct,
  revenue_due_15_18m_pct,
  revenue_due_18_21m_pct,
  revenue_due_21_24m_pct,
  revenue_due_24_27m_pct,
  revenue_due_27_30m_pct,
  revenue_due_30_33m_pct,
  revenue_due_33_36m_pct,
  revenue_due_over_36m_pct,
  revenue_due_undetermined_pct,
  revenue_igpm_pct, revenue_inpc_pct, revenue_ipca_pct, revenue_incc_pct,
  created_at, updated_at
FROM fiis_financials;
-- =====================================================================
-- VIEW: fiis_financials_risk
-- =====================================================================
CREATE OR REPLACE VIEW fiis_financials_risk AS
SELECT
  ticker,
  volatility_ratio, sharpe_ratio, treynor_ratio, jensen_alpha, beta_index, sortino_ratio, max_drawdown, r_squared,
  created_at, updated_at
FROM fiis_financials;
-- =====================================================================
-- VIEW: rf_daily_series_mat
-- =====================================================================
CREATE MATERIALIZED VIEW rf_daily_series_mat AS
SELECT
  date_taxes::date AS ref_date,
  (cdi_taxes / 100.0) / 252.0 AS rf_daily
FROM hist_taxes
WHERE cdi_taxes IS NOT NULL
ORDER BY ref_date;
-- =====================================================================
-- INDEX VIEW: rf_daily_series_mat
-- =====================================================================
CREATE INDEX IF NOT EXISTS idx_rf_daily_series_mat ON rf_daily_series_mat(ref_date);
-- =====================================================================
-- VIEW: market_index_series
-- =====================================================================
CREATE MATERIALIZED VIEW market_index_series AS
SELECT
  date_taxes::date AS ref_date,
  'IFIX'::text AS symbol,
  ifix_taxes::numeric AS index_value
FROM hist_taxes
WHERE ifix_taxes IS NOT NULL
  AND ifix_taxes > 0     -- evita zeros
UNION ALL
SELECT
  date_taxes::date AS ref_date,
  'IBOV'::text AS symbol,
  ibovespa_taxes::numeric AS index_value
FROM hist_taxes
WHERE ibovespa_taxes IS NOT NULL
  AND ibovespa_taxes > 0
ORDER BY symbol, ref_date;
-- =====================================================================
-- INDEX VIEW: market_index_series
-- =====================================================================
CREATE INDEX IF NOT EXISTS idx_market_index_series ON market_index_series(symbol, ref_date);
-- =====================================================================
-- VIEW: financials_tickers_typed
-- =====================================================================
CREATE OR REPLACE VIEW financials_tickers_typed AS
WITH raw AS (
  SELECT
    f.ticker,
    NULLIF(TRIM(f.equity::text), '')                    AS equity_raw,
    NULLIF(TRIM(f.total_liabilities::text), '')         AS total_liabilities_raw,
    NULLIF(TRIM(f.total_cash::text), '')                AS total_cash_raw,
    NULLIF(TRIM(f.dividend_to_distribute::text), '')    AS dividend_to_distribute_raw,
    NULLIF(TRIM(f.expected_revenue::text), '')            AS expected_revenue_raw,
    COALESCE(f.shares_count, 0)::numeric                AS shares_count
  FROM financials_tickers f
),
norm AS (
  SELECT
    r.ticker,
    /* troca vírgula por ponto e remove tudo que não é dígito, ponto ou sinal */
    COALESCE(REGEXP_REPLACE(REPLACE(r.equity_raw, ',', '.'),                    '[^0-9\.\-]+', '', 'g'), '') AS equity_txt,
    COALESCE(REGEXP_REPLACE(REPLACE(r.total_liabilities_raw, ',', '.'),         '[^0-9\.\-]+', '', 'g'), '') AS total_liabilities_txt,
    COALESCE(REGEXP_REPLACE(REPLACE(r.total_cash_raw, ',', '.'),                '[^0-9\.\-]+', '', 'g'), '') AS total_cash_txt,
    COALESCE(REGEXP_REPLACE(REPLACE(r.dividend_to_distribute_raw, ',', '.'),    '[^0-9\.\-]+', '', 'g'), '') AS dividend_to_distribute_txt,
    COALESCE(REGEXP_REPLACE(REPLACE(r.expected_revenue_raw, ',', '.'),          '[^0-9\.\-]+', '', 'g'), '') AS expected_revenue_txt,
    r.shares_count
  FROM raw r
)
SELECT
  n.ticker,
  CASE WHEN n.equity_txt ~ '^-?\d+(\.\d+)?$'
       THEN n.equity_txt::numeric ELSE NULL END                 AS equity,
  CASE WHEN n.total_liabilities_txt ~ '^-?\d+(\.\d+)?$'
       THEN n.total_liabilities_txt::numeric ELSE NULL END      AS total_liabilities,
  CASE WHEN n.total_cash_txt ~ '^-?\d+(\.\d+)?$'
       THEN n.total_cash_txt::numeric ELSE NULL END             AS total_cash,
  CASE WHEN n.dividend_to_distribute_txt ~ '^-?\d+(\.\d+)?$'
       THEN n.dividend_to_distribute_txt::numeric ELSE NULL END AS dividend_to_distribute,
  CASE WHEN n.expected_revenue_txt ~ '^-?\d+(\.\d+)?$'
       THEN n.expected_revenue_txt::numeric ELSE NULL END       AS expected_revenue,
  n.shares_count
FROM norm n;
-- =========================================
-- VIEW: fiis_markowitz_universe
-- 1) Universo elegível (view)
-- =========================================
CREATE OR REPLACE VIEW fiis_markowitz_universe AS
SELECT
    cad.ticker,
    cad.ipo_date,
    cad.b3_name,
    cad.classification,
    cad.sector,
    cad.sub_sector,
    cad.target_market,
    cad.shares_count,
    cad.shareholders_count,
    cad.ifil_weight_pct,
    cad.ifix_weight_pct,
    cad.created_at,
    cad.updated_at
FROM fiis_cadastro cad
WHERE cad.ipo_date::date <= (CURRENT_DATE - INTERVAL '5 years');
-- =========================================
-- TABLE: fiis_markowitz_monthly_returns
-- 2) Retornos mensais total return (preço + dividendos)
-- =========================================
CREATE TABLE IF NOT EXISTS fiis_markowitz_monthly_returns (
    ticker        TEXT      NOT NULL,
    ref_month     DATE      NOT NULL,  -- sempre dia 1 do mês
    price_start   NUMERIC   NOT NULL,
    price_end     NUMERIC   NOT NULL,
    dividends_sum NUMERIC   NOT NULL,
    total_return  NUMERIC   NOT NULL,  -- (P_end + D_sum) / P_start - 1
    created_at    TIMESTAMP NOT NULL DEFAULT now(),
    updated_at    TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT pk_fiis_markowitz_monthly_returns PRIMARY KEY (ticker, ref_month)
);
-- =========================================
-- TABLE: fiis_markowitz_stats
-- 3) Estatísticas por FII (µ, σ) na janela
-- =========================================
CREATE TABLE IF NOT EXISTS fiis_markowitz_stats (
    ticker                 TEXT      NOT NULL,
    as_of                  DATE      NOT NULL, -- último mês usado
    obs_months             INTEGER   NOT NULL, -- nº de meses no cálculo
    mean_return_monthly    NUMERIC   NOT NULL,
    stddev_return_monthly  NUMERIC   NOT NULL,
    mean_return_annual     NUMERIC   NOT NULL,
    stddev_return_annual   NUMERIC   NOT NULL,
    created_at             TIMESTAMP NOT NULL DEFAULT now(),
    updated_at             TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT pk_fiis_markowitz_stats PRIMARY KEY (ticker, as_of)
);
-- =========================================
-- TABLE: fiis_markowitz_covariance
-- 4) Matriz de covariância (forma long)
-- =========================================
CREATE TABLE IF NOT EXISTS fiis_markowitz_covariance (
    as_of        DATE      NOT NULL,
    ticker_i     TEXT      NOT NULL,
    ticker_j     TEXT      NOT NULL,
    cov_monthly  NUMERIC   NOT NULL,
    corr         NUMERIC,
    created_at   TIMESTAMP NOT NULL DEFAULT now(),
    updated_at   TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT pk_fiis_markowitz_covariance PRIMARY KEY (as_of, ticker_i, ticker_j)
);
-- =========================================
-- TABLE: fiis_markowitz_frontier
-- 5) Fronteira eficiente oficial (curva global)
-- =========================================
CREATE TABLE IF NOT EXISTS fiis_markowitz_frontier (
    as_of             DATE      NOT NULL,  -- mesma data das stats/cov
    point_id          INTEGER   NOT NULL,  -- ordem na curva
    exp_return_annual NUMERIC   NOT NULL,  -- µ_p
    risk_annual       NUMERIC   NOT NULL,  -- σ_p
    sharpe_ratio      NUMERIC,
    weights_json      JSONB,
    created_at        TIMESTAMP NOT NULL DEFAULT now(),
    updated_at        TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT pk_fiis_markowitz_frontier PRIMARY KEY (as_of, point_id)
);
-- =========================================
-- VIEW: view_markowitz_frontier_plot
-- 6) Grafico Fronteira eficiente oficial (curva global)
-- =========================================
CREATE OR REPLACE VIEW view_markowitz_frontier_plot AS
SELECT
    as_of,
    point_id,
    exp_return_annual,
    risk_annual,
    sharpe_ratio
FROM fiis_markowitz_frontier;
-- =========================================
-- VIEW: view_markowitz_universe_stats
-- 7) Universo com µ e σ (por ticker)
-- =========================================
CREATE OR REPLACE VIEW view_markowitz_universe_stats AS
SELECT
    s.as_of,
    s.ticker,
    s.mean_return_annual,
    s.stddev_return_annual,
    s.obs_months
FROM fiis_markowitz_stats s;
-- =========================================
-- VIEW: view_markowitz_frontier_best_sharpe
-- 8) Best sharpe
-- =========================================
CREATE OR REPLACE VIEW view_markowitz_frontier_best_sharpe AS
SELECT f.*
FROM fiis_markowitz_frontier f
JOIN (
    SELECT as_of,
           MAX(sharpe_ratio) AS max_sharpe
    FROM fiis_markowitz_frontier
    GROUP BY as_of
) s
  ON f.as_of = s.as_of
 AND f.sharpe_ratio = s.max_sharpe;
-- =========================================
-- VIEW: view_markowitz_sirios_portfolios
-- 9) Portifolio Sirios
-- =========================================
CREATE OR REPLACE VIEW view_markowitz_sirios_portfolios AS
SELECT
    as_of,
    portfolio_id,
    n_assets,
    objective,
    exp_return_annual,
    risk_annual,
    sharpe_ratio,
    weights_json
FROM fiis_markowitz_sirios_portfolios;
-- =========================================
-- VIEW: view_markowitz_sirios_portfolios_latest
-- 10) Última data (as_of) de fronteira
-- =========================================
CREATE OR REPLACE VIEW view_markowitz_sirios_portfolios_latest AS
SELECT *
FROM view_markowitz_sirios_portfolios
WHERE as_of = (
    SELECT MAX(as_of) FROM fiis_markowitz_sirios_portfolios
);
-- =====================================================================
-- FUNCTION fn_markowitz_eval_portfolio
-- =====================================================================
CREATE OR REPLACE FUNCTION fn_markowitz_eval_portfolio(
    p_as_of    date,
    p_weights  jsonb
)
RETURNS TABLE (
    as_of              date,
    n_assets           integer,
    exp_return_annual  numeric,
    risk_annual        numeric,
    sharpe_ratio       numeric,
    rf_annual          numeric,
    weights_normalized jsonb
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_n_assets          integer;
    v_mu_annual         numeric;
    v_var_annual        numeric;
    v_sigma_annual      numeric;
    v_rf_annual         numeric;
    v_sharpe            numeric;
    v_weights_normalized jsonb;
BEGIN
    -- se não vier peso nenhum, não retorna nada
    IF p_weights IS NULL OR jsonb_typeof(p_weights) <> 'object' THEN
        RETURN;
    END IF;

    WITH
    -- 1) pesos brutos vindos do JSON
    raw_w AS (
        SELECT
            UPPER(key)                         AS ticker,
            (value::text)::numeric             AS weight_raw
        FROM jsonb_each(p_weights)
        WHERE (value::text)::numeric IS NOT NULL
    ),
    -- 2) normalização para somar 1
    norm AS (
        SELECT
            ticker,
            weight_raw,
            weight_raw / NULLIF(SUM(weight_raw) OVER (), 0) AS weight
        FROM raw_w
    ),
    -- 3) junta com stats (retorno anual por ticker e as_of)
    stats AS (
        SELECT
            n.ticker,
            n.weight,
            s.mean_return_annual
        FROM norm n
        JOIN fiis_markowitz_stats s
          ON s.ticker = n.ticker
         AND s.as_of  = p_as_of
    ),
    mu_calc AS (
        SELECT
            COUNT(*)                         AS n_assets,
            SUM(weight * mean_return_annual) AS exp_return_annual
        FROM stats
    ),
    -- 4) monta pares (i,j) de tickers com pesos
    var_pairs AS (
        SELECT
            si.ticker AS ti,
            sj.ticker AS tj,
            si.weight AS wi,
            sj.weight AS wj
        FROM stats si
        CROSS JOIN stats sj
    ),
    -- 5) junta com matriz de covariância e anualiza (cov_monthly * 12)
    var_calc AS (
        SELECT
            SUM(v.wi * v.wj * c.cov_monthly * 12) AS var_annual
        FROM var_pairs v
        JOIN fiis_markowitz_covariance c
          ON c.as_of    = p_as_of
         AND c.ticker_i = v.ti
         AND c.ticker_j = v.tj
    ),
    -- 6) risk-free anual a partir dos últimos 252 dias úteis até p_as_of
    rf AS (
        SELECT
            COALESCE(
                ((1 + AVG(rf_daily))^252 - 1),
                0
            ) AS rf_annual
        FROM (
            SELECT rf_daily
            FROM rf_daily_series_mat
            WHERE ref_date <= p_as_of
            ORDER BY ref_date DESC
            LIMIT 252
        ) x
    ),
    -- 7) JSON de pesos normalizados que efetivamente entraram no cálculo
    w_json AS (
        SELECT jsonb_object_agg(ticker, weight) AS weights_json
        FROM stats
    )
    SELECT
        mu_calc.n_assets,
        mu_calc.exp_return_annual,
        var_calc.var_annual,
        rf.rf_annual,
        w_json.weights_json
    INTO
        v_n_assets,
        v_mu_annual,
        v_var_annual,
        v_rf_annual,
        v_weights_normalized
    FROM mu_calc, var_calc, rf, w_json;

    -- se não tiver ativo válido / estatística, não retorna nada
    IF v_n_assets IS NULL OR v_n_assets = 0 OR v_var_annual IS NULL THEN
        RETURN;
    END IF;

    v_sigma_annual := sqrt(v_var_annual);

    IF v_sigma_annual IS NULL OR v_sigma_annual <= 0 THEN
        v_sharpe := NULL;
    ELSE
        v_sharpe := (v_mu_annual - v_rf_annual) / v_sigma_annual;
    END IF;

    as_of              := p_as_of;
    n_assets           := v_n_assets;
    exp_return_annual  := v_mu_annual;
    risk_annual        := v_sigma_annual;
    sharpe_ratio       := v_sharpe;
    rf_annual          := v_rf_annual;
    weights_normalized := v_weights_normalized;

    RETURN NEXT;
END;
$$;
-- =========================================
-- VIEW: fiis_rankings_quant
-- =========================================
CREATE MATERIALIZED VIEW fiis_rankings_quant AS
WITH base AS (
  SELECT
    ticker,
    dy_monthly_pct,
    dy_pct,
    sum_anual_dy_amt,
    market_cap_value,
    equity_value,
    sharpe_ratio,
    sortino_ratio,
    volatility_ratio,
    max_drawdown
  FROM fiis_financials -- ou direto de view_fiis_info, se preferir
)
SELECT
  ticker,

  -- Dividendos
  ROW_NUMBER() OVER (ORDER BY dy_pct DESC NULLS LAST)         AS rank_dy_12m,
  ROW_NUMBER() OVER (ORDER BY dy_monthly_pct DESC NULLS LAST) AS rank_dy_monthly,
  ROW_NUMBER() OVER (ORDER BY sum_anual_dy_amt DESC NULLS LAST) AS rank_dividends_12m,

  -- Tamanho / PL
  ROW_NUMBER() OVER (ORDER BY market_cap_value DESC NULLS LAST) AS rank_market_cap,
  ROW_NUMBER() OVER (ORDER BY equity_value DESC NULLS LAST)     AS rank_equity,

  -- Risco / retorno
  ROW_NUMBER() OVER (ORDER BY sharpe_ratio DESC NULLS LAST)   AS rank_sharpe,
  ROW_NUMBER() OVER (ORDER BY sortino_ratio DESC NULLS LAST)  AS rank_sortino,
  ROW_NUMBER() OVER (ORDER BY volatility_ratio ASC NULLS LAST) AS rank_low_volatility,
  ROW_NUMBER() OVER (ORDER BY max_drawdown ASC NULLS LAST)     AS rank_low_drawdown

FROM base;

CREATE UNIQUE INDEX idx_fiis_rankings_quant ON fiis_rankings_quant(ticker);

-- =====================================================================
-- VIEW: fiis_rankings
-- =====================================================================
CREATE OR REPLACE VIEW fiis_rankings AS
SELECT
  i.ticker,
  i.users_ranking_count        AS users_rank_position,
  i.users_rank_movement_count  AS users_rank_net_movement,
  i.sirios_ranking_count       AS sirios_rank_position,
  i.sirios_rank_movement_count AS sirios_rank_net_movement,
  i.ifix_ranking_count         AS ifix_rank_position,
  i.ifix_rank_movement_count   AS ifix_rank_net_movement,
  i.ifil_ranking_count         AS ifil_rank_position,
  i.ifil_rank_movement_count   AS ifil_rank_net_movement,
  q.rank_dy_12m,
  q.rank_dy_monthly,
  q.rank_dividends_12m,
  q.rank_market_cap,
  q.rank_equity,
  q.rank_sharpe,
  q.rank_sortino,
  q.rank_low_volatility,
  q.rank_low_drawdown,
  i.created_at,
  i.updated_at
FROM view_fiis_info i
LEFT JOIN fiis_rankings_quant q USING (ticker);
-- =====================================================================
-- VIEW: fiis_yield_history
-- =====================================================================
CREATE OR REPLACE VIEW fiis_yield_history AS
WITH monthly_dividends AS (
    SELECT
        d.ticker,
        date_trunc('month', d.payment_date::timestamp)::date AS ref_month,
        SUM(d.amount) AS dividends_sum
    FROM hist_dividends d
    GROUP BY
        d.ticker,
        date_trunc('month', d.payment_date::timestamp)
),

monthly_prices AS (
    -- Subselect para normalizar tipos e evitar repetir date_trunc
    SELECT DISTINCT ON (p.ticker, p.month_ref)
        p.ticker,
        p.month_ref       AS ref_month,
        p.close_price     AS price_ref
    FROM (
        SELECT
            fp.ticker,
            fp.traded_at::timestamp              AS traded_ts,
            fp.close_price,
            date_trunc('month', fp.traded_at::timestamp)::date AS month_ref
        FROM fiis_precos fp
    ) p
    ORDER BY
        p.ticker,
        p.month_ref ASC,
        p.traded_ts DESC   -- pega o último preço do mês
)

SELECT
    m.ticker,
    m.ref_month,
    m.dividends_sum,
    mp.price_ref,
    CASE
        WHEN mp.price_ref IS NOT NULL AND mp.price_ref > 0
            THEN m.dividends_sum / mp.price_ref
        ELSE NULL
    END AS dy_monthly
FROM monthly_dividends m
LEFT JOIN monthly_prices mp
    ON mp.ticker = m.ticker
   AND mp.ref_month = m.ref_month;

-- =====================================================================
-- VIEW: fiis_yield_history
-- =====================================================================
CREATE OR REPLACE VIEW fii_overview AS
SELECT
    c.ticker,

    -- Cadastro
    c.display_name,
    c.b3_name,
    c.classification,
    c.sector,
    c.sub_sector,
    c.management_type,
    c.target_market,
    c.is_exclusive,
    c.ifil_weight_pct,
    c.ifix_weight_pct,
    c.shares_count,
    c.shareholders_count,

    -- Snapshot financeiro (D-1)
    s.dy_monthly_pct,
    s.dy_pct AS dy_12m_pct,
    s.sum_anual_dy_amt    AS dividends_12m_amt,
    s.last_dividend_amt,
    s.last_payment_date,
    s.market_cap_value,
    s.enterprise_value,
    s.price_book_ratio,
    s.equity_per_share,
    s.revenue_per_share,
    s.dividend_payout_pct,
    s.growth_rate,
    s.cap_rate,
    s.leverage_ratio,
    s.equity_value,
    s.variation_month_ratio,
    s.variation_year_ratio,
    s.equity_month_ratio,
    s.dividend_reserve_amt,
    s.admin_fee_due_amt,
    s.perf_fee_due_amt,
    s.total_cash_amt,
    s.expected_revenue_amt,
    s.liabilities_total_amt,
    s.created_at  AS snapshot_created_at,
    s.updated_at  AS snapshot_updated_at,

    -- Risco quantitativo
    r.volatility_ratio,
    r.sharpe_ratio,
    r.treynor_ratio,
    r.jensen_alpha,
    r.beta_index,
    r.sortino_ratio,
    r.max_drawdown,
    r.r_squared,
    r.created_at AS risk_created_at,
    r.updated_at AS risk_updated_at,

    -- Rankings
    rk.users_rank_position,
    rk.sirios_rank_position,
    rk.ifix_rank_position,
    rk.ifil_rank_position,
    rk.rank_dy_12m,
    rk.rank_dy_monthly,
    rk.rank_dividends_12m,
    rk.rank_market_cap,
    rk.rank_equity,
    rk.rank_sharpe,
    rk.rank_sortino,
    rk.rank_low_volatility,
    rk.rank_low_drawdown,
    rk.created_at AS rankings_created_at,
    rk.updated_at AS rankings_updated_at

FROM fiis_cadastro c
LEFT JOIN fiis_financials_snapshot s
       ON s.ticker = c.ticker
LEFT JOIN fiis_financials_risk r
       ON r.ticker = c.ticker
LEFT JOIN fiis_rankings rk
       ON rk.ticker = c.ticker;

-- =====================================================================
-- VIEW: client_fiis_dividends_evolution
-- =====================================================================
CREATE OR REPLACE VIEW public.client_fiis_dividends_evolution AS
WITH docs AS (
    SELECT DISTINCT document_number
    FROM equities_positions
)
SELECT
    d.document_number,
    evo.year_reference,
    evo.month_number,
    evo.month_name,
    evo.total_dividends
FROM docs d
CROSS JOIN LATERAL public.calc_fiis_dividends_evolution(d.document_number) AS evo;

-- =====================================================================
-- VIEW: client_fiis_performance_vs_benchmark
-- =====================================================================
CREATE OR REPLACE VIEW public.client_fiis_performance_vs_benchmark AS
WITH docs AS (
    SELECT DISTINCT document_number
    FROM equities_positions
),
bench AS (
    SELECT benchmark_code FROM public.allowed_benchmarks
)
SELECT
    d.document_number,
    b.benchmark_code,
    perf.date_reference,
    perf.portfolio_amount,
    perf.portfolio_return_pct,
    perf.benchmark_value,
    perf.benchmark_return_pct
FROM docs d
CROSS JOIN bench b
CROSS JOIN LATERAL public.calc_fiis_performance_vs_benchmark(
    d.document_number,
    b.benchmark_code
) AS perf;

-- =====================================================================
-- REFRESHS MATERIALIZED VIEW
-- =====================================================================
REFRESH MATERIALIZED VIEW view_fiis_info;
REFRESH MATERIALIZED VIEW view_fiis_history_dividends;
REFRESH MATERIALIZED VIEW view_fiis_history_assets;
REFRESH MATERIALIZED VIEW view_fiis_history_judicial;
REFRESH MATERIALIZED VIEW view_fiis_history_prices;
REFRESH MATERIALIZED VIEW view_fiis_history_news;
REFRESH MATERIALIZED VIEW history_market_indicators;
REFRESH MATERIALIZED VIEW view_history_indexes;
REFRESH MATERIALIZED VIEW view_market_indicators;
REFRESH MATERIALIZED VIEW history_b3_indexes;
REFRESH MATERIALIZED VIEW history_currency_rates;
REFRESH MATERIALIZED VIEW rf_daily_series_mat;
REFRESH MATERIALIZED VIEW market_index_series;
REFRESH MATERIALIZED VIEW fiis_rankings_quant;
REFRESH MATERIALIZED VIEW client_fiis_positions;
-- =====================================================================
-- OWNER EDGE USER
-- =====================================================================
ALTER MATERIALIZED VIEW public.view_fiis_info OWNER TO edge_user;
ALTER MATERIALIZED VIEW public.view_fiis_history_dividends OWNER TO edge_user;
ALTER MATERIALIZED VIEW public.view_fiis_history_assets OWNER TO edge_user;
ALTER MATERIALIZED VIEW public.view_fiis_history_judicial OWNER TO edge_user;
ALTER MATERIALIZED VIEW public.view_fiis_history_prices OWNER TO edge_user;
ALTER MATERIALIZED VIEW public.view_fiis_history_news OWNER TO edge_user;
ALTER MATERIALIZED VIEW public.history_market_indicators OWNER TO edge_user;
ALTER MATERIALIZED VIEW public.view_history_indexes OWNER TO edge_user;
ALTER MATERIALIZED VIEW public.view_market_indicators OWNER TO edge_user;
ALTER MATERIALIZED VIEW public.history_b3_indexes OWNER TO edge_user;
ALTER MATERIALIZED VIEW public.history_currency_rates OWNER TO edge_user;
ALTER MATERIALIZED VIEW public.rf_daily_series_mat OWNER TO edge_user;
ALTER MATERIALIZED VIEW public.market_index_series OWNER TO edge_user;
ALTER MATERIALIZED VIEW public.fiis_rankings_quant OWNER TO edge_user;
ALTER MATERIALIZED VIEW public.client_fiis_positions OWNER TO edge_user;
-- =====================================================================
ALTER VIEW public.fii_overview OWNER TO edge_user;
ALTER VIEW public.fiis_yield_history OWNER TO edge_user;
ALTER VIEW public.fiis_markowitz_universe OWNER TO edge_user;
ALTER VIEW public.fiis_cadastro OWNER TO edge_user;
ALTER VIEW public.fiis_dividendos OWNER TO edge_user;
ALTER VIEW public.fiis_precos OWNER TO edge_user;
ALTER VIEW public.fiis_rankings OWNER TO edge_user;
ALTER VIEW public.fiis_imoveis OWNER TO edge_user;
ALTER VIEW public.fiis_processos OWNER TO edge_user;
ALTER VIEW public.fiis_noticias OWNER TO edge_user;
ALTER VIEW public.fiis_financials_snapshot OWNER TO edge_user;
ALTER VIEW public.fiis_financials_risk OWNER TO edge_user;
ALTER VIEW public.fiis_financials_revenue_schedule OWNER TO edge_user;
ALTER VIEW public.fiis_financials OWNER TO edge_user;
ALTER VIEW public.financials_tickers_typed OWNER TO edge_user;
ALTER VIEW public.view_markowitz_sirios_portfolios_latest OWNER TO edge_user;
ALTER VIEW public.view_markowitz_sirios_portfolios OWNER TO edge_user;
ALTER VIEW public.view_markowitz_frontier_best_sharpe OWNER TO edge_user;
ALTER VIEW public.view_markowitz_universe_stats OWNER TO edge_user;
ALTER VIEW public.view_markowitz_frontier_plot OWNER TO edge_user;
ALTER VIEW public.client_fiis_dividends_evolution OWNER TO edge_user;
ALTER VIEW public.client_fiis_performance_vs_benchmark OWNER TO edge_user;
-- =====================================================================

select * from explain_events
select * from narrator_events