# app/narrator/narrator.py
from __future__ import annotations

import logging
import os
import re
import threading
import time
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from contextlib import contextmanager

from app.narrator.canonical import extract_canonical_value
from app.narrator.formatter import build_narrator_text
from app.narrator.prompts import (
    build_bucket_d_global_prompt,
    build_prompt,
    render_narrative,
)
from app.observability.metrics import (
    emit_counter as counter,
    emit_histogram as histogram,
)
from app.utils.filecache import load_yaml_cached
import yaml

try:
    from app.rag.ollama_client import OllamaClient
except Exception:  # pragma: no cover - dependência opcional
    OllamaClient = None  # type: ignore

_FAILSAFE_TEXT = (
    "Não sei responder com segurança agora. Exemplos de perguntas válidas: "
    "'Qual o cnpj do MCCI11', 'Qual o preço do MXRF11 hoje'."
)

LOGGER = logging.getLogger(__name__)
_ENTITY_ROOT = Path("data/entities")
_NARRATOR_POLICY_PATH = Path("data/policies/narrator.yaml")
_NARRATOR_SHADOW_POLICY_PATH = Path("data/policies/narrator_shadow.yaml")
_TICKER_RE = re.compile(r"\b([A-Z]{4}\d{2})\b", re.IGNORECASE)
_FILTER_FIELD_NAMES = ("filters", "filter")
_DIGIT_RE = re.compile(r"\d")
_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_NARRATOR_SEMAPHORE: threading.Semaphore | None = None
_NARRATOR_SEMAPHORE_SIZE = 0


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _get_narrator_semaphore() -> threading.Semaphore:
    global _NARRATOR_SEMAPHORE, _NARRATOR_SEMAPHORE_SIZE
    desired = max(1, _env_int("NARRATOR_MAX_CONCURRENCY", 1))
    if _NARRATOR_SEMAPHORE is None or desired != _NARRATOR_SEMAPHORE_SIZE:
        _NARRATOR_SEMAPHORE = threading.Semaphore(desired)
        _NARRATOR_SEMAPHORE_SIZE = desired
    return _NARRATOR_SEMAPHORE


@contextmanager
def _narrator_llm_slot(timeout_s: float = 0):
    semaphore = _get_narrator_semaphore()
    acquired = False
    try:
        acquired = semaphore.acquire(timeout=timeout_s)
        yield acquired
    finally:
        if acquired:
            try:
                semaphore.release()
            except ValueError:
                pass


def _policy_timeout_seconds(policy_guards: Dict[str, Any]) -> float | None:
    if not isinstance(policy_guards, dict):
        return None
    raw = policy_guards.get("timeout_seconds")
    if raw is None:
        return None
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return None
    if val <= 0:
        return None
    return val


def _apply_client_timeout_temporarily(
    client: Any, timeout_s: float | None
) -> tuple[bool, float | None]:
    if client is None or timeout_s is None:
        return (False, None)
    if not hasattr(client, "timeout"):
        return (False, None)
    try:
        prev = float(getattr(client, "timeout"))
    except Exception:
        prev = None
    try:
        setattr(client, "timeout", float(timeout_s))
        return (True, prev)
    except Exception:
        return (False, prev)


def _extract_numbers_and_dates(text: str) -> set[str]:
    numbers = set(re.findall(r"\b\d+(?:[.,]\d+)?\b", text))
    dates = set(re.findall(r"\b\d{1,4}[/-]\d{1,2}[/-]\d{1,4}\b", text))
    return numbers.union(dates)


def _extract_urls(text: str) -> set[str]:
    return set(_URL_RE.findall(text))


def _contains_pipe_table(text: str) -> bool:
    if "|" not in text:
        return False
    for line in text.splitlines():
        pipes = line.count("|")
        if pipes >= 2:
            return True
    return False


def _contains_markdown_table(text: str) -> bool:
    if "|" not in text:
        return False
    lines = [ln.strip() for ln in text.splitlines() if "|" in ln]
    for idx, line in enumerate(lines[:-1]):
        if line.count("|") < 2:
            continue
        next_line = lines[idx + 1]
        if re.match(r"^\|?\s*:?-{3,}", next_line):
            return True
    return False


def _get_policy_guards(policy: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(policy, dict):
        return {}
    guards = policy.get("policy_guards")
    return guards if isinstance(guards, dict) else {}


def _fail_closed_action(policy_guards: Dict[str, Any], key: str) -> str:
    cfg = policy_guards.get("fail_closed") if isinstance(policy_guards, dict) else {}
    if isinstance(cfg, dict):
        action = cfg.get(key)
        if isinstance(action, str) and action.strip():
            return action.strip()
    return "return_baseline"


def _policy_violation_reason(
    baseline_text: str,
    candidate_text: str,
    policy_guards: Dict[str, Any],
) -> str | None:
    if not policy_guards:
        return None

    invariants_raw = policy_guards.get("invariants_prohibited")
    invariants = (
        {str(item) for item in invariants_raw}
        if isinstance(invariants_raw, (list, tuple, set))
        else set()
    )
    rewrite_only_default = bool(policy_guards.get("rewrite_only_default", False))

    baseline = baseline_text or ""
    candidate = candidate_text or ""

    check_numbers = rewrite_only_default or "change_numbers_or_dates" in invariants
    if check_numbers:
        if _extract_numbers_and_dates(baseline) != _extract_numbers_and_dates(
            candidate
        ):
            return "change_numbers_or_dates"

    check_tickers = rewrite_only_default or "change_tickers" in invariants
    if check_tickers:
        if set(_TICKER_RE.findall(baseline.upper())) != set(
            _TICKER_RE.findall(candidate.upper())
        ):
            return "change_tickers"

    check_urls = rewrite_only_default or "change_urls" in invariants
    if check_urls:
        if _extract_urls(baseline) != _extract_urls(candidate):
            return "change_urls"

    baseline_has_pipe = _contains_pipe_table(baseline)
    candidate_has_pipe = _contains_pipe_table(candidate)

    if "emit_pipe_tables" in invariants or (
        not baseline_has_pipe and candidate_has_pipe
    ):
        if candidate_has_pipe and not baseline_has_pipe:
            return "emit_pipe_tables"

    baseline_has_markdown = _contains_markdown_table(baseline)
    candidate_has_markdown = _contains_markdown_table(candidate)

    if "emit_markdown_tables" in invariants or (
        not baseline_has_markdown and candidate_has_markdown
    ):
        if candidate_has_markdown and not baseline_has_markdown:
            return "emit_markdown_tables"

    return None


def _entity_yaml_path(entity: str) -> Path:
    base_dir = _ENTITY_ROOT / entity
    new_path = base_dir / f"{entity}.yaml"
    legacy_path = base_dir / "entity.yaml"
    if new_path.exists():
        return new_path
    if legacy_path.exists():
        return legacy_path
    return new_path


def _json_sanitise(obj: Any) -> Any:
    """
    Normaliza estruturas para algo seguro para JSON / prompts:
    - Decimal -> float
    - dict/list/tuple/set -> recursivo
    Mantém o restante inalterado.
    """
    if isinstance(obj, Decimal):
        # Se preferir preservar formatação, pode trocar para str(obj)
        return float(obj)

    if isinstance(obj, dict):
        return {k: _json_sanitise(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple, set)):
        t = type(obj)
        return t(_json_sanitise(v) for v in obj)

    return obj


def _load_entity_config(entity: str) -> Dict[str, Any]:
    if not entity:
        return {}
    path = _entity_yaml_path(entity)
    try:
        return load_yaml_cached(str(path)) or {}
    except Exception:
        return {}


def _empty_message(entity: str) -> str | None:
    cfg = _load_entity_config(entity)
    presentation = cfg.get("presentation") if isinstance(cfg, dict) else None
    if isinstance(presentation, dict):
        message = presentation.get("empty_message")
        if isinstance(message, str) and message.strip():
            return message.strip()
    return None


def _rows_to_lines(
    rows: Iterable[Dict[str, Any]],
    requested_metrics: Optional[Iterable[str]] = None,
) -> str:
    lines: list[str] = []
    requested: list[str] = []
    if requested_metrics:
        requested = [
            str(metric)
            for metric in requested_metrics
            if isinstance(metric, str) and metric.strip()
        ]
        # garante ordem determinística e remove duplicatas
        seen_req: Dict[str, None] = {}
        for metric in requested:
            if metric not in seen_req:
                seen_req[metric] = None
        requested = list(seen_req.keys())

    for row in rows:
        if not isinstance(row, dict):
            continue
        parts: list[str] = []
        keys_order: list[str]
        if requested:
            keys_order = []
            if "ticker" in row:
                keys_order.append("ticker")
            keys_order.extend(
                [key for key in requested if key != "ticker" and key in row]
            )
        else:
            keys_order = [k for k in row.keys() if k != "meta"]
        for key in keys_order:
            if key == "meta":
                continue
            if key not in row:
                continue
            item_val = row.get(key)
            if item_val is None:
                continue
            text = str(item_val)
            if not text:
                continue
            parts.append(f"**{key}**: {text}")
        if parts:
            lines.append("- " + "; ".join(parts))
    return "\n".join(lines).strip()


def _compact_facts_payload(
    results: Dict[str, Any] | None,
    meta: Dict[str, Any] | None,
    *,
    max_rows: int = 5,
    max_columns: int = 6,
) -> Dict[str, Any]:
    """Reduz resultados SQL para um payload compacto e seguro para prompts."""

    payload: Dict[str, Any] = {}

    def _truncate_rows(rows: Iterable[Dict[str, Any]]) -> list[Dict[str, Any]]:
        trimmed: list[Dict[str, Any]] = []
        for row in list(rows)[: max_rows if max_rows > 0 else None]:
            if not isinstance(row, dict):
                continue
            compact: Dict[str, Any] = {}
            for idx, (key, value) in enumerate(row.items()):
                if key == "meta":
                    continue
                if max_columns > 0 and idx >= max_columns:
                    break
                compact[key] = value
            if compact:
                trimmed.append(compact)
        return trimmed

    if isinstance(results, dict):
        rows = results.get("rows") or results.get("data") or []
        if isinstance(rows, list):
            compact_rows = _truncate_rows(rows)
            if compact_rows:
                payload["rows"] = compact_rows

        for key in ("summary", "totals", "labels"):
            if key in results:
                payload[key] = results.get(key)

    if isinstance(meta, dict):
        meta_fields = {}
        for key in ("window", "aggregation", "period"):
            if key in meta:
                meta_fields[key] = meta.get(key)
        if meta_fields:
            payload["meta"] = meta_fields

    return _json_sanitise(payload)


def _default_text(entity: str, facts: Dict[str, Any]) -> str:
    rows = list((facts or {}).get("rows") or [])
    requested_metrics = (facts or {}).get("requested_metrics")
    candidates = [
        (facts or {}).get("rendered"),
        (facts or {}).get("rendered_text"),
        (facts or {}).get("text"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    if rows:
        rendered = _rows_to_lines(rows, requested_metrics=requested_metrics)
        if rendered:
            return rendered
    message = _empty_message(entity)
    if message:
        return message
    return "Sem dados disponíveis no momento."


def _iter_filter_payloads(source: Dict[str, Any] | None) -> Iterable[Any]:
    if not isinstance(source, dict):
        return []
    payloads = []
    for field in _FILTER_FIELD_NAMES:
        if field in source:
            payloads.append(source[field])
    nested_meta = source.get("meta")
    if isinstance(nested_meta, dict):
        payloads.extend(_iter_filter_payloads(nested_meta))
    return payloads


def _collect_filter_texts(payload: Any) -> Iterable[str]:
    texts: list[str] = []
    if isinstance(payload, str):
        texts.append(payload)
    elif isinstance(payload, dict):
        for value in payload.values():
            texts.extend(_collect_filter_texts(value))
    elif isinstance(payload, (list, tuple, set)):
        for item in payload:
            texts.extend(_collect_filter_texts(item))
    return texts


def _best_rag_chunk_text(
    rag_ctx: Dict[str, Any] | None, *, max_chars: int = 900
) -> str:
    if not isinstance(rag_ctx, dict):
        return ""
    chunks = rag_ctx.get("chunks")
    if not isinstance(chunks, list):
        return ""
    best_text = ""
    best_score = float("-inf")
    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue
        raw_text = chunk.get("text")
        if not isinstance(raw_text, str):
            continue
        text = raw_text.strip()
        if not text:
            continue
        score_raw = chunk.get("score", 0.0)
        try:
            score = float(score_raw)
        except (TypeError, ValueError):
            score = 0.0
        if score > best_score:
            best_score = score
            best_text = text
    if not best_text:
        return ""
    if max_chars > 0 and len(best_text) > max_chars:
        truncated = best_text[:max_chars].rsplit(" ", 1)[0].strip()
        if not truncated:
            truncated = best_text[:max_chars].strip()
        best_text = truncated + "..."
    return best_text


def _shrink_rag_for_concept(
    rag_ctx: Dict[str, Any] | None, *, max_chars: int = 900
) -> Dict[str, Any] | None:
    """
    Em modo conceitual, reduz o contexto de RAG para apenas o melhor chunk,
    com texto truncado, para evitar prompts gigantes e dispersão de foco.
    """
    if not isinstance(rag_ctx, dict):
        return None
    if not rag_ctx.get("enabled"):
        return None

    chunks = rag_ctx.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        return None

    best_chunk: Dict[str, Any] | None = None
    best_score = float("-inf")

    for ch in chunks:
        if not isinstance(ch, dict):
            continue
        raw_text = ch.get("text")
        if not isinstance(raw_text, str):
            continue
        text = raw_text.strip()
        if not text:
            continue
        score_raw = ch.get("score", 0.0)
        try:
            score = float(score_raw)
        except (TypeError, ValueError):
            score = 0.0
        if score > best_score:
            best_score = score
            best_chunk = ch

    if not best_chunk:
        return None

    new_chunk = dict(best_chunk)
    raw_text = new_chunk.get("text") or ""
    if isinstance(raw_text, str) and max_chars > 0 and len(raw_text) > max_chars:
        truncated = raw_text[:max_chars].rsplit(" ", 1)[0].strip()
        if not truncated:
            truncated = raw_text[:max_chars].strip()
        new_chunk["text"] = truncated + "..."

    policy_raw = rag_ctx.get("policy") or {}
    collections = None
    if isinstance(policy_raw, dict):
        collections = policy_raw.get("collections")
    if not collections:
        collections = rag_ctx.get("used_collections")

    new_ctx: Dict[str, Any] = {
        "enabled": True,
        "intent": rag_ctx.get("intent"),
        "entity": rag_ctx.get("entity"),
        "chunks": [new_chunk],
        "policy": {
            "max_chunks": 1,
            "collections": collections,
        },
        "used_collections": rag_ctx.get("used_collections"),
    }

    return new_ctx


def _extract_tickers_from_question_and_filters(
    question: str,
    meta: Dict[str, Any] | None,
    facts: Dict[str, Any] | None,
) -> set[str]:
    tickers: set[str] = set()

    def _apply_regex(text: str | None) -> None:
        if not isinstance(text, str):
            return
        for match in _TICKER_RE.findall(text):
            tickers.add(match.upper())

    _apply_regex(question)

    for payload in _iter_filter_payloads(meta):
        for text in _collect_filter_texts(payload):
            _apply_regex(text)

    for payload in _iter_filter_payloads(facts):
        for text in _collect_filter_texts(payload):
            _apply_regex(text)

    return tickers


def _load_narrator_policy(path: str = str(_NARRATOR_POLICY_PATH)) -> Dict[str, Any]:
    """
    Carrega política declarativa do Narrator a partir de data/policies/narrator.yaml.

    Falha rápido para arquivos ausentes, YAML inválido ou estrutura incorreta.
    """

    policy_path = Path(path)
    if not policy_path.exists():
        LOGGER.error("Narrator policy ausente em %s", policy_path)
        raise RuntimeError(f"Narrator policy ausente: {policy_path}")

    try:
        data = load_yaml_cached(str(policy_path))
    except (yaml.YAMLError, OSError, RuntimeError) as exc:
        LOGGER.error(
            "Erro ao carregar Narrator policy de %s", policy_path, exc_info=True
        )
        raise ValueError(f"Narrator policy inválida: {policy_path}") from exc
    except Exception as exc:  # pragma: no cover - caminho excepcional
        LOGGER.error(
            "Erro inesperado ao carregar Narrator policy de %s",
            policy_path,
            exc_info=True,
        )
        raise RuntimeError(f"Erro ao carregar Narrator policy: {policy_path}") from exc

    if not isinstance(data, dict):
        LOGGER.error("Narrator policy inválida (esperado mapeamento): %s", policy_path)
        raise ValueError(
            f"Narrator policy inválida: esperado mapeamento em {policy_path}"
        )

    cfg = data.get("narrator")
    if not isinstance(cfg, dict):
        LOGGER.error(
            "Narrator policy inválida: bloco 'narrator' ausente ou malformado em %s",
            policy_path,
        )
        raise ValueError(
            f"Narrator policy inválida: bloco 'narrator' deve ser mapeamento em {policy_path}"
        )

    required_fields: dict[str, type] = {
        "model": str,
        "llm_enabled": bool,
        "shadow": bool,
    }

    for key, expected_type in required_fields.items():
        if key not in cfg:
            LOGGER.error("Narrator policy malformada: campo '%s' é obrigatório", key)
            raise ValueError(f"Narrator policy malformada: campo '{key}' é obrigatório")

        value = cfg.get(key)
        if expected_type is bool:
            if not isinstance(value, bool):
                LOGGER.error("Narrator policy malformada: '%s' deve ser booleano", key)
                raise ValueError(
                    f"Narrator policy malformada: '{key}' deve ser booleano"
                )
        elif expected_type is str:
            if not isinstance(value, str) or not value.strip():
                LOGGER.error(
                    "Narrator policy malformada: '%s' deve ser string não vazia",
                    key,
                )
                raise ValueError(
                    f"Narrator policy malformada: '{key}' deve ser string não vazia"
                )

    # Retorna o YAML completo (fonte de verdade), preservando seções como:
    # default, entities, buckets, policy_guards, etc.
    # A validação obrigatória permanece no bloco data["narrator"].
    return data


def _coerce_env_flag(raw: str | None) -> Optional[bool]:
    if raw is None:
        return None
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return None


def _load_narrator_shadow_policy(
    path: str = str(_NARRATOR_SHADOW_POLICY_PATH),
) -> Dict[str, Any]:
    policy_path = Path(path)
    if not policy_path.exists():
        LOGGER.error("Narrator shadow policy ausente em %s", policy_path)
        raise RuntimeError(f"Narrator shadow policy ausente: {policy_path}")

    try:
        data = load_yaml_cached(str(policy_path))
    except (yaml.YAMLError, OSError, RuntimeError) as exc:
        LOGGER.error(
            "Erro ao carregar Narrator shadow policy de %s", policy_path, exc_info=True
        )
        raise ValueError(f"Narrator shadow policy inválida: {policy_path}") from exc
    except Exception as exc:  # pragma: no cover - caminho excepcional
        LOGGER.error(
            "Erro inesperado ao carregar Narrator shadow policy de %s",
            policy_path,
            exc_info=True,
        )
        raise RuntimeError(
            f"Erro ao carregar Narrator shadow policy: {policy_path}"
        ) from exc

    if not isinstance(data, dict):
        LOGGER.error(
            "Narrator shadow policy inválida (esperado mapeamento): %s", policy_path
        )
        raise ValueError(
            f"Narrator shadow policy inválida: esperado mapeamento em {policy_path}"
        )

    cfg = (
        data.get("narrator_shadow")
        if isinstance(data.get("narrator_shadow"), dict)
        else data
    )

    return cfg if isinstance(cfg, dict) else {}


def _get_effective_policy(entity: str | None, policy: Dict[str, Any]) -> Dict[str, Any]:
    """Combina política global do Narrator com overrides específicos por entidade."""

    policy_dict = policy or {}
    default_policy = {}
    if isinstance(policy_dict, dict):
        default_policy = (
            policy_dict.get("default")
            if isinstance(policy_dict.get("default"), dict)
            else {}
        )

    effective_policy = {
        "llm_enabled": False,
        "shadow": False,
        "max_llm_rows": 0,
        "use_rag_in_prompt": False,
        "model": "sirios-narrator:latest",
    }

    base_overrides = {
        k: v
        for k, v in policy_dict.items()
        if k not in {"default", "entities", "terms", "version"}
    }

    if isinstance(default_policy, dict):
        effective_policy.update(default_policy)

    effective_policy.update(base_overrides)

    entities_cfg = policy_dict.get("entities") if isinstance(policy_dict, dict) else {}
    if isinstance(entities_cfg, dict):
        entity_policy_raw = entities_cfg.get(entity or "")
        if isinstance(entity_policy_raw, dict):
            effective_policy.update(entity_policy_raw)

    return effective_policy


class Narrator:
    def __init__(self, model: str | None = None, style: str = "executivo"):
        # Política declarativa (fonte de verdade)
        policy_payload = _load_narrator_policy()
        self._policy_status: str = "ok"
        self._policy_error: str | None = None
        policy_content: Dict[str, Any] = {}

        if isinstance(policy_payload, dict):
            if "status" in policy_payload:
                self._policy_status = policy_payload.get("status", "ok") or "ok"
            raw_error = policy_payload.get("error")
            if isinstance(raw_error, str) and raw_error.strip():
                self._policy_error = raw_error.strip()

            # 1) wrapper (quality push / runtime)
            candidate_policy = policy_payload.get("policy")
            if isinstance(candidate_policy, dict):
                policy_content = candidate_policy
            else:
                # 2) YAML com nó raiz "narrator:"
                candidate_narrator = policy_payload.get("narrator")
                if isinstance(candidate_narrator, dict):
                    policy_content = candidate_narrator
                # 3) policy já flat
                elif "status" not in policy_payload:
                    policy_content = policy_payload

        self.policy = policy_content
        self.shadow_policy = _load_narrator_shadow_policy()
        self.bucket_policy: Dict[str, Any] = (
            policy_content.get("buckets") if isinstance(policy_content, dict) else {}
        )

        default_policy = _get_effective_policy(None, self.policy)

        # Política específica por entidade (opcional)
        entities_cfg = (
            self.policy.get("entities") if isinstance(self.policy, dict) else {}
        )
        self.entities_policy: Dict[str, Any] = (
            entities_cfg if isinstance(entities_cfg, dict) else {}
        )

        # Modelo / estilo: prioridade → arg explícito > YAML > env > default
        self.model = (
            model
            or default_policy.get("model")
            or self.policy.get("model")
            or os.getenv("NARRATOR_MODEL")
            or "sirios-narrator:latest"
        )
        self.style = style or self.policy.get("style") or "executivo"

        # Flags: **apenas YAML** define habilitação e shadow;
        # env é ignorado para evitar heurísticas escondidas.
        self.enabled = bool(default_policy.get("llm_enabled", False))
        self.shadow = (
            bool(default_policy.get("shadow", False))
            and self._is_shadow_globally_enabled()
        )

        # Limite de linhas para uso de LLM (0 = nunca usar LLM)
        max_rows = default_policy.get("max_llm_rows", 0)
        try:
            self.max_llm_rows = int(max_rows)
        except (TypeError, ValueError):
            self.max_llm_rows = 0

        # (Reservado) limites de tokens — ainda não usados no prompt builder,
        # mas já carregados da política para futuro hardening.
        self.max_prompt_tokens = int(self.policy.get("max_prompt_tokens", 0) or 0)
        self.max_output_tokens = int(self.policy.get("max_output_tokens", 0) or 0)

        self.client = OllamaClient() if OllamaClient else None

    def _shadow_cfg(self) -> Dict[str, Any]:
        return self.shadow_policy if isinstance(self.shadow_policy, dict) else {}

    def _is_shadow_globally_enabled(self) -> bool:
        shadow_cfg = self._shadow_cfg()
        enabled = bool(shadow_cfg.get("enabled", False))
        env_override = _coerce_env_flag(os.getenv("NARRATOR_SHADOW_GLOBAL"))
        if env_override is not None:
            enabled = env_override

        env_label = os.getenv("SIRIOS_ENV", os.getenv("ENVIRONMENT", "dev"))
        env_allowlist = shadow_cfg.get("environment_allowlist")
        if isinstance(env_allowlist, list) and env_allowlist:
            if env_label not in env_allowlist:
                return False

        return enabled

    # ------------------------------------------------------------------
    # Narrativa pós-SQL para buckets globais (D)
    # ------------------------------------------------------------------

    def render_global_post_sql(
        self,
        *,
        question: str,
        entity: str,
        bucket: str,
        results: Dict[str, Any] | None,
        meta: Dict[str, Any] | None,
        context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Gera narrativa global usando LLM, preservando resultados."""

        effective_meta = dict(meta) if isinstance(meta, dict) else {}
        # Usa a mesma resolução de policy do restante do Narrator
        global_policy = _get_effective_policy(None, self.policy)
        if not bool(global_policy.get("llm_enabled", False)):
            return effective_meta

        bucket_cfg = (
            self.bucket_policy.get(bucket, {})
            if isinstance(self.bucket_policy, dict)
            else {}
        )
        if not isinstance(bucket_cfg, dict) or not bucket_cfg.get("llm_enabled"):
            return effective_meta

        if bucket_cfg.get("mode") != "global_post_sql":
            return effective_meta

        entities_allowed = bucket_cfg.get("entities")
        if isinstance(entities_allowed, list) and entities_allowed:
            if entity not in entities_allowed:
                return effective_meta

        max_rows = bucket_cfg.get("max_rows", 5)
        max_columns = bucket_cfg.get("max_columns", 6)
        try:
            max_rows = int(max_rows)
        except (TypeError, ValueError):
            max_rows = 5
        try:
            max_columns = int(max_columns)
        except (TypeError, ValueError):
            max_columns = 6

        facts_payload = _compact_facts_payload(
            results, effective_meta, max_rows=max_rows, max_columns=max_columns
        )

        model = bucket_cfg.get("model") or self.model
        temperature = bucket_cfg.get("temperature")
        max_tokens = bucket_cfg.get("max_tokens")

        prompt = build_bucket_d_global_prompt(
            question=question,
            entity=entity,
            bucket=bucket,
            facts_payload=facts_payload,
            policy=bucket_cfg,
            meta=context or {},
        )

        client = self.client
        if client is None:
            return effective_meta

        t0 = time.perf_counter()
        outcome = "ok"
        entity_label = str(entity or "")
        bucket_label = str(bucket or "")
        with _narrator_llm_slot(timeout_s=0) as acquired:
            if not acquired:
                latency_s = time.perf_counter() - t0
                counter(
                    "services_narrator_llm_requests_total",
                    outcome="overload",
                    bucket=bucket_label,
                    entity=entity_label,
                )
                histogram(
                    "services_narrator_llm_latency_seconds",
                    latency_s,
                    bucket=bucket_label,
                    entity=entity_label,
                )
                effective_meta["narrative_error"] = "narrator_concurrency_limit"
                effective_meta["narrative_overload"] = True
                return effective_meta
            try:
                response = client.generate(
                    prompt,
                    model=model,
                    stream=False,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                narrative = (response or "").strip()
                if narrative:
                    effective_meta["narrative"] = narrative
            except Exception as exc:  # pragma: no cover - caminho excepcional
                effective_meta["narrative_error"] = str(exc)
                outcome = "error"
        latency_s = time.perf_counter() - t0

        entity_label = str(entity or "")
        bucket_label = str(bucket or "")
        counter(
            "services_narrator_llm_requests_total",
            outcome=outcome,
            bucket=bucket_label,
            entity=entity_label,
        )
        histogram(
            "services_narrator_llm_latency_seconds",
            latency_s,
            bucket=bucket_label,
            entity=entity_label,
        )

        return effective_meta

    def get_effective_policy(self, entity: str | None) -> Dict[str, Any]:
        base_policy = _get_effective_policy(entity, self.policy)
        effective = dict(base_policy)
        effective["model"] = effective.get("model") or self.model
        effective["llm_enabled"] = bool(effective.get("llm_enabled", False))
        shadow_allowed = bool(effective.get("shadow", False))
        effective["shadow"] = shadow_allowed and self._is_shadow_globally_enabled()
        effective["shadow_global_enabled"] = self._is_shadow_globally_enabled()
        return effective

    # ---------------------------------------------------------------------
    # Decisão de uso de LLM — 100% baseada em policy (sem heurísticas fixas)
    # ---------------------------------------------------------------------
    def _should_use_llm(
        self, facts: Dict[str, Any], effective_policy: Dict[str, Any]
    ) -> bool:
        """
        Regras:
          - se Narrator estiver desabilitado na policy → nunca usa LLM;
          - se max_llm_rows == 0 → nunca usa LLM;
          - se len(rows) > max_llm_rows → não usa LLM;
        """
        enabled = bool((effective_policy or {}).get("llm_enabled", False))
        if not enabled:
            return False

        rows = list((facts or {}).get("rows") or [])
        rows_count = len(rows)

        max_rows = (effective_policy or {}).get("max_llm_rows", 0)
        try:
            max_llm_rows = int(max_rows)
        except (TypeError, ValueError):
            max_llm_rows = 0

        if max_llm_rows <= 0:
            return False

        if rows_count > max_llm_rows:
            return False

        return True

    # ---------------------------------------------------------------------

    def render(
        self, question: str, facts: Dict[str, Any], meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        t0_global = time.perf_counter()
        raw_meta = meta or {}
        raw_facts = facts or {}
        entity = raw_meta.get("entity") or ""
        intent = raw_meta.get("intent") or ""
        template_id = raw_meta.get("template_id") or raw_facts.get("result_key")
        render_meta: Dict[str, Any] = dict(raw_meta)

        # meta.compute.mode (quando presente) é a fonte primária para o modo
        # de computação: "concept" vs "data"/"default".
        compute_mode_meta: Optional[str] = None
        compute_block = raw_meta.get("compute")
        if isinstance(compute_block, dict):
            raw_mode = compute_block.get("mode")
            if isinstance(raw_mode, str):
                m = raw_mode.strip().lower()
                if m in ("concept", "data", "default"):
                    compute_mode_meta = m

        # Política efetiva (global + overrides da entidade)
        effective_policy = self.get_effective_policy(entity)
        effective_enabled = bool(effective_policy.get("llm_enabled", self.enabled))
        effective_shadow = bool(effective_policy.get("shadow", self.shadow))
        max_rows_policy = effective_policy.get("max_llm_rows", self.max_llm_rows)
        try:
            effective_max_llm_rows = int(max_rows_policy)
        except (TypeError, ValueError):
            effective_max_llm_rows = 0

        use_rag_in_prompt = bool(effective_policy.get("use_rag_in_prompt", False))
        rag_snippet_max_chars = effective_policy.get("rag_snippet_max_chars", 900)
        try:
            rag_snippet_max_chars = int(rag_snippet_max_chars)
        except (TypeError, ValueError):
            rag_snippet_max_chars = 900
        effective_model = effective_policy.get("model") or self.model

        narrator_meta: Dict[str, Any] = {
            "enabled": effective_enabled,
            "shadow": effective_shadow,
            "model": effective_model,
            "latency_ms": None,
            "error": None,
            "used": False,
            "strategy": "deterministic",
            "effective_policy": _json_sanitise(
                {
                    "llm_enabled": effective_enabled,
                    "shadow": effective_shadow,
                    "max_llm_rows": effective_max_llm_rows,
                    "use_rag_in_prompt": use_rag_in_prompt,
                    "rewrite_only": bool(effective_policy.get("rewrite_only", False)),
                    "model": effective_model,
                }
            ),
            "rag": None,
            "compute_mode": None,
        }

        # Política específica da entidade (se houver)
        entity_policy = effective_policy
        prefer_concept_when_no_ticker = bool(
            entity_policy.get("prefer_concept_when_no_ticker", False)
        )
        rag_fallback_when_no_rows = bool(
            entity_policy.get("rag_fallback_when_no_rows", False)
        )
        concept_with_data_when_rag = bool(
            entity_policy.get("concept_with_data_when_rag", False)
        )

        # Decisão de modo:
        # - concept_mode=True  -> resposta conceitual (ignora rows)
        # - concept_mode=False -> resposta baseada em rows (por fundo)
        concept_mode = False
        effective_facts: Dict[str, Any] = dict(raw_facts)

        # Ordem de precedência:
        # 1) meta.compute.mode (quando definido)
        # 2) policy prefer_concept_when_no_ticker (fallback)
        if compute_mode_meta == "concept":
            concept_mode = True
        elif compute_mode_meta in ("data", "default"):
            concept_mode = False
        elif prefer_concept_when_no_ticker:
            detected_tickers = _extract_tickers_from_question_and_filters(
                question=question,
                meta=render_meta,
                facts=effective_facts,
            )
            if not detected_tickers:
                concept_mode = True

        # Normaliza render_meta.compute para refletir o modo efetivo
        if not isinstance(render_meta.get("compute"), dict):
            render_meta["compute"] = {"mode": "concept" if concept_mode else "data"}
        else:
            compute_block_rm = render_meta["compute"]
            if "mode" not in compute_block_rm:
                compute_block_rm["mode"] = "concept" if concept_mode else "data"

        compute_mode_effective = "concept" if concept_mode else "data"
        narrator_meta["compute_mode"] = compute_mode_effective

        # ------------------------------------------------------------------
        # Métrica foco (focus_metric_key) — vinda da ontologia / requested_metrics
        # ------------------------------------------------------------------
        focus_metric_key: str | None = None
        focus_meta = render_meta.get("focus")
        if isinstance(focus_meta, dict):
            candidate = focus_meta.get("metric_key")
            if isinstance(candidate, str) and candidate.strip():
                focus_metric_key = candidate.strip()

        if focus_metric_key is None:
            requested_metrics = effective_facts.get("requested_metrics")
            if (
                isinstance(requested_metrics, (list, tuple))
                and len(requested_metrics) == 1
            ):
                candidate = requested_metrics[0]
                if isinstance(candidate, str) and candidate.strip():
                    focus_metric_key = candidate.strip()
        # ------------------------------------------------------------------
        # Propaga foco para o prompt via meta.focus.metric_key (contrato do prompt)
        # Sem heurística: deriva 1:1 de requested_metrics (declarativo no YAML).
        # ------------------------------------------------------------------
        if focus_metric_key:
            if not isinstance(render_meta.get("focus"), dict):
                render_meta["focus"] = {}
            mk_existing = render_meta["focus"].get("metric_key")
            if not isinstance(mk_existing, str) or not mk_existing.strip():
                render_meta["focus"]["metric_key"] = focus_metric_key

        canonical_value = extract_canonical_value(effective_facts, focus_metric_key)
        if canonical_value:
            effective_facts["llm_canonical_value"] = canonical_value
            effective_facts["llm_focus_metric_key"] = focus_metric_key
            narrator_meta["canonical"] = {
                "metric_key": focus_metric_key,
                "value": canonical_value,
            }
            preview_value = canonical_value
            if isinstance(preview_value, str) and len(preview_value) > 80:
                preview_value = preview_value[:77] + "..."
            LOGGER.debug(
                "NARRATOR_CANONICAL_VALUE metric_key=%s value=%s",
                focus_metric_key,
                preview_value,
            )

        narrator_meta["focus_metric_key"] = focus_metric_key

        if concept_mode:
            render_meta["narrator_mode"] = "concept"
            # Evita que perguntas conceituais virem "Índice de Treynor do LPLP11 = 0,00%"
            effective_facts["narrator_mode"] = "concept"
            effective_facts["rows"] = []
            if "rows_sample" in effective_facts:
                effective_facts["rows_sample"] = []
            if "primary" in effective_facts:
                effective_facts["primary"] = {}

        # Contexto de RAG (opcional, injetado pelo Orchestrator em meta['rag'])
        # Regra:
        #   - se meta.rag não existir ou não for dict → rag_ctx = None
        #   - se meta.rag existir e for dict → repassado como está p/ build_prompt
        #   - se meta.rag_debug_disable=True → força rag_ctx=None (modo debug)
        rag_raw = render_meta.get("rag")
        rag_ctx = rag_raw if isinstance(rag_raw, dict) else None

        rag_debug_disable = bool(render_meta.get("rag_debug_disable"))
        if rag_debug_disable:
            rag_ctx = None

        if rag_ctx is not None:
            rag_enabled = bool(rag_ctx.get("enabled"))
            rag_chunks_count = len(rag_ctx.get("chunks") or [])
        else:
            rag_enabled = False
            rag_chunks_count = 0
        rag_best_text = _best_rag_chunk_text(rag_ctx)

        narrator_meta["rag"] = _json_sanitise(rag_ctx)

        rag_ctx_for_prompt = rag_ctx if rag_enabled else None
        if rag_ctx_for_prompt is not None:
            if not use_rag_in_prompt:
                shrunk = _shrink_rag_for_concept(
                    rag_ctx_for_prompt, max_chars=rag_snippet_max_chars
                )
                rag_ctx_for_prompt = (
                    shrunk if shrunk is not None else rag_ctx_for_prompt
                )
            elif concept_mode:
                # Em modo conceitual, usamos apenas um chunk enxuto de RAG
                shrunk = _shrink_rag_for_concept(
                    rag_ctx_for_prompt, max_chars=rag_snippet_max_chars
                )
                rag_ctx_for_prompt = shrunk if shrunk is not None else None

        LOGGER.info(
            "narrator_render entity=%s intent=%s rows_count=%s template_id=%s "
            "enabled=%s shadow=%s model=%s rag_enabled=%s chunks=%s",
            entity,
            intent,
            len(effective_facts.get("rows") or []),
            template_id or "",
            effective_enabled,
            effective_shadow,
            effective_model,
            rag_enabled,
            rag_chunks_count,
        )

        # 1) renderizador especializado
        deterministic_text = render_narrative(render_meta, effective_facts, self.policy)

        if (
            concept_with_data_when_rag
            and rag_best_text
            and (effective_facts.get("rows") or [])
        ):
            rows_block = _rows_to_lines(
                effective_facts.get("rows") or [],
                requested_metrics=effective_facts.get("requested_metrics"),
            )
            if rows_block:
                deterministic_text = (
                    f"{rag_best_text}\n\n**Dados mais recentes:**\n{rows_block}"
                )
        elif (
            rag_fallback_when_no_rows
            and not (effective_facts.get("rows") or [])
            and rag_best_text
        ):
            deterministic_text = rag_best_text

        # 2) formatter genérico
        if not deterministic_text:
            try:
                deterministic_text = build_narrator_text(
                    {"facts": effective_facts or {}}
                )
            except Exception:
                deterministic_text = ""

        # 3) fallback padrão
        baseline_text = deterministic_text or _default_text(entity, effective_facts)
        policy_guards = _get_policy_guards(effective_policy) or _get_policy_guards(
            self.policy
        )
        rows_count = len(effective_facts.get("rows") or [])

        def _finalize_response(
            text: str,
            *,
            tokens_in: int = 0,
            tokens_out: int | None = None,
            latency_ms: float | None = None,
            error: str | None = None,
            strategy_override: str | None = None,
        ) -> Dict[str, Any]:
            computed_tokens_out = (
                tokens_out if tokens_out is not None else len((text or "").split())
            )
            elapsed_ms = (
                latency_ms
                if latency_ms is not None
                else (time.perf_counter() - t0_global) * 1000.0
            )

            narrator_meta["latency_ms"] = elapsed_ms
            if error is not None:
                narrator_meta["error"] = error
            if strategy_override:
                narrator_meta["strategy"] = strategy_override

            final_strategy = narrator_meta.get("strategy") or "deterministic"

            if effective_enabled and effective_max_llm_rows > 0:
                try:
                    prompt_text = text or ""
                    prompt_len_chars = len(prompt_text)
                except Exception:
                    prompt_len_chars = 0

                entity_label = str(entity or "")
                strategy_label = narrator_meta.get("strategy") or "deterministic"

                counter(
                    "sirios_narrator_tokens_in_total",
                    entity=entity_label,
                    strategy=strategy_label,
                )
                if computed_tokens_out > 0:
                    counter(
                        "sirios_narrator_tokens_out_total",
                        entity=entity_label,
                        strategy=strategy_label,
                    )

                histogram(
                    "sirios_narrator_prompt_chars_total",
                    float(prompt_len_chars),
                    entity=entity_label,
                    strategy=strategy_label,
                )
                histogram(
                    "sirios_narrator_prompt_rows_total",
                    float(rows_count),
                    entity=entity_label,
                    strategy=strategy_label,
                )

            return {
                "text": text,
                "score": 1.0 if text else 0.0,
                "hints": {
                    "style": self.style,
                    "mode": "concept" if concept_mode else "default",
                    "strategy": final_strategy,
                },
                "strategy": final_strategy,
                "tokens": {"in": tokens_in, "out": computed_tokens_out},
                "latency_ms": elapsed_ms,
                "error": error,
                "enabled": narrator_meta.get("enabled", False),
                "shadow": narrator_meta.get("shadow", False),
                "meta": {"narrator": narrator_meta},
            }

        if not effective_enabled:
            return _finalize_response(
                baseline_text,
                error="llm_disabled_by_policy",
                strategy_override="llm_disabled_by_policy",
            )

        if effective_max_llm_rows <= 0:
            return _finalize_response(
                baseline_text,
                error="llm_disabled_by_policy",
                strategy_override="llm_disabled_by_policy",
            )

        if rows_count > effective_max_llm_rows:
            return _finalize_response(
                baseline_text,
                error="llm_skipped_max_rows",
                strategy_override="llm_skipped_max_rows",
            )

        if self.client is None:
            return _finalize_response(
                baseline_text,
                error="client_unavailable",
                strategy_override="llm_failed",
            )

        # ------------------------------------------------------------------
        # Fail-safe de evidência: se não há linhas nem chunks de RAG,
        # consideramos que não há contexto suficiente para o LLM trabalhar
        # sem risco de deriva. Nesses casos, não chamamos o modelo e
        # respondemos diretamente com o texto de segurança canônico.
        # ------------------------------------------------------------------
        rewrite_only = bool(effective_policy.get("rewrite_only", False))

        # Em rewrite-only, o Presenter injeta `rendered_text` e pode remover rows/primary.
        # Portanto, o baseline textual vira a evidência primária (âncora factual).
        rendered_text = effective_facts.get("rendered_text")
        has_rendered_text = isinstance(rendered_text, str) and bool(
            rendered_text.strip()
        )

        has_rows = bool(effective_facts.get("rows") or effective_facts.get("primary"))
        rag_chunks = []
        if isinstance(rag_ctx, dict) and rag_ctx.get("enabled"):
            rag_chunks = rag_ctx.get("chunks") or []
        has_rag = bool(rag_chunks)

        # Se rewrite-only estiver ativo, aceitamos `rendered_text` como evidência suficiente.
        if rewrite_only and has_rendered_text:
            pass
        elif not has_rows and not has_rag:
            return _finalize_response(
                _FAILSAFE_TEXT,
                error="llm_skipped_no_evidence",
                strategy_override="llm_skipped_no_evidence",
            )

        prompt_facts = dict(effective_facts or {})
        prompt_facts.setdefault("rendered_text", baseline_text)
        if "fallback_message" not in prompt_facts:
            fallback_message = _empty_message(entity)
            if fallback_message:
                prompt_facts["fallback_message"] = fallback_message

        prompt_meta = dict(render_meta)
        if concept_mode:
            prompt_meta.setdefault("narrator_mode", "concept")

        # Injeta foco explícito no meta do prompt
        if focus_metric_key:
            focus_block = prompt_meta.get("focus")
            if not isinstance(focus_block, dict):
                focus_block = {}
            focus_block["metric_key"] = focus_metric_key
            prompt_meta["focus"] = focus_block

        prompt_facts = _json_sanitise(prompt_facts)
        prompt_meta = _json_sanitise(prompt_meta)
        rag_ctx_sanitised = (
            _json_sanitise(rag_ctx_for_prompt)
            if rag_ctx_for_prompt is not None
            else None
        )

        t0 = time.perf_counter()
        policy_violation: str | None = None
        try:
            prompt = build_prompt(
                question=question,
                facts=prompt_facts,
                meta=prompt_meta,
                style=self.style,
                rag=rag_ctx_sanitised,
                effective_policy=effective_policy,
            )
        except TypeError:
            prompt = build_prompt(
                question=question,
                facts=prompt_facts,
                meta=prompt_meta,
                style=self.style,
                rag=rag_ctx_sanitised,
            )

        tokens_in = len(prompt.split()) if prompt else 0

        text = baseline_text
        error: str | None = None
        tokens_out = 0
        llm_intro_used = False
        llm_intro_tokens = 0

        narrator_meta["used"] = True

        entity_label = str(entity or "")
        bucket_label = str(bucket or "")
        with _narrator_llm_slot(timeout_s=0) as acquired:
            if not acquired:
                latency_s = time.perf_counter() - t0
                counter(
                    "services_narrator_llm_requests_total",
                    outcome="overload",
                    bucket=bucket_label,
                    entity=entity_label,
                )
                histogram(
                    "services_narrator_llm_latency_seconds",
                    latency_s,
                    bucket=bucket_label,
                    entity=entity_label,
                )
                return _finalize_response(
                    baseline_text,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    latency_ms=(time.perf_counter() - t0) * 1000.0,
                    error="llm_concurrency_limited",
                    strategy_override="llm_concurrency_limited",
                )

            try:
                timeout_s = _policy_timeout_seconds(policy_guards)
                applied, prev_timeout = _apply_client_timeout_temporarily(
                    self.client, timeout_s
                )
                if applied:
                    narrator_meta["policy_timeout_seconds"] = timeout_s

                try:
                    response = self.client.generate(
                        prompt, model=effective_model, stream=False
                    )
                finally:
                    if applied:
                        # restaura timeout anterior para não contaminar outros call sites
                        if prev_timeout is not None:
                            try:
                                setattr(self.client, "timeout", float(prev_timeout))
                            except Exception:
                                pass
                candidate = (response or "").strip()
                # Sanitização leve de prefixos comuns (somente em rewrite-only)
                if bool(effective_policy.get("rewrite_only")) and candidate:
                    for prefix in (
                        "**SAÍDA**",
                        "SAÍDA",
                        "**OUTPUT**",
                        "OUTPUT",
                        "RESPOSTA",
                        "**RESPOSTA**",
                    ):
                        if candidate.startswith(prefix):
                            candidate = candidate[len(prefix) :].lstrip(" \n:-—")
                            break

                if candidate:
                    if rewrite_only:
                        rendered_text = effective_facts.get("rendered_text", "").strip()
                        intro = candidate.strip()
                        intro_lines = intro.splitlines()
                        invalid_intro = False

                        if not intro:
                            invalid_intro = True
                        if "|" in intro or re.search(r"\n\s*\|", intro):
                            invalid_intro = True
                        if any(line.count("|") >= 2 for line in intro_lines):
                            invalid_intro = True
                        if re.search(r"TEXTO_BASE", intro, re.IGNORECASE):
                            invalid_intro = True
                        if len(intro_lines) > 5:
                            invalid_intro = True
                        digit_count = sum(1 for ch in intro if ch.isdigit())
                        if digit_count > 6:
                            if not effective_facts.get("llm_canonical_value"):
                                invalid_intro = True
                        if re.search(r"\d+(?:º|°)", intro):
                            invalid_intro = True
                        if re.search(
                            r"\b(?:posi[cç][aã]o|rank(?:ing)?)\s*\d", intro, re.IGNORECASE
                        ):
                            invalid_intro = True

                        canonical_value = effective_facts.get("llm_canonical_value")
                        canonical_str = (
                            str(canonical_value).strip()
                            if canonical_value is not None
                            else ""
                        )
                        has_digits = bool(_DIGIT_RE.search(intro))

                        if canonical_str:
                            if has_digits:
                                if canonical_str in intro:
                                    intro_without_canonical = intro.replace(
                                        canonical_str, "", 1
                                    )
                                    if _DIGIT_RE.search(intro_without_canonical):
                                        invalid_intro = True
                                else:
                                    invalid_intro = True
                        elif has_digits:
                            invalid_intro = True

                        if invalid_intro or not rendered_text:
                            LOGGER.warning(
                                "LLM rewrite-only violou contrato (intro inválido). Fallback para baseline."
                            )
                            text = rendered_text or baseline_text
                            tokens_out = 0
                            llm_intro_used = False
                            llm_intro_tokens = 0
                        else:
                            text = f"{intro}\n\n{rendered_text}" if intro else rendered_text
                            tokens_out = len(text.split())
                            llm_intro_used = True
                            llm_intro_tokens = len(intro.split())
                    else:
                        text = candidate
                        tokens_out = len(candidate.split())

                policy_violation = _policy_violation_reason(
                    baseline_text, text, policy_guards
                )

            except Exception as exc:  # pragma: no cover - caminho excepcional
                error_label = "llm_error"
                if isinstance(exc, TimeoutError) or "timeout" in str(exc).lower():
                    error_label = "llm_timeout"
                error = f"{error_label}: {exc}"
                LOGGER.error(
                    "NARRATOR_LLM_ERROR entity=%s intent=%s model=%s error=%s",
                    entity,
                    intent,
                    effective_model,
                    exc,
                )

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        narrator_meta["latency_ms"] = elapsed_ms
        narrator_meta["llm_intro_used"] = llm_intro_used
        narrator_meta["llm_intro_tokens"] = llm_intro_tokens

        LOGGER.info(
            "NARRATOR_FINAL_TEXT entity=%s intent=%s model=%s "
            "used_llm=%s latency_ms=%.2f error=%s text_preview=%s",
            entity,
            intent,
            effective_model,
            llm_intro_used,
            elapsed_ms,
            error,
            (text[:120] + "..." if isinstance(text, str) and len(text) > 120 else text),
        )

        if policy_violation:
            action = _fail_closed_action(policy_guards, "on_violation")
            narrator_meta["strategy"] = "policy_violation"
            narrator_meta["error"] = f"policy_violation:{policy_violation}"
            chosen_text = baseline_text if action == "return_baseline" else text
            return _finalize_response(
                chosen_text,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=elapsed_ms,
                error=f"policy_violation:{policy_violation}",
                strategy_override="policy_violation",
            )

        if error:
            action_key = "on_timeout" if error.startswith("llm_timeout") else "on_error"
            action = _fail_closed_action(policy_guards, action_key)
            # Fail-safe alinhado ao data/policies/llm_prompts.md:
            # não tentar "salvar" a resposta com baseline potencialmente contaminado.

            return _finalize_response(
                baseline_text if action == "return_baseline" else _FAILSAFE_TEXT,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=elapsed_ms,
                error=error,
                strategy_override="llm_failed",
            )

        if effective_shadow:
            narrator_meta["strategy"] = "llm_shadow"
            return _finalize_response(
                baseline_text,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=elapsed_ms,
                strategy_override="llm_shadow",
            )

        narrator_meta["strategy"] = "llm"
        return _finalize_response(
            text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=elapsed_ms,
            strategy_override="llm",
        )
