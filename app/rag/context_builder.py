# app/rag/context_builder.py
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from app.rag.index_reader import EmbeddingStore
from app.rag.ollama_client import OllamaClient
from app.utils.filecache import cached_embedding_store, load_yaml_cached

LOGGER = logging.getLogger(__name__)

_RAG_POLICY_PATH = os.getenv("RAG_POLICY_PATH", "data/policies/rag.yaml")
_RAG_INDEX_PATH = os.getenv("RAG_INDEX_PATH", "data/embeddings/store/embeddings.jsonl")


def load_rag_policy() -> Dict[str, Any]:
    """Carrega e cacheia a política de RAG a partir de data/policies/rag.yaml.

    Se o arquivo não existir ou estiver inválido, retorna um dicionário vazio.
    Não levanta exceção para o chamador.
    """

    try:
        data = load_yaml_cached(str(_RAG_POLICY_PATH)) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _rag_section(policy: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(policy, dict):
        return {}
    if isinstance(policy.get("rag"), dict):
        return policy.get("rag") or {}
    return policy


def is_rag_enabled(
    intent: str, entity: str, *, policy: Optional[Dict[str, Any]] = None
) -> bool:
    """Retorna True se RAG estiver habilitado para o par (intent, entity),
    de acordo com a política de RAG.

    Se não houver política específica, usa a seção default (se existir).
    """

    policy = policy or load_rag_policy()
    if not policy:
        return False

    routing = policy.get("routing") if isinstance(policy, dict) else None
    deny_intents = (
        set(routing.get("deny_intents") or []) if isinstance(routing, dict) else set()
    )
    allow_intents = (
        set(routing.get("allow_intents") or []) if isinstance(routing, dict) else set()
    )

    if intent and intent in deny_intents:
        return False
    if allow_intents and intent not in allow_intents:
        return False

    rag_policy = _rag_section(policy)
    entities_cfg = rag_policy.get("entities") if isinstance(rag_policy, dict) else None
    if isinstance(entities_cfg, dict):
        if entity in entities_cfg:
            return True
        # se a entidade não estiver em entities_cfg, cai na default/profiles abaixo
    default_cfg = rag_policy.get("default") if isinstance(rag_policy, dict) else None
    profiles_cfg = rag_policy.get("profiles") if isinstance(rag_policy, dict) else None

    if default_cfg or profiles_cfg:
        return True

    return False


def _extract_text(item: Dict[str, Any]) -> str:
    for key in ("text", "content", "body", "snippet"):
        val = item.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""


def _normalize_chunk(item: Dict[str, Any]) -> Dict[str, Any]:
    chunk: Dict[str, Any] = {
        "text": _extract_text(item),
        "score": float(item.get("score", 0.0) or 0.0),
    }
    for key in (
        "doc_id",
        "chunk_id",
        "source_id",
        "collection",
        "path",
        "entity",
        "tags",
    ):
        if key in item:
            chunk[key] = item.get(key)
    return chunk


def _resolve_policy(entity: str, policy: Dict[str, Any]) -> Dict[str, Any]:
    rag_policy = _rag_section(policy)
    if not isinstance(rag_policy, dict):
        return {}

    entities_cfg = (
        rag_policy.get("entities")
        if isinstance(rag_policy.get("entities"), dict)
        else {}
    )
    if entity in entities_cfg:
        entity_cfg = entities_cfg.get(entity) or {}
    else:
        entity_cfg = rag_policy.get("default") or {}

    if not entity_cfg and isinstance(rag_policy.get("profiles"), dict):
        entity_cfg = rag_policy.get("profiles", {}).get("default") or {}

    if not isinstance(entity_cfg, dict):
        return {}

    return entity_cfg


def _clamp_max_chunks(value: Any, default: int = 5) -> int:
    try:
        ivalue = int(value)
    except (TypeError, ValueError):
        ivalue = default
    return max(1, min(20, ivalue))


def build_context(
    question: str,
    intent: str,
    entity: str,
    *,
    max_tokens: Optional[int] = None,
    policy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Monta o contexto de RAG para uma pergunta.

    Esta função é determinística e NÃO chama LLM.

    Retorna um dicionário com chaves do tipo:
      - 'enabled': bool
      - 'question': str
      - 'intent': str
      - 'entity': str
      - 'used_collections': List[str]
      - 'chunks': List[Dict[str, Any]]  # cada chunk com texto + metadados
      - 'total_chunks': int
      - 'policy': Dict[str, Any]  # snapshot mínimo da policy aplicada (opcional)
      - 'error': Optional[str]
    """

    applied_policy = policy or load_rag_policy()
    if not is_rag_enabled(intent, entity, policy=applied_policy):
        return {
            "enabled": False,
            "question": question,
            "intent": intent,
            "entity": entity,
            "used_collections": [],
            "chunks": [],
            "total_chunks": 0,
            "error": None,
        }

    resolved_policy = _resolve_policy(entity, applied_policy)

    collections = []
    if isinstance(resolved_policy.get("collections"), list):
        collections = [str(c) for c in resolved_policy.get("collections") if c]

    k_value = resolved_policy.get("max_chunks")
    if k_value is None:
        k_value = resolved_policy.get("k")
    max_chunks_val = _clamp_max_chunks(k_value, default=5)

    min_score_raw = resolved_policy.get("min_score")
    try:
        min_score_val = float(min_score_raw)
    except (TypeError, ValueError):
        min_score_val = None

    if max_tokens is None:
        max_tokens_policy = resolved_policy.get("max_tokens")
        if max_tokens_policy is None:
            max_tokens_policy = resolved_policy.get("max_context_chars")
        try:
            max_tokens = (
                int(max_tokens_policy) if max_tokens_policy is not None else None
            )
        except (TypeError, ValueError):
            max_tokens = None

    try:
        store: EmbeddingStore = cached_embedding_store(_RAG_INDEX_PATH)
        embedder = OllamaClient()
        vectors = embedder.embed([question])
        qvec: List[float] = (
            vectors[0] if vectors and isinstance(vectors[0], list) else []
        )
        if not qvec:
            raise RuntimeError("embedding-vector-empty")
        results = (
            store.search_by_vector(qvec, k=max_chunks_val, min_score=min_score_val)
            or []
        )
    except Exception as exc:  # pragma: no cover - robust fallback
        LOGGER.warning("RAG search failed: %s", exc)
        return {
            "enabled": False,
            "question": question,
            "intent": intent,
            "entity": entity,
            "used_collections": collections,
            "chunks": [],
            "total_chunks": 0,
            "error": str(exc),
        }

    chunks = [_normalize_chunk(item) for item in results]

    snapshot_policy = {
        "max_chunks": max_chunks_val,
        "collections": collections,
    }
    if min_score_val is not None:
        snapshot_policy["min_score"] = min_score_val
    if max_tokens is not None:
        snapshot_policy["max_tokens"] = max_tokens

    return {
        "enabled": True,
        "question": question,
        "intent": intent,
        "entity": entity,
        "used_collections": collections,
        "chunks": chunks,
        "total_chunks": len(chunks),
        "policy": snapshot_policy,
        "error": None,
    }
