# app/observability/instrumentation.py

from contextlib import contextmanager
from typing import Optional
from opentelemetry.trace import SpanKind
from .runtime import (
    load_config,
    tracer as get_tracer,
    init_planner_metrics,
    init_sql_metrics,
    init_cache_metrics,
    sql_sanitize,
    hash_key,
)
CFG = load_config()
TR_PLANNER = get_tracer("planner")
TR_EXECUTOR = get_tracer("executor")
TR_CACHE = get_tracer("cache")
PM = init_planner_metrics(CFG)
SM = init_sql_metrics(CFG)
CM = init_cache_metrics(CFG)

@contextmanager
def span_planner_route(intent: str, entity: str, confidence: Optional[float] = None, tokens_matched: Optional[int] = None, ontology_version: Optional[str] = None):
    with TR_PLANNER.start_as_current_span("planner.route", kind=SpanKind.INTERNAL) as sp:
        sp.set_attribute("planner.intent", intent)
        sp.set_attribute("planner.entity", entity)
        if confidence is not None:
            sp.set_attribute("planner.confidence", float(confidence))
        if tokens_matched is not None:
            sp.set_attribute("planner.tokens_matched", int(tokens_matched))
        if ontology_version:
            sp.set_attribute("planner.ontology_version", ontology_version)
        yield sp

def planner_mark_decision(intent: str, entity: str, outcome: str):
    if PM["decisions"]:
        PM["decisions"].labels(intent=intent, entity=entity, outcome=outcome).inc()

def planner_stage_observe(stage: str, seconds: float):
    if PM["duration"]:
        PM["duration"].labels(stage=stage).observe(seconds)

@contextmanager
def span_sql_execute(entity: str, db_name: str, statement: str, max_len: int = 512):
    sanitized = sql_sanitize(statement, max_len=max_len)
    with TR_EXECUTOR.start_as_current_span("sql.execute", kind=SpanKind.CLIENT) as sp:
        sp.set_attribute("db.system", "postgresql")
        sp.set_attribute("db.name", db_name)
        sp.set_attribute("db.sql.table", entity)
        sp.set_attribute("db.statement", sanitized)
        yield sp

def sql_observe_duration(entity: str, db_name: str, seconds: float):
    if SM["qhist"]:
        SM["qhist"].labels(entity=entity, db_name=db_name).observe(seconds)

def sql_rows_returned(entity: str, nrows: int):
    if SM["rows"]:
        SM["rows"].labels(entity=entity).inc(nrows)

def sql_error(entity: str, error_code: str):
    if SM["errors"]:
        SM["errors"].labels(entity=entity, error_code=error_code).inc(1)

@contextmanager
def span_cache(op: str, key: str, ttl: Optional[int] = None):
    key_hash = hash_key(key)
    with TR_CACHE.start_as_current_span(f"cache.{op}", kind=SpanKind.CLIENT) as sp:
        sp.set_attribute("cache.system", "redis")
        sp.set_attribute("cache.key_hash", key_hash)
        if ttl is not None:
            sp.set_attribute("cache.ttl", int(ttl))
        yield sp

def cache_observe(op: str, outcome: str, seconds: float):
    if CM["latency"]:
        CM["latency"].labels(op=op).observe(seconds)
    if CM["ops"]:
        CM["ops"].labels(op=op, outcome=outcome).inc(1)
