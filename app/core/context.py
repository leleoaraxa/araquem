# app/core/context.py
import os

from app.cache.rt_cache import RedisCache, CachePolicies, read_through
from app.executor.pg import PgExecutor
from app.observability.runtime import bootstrap, load_config
from app.orchestrator.routing import Orchestrator
from app.planner.planner import Planner

ONTO_PATH = os.getenv("ONTOLOGY_PATH", "data/ontology/entity.yaml")
cfg = load_config()
bootstrap(service_name="api", cfg=cfg)

cache = RedisCache(os.getenv("REDIS_URL", "redis://redis:6379/0"))
policies = CachePolicies()
planner = Planner(ONTO_PATH)
executor = PgExecutor()
orchestrator = Orchestrator(planner, executor, cache=cache, cache_policies=policies)

__all__ = [
    "cache",
    "policies",
    "planner",
    "executor",
    "orchestrator",
    "cfg",
    "ONTO_PATH",
    "RedisCache",
    "CachePolicies",
    "read_through",
    "Planner",
    "PgExecutor",
    "Orchestrator",
]
