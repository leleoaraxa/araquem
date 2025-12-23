#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: quality_push_cron.py
Purpose: Automatizar envio e validação de datasets de qualidade para /ops/quality/push.
Compliance: Guardrails Araquem v2.1.1
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib import error, request

from app.api.ops.quality_contracts import (
    RoutingPayloadValidationError,
    validate_routing_payload_contract,
)

BASE_ALLOWED_TYPES: Set[str] = {"routing", "projection"}
DEFAULT_GLOB = "data/ops/quality/*.json"
DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = int(os.getenv("QUALITY_HTTP_TIMEOUT", "120"))


def load_json(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Load a JSON file returning the payload or an error message."""
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle), None
    except Exception as exc:  # pragma: no cover - exercised via tests/cli
        return None, str(exc)


def _validate_samples_list(
    data: Dict[str, Any],
) -> Tuple[bool, Optional[str], List[Any]]:
    samples = data.get("samples")
    if not isinstance(samples, list) or not samples:
        return False, "samples must be a non-empty list", []
    return True, None, samples


def _validate_tags(value: Any, path: str) -> Tuple[bool, Optional[str]]:
    if value is None:
        return True, None
    if not isinstance(value, list):
        return False, f"{path} must be a list of non-empty strings"
    for index, tag in enumerate(value):
        if not isinstance(tag, str) or not tag.strip():
            return False, f"{path}[{index}] must be a non-empty string"
    return True, None


def validate_routing_payload(
    data: Dict[str, Any],
) -> Tuple[bool, Optional[str], List[Dict[str, Any]]]:
    try:
        payloads, _, _ = validate_routing_payload_contract(data)
    except RoutingPayloadValidationError as exc:
        return False, str(exc), []
    return True, None, payloads


def validate_projection_payload(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    entity = data.get("entity")
    result_key = data.get("result_key")
    must_have_columns = data.get("must_have_columns")

    if not isinstance(entity, str) or not entity.strip():
        return False, "entity must be a non-empty string"
    if not isinstance(result_key, str) or not result_key.strip():
        return False, "result_key must be a non-empty string"
    if not isinstance(must_have_columns, list) or not all(
        isinstance(column, str) and column.strip() for column in must_have_columns
    ):
        return False, "must_have_columns must be a list of non-empty strings"

    ok, error_message, samples = _validate_samples_list(data)
    if not ok:
        return False, error_message

    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            return False, f"samples[{index}] must be an object"
        question = sample.get("question")
        if not isinstance(question, str) or not question.strip():
            return False, f"samples[{index}].question must be a non-empty string"

    return True, None


def validate_rag_payload(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    defaults = data.get("defaults") or {}
    if defaults and not isinstance(defaults, dict):
        return False, "defaults must be an object"

    for key in ("k", "min_score"):
        if key in defaults:
            value = defaults[key]
            if key == "k":
                if not isinstance(value, int) or value < 1:
                    return False, "defaults.k must be an integer >= 1"
            elif key == "min_score":
                if not isinstance(value, (int, float)):
                    return False, "defaults.min_score must be a number between 0 and 1"
                value_f = float(value)
                if value_f < 0 or value_f > 1:
                    return False, "defaults.min_score must be between 0 and 1"

    ok_tags, err_tags = _validate_tags(defaults.get("tags"), "defaults.tags")
    if not ok_tags:
        return False, err_tags

    ok, error_message, samples = _validate_samples_list(data)
    if not ok:
        return False, error_message

    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            return False, f"samples[{index}] must be an object"
        question = sample.get("question")
        if not isinstance(question, str) or not question.strip():
            return False, f"samples[{index}].question must be a non-empty string"
        expect = sample.get("expect")
        if not isinstance(expect, dict):
            return False, f"samples[{index}].expect must be an object"
        doc_id_prefix = expect.get("doc_id_prefix")
        if not isinstance(doc_id_prefix, str) or not doc_id_prefix.strip():
            return (
                False,
                f"samples[{index}].expect.doc_id_prefix must be a non-empty string",
            )

        if "k" in expect:
            value = expect["k"]
            if not isinstance(value, int) or value < 1:
                return False, f"samples[{index}].expect.k must be an integer >= 1"
        if "min_score" in expect:
            value = expect["min_score"]
            if not isinstance(value, (int, float)):
                return (
                    False,
                    f"samples[{index}].expect.min_score must be a number between 0 and 1",
                )
            value_f = float(value)
            if value_f < 0 or value_f > 1:
                return (
                    False,
                    f"samples[{index}].expect.min_score must be between 0 and 1",
                )

        ok_tags, err_tags = _validate_tags(
            expect.get("tags"), f"samples[{index}].expect.tags"
        )
        if not ok_tags:
            return False, err_tags

    return True, None


def make_headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("QUALITY_OPS_TOKEN")
    if token:
        headers["X-Ops-Token"] = token
    bearer = os.environ.get("QUALITY_AUTH_BEARER")
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    return headers


def allowed_types() -> Set[str]:
    allowed = set(BASE_ALLOWED_TYPES)
    if os.getenv("QUALITY_ALLOW_RAG") == "1":
        allowed.add("rag_search")
    return allowed


def should_post(data: Dict[str, Any]) -> Tuple[bool, Optional[str], str, int]:
    if not isinstance(data, dict):
        return False, "invalid schema: payload must be an object", "", 0

    raw_type = data.get("type") or ""
    type_name = raw_type.strip().lower()
    allowed = allowed_types()
    if type_name not in allowed:
        return False, f"unsupported type '{type_name}'", type_name, 0

    if type_name == "routing":
        valid, error_message, payloads = validate_routing_payload(data)
        items_len = len(payloads)
    elif type_name == "projection":
        valid, error_message = validate_projection_payload(data)
        items_len = len(data.get("samples") or [])
    else:
        valid, error_message = validate_rag_payload(data)
        items_len = len(data.get("samples") or [])

    if not valid:
        return (
            False,
            f"invalid schema: {error_message}",
            type_name,
            items_len,
        )

    return True, None, type_name, items_len


def post_payload(data: Dict[str, Any], timeout=DEFAULT_TIMEOUT) -> Tuple[int, str]:
    api_url = os.environ.get("API_URL", DEFAULT_API_URL).rstrip("/")
    url = f"{api_url}/ops/quality/push"
    body = json.dumps(data).encode("utf-8")
    headers = make_headers()
    req = request.Request(url, data=body, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            status = response.getcode()
            payload = response.read().decode("utf-8", "replace")
            return status, payload
    except error.HTTPError as exc:
        payload = exc.read().decode("utf-8", "replace")
        return exc.code, payload


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Push quality samples to API")
    parser.add_argument(
        "--dry-run", action="store_true", help="List files that would be posted"
    )
    parser.add_argument("--glob", help="Override glob pattern for sample discovery")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    glob_pattern = os.environ.get("QUALITY_SAMPLES_GLOB", args.glob or DEFAULT_GLOB)
    base = Path.cwd()
    files = sorted(base.glob(glob_pattern))

    posted = 0
    skipped = 0
    errors_parse = 0
    errors_http = 0
    total = 0

    for path in files:
        total += 1
        data, load_error = load_json(path)
        if load_error is not None:
            errors_parse += 1
            print(f"[error] parse {path} → {load_error}")
            continue

        ok, reason, type_name, items_len = should_post(data)
        if not ok:
            message = reason or "unknown reason"
            if message.startswith("unsupported type"):
                skipped += 1
                print(f"[skip] {path} → {message}")
            else:
                errors_parse += 1
                print(f"[error] {path} → {message}")
            continue

        label = "payloads" if type_name == "routing" else "samples"
        print(f"[post] {path} (type={type_name}, {label}={items_len})")
        if args.dry_run:
            posted += 1
            continue

        try:
            status, response_body = post_payload(data)
        except (
            error.URLError
        ) as exc:  # pragma: no cover - network issues are hard to simulate
            errors_http += 1
            print(f"[error] post {path} → network error: {exc}")
            continue

        if status != 200:
            errors_http += 1
            truncated_body = response_body.strip()
            print(f"[error] post {path} → {status}: {truncated_body}")
            continue

        posted += 1

    summary = (
        f"[summary] posted={posted} skipped={skipped} "
        f"errors_parse={errors_parse} errors_http={errors_http} total={total}"
    )
    print(summary)

    return 0 if errors_parse == 0 and errors_http == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
