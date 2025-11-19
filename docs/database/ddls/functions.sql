DROP FUNCTION IF EXISTS calc_fiis_average_price(text, text, date)

CREATE OR REPLACE FUNCTION calc_fiis_average_price(
    document_number_in  text,
    ticker_in           text,
    reference_date_in   date
)
RETURNS numeric
LANGUAGE plpgsql
AS $$
DECLARE
    v_qty        numeric := 0;
    v_pm         numeric := NULL;
    ev           record;
    v_side       text;
    v_trade_qty  numeric;
    v_trade_px   numeric;
BEGIN
    FOR ev IN
        SELECT *
        FROM (
            -- 1) Eventos de trade (compra/venda)
            SELECT
                'TRADE'::text AS event_kind,
                at.trade_date_time          AS event_time,
                at.side                     AS side,
                at.trade_quantity           AS trade_quantity,
                COALESCE(at.price_value, at.original_trade_price_value) AS trade_price,
                NULL::numeric               AS movement_factor,
                NULL::text                  AS movement_type
            FROM assets_trading at
            WHERE at.document_number = document_number_in
              AND TRIM(at.ticker_symbol) = TRIM(ticker_in)
              AND at.trade_date_time::date <= reference_date_in

            UNION ALL

            -- 2) Eventos de corporate action (Desdobro / Agrupamento)
            --    Fator = nova_quantidade / quantidade_anterior (derivado de equities_positions)
            SELECT
                'CA'::text                  AS event_kind,
                m.reference_date::timestamp AS event_time,
                NULL::text                  AS side,
                NULL::numeric               AS trade_quantity,
                NULL::numeric               AS trade_price,
                (
                    SELECT
                        ep_new.equities_quantity
                        / NULLIF(ep_old.equities_quantity, 0)
                    FROM equities_positions ep_new
                    JOIN LATERAL (
                        SELECT ep2.equities_quantity
                        FROM equities_positions ep2
                        WHERE ep2.document_number = m.document_number
                          AND TRIM(ep2.ticker_symbol) = TRIM(m.ticker_symbol)
                          AND ep2.reference_date  < m.reference_date
                        ORDER BY ep2.reference_date DESC
                        LIMIT 1
                    ) AS ep_old(equities_quantity)
                        ON TRUE
                    WHERE ep_new.document_number = m.document_number
                      AND TRIM(ep_new.ticker_symbol) = TRIM(m.ticker_symbol)
                      AND ep_new.reference_date  = m.reference_date
                    LIMIT 1
                ) AS movement_factor,
                m.movement_type             AS movement_type
            FROM movement m
            WHERE m.document_number        = document_number_in
              AND TRIM(m.ticker_symbol)    = TRIM(ticker_in)
              AND m.reference_date        <= reference_date_in
              AND m.product_category_name  = 'Renda Variavel'
              AND m.product_type_name      = 'FII - Fundo de Investimento Imobiliário'
              AND m.movement_type IN ('Desdobro','Agrupamento')
        ) ev_all
        ORDER BY
            ev_all.event_time,
            CASE WHEN ev_all.event_kind = 'CA' THEN 0 ELSE 1 END
    LOOP
        IF ev.event_kind = 'TRADE' THEN
            -- Normaliza o side
            v_side := upper(COALESCE(ev.side, ''));

            -- COMPRA
            IF v_side LIKE 'C%' OR v_side LIKE 'BUY%' OR v_side LIKE 'COMPRA%' THEN
                v_trade_qty := ev.trade_quantity;
                v_trade_px  := ev.trade_price;

                IF v_trade_qty IS NULL OR v_trade_px IS NULL THEN
                    CONTINUE;
                END IF;

                IF v_pm IS NULL OR v_qty = 0 THEN
                    -- novo ciclo
                    v_pm  := v_trade_px;
                    v_qty := v_trade_qty;
                ELSE
                    IF (v_qty + v_trade_qty) > 0 THEN
                        v_pm := (v_pm * v_qty + v_trade_px * v_trade_qty)
                               / (v_qty + v_trade_qty);
                    END IF;
                    v_qty := v_qty + v_trade_qty;
                END IF;

            -- VENDA
            ELSIF v_side LIKE 'V%' OR v_side LIKE 'SELL%' OR v_side LIKE 'VENDA%' THEN
                v_trade_qty := ev.trade_quantity;

                IF v_trade_qty IS NULL THEN
                    CONTINUE;
                END IF;

                v_qty := v_qty - v_trade_qty;

                -- Se zerou ou ficou negativa, encerra ciclo
                IF v_qty <= 0 THEN
                    v_qty := 0;
                    v_pm  := NULL;
                END IF;
            END IF;

        ELSIF ev.event_kind = 'CA' THEN
            -- Evento de Desdobro/Agrupamento: aplica fator se houver posição
            IF ev.movement_factor IS NOT NULL
               AND ev.movement_factor > 0
               AND v_qty > 0
               AND v_pm IS NOT NULL THEN

                -- Fator calculado como nova_qty / antiga_qty
                -- Então quantidade *= fator e PM /= fator
                v_qty := v_qty * ev.movement_factor;
                v_pm  := v_pm  / ev.movement_factor;
            END IF;
        END IF;
    END LOOP;

    IF v_pm IS NULL THEN
        RETURN NULL;
    END IF;

    RETURN ROUND(v_pm, 2);
END;
$$;

DROP FUNCTION IF EXISTS calc_fiis_portfolio(text)

CREATE OR REPLACE FUNCTION calc_fiis_portfolio(document_number_in text)
RETURNS TABLE (
    ticker_symbol               text,
    equities_quantity           numeric,
    closing_price               numeric,
    average_price               numeric,
    profitability_percentage    numeric,
    update_value                numeric,
    reference_date              date,
    percentage                  numeric
)
LANGUAGE sql
AS $$
    WITH pos AS (
        SELECT
            document_number,
            TRIM(ticker_symbol) AS ticker_symbol,
            equities_quantity,
            closing_price,
            update_value,
            reference_date
        FROM equities_positions
        WHERE document_number       = document_number_in
          AND product_category_name = 'Renda Variavel'
          AND product_type_name     = 'FII - Fundo de Investimento Imobiliário'
          AND specification_code    = 'Cotas'
    ),

    -- 1) última data GLOBAL da carteira
    last_date AS (
        SELECT MAX(reference_date) AS max_date
        FROM pos
    ),

    -- 2) carteira REAL atual = somente registros dessa última data
    current_pos AS (
        SELECT p.*
        FROM pos p
        JOIN last_date ld ON p.reference_date = ld.max_date
    ),

    -- 3) junta carteira atual + preço médio contábil ajustado (trades + movement)
    merged AS (
        SELECT
            c.ticker_symbol,
            c.equities_quantity,
            c.closing_price,
            calc_fiis_average_price(
                document_number_in,
                c.ticker_symbol,
                c.reference_date
            ) AS avg_price,
            c.update_value,
            c.reference_date
        FROM current_pos c
    )

    -- 4) SELECT final: PM arredondado, rentabilidade e % da carteira por VALOR
    SELECT
        ticker_symbol,
        equities_quantity,
        closing_price,
        ROUND(avg_price, 2) AS average_price,
        ROUND(
            CASE
                WHEN avg_price IS NULL OR avg_price = 0
                    THEN NULL
                ELSE (closing_price - avg_price) / avg_price * 100
            END,
            2
        ) AS profitability_percentage,
        update_value,
        reference_date,
        ROUND(
            update_value * 100.0
            / NULLIF(SUM(update_value) OVER (), 0),
            2
        ) AS percentage
    FROM merged
    ORDER BY ticker_symbol, reference_date;
$$;


DROP FUNCTION IF EXISTS calc_fiis_performance_vs_benchmark(text, text)

CREATE OR REPLACE FUNCTION calc_fiis_performance_vs_benchmark(
    document_number_in text,
    benchmark_in text  -- 'IFIX', 'IFIL', 'IBOV', 'CDI'
)
RETURNS TABLE (
    reference_date           date,
    portfolio_value          numeric,
    portfolio_return_pct     numeric,
    benchmark_value          numeric,
    benchmark_return_pct     numeric
)
LANGUAGE plpgsql
AS $$
BEGIN
    --------------------------------------------------------------------
    -- BRANCH CDI
    --------------------------------------------------------------------
    IF upper(benchmark_in) = 'CDI' THEN
        RETURN QUERY
        WITH portfolio AS (
            SELECT
                reference_date,
                SUM(update_value) AS portfolio_value
            FROM equities_positions
            WHERE document_number       = document_number_in
              AND product_category_name = 'Renda Variavel'
              AND product_type_name     = 'FII - Fundo de Investimento Imobiliário'
              AND specification_code    = 'Cotas'
            GROUP BY reference_date
        ),
        bounds AS (
            SELECT
                MIN(reference_date) AS min_date,
                MAX(reference_date) AS max_date
            FROM portfolio
        ),
        dividends AS (
            SELECT
                reference_date,
                SUM(operation_value) AS div_value
            FROM movement
            WHERE document_number       = document_number_in
              AND product_category_name = 'Renda Variavel'
              AND product_type_name     = 'FII - Fundo de Investimento Imobiliário'
              AND movement_type         = 'Rendimento'
              AND operation_type        = 'Credito'
            GROUP BY reference_date
        ),
        port_enriched AS (
            SELECT
                p.reference_date,
                p.portfolio_value,
                COALESCE(d.div_value, 0) AS div_value
            FROM portfolio p
            LEFT JOIN dividends d USING (reference_date)
        ),
        port_with_cum AS (
            SELECT
                reference_date,
                portfolio_value,
                SUM(div_value) OVER (ORDER BY reference_date) AS cum_div,
                FIRST_VALUE(portfolio_value) OVER (ORDER BY reference_date) AS first_value
            FROM port_enriched
        ),
        port_return AS (
            SELECT
                reference_date,
                portfolio_value,
                (portfolio_value + cum_div) / NULLIF(first_value, 0) - 1 AS portfolio_return
            FROM port_with_cum
        ),
        cdi_raw AS (
            SELECT
                h.indicator_date AS indicator_date,
                h.indicator_amt  AS daily_rate
            FROM history_market_indicators h
            JOIN bounds b
              ON h.indicator_date BETWEEN b.min_date AND b.max_date
            WHERE h.indicator_name = 'CDI'
        ),
        cdi_cum AS (
            SELECT
                indicator_date,
                EXP(
                    SUM(LN(1 + daily_rate / 100.0)) OVER (ORDER BY indicator_date)
                ) AS cdi_index
            FROM cdi_raw
        ),
        cdi_norm AS (
            SELECT
                indicator_date,
                cdi_index,
                (cdi_index / FIRST_VALUE(cdi_index) OVER (ORDER BY indicator_date) - 1)
                    AS cdi_return
            FROM cdi_cum
        ),
        joined AS (
            SELECT
                p.reference_date,
                p.portfolio_value,
                p.portfolio_return,
                c.cdi_index AS benchmark_value,
                c.cdi_return AS benchmark_return
            FROM port_return p
            LEFT JOIN cdi_norm c
              ON c.indicator_date = p.reference_date
        )
        SELECT
            j.reference_date,
            j.portfolio_value,
            ROUND(j.portfolio_return * 100, 2) AS portfolio_return_pct,
            j.benchmark_value,
            ROUND(j.benchmark_return * 100, 2) AS benchmark_return_pct
        FROM joined j
        ORDER BY j.reference_date;

    --------------------------------------------------------------------
    -- BRANCH IFIX / IFIL / IBOV
    --------------------------------------------------------------------
    ELSE
        RETURN QUERY
        WITH portfolio AS (
            SELECT
                reference_date,
                SUM(update_value) AS portfolio_value
            FROM equities_positions
            WHERE document_number       = document_number_in
              AND product_category_name = 'Renda Variavel'
              AND product_type_name     = 'FII - Fundo de Investimento Imobiliário'
              AND specification_code    = 'Cotas'
            GROUP BY reference_date
        ),
        bounds AS (
            SELECT
                MIN(reference_date) AS min_date,
                MAX(reference_date) AS max_date
            FROM portfolio
        ),
        dividends AS (
            SELECT
                reference_date,
                SUM(operation_value) AS div_value
            FROM movement
            WHERE document_number       = document_number_in
              AND product_category_name = 'Renda Variavel'
              AND product_type_name     = 'FII - Fundo de Investimento Imobiliário'
              AND movement_type         = 'Rendimento'
              AND operation_type        = 'Credito'
            GROUP BY reference_date
        ),
        port_enriched AS (
            SELECT
                p.reference_date,
                p.portfolio_value,
                COALESCE(d.div_value, 0) AS div_value
            FROM portfolio p
            LEFT JOIN dividends d USING (reference_date)
        ),
        port_with_cum AS (
            SELECT
                reference_date,
                portfolio_value,
                SUM(div_value) OVER (ORDER BY reference_date) AS cum_div,
                FIRST_VALUE(portfolio_value) OVER (ORDER BY reference_date) AS first_value
            FROM port_enriched
        ),
        port_return AS (
            SELECT
                reference_date,
                portfolio_value,
                (portfolio_value + cum_div) / NULLIF(first_value, 0) - 1 AS portfolio_return
            FROM port_with_cum
        ),
        idx_raw AS (
            SELECT
                h.index_date,
                CASE upper(benchmark_in)
                    WHEN 'IFIX' THEN h.ifix_points_count
                    WHEN 'IFIL' THEN h.ifil_points_count
                    WHEN 'IBOV' THEN h.ibov_points_count
                END AS idx_points
            FROM history_b3_indexes h
            JOIN bounds b
              ON h.index_date BETWEEN b.min_date AND b.max_date
        ),
        idx_filtered AS (
            SELECT
                index_date,
                idx_points
            FROM idx_raw
            WHERE idx_points IS NOT NULL
        ),
        idx_norm AS (
            SELECT
                index_date,
                idx_points,
                (idx_points / FIRST_VALUE(idx_points) OVER (ORDER BY index_date) - 1)
                    AS idx_return
            FROM idx_filtered
        ),
        joined AS (
            SELECT
                p.reference_date,
                p.portfolio_value,
                p.portfolio_return,
                i.idx_points AS benchmark_value,
                i.idx_return AS benchmark_return
            FROM port_return p
            LEFT JOIN idx_norm i
              ON i.index_date = p.reference_date
        )
        SELECT
            j.reference_date,
            j.portfolio_value,
            ROUND(j.portfolio_return * 100, 2) AS portfolio_return_pct,
            j.benchmark_value,
            ROUND(j.benchmark_return * 100, 2) AS benchmark_return_pct
        FROM joined j
        ORDER BY j.reference_date;
    END IF;
END;
$$;

SELECT * FROM calc_fiis_performance_vs_benchmark('66140994691', 'IFIX');
SELECT * FROM calc_fiis_performance_vs_benchmark('66140994691', 'CDI');
SELECT reference_date, portfolio_value, portfolio_return_pct, benchmark_value, benchmark_return_pct FROM calc_fiis_performance_vs_benchmark('66140994691', 'CDI'); -- 'IFIX', 'IFIL', 'IBOV', 'CDI'


select * from movement where document_number = '66140994691' order by 3 desc -- Movimentação realizada na conta (Extrato)
select * from equities_positions where document_number = '66140994691'  order by 3 desc -- Posição da carteira do cliente
select * from provisioned_events where document_number = '66140994691' order by 3 desc -- Provisionamento futuro
select * from assets_trading where document_number = '66140994691' -- Negociação de Ativos
