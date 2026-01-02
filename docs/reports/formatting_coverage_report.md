# Relatório de cobertura de formatação

## Resumo por entidade

| Entidade | Status | Observação |
| --- | --- | --- |
| client_fiis_positions | PASS | Cobertura completa |
| client_fiis_dividends_evolution | PASS | Cobertura completa |
| client_fiis_performance_vs_benchmark | PASS | Cobertura completa |
| client_fiis_performance_vs_benchmark_summary | PASS | Cobertura completa |
| fiis_registrations | PASS | Cobertura completa |
| fiis_dividends | PASS | Cobertura completa |
| fiis_yield_history | PASS | Cobertura completa |
| fiis_overview | PASS | Cobertura completa |
| fiis_financials_snapshot | PASS | Cobertura completa |
| fiis_financials_revenue_schedule | PASS | Cobertura completa |
| fiis_financials_risk | PASS | Cobertura completa |
| fiis_real_estate | PASS | Cobertura completa |
| fiis_news | PASS | Cobertura completa |
| fiis_quota_prices | PASS | Cobertura completa |
| fiis_legal_proceedings | PASS | Cobertura completa |
| fiis_rankings | PASS | Cobertura completa |
| history_b3_indexes | PASS | Cobertura completa |
| history_currency_rates | PASS | Cobertura completa |
| history_market_indicators | PASS | Cobertura completa |
| fiis_dividends_yields | PASS | Cobertura completa |
| client_fiis_enriched_portfolio | PASS | Cobertura completa |
| macro_consolidada | PASS | Cobertura completa |

## Placeholders adicionados

| Campo | Filtro |
| --- | --- |
| adj_close_price | currency_br |
| admin_fee_due_amt | currency_br |
| average_price | currency_br |
| cap_rate | percent_raw_br |
| cdi | number_br |
| created_at | datetime_br |
| date_reference | date_br |
| dividend_reserve_amt | currency_br |
| dividends_12m_amt | currency_br |
| dividends_sum | currency_br |
| equity_month_ratio | percent_raw_br |
| equity_per_share | currency_br |
| equity_value | currency_br |
| eur_buy_amt | number_br |
| eur_sell_amt | number_br |
| expected_revenue_amt | currency_br |
| growth_rate | percent_raw_br |
| ibov_points | number_br |
| ibov_points_count | number_br |
| ifil_points_count | number_br |
| ifix_points | number_br |
| ifix_points_count | number_br |
| index_date | date_br |
| indicator_amt | percent_raw_br |
| indicator_date | datetime_br |
| ipca | number_br |
| ipo_date | date_br |
| last_dividend_amt | currency_br |
| last_payment_date | date_br |
| month_dividends_amt | currency_br |
| month_number | int_br |
| month_price_ref | currency_br |
| perf_fee_due_amt | currency_br |
| portfolio_value | currency_br |
| position_date | date_br |
| position_value | currency_br |
| price_book_ratio | percent_raw_br |
| price_ref | currency_br |
| rank_dividends_12m | int_br |
| rank_dy_12m | int_br |
| rank_dy_monthly | int_br |
| rank_equity | int_br |
| rank_low_drawdown | int_br |
| rank_low_volatility | int_br |
| rank_market_cap | int_br |
| rank_sharpe | int_br |
| rank_sortino | int_br |
| rankings_created_at | datetime_br |
| rankings_updated_at | datetime_br |
| rate_date | date_br |
| ref_date | date_br |
| ref_month | date_br |
| revenue_due_12_15m_pct | percent_br |
| revenue_due_15_18m_pct | percent_br |
| revenue_due_18_21m_pct | percent_br |
| revenue_due_21_24m_pct | percent_br |
| revenue_due_24_27m_pct | percent_br |
| revenue_due_27_30m_pct | percent_br |
| revenue_due_30_33m_pct | percent_br |
| revenue_due_33_36m_pct | percent_br |
| revenue_due_3_6m_pct | percent_br |
| revenue_due_6_9m_pct | percent_br |
| revenue_due_undetermined_pct | percent_br |
| revenue_incc_pct | percent_br |
| revenue_inpc_pct | percent_br |
| revenue_per_share | percent_raw_br |
| risk_created_at | datetime_br |
| risk_updated_at | datetime_br |
| selic | number_br |
| shareholders_count | number_br |
| shares_count | number_br |
| snapshot_created_at | datetime_br |
| snapshot_updated_at | datetime_br |
| sum_anual_dy_amt | currency_br |
| total_dividends | currency_br |
| updated_at | datetime_br |
| usd_buy_amt | number_br |
| usd_sell_amt | number_br |
| variation_month_ratio | percent_raw_br |
| variation_year_ratio | percent_raw_br |
| year_reference | int_br |

## Filtros redundantes removidos nos templates

Nenhum ajuste em templates foi necessário.

## Detalhamento por entidade

### client_fiis_positions

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| document_number | string | N/A | - | - |
| position_date | date | Y | date_br | - |
| ticker | string | N/A | - | - |
| fii_name | string | N/A | - | - |
| participant_name | string | N/A | - | - |
| qty | integer | Y | int_br | - |
| closing_price | number | Y | currency_br | - |
| update_value | number | Y | currency_br | - |
| available_quantity | integer | Y | int_br | - |
| average_price | number | Y | currency_br | - |
| profitability_percentage | number | Y | percent_raw_br | - |
| percentage | number | Y | percent_raw_br | - |
| created_at | timestamp | Y | datetime_br | - |
| updated_at | timestamp | Y | datetime_br | - |

### client_fiis_dividends_evolution

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| document_number | string | N/A | - | - |
| year_reference | integer | Y | int_br | - |
| month_number | integer | Y | int_br | - |
| month_name | string | N/A | - | - |
| total_dividends | number | Y | currency_br | - |

### client_fiis_performance_vs_benchmark

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| document_number | string | N/A | - | - |
| benchmark_code | string | N/A | - | - |
| date_reference | date | Y | date_br | - |
| portfolio_amount | number | Y | currency_br | - |
| portfolio_return_pct | number | Y | percent_raw_br | - |
| benchmark_value | number | Y | currency_br | - |
| benchmark_return_pct | number | Y | percent_raw_br | - |

### client_fiis_performance_vs_benchmark_summary

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| document_number | string | N/A | - | - |
| benchmark_code | string | N/A | - | - |
| date_reference | date | Y | date_br | - |
| portfolio_amount | number | Y | currency_br | - |
| portfolio_return_pct | number | Y | percent_raw_br | - |
| benchmark_value | number | Y | currency_br | - |
| benchmark_return_pct | number | Y | percent_raw_br | - |
| excess_return_pct | number | Y | percent_raw_br | - |

### fiis_registrations

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| ticker | string | N/A | - | - |
| fii_cnpj | string | Y | cnpj_mask | - |
| display_name | string | N/A | - | - |
| b3_name | string | N/A | - | - |
| classification | string | N/A | - | - |
| sector | string | N/A | - | - |
| sub_sector | string | N/A | - | - |
| management_type | string | N/A | - | - |
| target_market | string | N/A | - | - |
| is_exclusive | boolean | N/A | - | - |
| isin | string | N/A | - | - |
| ipo_date | date | Y | date_br | - |
| website_url | string | N/A | - | - |
| admin_name | string | N/A | - | - |
| admin_cnpj | string | Y | cnpj_mask | - |
| custodian_name | string | N/A | - | - |
| ifil_weight_pct | number | Y | percent_raw_br | - |
| ifix_weight_pct | number | Y | percent_raw_br | - |
| shares_count | number | Y | number_br | - |
| shareholders_count | number | Y | number_br | - |
| created_at | datetime | Y | datetime_br | - |
| updated_at | datetime | Y | datetime_br | - |

### fiis_dividends

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| ticker | string | N/A | - | - |
| payment_date | date | Y | date_br | - |
| dividend_amt | number | Y | currency_br | - |
| traded_until_date | date | Y | date_br | - |
| created_at | datetime | Y | datetime_br | - |
| updated_at | datetime | Y | datetime_br | - |

### fiis_yield_history

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| ticker | string | N/A | - | - |
| ref_month | date | Y | date_br | - |
| dividends_sum | number | Y | currency_br | - |
| price_ref | number | Y | currency_br | - |
| dy_monthly | number | Y | percent_raw_br | - |

### fiis_overview

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| ticker | string | N/A | - | - |
| display_name | string | N/A | - | - |
| b3_name | string | N/A | - | - |
| classification | string | N/A | - | - |
| sector | string | N/A | - | - |
| sub_sector | string | N/A | - | - |
| management_type | string | N/A | - | - |
| target_market | string | N/A | - | - |
| is_exclusive | boolean | N/A | - | - |
| ifil_weight_pct | number | Y | percent_raw_br | - |
| ifix_weight_pct | number | Y | percent_raw_br | - |
| shares_count | number | Y | number_br | - |
| shareholders_count | number | Y | number_br | - |
| dy_monthly_pct | number | Y | percent_raw_br | - |
| dy_12m_pct | number | Y | percent_raw_br | - |
| dividends_12m_amt | number | Y | currency_br | - |
| last_dividend_amt | number | Y | currency_br | - |
| last_payment_date | date | Y | date_br | - |
| market_cap_value | number | Y | currency_br | - |
| enterprise_value | number | Y | currency_br | - |
| price_book_ratio | number | Y | percent_raw_br | - |
| equity_per_share | number | Y | currency_br | - |
| revenue_per_share | number | Y | percent_raw_br | - |
| dividend_payout_pct | number | Y | percent_raw_br | - |
| growth_rate | number | Y | percent_raw_br | - |
| cap_rate | number | Y | percent_raw_br | - |
| leverage_ratio | number | Y | number_br | - |
| equity_value | number | Y | currency_br | - |
| variation_month_ratio | number | Y | percent_raw_br | - |
| variation_year_ratio | number | Y | percent_raw_br | - |
| equity_month_ratio | number | Y | percent_raw_br | - |
| dividend_reserve_amt | number | Y | currency_br | - |
| admin_fee_due_amt | number | Y | currency_br | - |
| perf_fee_due_amt | number | Y | currency_br | - |
| total_cash_amt | number | Y | currency_br | - |
| expected_revenue_amt | number | Y | currency_br | - |
| liabilities_total_amt | number | Y | currency_br | - |
| snapshot_created_at | datetime | Y | datetime_br | - |
| snapshot_updated_at | datetime | Y | datetime_br | - |
| volatility_ratio | number | Y | number_raw_br | - |
| sharpe_ratio | number | Y | number_raw_br | - |
| treynor_ratio | number | Y | number_raw_br | - |
| jensen_alpha | number | Y | number_raw_br | - |
| beta_index | number | Y | number_raw_br | - |
| sortino_ratio | number | Y | number_raw_br | - |
| max_drawdown | number | Y | percent_br | - |
| r_squared | number | Y | percent_br | - |
| risk_created_at | datetime | Y | datetime_br | - |
| risk_updated_at | datetime | Y | datetime_br | - |
| users_rank_position | integer | Y | int_br | - |
| sirios_rank_position | integer | Y | int_br | - |
| ifix_rank_position | integer | Y | int_br | - |
| ifil_rank_position | integer | Y | int_br | - |
| rank_dy_12m | integer | Y | int_br | - |
| rank_dy_monthly | integer | Y | int_br | - |
| rank_dividends_12m | integer | Y | int_br | - |
| rank_market_cap | integer | Y | int_br | - |
| rank_equity | integer | Y | int_br | - |
| rank_sharpe | integer | Y | int_br | - |
| rank_sortino | integer | Y | int_br | - |
| rank_low_volatility | integer | Y | int_br | - |
| rank_low_drawdown | integer | Y | int_br | - |
| rankings_created_at | datetime | Y | datetime_br | - |
| rankings_updated_at | datetime | Y | datetime_br | - |

### fiis_financials_snapshot

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| ticker | string | N/A | - | - |
| dy_monthly_pct | number | Y | percent_raw_br | - |
| dy_pct | number | Y | percent_raw_br | - |
| sum_anual_dy_amt | number | Y | currency_br | - |
| last_dividend_amt | number | Y | currency_br | - |
| last_payment_date | date | Y | date_br | - |
| market_cap_value | number | Y | currency_br | - |
| enterprise_value | number | Y | currency_br | - |
| price_book_ratio | number | Y | percent_raw_br | - |
| equity_per_share | number | Y | currency_br | - |
| revenue_per_share | number | Y | percent_raw_br | - |
| dividend_payout_pct | number | Y | percent_raw_br | - |
| growth_rate | number | Y | percent_raw_br | - |
| cap_rate | number | Y | percent_raw_br | - |
| leverage_ratio | number | Y | number_br | - |
| equity_value | number | Y | currency_br | - |
| variation_month_ratio | number | Y | percent_raw_br | - |
| variation_year_ratio | number | Y | percent_raw_br | - |
| admin_fee_due_amt | number | Y | currency_br | - |
| perf_fee_due_amt | number | Y | currency_br | - |
| total_cash_amt | number | Y | currency_br | - |
| expected_revenue_amt | number | Y | currency_br | - |
| liabilities_total_amt | number | Y | currency_br | - |
| equity_month_ratio | number | Y | percent_raw_br | - |
| dividend_reserve_amt | number | Y | currency_br | - |
| created_at | datetime | Y | datetime_br | - |
| updated_at | datetime | Y | datetime_br | - |

### fiis_financials_revenue_schedule

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| ticker | string | N/A | - | - |
| revenue_due_0_3m_pct | number | Y | percent_br | - |
| revenue_due_3_6m_pct | number | Y | percent_br | - |
| revenue_due_6_9m_pct | number | Y | percent_br | - |
| revenue_due_9_12m_pct | number | Y | percent_br | - |
| revenue_due_12_15m_pct | number | Y | percent_br | - |
| revenue_due_15_18m_pct | number | Y | percent_br | - |
| revenue_due_18_21m_pct | number | Y | percent_br | - |
| revenue_due_21_24m_pct | number | Y | percent_br | - |
| revenue_due_24_27m_pct | number | Y | percent_br | - |
| revenue_due_27_30m_pct | number | Y | percent_br | - |
| revenue_due_30_33m_pct | number | Y | percent_br | - |
| revenue_due_33_36m_pct | number | Y | percent_br | - |
| revenue_due_over_36m_pct | number | Y | percent_br | - |
| revenue_due_undetermined_pct | number | Y | percent_br | - |
| revenue_igpm_pct | number | Y | percent_br | - |
| revenue_inpc_pct | number | Y | percent_br | - |
| revenue_ipca_pct | number | Y | percent_br | - |
| revenue_incc_pct | number | Y | percent_br | - |
| created_at | datetime | Y | datetime_br | - |
| updated_at | datetime | Y | datetime_br | - |

### fiis_financials_risk

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| ticker | string | N/A | - | - |
| volatility_ratio | number | Y | number_raw_br | - |
| sharpe_ratio | number | Y | number_raw_br | - |
| treynor_ratio | number | Y | number_raw_br | - |
| jensen_alpha | number | Y | number_raw_br | - |
| beta_index | number | Y | number_raw_br | - |
| sortino_ratio | number | Y | number_raw_br | - |
| max_drawdown | number | Y | percent_br | - |
| r_squared | number | Y | percent_br | - |
| created_at | datetime | Y | datetime_br | - |
| updated_at | datetime | Y | datetime_br | - |

### fiis_real_estate

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| ticker | string | N/A | - | - |
| asset_name | string | N/A | - | - |
| asset_class | string | N/A | - | - |
| asset_address | string | N/A | - | - |
| total_area | number | Y | number_m2_br | - |
| units_count | integer | Y | int_br | - |
| vacancy_ratio | number | Y | percent_raw_br | - |
| non_compliant_ratio | number | Y | percent_raw_br | - |
| assets_status | string | N/A | - | - |
| created_at | datetime | Y | datetime_br | - |
| updated_at | datetime | Y | datetime_br | - |

### fiis_news

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| ticker | string | N/A | - | - |
| source | string | N/A | - | - |
| title | string | N/A | - | - |
| tags | string | N/A | - | - |
| description | string | N/A | - | - |
| url | string | N/A | - | - |
| image_url | string | N/A | - | - |
| published_at | datetime | Y | datetime_br | - |
| created_at | datetime | Y | datetime_br | - |
| updated_at | datetime | Y | datetime_br | - |

### fiis_quota_prices

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| ticker | string | N/A | - | - |
| traded_at | date | Y | date_br | - |
| close_price | number | Y | currency_br | - |
| adj_close_price | number | Y | currency_br | - |
| open_price | number | Y | currency_br | - |
| max_price | number | Y | currency_br | - |
| min_price | number | Y | currency_br | - |
| daily_variation_pct | number | Y | percent_raw_br | - |
| created_at | datetime | Y | datetime_br | - |
| updated_at | datetime | Y | datetime_br | - |

### fiis_legal_proceedings

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| ticker | string | N/A | - | - |
| process_number | string | N/A | - | - |
| judgment | string | N/A | - | - |
| instance | string | N/A | - | - |
| initiation_date | date | Y | date_br | - |
| cause_amt | number | Y | currency_br | - |
| process_parts | string | N/A | - | - |
| loss_risk_pct | number | Y | percent_br | - |
| main_facts | string | N/A | - | - |
| loss_impact_analysis | string | N/A | - | - |
| created_at | timestamp | Y | datetime_br | - |
| updated_at | timestamp | Y | datetime_br | - |

### fiis_rankings

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| ticker | string | N/A | - | - |
| users_rank_position | integer | Y | int_br | - |
| users_rank_net_movement | integer | Y | int_br | - |
| sirios_rank_position | integer | Y | int_br | - |
| sirios_rank_net_movement | integer | Y | int_br | - |
| ifix_rank_position | integer | Y | int_br | - |
| ifix_rank_net_movement | integer | Y | int_br | - |
| ifil_rank_position | integer | Y | int_br | - |
| ifil_rank_net_movement | integer | Y | int_br | - |
| rank_dy_12m | integer | Y | int_br | - |
| rank_dy_monthly | integer | Y | int_br | - |
| rank_dividends_12m | integer | Y | int_br | - |
| rank_market_cap | integer | Y | int_br | - |
| rank_equity | integer | Y | int_br | - |
| rank_sharpe | integer | Y | int_br | - |
| rank_sortino | integer | Y | int_br | - |
| rank_low_volatility | integer | Y | int_br | - |
| rank_low_drawdown | integer | Y | int_br | - |
| created_at | datetime | Y | datetime_br | - |
| updated_at | datetime | Y | datetime_br | - |

### history_b3_indexes

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| index_date | datetime | Y | date_br | - |
| ibov_points_count | number | Y | number_br | - |
| ibov_var_pct | number | Y | percent_raw_br | - |
| ifix_points_count | number | Y | number_br | - |
| ifix_var_pct | number | Y | percent_raw_br | - |
| ifil_points_count | number | Y | number_br | - |
| ifil_var_pct | number | Y | percent_raw_br | - |
| created_at | datetime | Y | datetime_br | - |
| updated_at | datetime | Y | datetime_br | - |

### history_currency_rates

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| rate_date | datetime | Y | date_br | - |
| usd_buy_amt | number | Y | number_br | - |
| usd_sell_amt | number | Y | number_br | - |
| usd_var_pct | number | Y | percent_raw_br | - |
| eur_buy_amt | number | Y | number_br | - |
| eur_sell_amt | number | Y | number_br | - |
| eur_var_pct | number | Y | percent_raw_br | - |
| created_at | datetime | Y | datetime_br | - |
| updated_at | datetime | Y | datetime_br | - |

### history_market_indicators

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| indicator_date | datetime | Y | datetime_br | - |
| indicator_name | string | N/A | - | - |
| indicator_amt | number | Y | percent_raw_br | - |
| created_at | datetime | Y | datetime_br | - |
| updated_at | datetime | Y | datetime_br | - |

### fiis_dividends_yields

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| ticker | string | N/A | - | - |
| display_name | string | N/A | - | - |
| sector | string | N/A | - | - |
| sub_sector | string | N/A | - | - |
| classification | string | N/A | - | - |
| management_type | string | N/A | - | - |
| target_market | string | N/A | - | - |
| traded_until_date | date | Y | date_br | - |
| payment_date | date | Y | date_br | - |
| dividend_amt | number | Y | currency_br | - |
| ref_month | date | Y | date_br | - |
| month_dividends_amt | number | Y | currency_br | - |
| month_price_ref | number | Y | currency_br | - |
| dy_monthly | number | Y | percent_raw_br | - |
| dy_12m_pct | number | Y | percent_raw_br | - |
| dy_current_monthly_pct | number | Y | percent_raw_br | - |
| dividends_12m_amt | number | Y | currency_br | - |
| last_dividend_amt | number | Y | currency_br | - |
| last_payment_date | date | Y | date_br | - |

### client_fiis_enriched_portfolio

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| document_number | string | N/A | - | - |
| position_date | date | Y | date_br | - |
| ticker | string | N/A | - | - |
| fii_name | string | N/A | - | - |
| qty | integer | Y | int_br | - |
| closing_price | number | Y | currency_br | - |
| position_value | number | Y | currency_br | - |
| portfolio_value | number | Y | currency_br | - |
| weight_pct | number | Y | percent_raw_br | - |
| sector | string | N/A | - | - |
| sub_sector | string | N/A | - | - |
| classification | string | N/A | - | - |
| management_type | string | N/A | - | - |
| target_market | string | N/A | - | - |
| fii_cnpj | string | Y | cnpj_mask | - |
| dy_12m_pct | number | Y | percent_raw_br | - |
| dy_monthly_pct | number | Y | percent_raw_br | - |
| dividends_12m_amt | number | Y | currency_br | - |
| market_cap_value | number | Y | currency_br | - |
| equity_value | number | Y | currency_br | - |
| volatility_ratio | number | Y | number_raw_br | - |
| sharpe_ratio | number | Y | number_raw_br | - |
| sortino_ratio | number | Y | number_raw_br | - |
| max_drawdown | number | Y | percent_br | - |
| beta_index | number | Y | number_raw_br | - |
| sirios_rank_position | integer | Y | int_br | - |
| ifix_rank_position | integer | Y | int_br | - |
| rank_dy_12m | integer | Y | int_br | - |
| rank_sharpe | integer | Y | int_br | - |

### macro_consolidada

| Coluna | Tipo | Placeholder? | Filtro | Fallback |
| --- | --- | --- | --- | --- |
| ref_date | date | Y | date_br | - |
| ipca | number | Y | number_br | - |
| selic | number | Y | number_br | - |
| cdi | number | Y | number_br | - |
| ifix_points | number | Y | number_br | - |
| ifix_var_pct | number | Y | percent_raw_br | - |
| ibov_points | number | Y | number_br | - |
| ibov_var_pct | number | Y | percent_raw_br | - |
| usd_buy_amt | number | Y | number_br | - |
| usd_sell_amt | number | Y | number_br | - |
| usd_var_pct | number | Y | percent_raw_br | - |
| eur_buy_amt | number | Y | number_br | - |
| eur_sell_amt | number | Y | number_br | - |
| eur_var_pct | number | Y | percent_raw_br | - |
