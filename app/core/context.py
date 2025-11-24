# app/core/context.py
import os

from app.cache.rt_cache import RedisCache, CachePolicies, read_through
from app.executor.pg import PgExecutor
from app.observability.runtime import bootstrap, load_config
from app.orchestrator.routing import Orchestrator
from app.planner.planner import Planner

# NOVO: Context Manager canônico
from app.context.context_manager import ContextManager

ONTO_PATH = os.getenv("ONTOLOGY_PATH", "data/ontology/entity.yaml")
cfg = load_config()
bootstrap(service_name="api", cfg=cfg)

# ----------------------------
# BACKENDS CORE DO ARAQUEM
# ----------------------------
cache = RedisCache(os.getenv("REDIS_URL", "redis://redis:6379/0"))
policies = CachePolicies()
planner = Planner(ONTO_PATH)
executor = PgExecutor()
orchestrator = Orchestrator(planner, executor, cache=cache, cache_policies=policies)

# ----------------------------
# CONTEXTO CONVERSACIONAL (M12+)
# ----------------------------
# Instanciado agora, mas só tem efeito quando:
#   data/policies/context.yaml → context.enabled = true
#
# Backend padrão é in-memory (sem risco, sem persistência)
#
context_manager = ContextManager()  # policy carregada de data/policies/context.yaml

__all__ = [
    "cache",
    "policies",
    "planner",
    "executor",
    "orchestrator",
    "context_manager",
    "cfg",
    "ONTO_PATH",
    "RedisCache",
    "CachePolicies",
    "read_through",
    "Planner",
    "PgExecutor",
    "Orchestrator",
]
