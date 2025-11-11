CREATE TABLE IF NOT EXISTS explain_events (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  request_id TEXT NOT NULL,
  question TEXT NOT NULL,
  intent TEXT NOT NULL,
  entity TEXT NOT NULL,
  route_id TEXT NOT NULL,
  features JSONB NOT NULL,
  sql_view TEXT NOT NULL,
  sql_hash TEXT NOT NULL,
  cache_policy TEXT NOT NULL,
  latency_ms DOUBLE PRECISION NOT NULL,
  gold_expected_entity TEXT,
  gold_expected_intent TEXT,
  gold_agree BOOLEAN
);


CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_explain_req
  ON explain_events (request_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_explain_ts
  ON explain_events (ts DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_explain_route
  ON explain_events (intent, entity, route_id, ts DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_explain_gold
  ON explain_events (gold_agree, intent, entity, ts DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_explain_features_gin
  ON explain_events USING GIN (features jsonb_path_ops);

ALTER TABLE public.explain_events OWNER TO edge_user;
