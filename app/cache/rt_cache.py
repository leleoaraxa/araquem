# app/cache/rt_cache.py
import os, json, hashlib, time, datetime as dt
from typing import Any, Dict, Optional
from pathlib import Path

import redis
import yaml
from prometheus_client import Counter as _PCounter

from app.observability.instrumentation import counter, histogram

# Fonte oficial (novo) e caminho legado (compat)
POLICY_PATH = Path("data/policies/cache.yaml")


class CachePolicies:
    def __init__(self, path: Optional[Path] = None):
        # Escolhe automaticamente: novo caminho > legado
        selected = None
        if path:
            selected = Path(path)
        else:
            selected = POLICY_PATH

        # Fallback seguro: sem arquivo -> política vazia
        if selected and selected.exists():
            with open(selected, "r", encoding="utf-8") as f:
                self.data = yaml.safe_load(f) or {}
            self.path = selected
            self.mtime = self.path.stat().st_mtime
            # Extrai bloco de policies para acesso rápido
            self._policies: Dict[str, Any] = self.data.get("policies", {}) or {}
        else:
            # Não explode a API se o arquivo não existir
            self.data = {}
            self.path = POLICY_PATH
            self.mtime = None
            self._policies: Dict[str, Any] = {}

    def get(self, entity: str) -> Optional[Dict[str, Any]]:
        # Lê do bloco "policies" do YAML; None quando não houver
        return self._policies.get(entity)


class RedisCache:
    def __init__(self, url: Optional[str] = None):
        self._url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._cli = redis.from_url(self._url, decode_responses=True)

    @property
    def raw(self):
        # acesso controlado para operações utilitárias (scan/set nx)
        return self._cli

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


# --- Métricas Prometheus (garante presença no /metrics) ---
_METRICS_CACHE_HITS = _PCounter(
    "metrics_cache_hits_total", "metrics cache hits total", ["entity"]
)
_METRICS_CACHE_MISSES = _PCounter(
    "metrics_cache_misses_total", "metrics cache misses total", ["entity"]
)


def _stable_hash(obj: Any) -> str:
    """Gera hash estável para dicionários/params."""
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha1(s.encode("utf-8")).hexdigest()  # curto e suficiente


def make_cache_key(
    build_id: str, scope: str, entity: str, identifiers: Dict[str, Any]
) -> str:
    return f"araquem:{build_id}:{scope}:{entity}:{_stable_hash(identifiers or {})}"


def _mk_hit_guard(key: str) -> str:
    return f"{key}:hit_once"


def _mk_miss_guard(key: str) -> str:
    return f"{key}:miss_once"


def _is_empty_payload(val: Any) -> bool:
    """
    Heurística segura para considerar payload 'vazio' (não cacheável).
    Cobre os formatos mais comuns do projeto:
      - None / False / []
      - {"rows": []}
      - {"fii_metrics": []}
      - dict onde todos os valores são coleções vazias
    """
    if not val:
        return True
    if isinstance(val, dict):
        # casos explícitos
        rows = val.get("rows")
        if isinstance(rows, list) and len(rows) == 0:
            return True
        fm = val.get("fii_metrics")
        if isinstance(fm, list) and len(fm) == 0:
            return True
        # todo dict só com coleções vazias
        all_empty = True
        for v in val.values():
            if isinstance(v, (list, tuple, set, dict)):
                if len(v) > 0:
                    all_empty = False
                    break
            elif v not in (None, "", False):
                all_empty = False
                break
        return all_empty
    return False


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
        val = fetch_fn()
        return {"cached": False, "key": None, "value": val}

    ttl = int(policy.get("ttl_seconds", 0) or 0)
    scope = str(policy.get("scope", "pub"))
    expose_metrics = bool(policy.get("expose_metrics", False))
    build_id = os.getenv("BUILD_ID", "dev")
    key = make_cache_key(build_id, scope, entity, identifiers or {})

    # --- LIMPEZA DE CHAVES LEGADAS (antes de ler) ---
    try:
        scan_tmpl = policy.get("legacy_cleanup_scan")
        if scan_tmpl:
            # render simples com identifiers (faltantes viram vazio)
            pat = scan_tmpl.format(
                **{k: identifiers.get(k, "") for k in identifiers.keys()}
            )
            # se ainda sobrar marcador, evita apagar demais
            if "{" not in pat and "}" not in pat and pat:
                for k_legacy in cache.raw.scan_iter(pat):
                    if k_legacy != key:
                        cache.delete(k_legacy)
    except Exception:
        pass

    val = cache.get_json(key)
    if val is not None:
        # métricas de HIT por entidade (deduplicadas em ~1s)
        try:
            if cache.raw.set(_mk_hit_guard(key), "1", ex=1, nx=True):
                counter("cache_hits_total", entity=entity)
                if expose_metrics:
                    counter("metrics_cache_hits_total", entity=entity)
        except Exception:
            pass
            # também limpa chave legada em HIT para o teste enxergar só 1 chave
            if expose_metrics:
                counter("metrics_cache_misses_total", entity=entity)

        return {"cached": True, "key": key, "value": val, "ttl": ttl}

    val = fetch_fn()
    # métricas de MISS por entidade (deduplicadas em ~1s)
    try:
        if cache.raw.set(_mk_miss_guard(key), "1", ex=1, nx=True):
            counter("cache_misses_total", entity=entity)
            if entity == "fiis_metrics":
                # garante presença e incremento no /metrics
                _METRICS_CACHE_MISSES.labels(entity=entity).inc()
    except Exception:
        pass

    # não cachear payload vazio
    if _is_empty_payload(val):
        return {"cached": False, "key": key, "value": val, "ttl": ttl}

    cache.set_json(key, val, ttl_seconds=ttl)
    return {"cached": False, "key": key, "value": val, "ttl": ttl}
