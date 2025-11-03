"""Utilities for hot reloading support."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path


def get_manifest_hash(path: str = "data/embeddings/store/manifest.json") -> str:
    """Return a stable string representing the current manifest state.

    The priority order is:
    1. Use the value of the ``tree`` field if present.
    2. Fallback to the ``sha_all`` field when available.
    3. Otherwise compute a SHA256 hash of the JSON payload (sorted keys).

    Any error (missing file, invalid JSON, etc.) results in the string ``"missing"``.
    """

    manifest_path = Path(path)
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return "missing"

    if isinstance(data, dict):
        for key in ("tree", "sha_all"):
            value = data.get(key)
            if isinstance(value, str) and value:
                return value

    try:
        serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    except (TypeError, ValueError):
        return "missing"

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
