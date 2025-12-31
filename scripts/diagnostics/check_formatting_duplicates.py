#!/usr/bin/env python3
"""Check for duplicate entries in data/policies/formatting.yaml."""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import yaml


def load_formatting_yaml(repo_root: Path) -> Tuple[str, Dict]:
    formatting_path = repo_root / "data" / "policies" / "formatting.yaml"
    if not formatting_path.exists():
        raise FileNotFoundError(f"Cannot find formatting.yaml at {formatting_path}")

    content = formatting_path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    if not isinstance(data, dict):
        raise ValueError("formatting.yaml must deserialize into a YAML mapping/dict.")

    return content, data


def extract_sections(data: Dict) -> Tuple[List, Dict, List]:
    placeholders = data.get("placeholders", [])
    filters = data.get("filters", {})
    terms = data.get("terms", [])

    if not isinstance(placeholders, list):
        raise ValueError("`placeholders` should be a list.")
    if not isinstance(filters, dict):
        raise ValueError("`filters` should be a mapping/dict.")
    if not isinstance(terms, list):
        raise ValueError("`terms` should be a list.")

    return placeholders, filters, terms


def analyze_placeholders(placeholders: List) -> Tuple[List[Dict], List[Dict]]:
    occurrences: Dict[str, List[Dict]] = defaultdict(list)
    invalid_fields: List[Dict] = []

    for idx, item in enumerate(placeholders):
        if not isinstance(item, dict):
            invalid_fields.append({"index": idx, "field": item})
            continue

        field = item.get("field")
        placeholder_filter = item.get("filter")
        if not isinstance(field, str) or not field.strip():
            invalid_fields.append({"index": idx, "field": field})
            continue

        normalized = field.strip().lower()
        occurrences[normalized].append(
            {"index": idx, "field": field, "filter": placeholder_filter}
        )

    duplicates = [
        {"field": field, "occurrences": data}
        for field, data in occurrences.items()
        if len(data) > 1
    ]
    return duplicates, invalid_fields


def detect_filter_key_duplicates_from_text(content: str) -> List[Dict]:
    lines = content.splitlines()
    filters_indent = None
    filters_start = None

    for idx, line in enumerate(lines):
        match = re.match(r"^(\s*)filters:\s*(#.*)?$", line)
        if match:
            filters_indent = len(match.group(1))
            filters_start = idx + 1
            break

    if filters_indent is None or filters_start is None:
        return []

    seen: Dict[str, List[int]] = defaultdict(list)

    for i in range(filters_start, len(lines)):
        line = lines[i]
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))

        if stripped == "" or stripped.startswith("#"):
            continue
        if indent <= filters_indent:
            break

        key_match = re.match(r"^\s*([^\s:#][^:]*)\s*:\s*", line)
        if key_match:
            key = key_match.group(1).strip()
            seen[key].append(i + 1)

    duplicates = [
        {"key": key, "lines": sorted(line_numbers)}
        for key, line_numbers in seen.items()
        if len(line_numbers) > 1
    ]
    return duplicates


def analyze_terms(terms: Iterable) -> List[Dict]:
    occurrences: Dict[Tuple[str, str, str], List[int]] = defaultdict(list)

    for idx, item in enumerate(terms):
        if not isinstance(item, dict):
            continue

        name = item.get("name")
        scope = item.get("scope")
        version = item.get("version")

        if name is None or scope is None or version is None:
            continue

        normalized = (
            str(name).strip().lower(),
            str(scope).strip().lower(),
            str(version).strip(),
        )
        occurrences[normalized].append(idx)

    duplicates = [
        {"name": key[0], "scope": key[1], "version": key[2], "indices": idxs}
        for key, idxs in occurrences.items()
        if len(idxs) > 1
    ]
    return duplicates


def build_report(
    status: str,
    placeholder_duplicates: List[Dict],
    filter_duplicates: List[Dict],
    warnings: List[str],
) -> str:
    lines = ["# Formatting Duplicates Report", "", f"Status: {status}", ""]

    lines.append("## Placeholders")
    if placeholder_duplicates:
        for dup in placeholder_duplicates:
            indices = ", ".join(str(item["index"]) for item in dup["occurrences"])
            filters = ", ".join(
                str(item.get("filter")) for item in dup["occurrences"]
            )
            lines.append(
                f'- DUPLICATE field "{dup["field"]}" at indices [{indices}] '
                f"with filters [{filters}]"
            )
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Filters")
    if filter_duplicates:
        for dup in filter_duplicates:
            line_numbers = ", ".join(str(num) for num in dup["lines"])
            lines.append(
                f'- DUPLICATE key "{dup["key"]}" on lines [{line_numbers}]'
            )
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Warnings")
    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("Generated by scripts/diagnostics/check_formatting_duplicates.py")
    return "\n".join(lines)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    try:
        content, data = load_formatting_yaml(repo_root)
        placeholders, filters, terms = extract_sections(data)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}")
        return 1

    placeholder_duplicates, invalid_placeholders = analyze_placeholders(placeholders)
    filter_duplicates = detect_filter_key_duplicates_from_text(content)
    term_duplicates = analyze_terms(terms)

    warnings: List[str] = []
    for invalid in invalid_placeholders:
        warnings.append(
            f'invalid_placeholder_field at index {invalid["index"]}: {invalid["field"]!r}'
        )
    for dup in term_duplicates:
        warnings.append(
            "duplicate_term "
            f'(name="{dup["name"]}", scope="{dup["scope"]}", version="{dup["version"]}") '
            f"at indices {dup['indices']}"
        )

    has_failures = bool(placeholder_duplicates or filter_duplicates)
    status = "FAIL" if has_failures else "PASS"

    report = build_report(status, placeholder_duplicates, filter_duplicates, warnings)
    report_path = repo_root / "docs" / "reports" / "formatting_duplicates_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(report)

    return 2 if has_failures else 0


if __name__ == "__main__":
    sys.exit(main())
