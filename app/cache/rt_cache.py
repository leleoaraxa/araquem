# app/cache/rt_cache.py
import logging
import os, json, hashlib, time, datetime as dt
from functools import lru_cache
from typing import Any, Dict, Iterable, Optional
from pathlib import Path

import redis
import yaml

from app.utils.filecache import load_yaml_cached

from app.observability.instrumentation import counter, histogram

LOGGER = logging.getLogger(__name__)

# Fonte oficial (novo) e caminho legado (compat)
POLICY_PATH = Path("data/policies/cache.yaml")
ENTITY_ROOT = Path("data/entities")
CONFIG_VERSION_PATHS = [
    Path("data/ontology"),
    Path("data/entities"),
    Path("data/policies"),
    Path("data/embeddings"),
]


class CachePolicies:
    def __init__(self, path: Optional[Path] = None):
        self._status: str = "ok"
        self._error: Optional[str] = None
        self._private_cache: Dict[str, bool] = {}
        self._entity_root = ENTITY_ROOT
        # Escolhe automaticamente: novo caminho > legado
        selected = None
        if path:
            selected = Path(path)
        else:
            selected = POLICY_PATH

        self.path = selected or POLICY_PATH
        self.mtime = None

        if not self.path.exists():
            self.data = {}
            self._policies = {}
            self._status = "missing"
            self._error = f"Arquivo de políticas de cache ausente em {self.path}"
            LOGGER.warning("Política de cache ausente em %s; usando política vazia", self.path)
            return

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = yaml.safe_load(f) or {}
            self.mtime = self.path.stat().st_mtime
            if not isinstance(self.data, dict):
                raise ValueError("cache.yaml deve ser um mapeamento")
            policies_block = self.data.get("policies") or {}
            if policies_block and not isinstance(policies_block, dict):
                raise ValueError("Bloco 'policies' deve ser um mapeamento")
            self._policies = policies_block if isinstance(policies_block, dict) else {}
        except Exception as exc:
            self.data = {}
            self._policies = {}
            self._status = "invalid"
            self._error = str(exc)
            LOGGER.error(
                "Falha ao carregar políticas de cache de %s; usando política vazia",
                self.path,
                exc_info=True,
            )

    def get(self, entity: str) -> Optional[Dict[str, Any]]:
        # Lê do bloco "policies" do YAML; None quando não houver
        return self._policies.get(entity)

    def is_private_entity(self, entity: str) -> bool:
        if not entity:
            return False

        if entity in self._private_cache:
            return self._private_cache[entity]

        private_flag = False

        policy = self.get(entity)
        if isinstance(policy, dict) and policy.get("private") is True:
            private_flag = True

        if not private_flag:
            path = self._entity_root / str(entity) / "entity.yaml"
            if path.exists():
                try:
                    data = load_yaml_cached(str(path))
                    if isinstance(data, dict) and data.get("private") is True:
                        private_flag = True
                except Exception:
                    LOGGER.warning(
                        "Falha ao avaliar flag private em %s", path, exc_info=True
                    )

        self._private_cache[entity] = bool(private_flag)
        return self._private_cache[entity]


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


def _stable_hash(obj: Any) -> str:
    """Gera hash estável para dicionários/params."""
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha1(s.encode("utf-8")).hexdigest()  # curto e suficiente


def _iter_config_files() -> Iterable[Path]:
    for base in CONFIG_VERSION_PATHS:
        if not base.exists():
            LOGGER.warning("Caminho de configuração ausente: %s", base)
            continue
        if base.is_file():
            yield base
            continue
        for path in sorted(base.rglob("*.yaml")):
            if path.is_file():
                yield path


def _compute_config_version() -> str:
    hasher = hashlib.sha1()
    found_any = False
    for file_path in _iter_config_files():
        found_any = True
        rel = file_path.as_posix()
        try:
            content = file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            LOGGER.warning(
                "Arquivo de configuração ausente durante cálculo de versão: %s",
                file_path,
            )
            continue
        except Exception:
            LOGGER.warning(
                "Falha ao ler arquivo de configuração %s; ignorando",
                file_path,
                exc_info=True,
            )
            continue
        hasher.update(rel.encode("utf-8"))
        hasher.update(content.encode("utf-8"))

    if not found_any:
        LOGGER.warning(
            "Nenhum arquivo de configuração encontrado; usando versão baseada em hash vazio"
        )

    digest = hasher.hexdigest()
    return f"cfg-{digest[:8]}" if digest else "cfg-fallback"


@lru_cache(maxsize=1)
def get_config_version() -> str:
    try:
        return _compute_config_version()
    except Exception:
        LOGGER.error(
            "Erro ao calcular versão de configuração; usando fallback estável",
            exc_info=True,
        )
        return "cfg-fallback"


def make_cache_key(
    build_id: str, scope: str, entity: str, identifiers: Dict[str, Any]
) -> str:
    cfg_version = get_config_version()
    return f"araquem:{build_id}:{cfg_version}:{scope}:{entity}:{_stable_hash(identifiers or {})}"


def _mk_hit_guard(key: str) -> str:
    return f"{key}:hit_once"


def _mk_miss_guard(key: str) -> str:
    return f"{key}:miss_once"


def _mark_once(cache: "RedisCache", guard_key: str, ttl_seconds: int) -> bool:
    """Attempts to mark a guard key once, tolerating simplified cache fakes."""
    raw = getattr(cache, "raw", None)
    setter = getattr(raw, "set", None) if raw is not None else None
    if not callable(setter):
        return True
    try:
        return bool(setter(guard_key, "1", ex=ttl_seconds, nx=True))
    except Exception:
        return False


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


def is_cacheable_payload(val: Any) -> bool:
    """
    Retorna True quando o payload é elegível para cache.

    Compatível com payloads do orchestrator:
      - exige result_key definido em meta
      - exige lista de rows não vazia em results[result_key]
    Fallback: usa heurística genérica para formatos legados.
    """
    if isinstance(val, dict) and isinstance(val.get("results"), dict):
        results = val.get("results") or {}
        meta = val.get("meta") or {}
        result_key = meta.get("result_key") if isinstance(meta, dict) else None
        if result_key:
            rows = results.get(result_key)
            if isinstance(rows, list) and len(rows) > 0:
                return True
        return False

    return not _is_empty_payload(val)


def read_through(
    cache: RedisCache,
    policies: CachePolicies,
    entity: str,
    identifiers: Dict[str, Any],
    fetch_fn,
):
    """Aplica leitura com cache por entidade, respeitando TTL do YAML."""
    policy = policies.get(entity)
    is_private = policies.is_private_entity(entity)
    ttl: Optional[int] = None
    if policy and "ttl_seconds" in policy:
        try:
            ttl = int(policy.get("ttl_seconds", 0) or 0)
        except (TypeError, ValueError):
            ttl = 0

    if is_private:
        val = fetch_fn()
        return {"cached": False, "key": None, "value": val, "ttl": ttl}

    if not policy:
        # sem política → bypass cache
        val = fetch_fn()
        return {"cached": False, "key": None, "value": val, "ttl": ttl}

    scope = str(policy.get("scope", "pub"))
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
            if _mark_once(cache, _mk_hit_guard(key), ttl_seconds=1):
                counter("cache_hits_total", entity=entity)
                counter("metrics_cache_hits_total", entity=entity)
        except Exception:
            pass

        return {"cached": True, "key": key, "value": val, "ttl": ttl}

    val = fetch_fn()
    # métricas de MISS por entidade (deduplicadas em ~1s)
    try:
        if _mark_once(cache, _mk_miss_guard(key), ttl_seconds=1):
            counter("cache_misses_total", entity=entity)
            counter("metrics_cache_misses_total", entity=entity)
    except Exception:
        pass

    # não cachear payload vazio
    if _is_empty_payload(val):
        return {"cached": False, "key": key, "value": val, "ttl": ttl}

    ttl_to_use = ttl if isinstance(ttl, int) else 0

    cache.set_json(key, val, ttl_seconds=ttl_to_use)
    return {"cached": False, "key": key, "value": val, "ttl": ttl_to_use}
