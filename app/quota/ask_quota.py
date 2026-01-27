from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import redis

from app.utils.filecache import load_yaml_cached

LOGGER = logging.getLogger(__name__)

POLICY_PATH = Path("data/policies/ask_quota.yaml")

ALLOWED_USER_TYPES = ("anon", "free", "paid")

DEFAULT_POLICY: Dict[str, Any] = {
    "enabled": False,
    "defaults": {
        "anon": 3,
        "free": 30,
        "paid": 1000,
    },
    "blocked_message": (
        "Você está usando uma demonstração da Íris. Crie uma conta gratuita para continuar."
    ),
}


@dataclass(frozen=True)
class QuotaDecision:
    allowed: bool
    remaining: Optional[int]
    bypassed: bool = False


def normalize_user_type(value: Optional[str]) -> str:
    if value in ALLOWED_USER_TYPES:
        return value
    return "anon"


def load_ask_quota_policy(path: Path = POLICY_PATH) -> Dict[str, Any]:
    if not path.exists():
        LOGGER.warning("Política de quota ausente em %s; bypass ativado", path)
        return dict(DEFAULT_POLICY)

    raw = load_yaml_cached(str(path)) or {}
    if not isinstance(raw, dict):
        LOGGER.warning("ask_quota.yaml inválido; bypass ativado")
        return dict(DEFAULT_POLICY)

    policy = raw.get("ask_quota") or {}
    if policy and not isinstance(policy, dict):
        LOGGER.warning("ask_quota deve ser um mapeamento; bypass ativado")
        return dict(DEFAULT_POLICY)

    merged = {**DEFAULT_POLICY, **policy}
    defaults = merged.get("defaults")
    if not isinstance(defaults, dict):
        merged["defaults"] = dict(DEFAULT_POLICY["defaults"])
    else:
        fallback_defaults = DEFAULT_POLICY["defaults"]
        merged["defaults"] = {**fallback_defaults, **defaults}

    return merged


def build_quota_key(user_type: str, client_key: str, now: Optional[datetime] = None) -> str:
    if now is None:
        now = datetime.now(timezone.utc)
    year = f"{now.year:04d}"
    month = f"{now.month:02d}"
    return f"ask_quota:{user_type}:{client_key}:{year}:{month}"


def build_client_key(user_type: str, client_id: str, conversation_id: str) -> str:
    if user_type == "anon":
        return f"anon:{conversation_id}"
    return client_id


def get_blocked_message(policy: Optional[Dict[str, Any]], user_type: str) -> str:
    if isinstance(policy, dict):
        blocked_messages = policy.get("blocked_messages")
        if isinstance(blocked_messages, dict):
            message = blocked_messages.get(user_type)
            if isinstance(message, str) and message.strip():
                return message.strip()
        message = policy.get("blocked_message")
        if isinstance(message, str) and message.strip():
            return message.strip()
    return DEFAULT_POLICY["blocked_message"]


def _parse_int(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _get_limit(policy: Dict[str, Any], user_type: str) -> int:
    defaults = policy.get("defaults") if isinstance(policy, dict) else None
    if not isinstance(defaults, dict):
        defaults = DEFAULT_POLICY["defaults"]
    return _parse_int(defaults.get(user_type), DEFAULT_POLICY["defaults"][user_type])


def _update_quota(
    redis_client: redis.Redis,
    key: str,
    limit: int,
    max_retries: int = 5,
) -> QuotaDecision:
    attempts = max(1, max_retries)
    for _ in range(attempts):
        pipe = redis_client.pipeline()
        try:
            pipe.watch(key)
            data = pipe.hgetall(key) or {}
            if data:
                requests_total = _parse_int(data.get("requests_total"), limit)
                quota_remaining = _parse_int(data.get("quota_remaining"), limit)
                blocked_total = _parse_int(data.get("blocked_total"), 0)
            else:
                requests_total = limit
                quota_remaining = limit
                blocked_total = 0

            if quota_remaining <= 0:
                pipe.multi()
                if not data:
                    pipe.hset(
                        key,
                        mapping={
                            "requests_total": requests_total,
                            "quota_remaining": max(0, quota_remaining),
                            "blocked_total": blocked_total,
                        },
                    )
                pipe.hincrby(key, "blocked_total", 1)
                pipe.execute()
                return QuotaDecision(allowed=False, remaining=0)

            pipe.multi()
            if not data:
                pipe.hset(
                    key,
                    mapping={
                        "requests_total": requests_total,
                        "quota_remaining": quota_remaining,
                        "blocked_total": blocked_total,
                    },
                )
            pipe.hincrby(key, "quota_remaining", -1)
            pipe.execute()
            return QuotaDecision(allowed=True, remaining=max(0, quota_remaining - 1))
        except redis.WatchError:
            continue
        finally:
            try:
                pipe.reset()
            except Exception:
                pass

    LOGGER.warning("Falha ao aplicar quota após %s tentativas", attempts)
    return QuotaDecision(allowed=True, remaining=None)


def enforce_ask_quota(
    redis_client: redis.Redis,
    user_type: str,
    client_key: str,
    now: Optional[datetime] = None,
    policy: Optional[Dict[str, Any]] = None,
    max_retries: int = 5,
) -> QuotaDecision:
    policy_data = policy or load_ask_quota_policy()
    if not policy_data.get("enabled", False):
        return QuotaDecision(allowed=True, remaining=None, bypassed=True)

    normalized_type = normalize_user_type(user_type)
    limit = _get_limit(policy_data, normalized_type)
    key = build_quota_key(normalized_type, client_key, now=now)
    try:
        return _update_quota(redis_client, key, limit, max_retries=max_retries)
    except Exception:
        LOGGER.warning("Falha ao aplicar quota no Redis", exc_info=True)
        return QuotaDecision(allowed=True, remaining=None)
