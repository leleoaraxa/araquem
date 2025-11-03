from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Toggle global
_DISABLE = bool(int(os.getenv("FILECACHE_DISABLE", "0") or "0"))

_lock = threading.Lock()
_cache: Dict[str, Dict[str, Any]] = {}


def _stat_mtime(path: str) -> float:
    try:
        return Path(path).stat().st_mtime
    except Exception:
        return -1.0


def _get(path: str) -> Optional[Dict[str, Any]]:
    return _cache.get(path)


def _set(path: str, mtime: float, data: Any) -> None:
    _cache[path] = {"mtime": mtime, "data": data}


def load_yaml_cached(path: str) -> Dict[str, Any]:
    """Carrega YAML com cache por mtime. Retorna {} em falha."""
    if _DISABLE:
        try:
            return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        except Exception:
            return {}
    try:
        p_path = Path(path).resolve()
    except Exception:
        p_path = Path(path).absolute()
    p = str(p_path)
    m = _stat_mtime(p)
    with _lock:
        entry = _get(p)
        if entry and entry.get("mtime") == m and entry.get("data") is not None:
            return entry["data"]
        try:
            data = yaml.safe_load(p_path.read_text(encoding="utf-8")) or {}
        except Exception:
            data = {}
        _set(p, m, data)
        return data


def load_jsonl_cached(path: str) -> list[Dict[str, Any]]:
    """Lê JSONL como lista de dicts, com cache por mtime. Retorna [] em falha."""
    if _DISABLE:
        try:
            return [
                json.loads(line)
                for line in Path(path).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        except Exception:
            return []
    try:
        p_path = Path(path).resolve()
    except Exception:
        p_path = Path(path).absolute()
    p = str(p_path)
    m = _stat_mtime(p)
    with _lock:
        entry = _get(p)
        if entry and entry.get("mtime") == m and isinstance(entry.get("data"), list):
            return entry["data"]
        rows: list[Dict[str, Any]] = []
        try:
            for line in p_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rows.append(json.loads(line))
        except Exception:
            rows = []
        _set(p, m, rows)
        return rows


from app.rag.index_reader import EmbeddingStore

_es_lock = threading.Lock()
_es_cache: Dict[str, Dict[str, Any]] = {}


def cached_embedding_store(path: str) -> EmbeddingStore:
    """
    Retorna um EmbeddingStore cacheado por mtime.
    Mantém a classe original sem mudar contrato.
    """
    if _DISABLE:
        return EmbeddingStore(path)
    try:
        p_path = Path(path).resolve()
    except Exception:
        p_path = Path(path).absolute()
    p = str(p_path)
    m = _stat_mtime(p)
    with _es_lock:
        entry = _es_cache.get(p)
        if entry and entry.get("mtime") == m and entry.get("store") is not None:
            return entry["store"]  # type: ignore
        store = EmbeddingStore(p)
        _es_cache[p] = {"mtime": m, "store": store}
        return store
