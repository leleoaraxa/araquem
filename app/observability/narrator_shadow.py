"""Narrator Shadow Collector.

Responsável por aplicar a policy declarativa do shadow (sampling, redaction,
sink) e registrar os eventos do Narrator sem impactar o fluxo do /ask.
"""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml

from app.narrator.narrator import _get_effective_policy, _load_narrator_policy
from app.observability.metrics import emit_counter as counter
from app.utils.filecache import load_yaml_cached

LOGGER = logging.getLogger(__name__)

_SHADOW_POLICY_PATH = Path("data/policies/narrator_shadow.yaml")


def _safe_counter(name: str, **labels: Any) -> None:
    try:
        counter(name, **labels)
    except Exception:
        LOGGER.debug("Ignorando métrica de shadow por backend indisponível", exc_info=True)


@dataclass
class NarratorShadowEvent:
    """Estrutura intermediária montada pelo Presenter."""

    request: Dict[str, Any]
    routing: Dict[str, Any]
    facts: Dict[str, Any]
    rag: Optional[Dict[str, Any]]
    narrator: Optional[Dict[str, Any]]
    presenter: Optional[Dict[str, Any]]
    environment: str = "dev"


class _ShadowSink:
    def write(self, record: Dict[str, Any]) -> None:
        raise NotImplementedError


class _FileShadowSink(_ShadowSink):
    def __init__(self, base_path: Path, filename_template: str) -> None:
        self.base_path = base_path
        self.filename_template = filename_template

    def _resolve_path(self, now: datetime) -> Path:
        filename = now.strftime(self.filename_template)
        return self.base_path / filename

    def write(self, record: Dict[str, Any]) -> None:
        now = datetime.now(timezone.utc)
        path = self._resolve_path(now)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(record, ensure_ascii=False)
        with path.open("a", encoding="utf-8") as f:
            f.write(payload + "\n")


def _load_shadow_policy(path: Path = _SHADOW_POLICY_PATH) -> Dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"Narrator shadow policy ausente: {path}")
    try:
        data = load_yaml_cached(str(path))
    except (yaml.YAMLError, OSError, RuntimeError) as exc:
        LOGGER.error("Erro ao carregar narrator_shadow policy de %s", path, exc_info=True)
        raise ValueError(f"Narrator shadow policy inválida: {path}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Narrator shadow policy deve ser um mapeamento em {path}")
    return data


def _get_shadow_cfg(policy: Dict[str, Any]) -> Dict[str, Any]:
    if "narrator_shadow" in policy:
        cfg = policy.get("narrator_shadow")
    else:
        cfg = policy
    return cfg if isinstance(cfg, dict) else {}


def _mask_value(value: Any) -> str:
    text = str(value)
    if len(text) <= 4:
        return "***"
    return f"***{text[-4:]}"


def _mask_fields(obj: Any, mask_fields: Iterable[str], masked: set[str]) -> Any:
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            if k in mask_fields:
                masked.add(k)
                out[k] = _mask_value(v)
            else:
                out[k] = _mask_fields(v, mask_fields, masked)
        return out
    if isinstance(obj, list):
        return [_mask_fields(item, mask_fields, masked) for item in obj]
    return obj


def _truncate_text(value: Any, limit: Optional[int], field: str, truncated: set[str]) -> Any:
    if not isinstance(value, str) or not limit:
        return value
    if len(value) > limit:
        truncated.add(field)
        return value[:limit]
    return value


def _strategy_uses_llm(strategy: Optional[str]) -> bool:
    if not isinstance(strategy, str):
        return False
    normalized = strategy.strip().lower()
    return normalized.startswith("llm")


def _resolve_entity_policy(entity: str, narrator_policy: Dict[str, Any]) -> Dict[str, Any]:
    cfg = narrator_policy.get("narrator") if isinstance(narrator_policy.get("narrator"), dict) else narrator_policy
    if not isinstance(cfg, dict):
        return {}
    return _get_effective_policy(entity, cfg)


def _resolve_sampling_policy(entity: str, shadow_cfg: Dict[str, Any]) -> Dict[str, Any]:
    sampling = shadow_cfg.get("sampling") if isinstance(shadow_cfg, dict) else {}
    entity_cfg = (sampling.get("entities", {}) or {}).get(entity, {}) if isinstance(sampling, dict) else {}
    default_cfg = sampling.get("default", {}) if isinstance(sampling, dict) else {}
    effective = dict(default_cfg if isinstance(default_cfg, dict) else {})
    if isinstance(entity_cfg, dict):
        effective.update(entity_cfg)
    return effective


def _should_sample(
    *,
    event: NarratorShadowEvent,
    narrator_policy: Dict[str, Any],
    shadow_cfg: Dict[str, Any],
) -> Tuple[bool, str, Dict[str, Any]]:
    entity = str(event.routing.get("entity") or event.facts.get("entity") or "")
    entity_policy = _resolve_entity_policy(entity, narrator_policy)
    if not entity_policy.get("llm_enabled") or not entity_policy.get("shadow"):
        return False, "shadow_disabled_entity", {}

    if not shadow_cfg.get("enabled"):
        return False, "shadow_disabled_global", {}

    allowlist = shadow_cfg.get("environment_allowlist") or []
    if allowlist and event.environment not in allowlist:
        return False, "environment_blocked", {}

    sampling_cfg = _resolve_sampling_policy(entity, shadow_cfg)

    narrator_meta = event.narrator or {}
    narrator_error = narrator_meta.get("error")
    narrator_strategy = narrator_meta.get("strategy")
    llm_used = _strategy_uses_llm(narrator_strategy)
    answer_final = (event.presenter or {}).get("answer_final")

    if sampling_cfg.get("always_on_llm_error") and narrator_error:
        return True, "llm_error_forced", sampling_cfg

    if sampling_cfg.get("only_when_llm_used") and not llm_used:
        return False, "llm_not_used", sampling_cfg

    if sampling_cfg.get("only_when_answer_nonempty") and not answer_final:
        return False, "empty_answer", sampling_cfg

    try:
        rate = float(sampling_cfg.get("rate", 0.0))
    except (TypeError, ValueError):
        rate = 0.0

    if rate <= 0:
        return False, "rate_zero", sampling_cfg

    if random.random() < rate:
        return True, "rate_hit", sampling_cfg

    return False, "rate_miss", sampling_cfg


def _sanitize_request_block(
    request: Dict[str, Any], mask_fields: Iterable[str], masked: set[str]
) -> Dict[str, Any]:
    allowed_keys = {"question", "conversation_id", "nickname", "client_id"}
    cleaned = {k: request.get(k) for k in allowed_keys if k in request}
    return _mask_fields(cleaned, mask_fields, masked)


def _build_facts_block(
    facts: Dict[str, Any],
    *,
    max_rows_sample: int,
    mask_fields: Iterable[str],
    masked: set[str],
) -> Dict[str, Any]:
    rows_raw = list(facts.get("rows") or []) if isinstance(facts, dict) else []
    rows_total = len(rows_raw)
    rows_sample: List[Dict[str, Any]] = []
    for row in rows_raw[:max_rows_sample]:
        if isinstance(row, dict):
            rows_sample.append(_mask_fields(dict(row), mask_fields, masked))

    aggregates = facts.get("aggregates") if isinstance(facts, dict) else None
    identifiers = facts.get("identifiers") if isinstance(facts, dict) else None

    payload: Dict[str, Any] = {
        "entity": facts.get("entity") or facts.get("intent") or facts.get("result_key"),
        "rows_total": rows_total,
        "rows_sample": rows_sample,
        "aggregates": aggregates if isinstance(aggregates, dict) else {},
    }
    if isinstance(identifiers, dict):
        payload["identifiers"] = _mask_fields(dict(identifiers), mask_fields, masked)
    return payload


def _build_rag_block(
    rag: Optional[Dict[str, Any]],
    *,
    max_chunks: int,
    snippet_limit: Optional[int],
    truncated: set[str],
    mask_fields: Iterable[str],
    masked: set[str],
) -> Dict[str, Any]:
    if not isinstance(rag, dict):
        return {"enabled": False, "collections": [], "chunks_sample": []}

    collections = rag.get("collections") or rag.get("datasets")
    chunks_raw = rag.get("chunks") or rag.get("chunks_sample") or []
    concepts_shadow_raw = rag.get("concepts_shadow")
    chunks_sample: List[Dict[str, Any]] = []
    for chunk in list(chunks_raw)[:max_chunks]:
        if not isinstance(chunk, dict):
            continue
        entry = dict(chunk)
        if "snippet" in entry:
            entry["snippet"] = _truncate_text(
                entry.get("snippet"), snippet_limit, "snippet", truncated
            )
        chunks_sample.append(_mask_fields(entry, mask_fields, masked))

    concepts_shadow: Optional[Dict[str, Any]] = None
    if isinstance(concepts_shadow_raw, dict):
        matches = concepts_shadow_raw.get("matches") or []
        query_ms = concepts_shadow_raw.get("query_embedding_ms")
        search_ms = concepts_shadow_raw.get("search_ms")
        latency_ms = None
        if isinstance(query_ms, int) and isinstance(search_ms, int):
            latency_ms = query_ms + search_ms
        elif isinstance(query_ms, int):
            latency_ms = query_ms
        elif isinstance(search_ms, int):
            latency_ms = search_ms
        concepts_shadow = {
            "enabled": bool(concepts_shadow_raw.get("enabled")),
            "reason": concepts_shadow_raw.get("reason"),
            "matches_count": len(matches) if isinstance(matches, list) else 0,
            "latency_ms": latency_ms,
        }

    return {
        "enabled": bool(rag.get("enabled")),
        "collections": collections if isinstance(collections, list) else [],
        "chunks_sample": chunks_sample,
        "concepts_shadow": concepts_shadow,
    }


def _build_narrator_block(narrator: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(narrator, dict):
        return {}
    return {
        "enabled": narrator.get("enabled"),
        "shadow": narrator.get("shadow"),
        "model": narrator.get("model"),
        "strategy": narrator.get("strategy"),
        "latency_ms": narrator.get("latency_ms"),
        "error": narrator.get("error"),
        "effective_policy": narrator.get("effective_policy"),
        "rag": narrator.get("rag"),
        "compute_mode": narrator.get("compute_mode"),
    }


def _build_presenter_block(
    presenter: Optional[Dict[str, Any]],
    *,
    max_chars: Dict[str, int],
    truncated: set[str],
) -> Dict[str, Any]:
    presenter = presenter or {}
    answer_final = _truncate_text(
        presenter.get("answer_final"), max_chars.get("answer_final"), "answer_final", truncated
    )
    answer_baseline = _truncate_text(
        presenter.get("answer_baseline"),
        max_chars.get("answer_baseline"),
        "answer_baseline",
        truncated,
    )
    prompt_preview = _truncate_text(
        presenter.get("prompt_preview"),
        max_chars.get("prompt_preview"),
        "prompt_preview",
        truncated,
    )

    return {
        "answer_final": answer_final,
        "answer_baseline": answer_baseline,
        "rows_used": presenter.get("rows_used"),
        "style": presenter.get("style"),
        "prompt_preview": prompt_preview,
    }


def _build_shadow_block(
    *,
    reason: str,
    sampling_cfg: Dict[str, Any],
    policy_version: Optional[int],
    masked: set[str],
    truncated: set[str],
    entity: str,
) -> Dict[str, Any]:
    sampling_snapshot = dict(sampling_cfg or {})
    sampling_snapshot["entity"] = entity
    return {
        "sampled": True,
        "reason": reason,
        "policy_version": policy_version,
        "sampling_config": sampling_snapshot,
        "redaction_applied": {
            "masked_fields": sorted(masked),
            "truncated_fields": sorted(truncated),
        },
    }


def _select_sink(shadow_cfg: Dict[str, Any]) -> _ShadowSink:
    storage = shadow_cfg.get("storage") if isinstance(shadow_cfg, dict) else {}
    sink_kind = storage.get("sink") if isinstance(storage, dict) else "file"
    if sink_kind != "file":
        raise ValueError(f"Sink não suportado: {sink_kind}")

    file_cfg = storage.get("file") if isinstance(storage, dict) else {}
    base_path = file_cfg.get("path") or "logs/narrator_shadow"
    filename_template = file_cfg.get("filename_template") or "narrator_shadow_%Y%m%d.jsonl"
    return _FileShadowSink(Path(base_path), filename_template)


def _policy_version(policy: Dict[str, Any]) -> Optional[int]:
    terms = policy.get("terms") if isinstance(policy, dict) else None
    if isinstance(terms, list) and terms:
        first = terms[0] or {}
        if isinstance(first, dict):
            version = first.get("version")
            try:
                return int(version)
            except (TypeError, ValueError):
                return None
    return None


def _shadow_payload_size_ok(record: Dict[str, Any], shadow_cfg: Dict[str, Any]) -> bool:
    storage = shadow_cfg.get("storage") if isinstance(shadow_cfg, dict) else {}
    max_kb = storage.get("max_shadow_payload_kb") if isinstance(storage, dict) else None
    if not max_kb:
        return True
    try:
        limit_bytes = int(max_kb) * 1024
    except (TypeError, ValueError):
        return True
    size_bytes = len(json.dumps(record, ensure_ascii=False).encode("utf-8"))
    return size_bytes <= limit_bytes


def collect_narrator_shadow(event: NarratorShadowEvent) -> None:
    """Aplica policy e persiste o NarratorShadowRecord."""

    try:
        shadow_policy = _load_shadow_policy()
        shadow_cfg = _get_shadow_cfg(shadow_policy)
        narrator_policy = _load_narrator_policy()

        should_sample, reason, sampling_cfg = _should_sample(
            event=event, narrator_policy=narrator_policy, shadow_cfg=shadow_cfg
        )
        if not should_sample:
            return

        redaction_cfg = shadow_cfg.get("redaction") if isinstance(shadow_cfg, dict) else {}
        mask_fields = set(redaction_cfg.get("mask_fields") or [])
        private_entities = set(shadow_cfg.get("private_entities") or [])
        max_rows_sample = int(redaction_cfg.get("max_rows_sample", 3) or 3)
        max_chars_cfg = redaction_cfg.get("max_chars") if isinstance(redaction_cfg, dict) else {}
        max_chars = {
            "answer_final": int(max_chars_cfg.get("answer_final", 0) or 0)
            if isinstance(max_chars_cfg, dict)
            else 0,
            "answer_baseline": int(max_chars_cfg.get("answer_baseline", 0) or 0)
            if isinstance(max_chars_cfg, dict)
            else 0,
            "prompt_preview": int(max_chars_cfg.get("prompt_preview", 0) or 0)
            if isinstance(max_chars_cfg, dict)
            else 0,
        }

        entity = str(event.routing.get("entity") or event.facts.get("entity") or "")
        is_private = entity in private_entities
        masked_fields: set[str] = set()
        truncated_fields: set[str] = set()

        request_block = _sanitize_request_block(event.request, mask_fields, masked_fields)

        # facts
        facts_block = _build_facts_block(
            event.facts,
            max_rows_sample=max_rows_sample,
            mask_fields=mask_fields,
            masked=masked_fields,
        )

        # routing
        routing_block = {k: event.routing.get(k) for k in ("intent", "entity", "planner_score", "tokens", "thresholds") if k in event.routing}

        # narrator effective policy for snippet limits
        effective_policy = _resolve_entity_policy(entity, narrator_policy)
        rag_snippet_limit = effective_policy.get("rag_snippet_max_chars")
        try:
            rag_snippet_limit_int = int(rag_snippet_limit) if rag_snippet_limit is not None else None
        except (TypeError, ValueError):
            rag_snippet_limit_int = None

        rag_block = _build_rag_block(
            event.rag,
            max_chunks=max_rows_sample,
            snippet_limit=rag_snippet_limit_int,
            truncated=truncated_fields,
            mask_fields=mask_fields,
            masked=masked_fields,
        )

        narrator_block = _build_narrator_block(event.narrator)

        presenter_block = _build_presenter_block(
            event.presenter,
            max_chars=max_chars,
            truncated=truncated_fields,
        )

        shadow_block = _build_shadow_block(
            reason=reason,
            sampling_cfg=sampling_cfg,
            policy_version=_policy_version(shadow_policy),
            masked=masked_fields,
            truncated=truncated_fields,
            entity=entity,
        )

        record = {
            "timestamp": datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "environment": event.environment,
            "request": request_block,
            "routing": routing_block,
            "facts": facts_block,
            "rag": rag_block,
            "narrator": narrator_block,
            "presenter": presenter_block,
            "shadow": shadow_block,
        }

        if is_private:
            record = _mask_fields(record, mask_fields, masked_fields)
            record["shadow"]["redaction_applied"]["masked_fields"] = sorted(masked_fields)

        if not _shadow_payload_size_ok(record, shadow_cfg):
            LOGGER.warning("Narrator shadow descartado por tamanho excedente")
            return

        sink = _select_sink(shadow_cfg)
        sink.write(record)
        _safe_counter("sirios_narrator_shadow_total", outcome="ok")
    except Exception:
        LOGGER.exception("Falha ao coletar Narrator Shadow", exc_info=True)
        _safe_counter("sirios_narrator_shadow_total", outcome="error")
