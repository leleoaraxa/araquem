# app/cache/rt_cache.py

import os, json, hashlib, datetime as dt
import time
import redis
import yaml

from typing import Any, Dict, Optional
from pathlib import Path
from app.observability.instrumentation import counter, histogram

POLICY_PATH = Path("data/entities/cache_policies.yaml")


class CachePolicies:
    def __init__(self, path: Path = POLICY_PATH):
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        self._policies = raw.get("policies") or {}

    def get(self, entity: str) -> Optional[Dict[str, Any]]:
        return self._policies.get(entity)


class RedisCache:
    def __init__(self, url: Optional[str] = None):
        self._url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._cli = redis.from_url(self._url, decode_responses=True)

    def ping(self) -> bool:
        try:
            return bool(self._cli.ping())
        except Exception:
            return False

    def get_json(self, key: str) -> Optional[Any]:
        t0 = time.perf_counter()
        try:
            s = self._cli.get(key)
            dt_ = time.perf_counter() - t0
            histogram("sirios_cache_latency_seconds", dt_, op="get")
            outcome = "hit" if s is not None else "miss"
            counter("sirios_cache_ops_total", op="get", outcome=outcome)
            return None if s is None else json.loads(s)
        except Exception:
            counter("sirios_cache_ops_total", op="get", outcome="error")
            raise

    def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        t0 = time.perf_counter()
        try:
            # serialização segura (str() para tipos não nativos JSON)
            s = json.dumps(value, ensure_ascii=False, default=str)
            self._cli.set(key, s, ex=ttl_seconds)
            dt_ = time.perf_counter() - t0
            histogram("sirios_cache_latency_seconds", dt_, op="set")
            counter("sirios_cache_ops_total", op="set", outcome="ok")
        except Exception:
            counter("sirios_cache_ops_total", op="set", outcome="error")
            raise

    def delete(self, key: str) -> int:
        return self._cli.delete(key)


def _stable_hash(obj: Any) -> str:
    """Gera hash estável para dicionários/params."""
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha1(s.encode("utf-8")).hexdigest()  # curto e suficiente


def make_cache_key(
    build_id: str, scope: str, entity: str, identifiers: Dict[str, Any]
) -> str:
    return f"araquem:{build_id}:{scope}:{entity}:{_stable_hash(identifiers or {})}"


def read_through(
    cache: RedisCache,
    policies: CachePolicies,
    entity: str,
    identifiers: Dict[str, Any],
    fetch_fn,
):
    """Aplica leitura com cache por entidade, respeitando TTL do YAML."""
    policy = policies.get(entity)
    if not policy:
        # sem política → bypass cache
        return {"cached": False, "key": None, "value": fetch_fn()}

    ttl = int(policy.get("ttl_seconds", 0) or 0)
    scope = str(policy.get("scope", "pub"))
    build_id = os.getenv("BUILD_ID", "dev")
    key = make_cache_key(build_id, scope, entity, identifiers or {})

    val = cache.get_json(key)
    if val is not None:
        return {"cached": True, "key": key, "value": val, "ttl": ttl}

    val = fetch_fn()
    cache.set_json(key, val, ttl_seconds=ttl)
    return {"cached": False, "key": key, "value": val, "ttl": ttl}
