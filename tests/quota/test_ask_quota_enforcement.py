from datetime import datetime, timezone

import redis

from app.quota.ask_quota import build_quota_key, enforce_ask_quota


class FakePipeline:
    def __init__(self, redis_client):
        self._redis = redis_client
        self._commands = []
        self._watched = []

    def watch(self, key):
        self._watched.append(key)

    def hgetall(self, key):
        return dict(self._redis.store.get(key, {}))

    def multi(self):
        return None

    def hset(self, key, mapping):
        self._commands.append(("hset", key, mapping))

    def hincrby(self, key, field, amount):
        self._commands.append(("hincrby", key, field, amount))

    def execute(self):
        if self._redis.fail_next_exec:
            self._redis.fail_next_exec = False
            raise redis.WatchError()
        for command in self._commands:
            if command[0] == "hset":
                _, key, mapping = command
                bucket = self._redis.store.setdefault(key, {})
                for field, value in mapping.items():
                    bucket[field] = value
            elif command[0] == "hincrby":
                _, key, field, amount = command
                bucket = self._redis.store.setdefault(key, {})
                current = int(bucket.get(field, 0))
                bucket[field] = current + int(amount)
        self._commands = []
        return []

    def reset(self):
        self._commands = []
        self._watched = []


class FakeRedis:
    def __init__(self):
        self.store = {}
        self.pipeline_called = 0
        self.fail_next_exec = False

    def pipeline(self):
        self.pipeline_called += 1
        return FakePipeline(self)


def _policy(limit):
    return {
        "enabled": True,
        "defaults": {"anon": limit, "free": limit, "paid": limit},
        "blocked_message": "blocked",
    }


def test_enforce_quota_initializes_and_decrements():
    now = datetime(2024, 1, 15, tzinfo=timezone.utc)
    redis_client = FakeRedis()

    decision = enforce_ask_quota(
        redis_client,
        "anon",
        "client",
        now=now,
        policy=_policy(3),
    )

    assert decision.allowed is True
    assert decision.remaining == 2

    key = build_quota_key("anon", "client", now=now)
    bucket = redis_client.store[key]
    assert int(bucket["requests_total"]) == 3
    assert int(bucket["quota_remaining"]) == 2
    assert int(bucket["blocked_total"]) == 0


def test_enforce_quota_decrements_multiple_times():
    now = datetime(2024, 2, 1, tzinfo=timezone.utc)
    redis_client = FakeRedis()
    policy = _policy(2)

    first = enforce_ask_quota(
        redis_client,
        "free",
        "client",
        now=now,
        policy=policy,
    )
    second = enforce_ask_quota(
        redis_client,
        "free",
        "client",
        now=now,
        policy=policy,
    )

    assert first.allowed is True
    assert first.remaining == 1
    assert second.allowed is True
    assert second.remaining == 0

    key = build_quota_key("free", "client", now=now)
    bucket = redis_client.store[key]
    assert int(bucket["quota_remaining"]) == 0


def test_enforce_quota_blocks_when_empty():
    now = datetime(2024, 3, 1, tzinfo=timezone.utc)
    redis_client = FakeRedis()
    policy = _policy(1)

    enforce_ask_quota(redis_client, "paid", "client", now=now, policy=policy)
    blocked = enforce_ask_quota(redis_client, "paid", "client", now=now, policy=policy)

    assert blocked.allowed is False
    assert blocked.remaining == 0

    key = build_quota_key("paid", "client", now=now)
    bucket = redis_client.store[key]
    assert int(bucket["blocked_total"]) == 1
    assert int(bucket["quota_remaining"]) == 0


def test_enforce_quota_retries_on_watch_error():
    now = datetime(2024, 4, 1, tzinfo=timezone.utc)
    redis_client = FakeRedis()
    redis_client.fail_next_exec = True
    policy = _policy(2)

    decision = enforce_ask_quota(
        redis_client,
        "anon",
        "client",
        now=now,
        policy=policy,
    )

    assert decision.allowed is True
    assert decision.remaining == 1
    assert redis_client.pipeline_called >= 2


def test_quota_bypass_when_disabled():
    now = datetime(2024, 5, 1, tzinfo=timezone.utc)
    redis_client = FakeRedis()

    decision = enforce_ask_quota(
        redis_client,
        "free",
        "client",
        now=now,
        policy={"enabled": False},
    )

    assert decision.bypassed is True
    assert redis_client.pipeline_called == 0
