-- =====================================================================
-- Table: narrator_events
-- =====================================================================
DROP INDEX IF EXISTS idx_narrator_req;
DROP INDEX IF EXISTS idx_narrator_ts;
DROP TABLE IF EXISTS narrator_events;

CREATE TABLE IF NOT EXISTS narrator_events
(
    id bigserial PRIMARY KEY,
    ts timestamp with time zone NOT NULL DEFAULT now(),
    request_id text COLLATE pg_catalog."default" NOT NULL,
    answer_text text COLLATE pg_catalog."default" NOT NULL,
    answer_len integer NOT NULL,
    answer_hash text COLLATE pg_catalog."default" NOT NULL,
    narrator_version text COLLATE pg_catalog."default" NOT NULL,
    narrator_style text COLLATE pg_catalog."default" NOT NULL,
    narrator_ok boolean,
    narrator_notes text COLLATE pg_catalog."default",
    CONSTRAINT narrator_events_req_fk FOREIGN KEY (request_id)
        REFERENCES explain_events (request_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_narrator_req
    ON narrator_events USING btree
    (request_id COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_narrator_ts
    ON narrator_events USING btree
    (ts DESC NULLS FIRST)
    TABLESPACE pg_default;

-- =====================================================================
-- Table: explain_events
-- =====================================================================
DROP INDEX IF EXISTS idx_explain_features_gin;
DROP INDEX IF EXISTS idx_explain_gold;
DROP INDEX IF EXISTS idx_explain_req;
DROP INDEX IF EXISTS idx_explain_route;
DROP INDEX IF EXISTS idx_explain_ts;
DROP TABLE IF EXISTS explain_events;

CREATE TABLE IF NOT EXISTS explain_events
(
    id bigserial PRIMARY KEY,
    ts timestamp with time zone NOT NULL DEFAULT now(),
    request_id text COLLATE pg_catalog."default" NOT NULL,
    question text COLLATE pg_catalog."default" NOT NULL,
    intent text COLLATE pg_catalog."default" NOT NULL,
    entity text COLLATE pg_catalog."default" NOT NULL,
    route_id text COLLATE pg_catalog."default" NOT NULL,
    features jsonb NOT NULL,
    sql_view text COLLATE pg_catalog."default" NOT NULL,
    sql_hash text COLLATE pg_catalog."default" NOT NULL,
    cache_policy text COLLATE pg_catalog."default" NOT NULL,
    latency_ms double precision NOT NULL,
    gold_expected_entity text COLLATE pg_catalog."default",
    gold_expected_intent text COLLATE pg_catalog."default",
    gold_agree boolean
);

CREATE INDEX IF NOT EXISTS idx_explain_features_gin
    ON explain_events USING gin
    (features jsonb_path_ops)
    TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_explain_gold
    ON explain_events USING btree
    (gold_agree ASC NULLS LAST, intent COLLATE pg_catalog."default" ASC NULLS LAST, entity COLLATE pg_catalog."default" ASC NULLS LAST, ts DESC NULLS FIRST)
    TABLESPACE pg_default;

CREATE UNIQUE INDEX IF NOT EXISTS idx_explain_req
    ON explain_events USING btree
    (request_id COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_explain_route
    ON explain_events USING btree
    (intent COLLATE pg_catalog."default" ASC NULLS LAST, entity COLLATE pg_catalog."default" ASC NULLS LAST, route_id COLLATE pg_catalog."default" ASC NULLS LAST, ts DESC NULLS FIRST)
    TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_explain_ts
    ON explain_events USING btree
    (ts DESC NULLS FIRST)
    TABLESPACE pg_default;

-- =====================================================================
-- Table: explain_events
-- =====================================================================
DROP INDEX IF EXISTS idx_explain_features_gin;
DROP INDEX IF EXISTS idx_explain_gold;
DROP INDEX IF EXISTS idx_explain_req;
DROP INDEX IF EXISTS idx_explain_route;
DROP INDEX IF EXISTS idx_explain_ts;
DROP TABLE IF EXISTS explain_events;

CREATE TABLE IF NOT EXISTS explain_events
(
    id bigserial PRIMARY KEY,
    ts timestamp with time zone NOT NULL DEFAULT now(),
    request_id text COLLATE pg_catalog."default" NOT NULL,
    question text COLLATE pg_catalog."default" NOT NULL,
    intent text COLLATE pg_catalog."default" NOT NULL,
    entity text COLLATE pg_catalog."default" NOT NULL,
    route_id text COLLATE pg_catalog."default" NOT NULL,
    features jsonb NOT NULL,
    sql_view text COLLATE pg_catalog."default" NOT NULL,
    sql_hash text COLLATE pg_catalog."default" NOT NULL,
    cache_policy text COLLATE pg_catalog."default" NOT NULL,
    latency_ms double precision NOT NULL,
    gold_expected_entity text COLLATE pg_catalog."default",
    gold_expected_intent text COLLATE pg_catalog."default",
    gold_agree boolean
);

CREATE INDEX IF NOT EXISTS idx_explain_features_gin
    ON explain_events USING gin
    (features jsonb_path_ops)
    TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_explain_gold
    ON explain_events USING btree
    (gold_agree ASC NULLS LAST, intent COLLATE pg_catalog."default" ASC NULLS LAST, entity COLLATE pg_catalog."default" ASC NULLS LAST, ts DESC NULLS FIRST)
    TABLESPACE pg_default;

CREATE UNIQUE INDEX IF NOT EXISTS idx_explain_req
    ON explain_events USING btree
    (request_id COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_explain_route
    ON explain_events USING btree
    (intent COLLATE pg_catalog."default" ASC NULLS LAST, entity COLLATE pg_catalog."default" ASC NULLS LAST, route_id COLLATE pg_catalog."default" ASC NULLS LAST, ts DESC NULLS FIRST)
    TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_explain_ts
    ON explain_events USING btree
    (ts DESC NULLS FIRST)
    TABLESPACE pg_default;

-- =====================================================================
-- Table: narrator_events
-- =====================================================================
DROP INDEX IF EXISTS idx_narrator_req;
DROP INDEX IF EXISTS idx_narrator_ts;
DROP TABLE IF EXISTS narrator_events;

CREATE TABLE IF NOT EXISTS narrator_events
(
    id bigserial PRIMARY KEY,
    ts timestamp with time zone NOT NULL DEFAULT now(),
    request_id text COLLATE pg_catalog."default" NOT NULL,
    answer_text text COLLATE pg_catalog."default" NOT NULL,
    answer_len integer NOT NULL,
    answer_hash text COLLATE pg_catalog."default" NOT NULL,
    narrator_version text COLLATE pg_catalog."default" NOT NULL,
    narrator_style text COLLATE pg_catalog."default" NOT NULL,
    narrator_ok boolean,
    narrator_notes text COLLATE pg_catalog."default",
    CONSTRAINT narrator_events_req_fk FOREIGN KEY (request_id)
        REFERENCES explain_events (request_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_narrator_req
    ON narrator_events USING btree
    (request_id COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_narrator_ts
    ON narrator_events USING btree
    (ts DESC NULLS FIRST)
    TABLESPACE pg_default;

CREATE TABLE IF NOT EXISTS public.allowed_benchmarks (benchmark_code text PRIMARY KEY);
INSERT INTO public.allowed_benchmarks (benchmark_code) VALUES ('CDI'), ('IFIX'), ('IFIL'), ('IBOV')
ON CONFLICT DO NOTHING;
