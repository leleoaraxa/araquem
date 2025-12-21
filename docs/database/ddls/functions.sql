DROP FUNCTION IF EXISTS calc_fiis_average_price(text, text, date);

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

DROP FUNCTION IF EXISTS calc_fiis_portfolio(text);

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


DROP FUNCTION IF EXISTS calc_fiis_performance_vs_benchmark(text, text);


CREATE OR REPLACE FUNCTION public.calc_fiis_performance_vs_benchmark(
	p_document_number text,
	p_indices text[],
	p_start_date date DEFAULT NULL::date,
	p_end_date date DEFAULT NULL::date)
    RETURNS TABLE(ref_date date, month_year text, series_id text, series_kind text, cumulative_return numeric, cumulative_index numeric, cumulative_dividends numeric)
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
BEGIN
    --------------------------------------------------------------------
    -- 0) Sanidade dos parâmetros
    --------------------------------------------------------------------
    IF p_indices IS NULL
       OR array_length(p_indices, 1) IS NULL
       OR array_length(p_indices, 1) = 0 THEN
        RAISE EXCEPTION 'Informe pelo menos um benchmark (CDI, IFIX, IFIL, IBOVESPA).';
    END IF;

    IF array_length(p_indices, 1) > 4 THEN
        RAISE EXCEPTION 'Número máximo de benchmarks é 4. Recebido: %',
            array_length(p_indices, 1);
    END IF;

    IF EXISTS (
        SELECT 1
        FROM unnest(p_indices) AS b(val)
        WHERE upper(val) NOT IN ('CDI','IFIX','IFIL','IBOVESPA')
    ) THEN
        RAISE EXCEPTION 'Benchmarks inválidos. Use apenas: CDI, IFIX, IFIL, IBOVESPA.';
    END IF;

    --------------------------------------------------------------------
    -- 1) Janela: p_start_date / p_end_date + limites da base
    --------------------------------------------------------------------
    RETURN QUERY
    WITH raw_bounds AS (
        SELECT
            MIN(date_trunc('month', h.date_taxes)::date) AS hist_min_month,
            MAX(date_trunc('month', h.date_taxes)::date) AS hist_max_month
        FROM hist_taxes h
    ),
    params AS (
        SELECT
            LEAST(
                COALESCE(date_trunc('month', p_end_date)::date,
                         date_trunc('month', CURRENT_DATE)::date),
                rb.hist_max_month
            ) AS max_month,
            GREATEST(
                COALESCE(date_trunc('month', p_start_date)::date,
                         rb.hist_min_month),
                rb.hist_min_month
            ) AS min_month
        FROM raw_bounds rb
    ),

    --------------------------------------------------------------------
    -- 2) Taxes mensais (CDI/SELIC mensal + níveis dos índices)
    --------------------------------------------------------------------
    taxes AS (
        SELECT DISTINCT ON (date_trunc('month', h.date_taxes))
               date_trunc('month', h.date_taxes)::date              AS ref_month,
               to_char(date_trunc('month', h.date_taxes),'MM/YYYY') AS month_year,
               TRUNC(POWER(1 + h.cdi_taxes   / 100.0, 1.0/12) - 1, 6) AS cdi_mensal,
               TRUNC(POWER(1 + h.selic_taxes / 100.0, 1.0/12) - 1, 6) AS selic_mensal,
               h.ibovespa_taxes                                       AS ibov,
               h.ifix_taxes                                           AS ifix,
               h.ifil_taxes                                           AS ifil
        FROM hist_taxes h
        JOIN params p
          ON h.date_taxes::date >= p.min_month
         AND h.date_taxes::date <  p.max_month + INTERVAL '1 month'
        ORDER BY date_trunc('month', h.date_taxes),
                 h.date_taxes DESC
    ),

    --------------------------------------------------------------------
    -- 3) Dividendos mensais
    --------------------------------------------------------------------
    dividends AS (
        SELECT
            date_trunc('month', reference_date)::date AS ref_month,
            SUM(operation_value)                      AS dividends
        FROM movement
        JOIN params p
          ON reference_date::date >= p.min_month
         AND reference_date::date <  p.max_month + INTERVAL '1 month'
        WHERE document_number       = p_document_number
          AND product_category_name = 'Renda Variavel'
          AND product_type_name     = 'FII - Fundo de Investimento Imobiliário'
          AND movement_type         = 'Rendimento'
          AND operation_type        = 'Credito'
        GROUP BY 1
    ),

    --------------------------------------------------------------------
    -- 4) Carteira diária
    -- Ajustes:
    --   (a) MATERIALIZED: garante 1 cálculo do agregado, evita loops explosivos
    --   (b) corte superior seguro: não precisamos de datas > fim da janela
    --------------------------------------------------------------------
    wallet_daily AS MATERIALIZED (
        SELECT
            ep.reference_date::date AS ref_date,
            SUM(ep.update_value)    AS portfolio_value
        FROM equities_positions ep
        JOIN params p
          ON ep.reference_date::date <= (p.max_month + INTERVAL '1 month - 1 day')::date
        WHERE ep.document_number       = p_document_number
          AND ep.product_category_name = 'Renda Variavel'
          AND ep.product_type_name     = 'FII - Fundo de Investimento Imobiliário'
          AND ep.specification_code    = 'Cotas'
        GROUP BY ep.reference_date::date
    ),

    -- Para cada mês da janela, pega o último valor de carteira (SET-BASED)
    wallet AS MATERIALIZED (
        SELECT
            x.ref_month,
            x.portfolio_value
        FROM (
            SELECT
                t.ref_month,
                wd.portfolio_value,
                row_number() OVER (
                    PARTITION BY t.ref_month
                    ORDER BY wd.ref_date DESC
                ) AS rn
            FROM taxes t
            LEFT JOIN wallet_daily wd
              ON wd.ref_date <= (t.ref_month + INTERVAL '1 month - 1 day')::date
        ) x
        WHERE x.rn = 1
    ),

    --------------------------------------------------------------------
    -- 5) Grid mensal: CDI / índices / carteira / dividendos
    --------------------------------------------------------------------
    base_months AS (
        SELECT
            t.ref_month,
            t.month_year,
            t.cdi_mensal,
            t.selic_mensal,
            t.ibov,
            t.ifix,
            t.ifil,
            COALESCE(d.dividends, 0)           AS dividends,
            COALESCE(w.portfolio_value, 0.0)   AS portfolio_value
        FROM taxes t
        LEFT JOIN dividends d USING (ref_month)
        LEFT JOIN wallet    w USING (ref_month)
    ),

    --------------------------------------------------------------------
    -- 6) Dividendos acumulados por mês
    --------------------------------------------------------------------
    dividends_cum AS (
        SELECT
            b.ref_month,
            b.month_year,
            b.dividends,
            COALESCE(
                SUM(b.dividends) OVER (ORDER BY b.ref_month),
                0
            ) AS cumulative_dividends
        FROM base_months b
    ),

    --------------------------------------------------------------------
    -- 7) Séries mensais de retorno (wallet + índices)
    --------------------------------------------------------------------
    wallet_series AS (
        SELECT
            b.ref_month                    AS ref_date,
            b.month_year,
            'WALLET'::text                 AS series_id,
            'WALLET'::text                 AS series_kind,
            CASE
                WHEN b.portfolio_value IS NULL
                     OR b.portfolio_value = 0
                     OR b.dividends = 0
                THEN 0.0
                ELSE b.dividends / b.portfolio_value
            END AS monthly_return
        FROM base_months b
    ),

    indices_cdi AS (
        SELECT
            b.ref_month                    AS ref_date,
            b.month_year,
            'CDI'::text                    AS series_id,
            'INDEX'::text                  AS series_kind,
            b.cdi_mensal                   AS monthly_return
        FROM base_months b
        WHERE 'CDI' = ANY (p_indices)
    ),

    indices_selic AS (
        SELECT
            b.ref_month                    AS ref_date,
            b.month_year,
            'SELIC'::text                  AS series_id,
            'INDEX'::text                  AS series_kind,
            b.selic_mensal                 AS monthly_return
        FROM base_months b
        WHERE 'SELIC' = ANY (p_indices)
    ),

    indices_ifix AS (
        SELECT
            b.ref_month                    AS ref_date,
            b.month_year,
            'IFIX'::text                   AS series_id,
            'INDEX'::text                  AS series_kind,
            CASE
                WHEN lag(b.ifix) OVER (ORDER BY b.ref_month) IS NULL
                     OR lag(b.ifix) OVER (ORDER BY b.ref_month) = 0
                THEN 0.0
                ELSE b.ifix
                     / NULLIF(
                         lag(b.ifix) OVER (ORDER BY b.ref_month),
                         0
                       ) - 1.0
            END AS monthly_return
        FROM base_months b
        WHERE 'IFIX' = ANY (p_indices)
    ),

    indices_ifil AS (
        SELECT
            b.ref_month                    AS ref_date,
            b.month_year,
            'IFIL'::text                   AS series_id,
            'INDEX'::text                  AS series_kind,
            CASE
                WHEN lag(b.ifil) OVER (ORDER BY b.ref_month) IS NULL
                     OR lag(b.ifil) OVER (ORDER BY b.ref_month) = 0
                THEN 0.0
                ELSE b.ifil
                     / NULLIF(
                         lag(b.ifil) OVER (ORDER BY b.ref_month),
                         0
                       ) - 1.0
            END AS monthly_return
        FROM base_months b
        WHERE 'IFIL' = ANY (p_indices)
    ),

    indices_ibov AS (
        SELECT
            b.ref_month                    AS ref_date,
            b.month_year,
            'IBOV'::text                   AS series_id,
            'INDEX'::text                  AS series_kind,
            CASE
                WHEN lag(b.ibov) OVER (ORDER BY b.ref_month) IS NULL
                     OR lag(b.ibov) OVER (ORDER BY b.ref_month) = 0
                THEN 0.0
                ELSE b.ibov
                     / NULLIF(
                         lag(b.ibov) OVER (ORDER BY b.ref_month),
                         0
                       ) - 1.0
            END AS monthly_return
        FROM base_months b
        WHERE 'IBOVESPA' = ANY (p_indices)
    ),

    indices_raw AS (
        SELECT * FROM indices_cdi
        UNION ALL
        SELECT * FROM indices_selic
        UNION ALL
        SELECT * FROM indices_ifix
        UNION ALL
        SELECT * FROM indices_ifil
        UNION ALL
        SELECT * FROM indices_ibov
    ),

    all_series AS (
        SELECT * FROM wallet_series
        UNION ALL
        SELECT * FROM indices_raw
    ),

    --------------------------------------------------------------------
    -- 8) Crescimento acumulado e normalização
    --------------------------------------------------------------------
    series_cum AS (
        SELECT
            s.ref_date,
            s.month_year,
            s.series_id,
            s.series_kind,
            s.monthly_return,
            EXP(
                SUM(
                    LN(1.0 + s.monthly_return)
                ) OVER (
                    PARTITION BY s.series_kind, s.series_id
                    ORDER BY s.ref_date
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                )
            ) AS growth
        FROM all_series s
    ),

    series_norm AS (
        SELECT
            sc.ref_date,
            sc.month_year,
            sc.series_id,
            sc.series_kind,
            sc.growth
              / FIRST_VALUE(sc.growth) OVER (
                    PARTITION BY sc.series_kind, sc.series_id
                    ORDER BY sc.ref_date
                ) AS norm_index
        FROM series_cum sc
    ),

    series_final AS (
        SELECT
            sn.ref_date,
            sn.month_year,
            sn.series_id,
            sn.series_kind,
            sn.norm_index,
            LAG(sn.norm_index) OVER (
                PARTITION BY sn.series_kind, sn.series_id
                ORDER BY sn.ref_date
            ) AS prev_index
        FROM series_norm sn
    )

    --------------------------------------------------------------------
    -- 9) Saída final com dividendos acumulados
    --------------------------------------------------------------------
    SELECT
        sf.ref_date,
        sf.month_year,
        sf.series_id,
        sf.series_kind,
        CASE
            WHEN sf.prev_index IS NULL THEN 0.00
            ELSE ROUND(((sf.norm_index / sf.prev_index) - 1.0) * 100.0, 2)
        END AS cumulative_return,
        ROUND(sf.norm_index * 100.0, 2) AS cumulative_index,
        COALESCE(dc.cumulative_dividends, 0.0) AS cumulative_dividends
    FROM series_final sf
    LEFT JOIN dividends_cum dc
           ON dc.ref_month = sf.ref_date
    ORDER BY sf.ref_date, sf.series_kind, sf.series_id;

END;
$BODY$;

DROP FUNCTION IF EXISTS calc_fiis_dividends_evolution(text);

CREATE OR REPLACE FUNCTION calc_fiis_dividends_evolution(
    document_number_in text
)
RETURNS TABLE (
    year_reference    integer,
    month_number      integer,
    month_name        text,
    total_dividends   numeric
)
LANGUAGE sql
AS $$
    WITH base AS (
        SELECT
            reference_date,
            date_part('year',  reference_date)::int  AS year_reference,
            date_part('month', reference_date)::int  AS month_number,
            operation_value
        FROM movement
        WHERE document_number       = document_number_in
          AND product_category_name = 'Renda Variavel'
          AND product_type_name     = 'FII - Fundo de Investimento Imobiliário'
          AND movement_type         = 'Rendimento'
          AND operation_type        = 'Credito'
    )
    SELECT
        year_reference,
        month_number,
        -- Nome do mês (respeita o locale do PostgreSQL, normalmente PT-BR)
        to_char(make_date(year_reference, month_number, 1), 'TMMonth') AS month_name,
        SUM(operation_value) AS total_dividends
    FROM base
    GROUP BY year_reference, month_number
    ORDER BY year_reference, month_number;
$$;

DROP FUNCTION IF EXISTS fc_fiis_portfolio(text);

CREATE OR REPLACE FUNCTION fc_fiis_portfolio(document_number_in text)
RETURNS TABLE (
	document_number             text,
    reference_date              date,
	ticker_symbol               text,
	corporation_name            text,
	participant_name            text,
    equities_quantity           numeric,
    closing_price               numeric,
    update_value                numeric,
	available_quantity          numeric,
	average_price               numeric,
    profitability_percentage    numeric,
    percentage                  numeric
)
LANGUAGE sql
AS $$
    WITH pos AS (
        SELECT
            document_number,
            reference_date,
			TRIM(ticker_symbol) AS ticker_symbol,
			corporation_name AS fii_name,
			participant_name AS stock_broker,
            equities_quantity,
            closing_price,
            update_value,
			available_quantity
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
			c.document_number,
			c.reference_date,
            c.ticker_symbol,
			c.fii_name,
			c.stock_broker,
            c.equities_quantity,
            c.closing_price,
			c.update_value,
			c.available_quantity,
            calc_fiis_average_price(
                document_number_in,
                c.ticker_symbol,
                c.reference_date
            ) AS avg_price
        FROM current_pos c
    )

    -- 4) SELECT final: PM arredondado, rentabilidade e % da carteira por VALOR
    SELECT
		document_number,
		reference_date,
        ticker_symbol,
		fii_name,
		stock_broker,
        equities_quantity,
        closing_price,
        update_value,
		available_quantity,
		ROUND(avg_price, 2) AS average_price,
        ROUND(
            CASE
                WHEN avg_price IS NULL OR avg_price = 0
                    THEN NULL
                ELSE (closing_price - avg_price) / avg_price * 100
            END,
            2
        ) AS profitability_percentage,
        ROUND(
            update_value * 100.0
            / NULLIF(SUM(update_value) OVER (), 0),
            2
        ) AS percentage
    FROM merged
    ORDER BY ticker_symbol, reference_date;
$$;
