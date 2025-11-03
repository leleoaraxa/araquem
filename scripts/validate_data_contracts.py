#!/usr/bin/env python3
"""Validate consistency of data contracts defined in the repository."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union

import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


def format_path(parts: Iterable[Union[str, int]]) -> str:
    formatted: List[str] = []
    for part in parts:
        if isinstance(part, int):
            formatted.append(f"[{part}]")
        else:
            formatted.append(str(part))
    return "/".join(formatted) if formatted else "<root>"


def load_yaml(path: Path) -> Tuple[Optional[dict], List[str]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except Exception as exc:  # pragma: no cover - defensive logging
        return None, [f"invalid YAML ({exc})"]

    if data is None:
        return None, ["empty document"]
    if not isinstance(data, dict):
        return None, ["invalid root type (expected mapping)"]
    return data, []


def normalize_window(value: Union[str, dict]) -> Optional[str]:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        if len(value) == 1:
            key, raw_val = next(iter(value.items()))
            return f"{key}:{raw_val}"
        if value:
            pairs = ",".join(f"{k}:{v}" for k, v in value.items())
            return pairs
    return None


def validate_param_inference(path: Path) -> Tuple[List[str], Dict[str, Set[str]]]:
    data, errors = load_yaml(path)
    if data is None:
        return errors, {}

    forbidden_keys = {"windows_allowed", "aggregations", "defaults"}

    def traverse(node: Union[dict, list], stack: List[str]) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                under_intents = bool(stack) and stack[0] == "intents"
                if key in forbidden_keys and not under_intents:
                    errors.append(
                        f"contains forbidden key '{key}' outside intents (path: {format_path(stack + [key])})"
                    )
                if (
                    key in {"limit", "order"}
                    and stack
                    and stack[-1] == "list"
                    and not under_intents
                ):
                    errors.append(
                        f"contains forbidden key 'list.{key}' outside intents (path: {format_path(stack + [key])})"
                    )
                traverse(value, stack + [str(key)])
        elif isinstance(node, list):
            for index, item in enumerate(node):
                traverse(item, stack + [str(index)])

    traverse(data, [])

    intent_windows: Dict[str, Set[str]] = {}
    intents = data.get("intents", {})
    if isinstance(intents, dict):
        for intent_name, intent_config in intents.items():
            if not isinstance(intent_config, dict):
                continue
            windows: Set[str] = set()
            default_window = intent_config.get("default_window")
            normalized = normalize_window(default_window) if default_window is not None else None
            if normalized:
                windows.add(normalized)

            agg_keywords = intent_config.get("agg_keywords", {})
            if isinstance(agg_keywords, dict):
                for agg_config in agg_keywords.values():
                    if not isinstance(agg_config, dict):
                        continue
                    window_value = agg_config.get("window")
                    normalized_window = (
                        normalize_window(window_value)
                        if window_value is not None
                        else None
                    )
                    if normalized_window:
                        windows.add(normalized_window)
                    for default in agg_config.get("window_defaults", []) or []:
                        normalized_default = normalize_window(default)
                        if normalized_default:
                            windows.add(normalized_default)
            intent_windows[intent_name] = windows

    return errors, intent_windows


def validate_entity(path: Path, intent_windows: Dict[str, Set[str]]) -> List[str]:
    data, errors = load_yaml(path)
    if data is None:
        return errors

    presentation = data.get("presentation")
    if not isinstance(presentation, dict) or "result_key" not in presentation:
        errors.append("missing presentation.result_key")

    aggregations = data.get("aggregations")
    normalized_windows: Set[str] = set()
    if not isinstance(aggregations, dict):
        errors.append("missing aggregations section")
    else:
        defaults = aggregations.get("defaults")
        if not isinstance(defaults, dict):
            errors.append("missing aggregations.defaults")
        windows_allowed = aggregations.get("windows_allowed")
        if not isinstance(windows_allowed, list):
            errors.append("missing aggregations.windows_allowed")
        else:
            for entry in windows_allowed:
                normalized = normalize_window(entry)
                if not normalized:
                    errors.append(f"invalid window format in aggregations.windows_allowed entry: {entry!r}")
                    continue
                normalized_windows.add(normalized)
            if "count:1" not in normalized_windows:
                errors.append("aggregations.windows_allowed must include count:1")

    ask = data.get("ask", {})
    intents = ask.get("intents") if isinstance(ask, dict) else None
    entity_intents: List[str] = []
    if isinstance(intents, list):
        entity_intents = [intent for intent in intents if isinstance(intent, str)]
    elif intents is not None:
        errors.append("ask.intents must be a list of intent names")

    required_windows: Set[str] = set()
    for intent_name in entity_intents:
        intent_required = intent_windows.get(intent_name)
        if intent_required is None:
            errors.append(f"unknown intent '{intent_name}' (not defined in param_inference.yaml)")
            continue
        required_windows.update(intent_required)

    if required_windows and normalized_windows:
        missing = sorted(required_windows - normalized_windows)
        if missing:
            errors.append(
                "missing windows in aggregations.windows_allowed: " + ", ".join(missing)
            )

    return errors


def validate_embeddings_index(path: Path) -> List[str]:
    data, errors = load_yaml(path)
    if data is None:
        return errors

    include = data.get("include")
    if not isinstance(include, list):
        return ["missing include list"]

    problems: List[str] = []
    for entry in include:
        if not isinstance(entry, dict):
            problems.append(f"invalid include entry (expected mapping): {entry!r}")
            continue
        file_path = entry.get("path")
        if not isinstance(file_path, str):
            problems.append("include entry missing string path")
            continue
        absolute = ROOT_DIR / file_path
        if not absolute.exists():
            problems.append(f"missing referenced file: {file_path}")
    return problems


def main() -> int:
    failed = False

    param_path = DATA_DIR / "ops" / "param_inference.yaml"
    param_errors, intent_windows = validate_param_inference(param_path)
    if param_errors:
        failed = True
        for error in param_errors:
            print(f"[fail] {param_path.relative_to(ROOT_DIR)} → {error}")
    else:
        print(f"[ok] {param_path.relative_to(ROOT_DIR)}")

    entities_dir = DATA_DIR / "entities"
    entity_paths = sorted(entities_dir.glob("*.yaml"))
    for entity_path in entity_paths:
        errors = validate_entity(entity_path, intent_windows)
        if errors:
            failed = True
            for error in errors:
                print(f"[fail] {entity_path.relative_to(ROOT_DIR)} → {error}")
        else:
            print(f"[ok] {entity_path.relative_to(ROOT_DIR)}")

    embeddings_path = DATA_DIR / "embeddings" / "index.yaml"
    embedding_errors = validate_embeddings_index(embeddings_path)
    if embedding_errors:
        failed = True
        for error in embedding_errors:
            print(f"[fail] {embeddings_path.relative_to(ROOT_DIR)} → {error}")
    else:
        print(f"[ok] {embeddings_path.relative_to(ROOT_DIR)}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
