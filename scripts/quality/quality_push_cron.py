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
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib import error, request

# Garantia local de PYTHONPATH para acesso a app/
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.api.ops.quality_contracts import (
    RoutingBatchMetadata,
    RoutingPayloadValidationError,
    validate_routing_payload_contract,
)

BASE_ALLOWED_TYPES: Set[str] = {"routing", "projection"}
DEFAULT_GLOB = "data/ops/quality/*.json"
DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = max(1, int(os.getenv("QUALITY_PUSH_TIMEOUT_S", os.getenv("QUALITY_HTTP_TIMEOUT", "30"))))
ROUTING_TIMEOUT = max(1, int(os.getenv("QUALITY_PUSH_TIMEOUT_ROUTING_S", "60")))
ROUTING_BATCH_SIZE = max(1, int(os.getenv("QUALITY_ROUTING_BATCH_SIZE", "100")))
PUSH_RETRIES = max(1, int(os.getenv("QUALITY_PUSH_RETRIES", "3")))
PUSH_RETRY_BACKOFF = max(0.0, float(os.getenv("QUALITY_PUSH_RETRY_BACKOFF_S", "2")))


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
        payloads, _, _, _ = validate_routing_payload_contract(data)
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


def _serialize_batch(batch: RoutingBatchMetadata) -> Dict[str, Any]:
    return {"id": batch.id, "index": batch.index, "total": batch.total}


def build_routing_batches(data: Dict[str, Any], batch_size: int) -> List[Dict[str, Any]]:
    payloads, suite_name, description, incoming_batch = validate_routing_payload_contract(data)

    base: Dict[str, Any] = {
        "type": "routing",
        "payloads": payloads,
        "description": description,
    }
    if suite_name is not None:
        base["suite"] = suite_name
    if description:
        base["description"] = description

    if incoming_batch is not None:
        base["batch"] = _serialize_batch(incoming_batch)
        return [base]

    effective_batch_size = max(1, int(batch_size))
    total_batches = max(1, (len(payloads) + effective_batch_size - 1) // effective_batch_size)
    batch_id = str(uuid.uuid4())

    batches: List[Dict[str, Any]] = []
    for index in range(total_batches):
        start = index * effective_batch_size
        end = start + effective_batch_size
        chunk = payloads[start:end]
        batch_payload = dict(base)
        batch_payload["payloads"] = chunk
        batch_payload["batch"] = {"id": batch_id, "index": index + 1, "total": total_batches}
        batches.append(batch_payload)
    return batches


def make_headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("QUALITY_OPS_TOKEN")
    if token:
        headers["X-OPS-TOKEN"] = token
    bearer = os.environ.get("QUALITY_AUTH_BEARER")
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    return headers


def allowed_types() -> Set[str]:
    allowed = set(BASE_ALLOWED_TYPES)
    if os.getenv("QUALITY_ALLOW_RAG") == "1":
        allowed.add("rag_search")
    return allowed


def effective_api_url() -> str:
    raw = os.environ.get("API_URL") or DEFAULT_API_URL
    return raw.rstrip("/")


def build_push_url(api_url: str) -> str:
    return f"{api_url}/ops/quality/push"


def is_timeout_error(exc: BaseException) -> bool:
    if isinstance(exc, TimeoutError):
        return True
    if isinstance(exc, error.URLError):
        reason = getattr(exc, "reason", None)
        if isinstance(reason, TimeoutError):
            return True
        if isinstance(reason, Exception) and "timed out" in str(reason).lower():
            return True
    return False


def log_post_details(
    source_path: Path,
    type_name: str,
    items_len: int,
    timeout_s: int,
    push_url: str,
    batch_label: Optional[str] = None,
    attempt: Optional[int] = None,
    total_attempts: Optional[int] = None,
) -> None:
    batch_info = f", batch={batch_label}" if batch_label else ""
    attempt_info = (
        f", attempt={attempt}/{total_attempts}" if attempt and total_attempts else ""
    )
    print(
        f"[post] {source_path} → url={push_url} type={type_name} "
        f"items_len={items_len} timeout_s={timeout_s}{batch_info}{attempt_info}"
    )


def should_post(
    data: Dict[str, Any], source_path: Optional[Path] = None
) -> Tuple[bool, Optional[str], str, int, bool]:
    prefix = f"{source_path}: " if source_path else ""
    if not isinstance(data, dict):
        return False, f"{prefix}invalid schema: payload must be an object", "", 0, False

    raw_type = data.get("type")
    if not isinstance(raw_type, str) or not raw_type.strip():
        return (
            False,
            f"{prefix}invalid schema: 'type' must be a non-empty string",
            "",
            0,
            False,
        )

    type_name = raw_type.strip().lower()
    allowed = allowed_types()
    if type_name not in allowed:
        return False, f"unsupported type '{type_name}'", type_name, 0, True

    items_len = 0
    skip = False
    if type_name == "routing":
        if "samples" in data:
            items_len = len(data.get("samples") or [])
            return (
                False,
                f"{prefix}invalid schema: routing uses 'payloads' (Suite v2); found legacy 'samples'",
                type_name,
                items_len,
                skip,
            )
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
            f"{prefix}invalid schema: {error_message}",
            type_name,
            items_len,
            skip,
        )

    return True, None, type_name, items_len, skip


def post_payload(push_url: str, data: Dict[str, Any], timeout: int) -> Tuple[int, str]:
    body = json.dumps(data).encode("utf-8")
    headers = make_headers()
    req = request.Request(push_url, data=body, headers=headers, method="POST")
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


def send_payload_with_retry(
    payload: Dict[str, Any],
    *,
    path: Path,
    type_name: str,
    items_len: int,
    timeout_s: int,
    batch_label: Optional[str],
    push_url: str,
) -> Tuple[bool, Optional[int]]:
    attempts = max(1, PUSH_RETRIES)
    for attempt in range(1, attempts + 1):
        log_post_details(
            path,
            type_name,
            items_len,
            timeout_s,
            push_url,
            batch_label=batch_label,
            attempt=attempt,
            total_attempts=attempts,
        )
        try:
            status, response_body = post_payload(push_url, payload, timeout=timeout_s)
        except (error.URLError, TimeoutError) as exc:  # pragma: no cover - hard to simulate live timeouts
            if is_timeout_error(exc) and attempt < attempts:
                delay = PUSH_RETRY_BACKOFF * (2 ** (attempt - 1))
                print(
                    f"[warn] post {path}{f' batch {batch_label}' if batch_label else ''} "
                    f"timed out; retrying in {delay:.1f}s"
                )
                time.sleep(delay)
                continue
            print(
                f"[error] post {path}{f' batch {batch_label}' if batch_label else ''} "
                f"→ network error: {exc}"
            )
            return False, None

        if status != 200:
            truncated_body = (response_body or "").strip()
            print(
                f"[error] post {path}{f' batch {batch_label}' if batch_label else ''} "
                f"→ {status}: {truncated_body}"
            )
            return False, status

        return True, status

    return False, None


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    glob_pattern = os.environ.get("QUALITY_SAMPLES_GLOB", args.glob or DEFAULT_GLOB)
    base = Path.cwd()
    files = sorted(base.glob(glob_pattern))

    skipped = 0
    errors_parse = 0
    errors_http = 0
    files_total = 0
    files_ok = 0
    http_posts_ok = 0
    push_base_url = effective_api_url()
    push_url = build_push_url(push_base_url)

    for path in files:
        data, load_error = load_json(path)
        if load_error is not None:
            files_total += 1
            errors_parse += 1
            print(f"[error] parse {path} → {load_error}")
            continue

        ok, reason, type_name, items_len, skip = should_post(data, source_path=path)
        if not ok:
            message = reason or "unknown reason"
            if skip:
                skipped += 1
                print(f"[skip] {path} → {message}")
            else:
                files_total += 1
                errors_parse += 1
                print(f"[error] {path} → {message}")
            continue

        files_total += 1
        if type_name == "routing":
            try:
                batches = build_routing_batches(data, ROUTING_BATCH_SIZE)
            except RoutingPayloadValidationError as exc:
                errors_parse += 1
                print(f"[error] {path} → invalid routing payload: {exc}")
                continue
            routing_failed = False
            for batch_payload in batches:
                batch_info = batch_payload.get("batch") or {}
                batch_label = f"{batch_info.get('index', '?')}/{batch_info.get('total', '?')}"
                batch_count = len(batch_payload.get("payloads") or [])
                if args.dry_run:
                    log_post_details(
                        path, type_name, batch_count, ROUTING_TIMEOUT, push_url, batch_label=batch_label
                    )
                    http_posts_ok += 1
                    continue

                success, _ = send_payload_with_retry(
                    batch_payload,
                    path=path,
                    type_name=type_name,
                    items_len=batch_count,
                    timeout_s=ROUTING_TIMEOUT,
                    batch_label=batch_label,
                    push_url=push_url,
                )
                if success:
                    http_posts_ok += 1
                    continue

                errors_http += 1
                routing_failed = True
                break

            if routing_failed:
                continue

            files_ok += 1
            continue
        else:
            if args.dry_run:
                log_post_details(
                    path, type_name, items_len, DEFAULT_TIMEOUT, push_url, batch_label=None
                )
                http_posts_ok += 1
                files_ok += 1
                continue

            success, _ = send_payload_with_retry(
                data,
                path=path,
                type_name=type_name,
                items_len=items_len,
                timeout_s=DEFAULT_TIMEOUT,
                batch_label=None,
                push_url=push_url,
            )
            if success:
                http_posts_ok += 1
                files_ok += 1
            else:
                errors_http += 1

            continue

    summary = (
        f"[summary] files_total={files_total} files_ok={files_ok} skipped={skipped} "
        f"errors_parse={errors_parse} errors_http={errors_http} http_posts_ok={http_posts_ok}"
    )
    print(summary)

    return 0 if files_ok == files_total else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
