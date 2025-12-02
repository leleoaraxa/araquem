# app/rag/context_builder.py
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional
from pathlib import Path

from app.rag.index_reader import EmbeddingStore
from app.rag.ollama_client import OllamaClient
from app.utils.filecache import cached_embedding_store, load_yaml_cached

LOGGER = logging.getLogger(__name__)

_RAG_POLICY_PATH = os.getenv("RAG_POLICY_PATH", "data/policies/rag.yaml")
_RAG_INDEX_PATH = os.getenv("RAG_INDEX_PATH", "data/embeddings/store/embeddings.jsonl")


def load_rag_policy() -> Dict[str, Any]:
    """Carrega e cacheia a política de RAG.

    Regras de guardrail:
      - se o arquivo não existir, RAG é tratado como desabilitado ({}), com warning.
      - se o arquivo existir mas for inválido/malformado, levanta RuntimeError para
        falhar rápido e evitar fallback silencioso.
    """

    policy_path = Path(_RAG_POLICY_PATH)
    if not policy_path.exists():
        LOGGER.warning("Política de RAG ausente; RAG considerado desabilitado")
        return {}

    try:
        data = load_yaml_cached(str(policy_path)) or {}
    except Exception as exc:  # pragma: no cover - erros inesperados
        LOGGER.error("Erro ao carregar política de RAG", exc_info=True)
        raise RuntimeError("Falha ao carregar política de RAG") from exc

    if not isinstance(data, dict):
        LOGGER.error("Política de RAG deve ser um mapeamento YAML")
        raise RuntimeError("Política de RAG inválida (não é um dict)")

    return data


def _rag_section(policy: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(policy, dict):
        return {}
    if isinstance(policy.get("rag"), dict):
        return policy.get("rag") or {}
    return policy


def get_rag_policy(
    *,
    entity: str | None,
    intent: str | None,
    compute_mode: str | None,
    has_ticker: bool,
    meta: Dict[str, Any] | None = None,  # reservado para uso futuro
    policy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Aplica a política declarativa de RAG e retorna o snapshot efetivo.

    A decisão de autorização vem exclusivamente de YAML (rag.yaml + concepts
    referenciados nas coleções). O Narrator ou outras camadas apenas consomem
    o resultado exposto aqui. O parâmetro ``meta`` está reservado para evoluções
    futuras (mantido para compatibilidade) e não altera a decisão atual.
    """

    applied_policy = policy if policy is not None else load_rag_policy()
    if not applied_policy:
        return {"enabled": False, "reason": "policy_missing"}

    current_intent = intent or ""
    current_entity = entity or ""
    routing_cfg = applied_policy.get("routing") if isinstance(applied_policy, dict) else {}

    deny_intents = set(routing_cfg.get("deny_intents") or []) if isinstance(routing_cfg, dict) else set()
    allow_intents = set(routing_cfg.get("allow_intents") or []) if isinstance(routing_cfg, dict) else set()

    if current_intent and current_intent in deny_intents:
        return {"enabled": False, "reason": "intent_denied"}
    if allow_intents and current_intent not in allow_intents:
        return {"enabled": False, "reason": "intent_not_allowed"}

    resolved_policy = _resolve_policy(current_entity, applied_policy)
    if not resolved_policy:
        return {"enabled": False, "reason": "entity_not_configured"}

    collections: list[str] = []
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

    resolved_mode = None
    if isinstance(resolved_policy.get("mode"), str):
        resolved_mode = resolved_policy.get("mode")
    if isinstance(compute_mode, str) and compute_mode.strip():
        resolved_mode = compute_mode.strip()

    snapshot: Dict[str, Any] = {
        "enabled": True,
        "entity": current_entity,
        "intent": current_intent,
        "mode": resolved_mode or "data_augmented",
        "profile": resolved_policy.get("profile"),
        "collections": collections,
        "max_chunks": max_chunks_val,
        "min_score": min_score_val,
        "has_ticker": bool(has_ticker),
    }

    # Metadados opcionais para debug, mantendo rastreabilidade da origem.
    routing_snapshot: Dict[str, Any] = {}
    if deny_intents:
        routing_snapshot["deny_intents"] = sorted(list(deny_intents))
    if allow_intents:
        routing_snapshot["allow_intents"] = sorted(list(allow_intents))
    if routing_snapshot:
        snapshot["routing"] = routing_snapshot

    policy_raw = resolved_policy.get("policy") if isinstance(resolved_policy, dict) else None
    if isinstance(policy_raw, dict):
        snapshot["raw"] = policy_raw

    return snapshot


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
    compute_mode: Optional[str] = None,
    has_ticker: bool = False,
    policy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Monta o contexto de RAG para uma pergunta.

    Esta função é determinística e NÃO chama LLM.

    A decisão de habilitar/desabilitar RAG vem toda de ``rag.yaml`` (ou da
    policy previamente carregada passada via ``policy``). A mesma instância de
    policy é usada em toda a função para evitar leituras duplicadas, e o
    snapshot resultante sempre é incluído no retorno, inclusive em cenários de
    erro.

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

    applied_policy = policy if policy is not None else load_rag_policy()
    policy_snapshot = get_rag_policy(
        entity=entity,
        intent=intent,
        compute_mode=compute_mode,
        has_ticker=has_ticker,
        policy=applied_policy,
    )
    if not policy_snapshot.get("enabled"):
        return {
            "enabled": False,
            "question": question,
            "intent": intent,
            "entity": entity,
            "used_collections": [],
            "chunks": [],
            "total_chunks": 0,
            "policy": policy_snapshot,
            "error": None,
        }

    resolved_policy = _resolve_policy(entity, applied_policy)

    collections = policy_snapshot.get("collections") or []
    max_chunks_val = _clamp_max_chunks(policy_snapshot.get("max_chunks"), default=5)
    min_score_val = policy_snapshot.get("min_score")

    if max_tokens is None:
        max_tokens_policy = None
        if isinstance(resolved_policy, dict):
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
        if not Path(_RAG_INDEX_PATH).exists():
            raise FileNotFoundError(f"RAG index não encontrado em {_RAG_INDEX_PATH}")

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
        error_policy = dict(policy_snapshot)
        error_policy.update(
            {
                "enabled": False,
                "reason": "error",
                "collections": collections,
                "max_chunks": max_chunks_val,
            }
        )
        if min_score_val is not None:
            error_policy["min_score"] = min_score_val
        if max_tokens is not None:
            error_policy["max_tokens"] = max_tokens

        return {
            "enabled": False,
            "question": question,
            "intent": intent,
            "entity": entity,
            "used_collections": collections,
            "chunks": [],
            "total_chunks": 0,
            "policy": error_policy,
            "error": str(exc),
        }

    chunks = [_normalize_chunk(item) for item in results]

    snapshot_policy = dict(policy_snapshot)
    snapshot_policy.update(
        {
            "max_chunks": max_chunks_val,
            "collections": collections,
        }
    )
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
