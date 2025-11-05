from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import string
from typing import Any, Dict, Iterable, List, Set

_TEMPLATE_DIR = Path("data/concepts")


_FORMATTER = string.Formatter()


@lru_cache(maxsize=32)
def _load_templates(entity: str) -> Dict[str, str]:
    path = _TEMPLATE_DIR / f"{entity}_templates.md"
    if not path.exists():
        return {}
    content = path.read_text(encoding="utf-8")
    templates: Dict[str, str] = {}
    current_key: str | None = None
    buffer: List[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            if current_key:
                templates[current_key] = "\n".join(buffer).strip()
            current_key = stripped[4:].strip()
            buffer = []
            continue
        if stripped == "---":
            continue
        buffer.append(line.rstrip())
    if current_key:
        templates[current_key] = "\n".join(buffer).strip()
    return templates


def _render_from_template(template: str, context: Dict[str, Any]) -> str:
    try:
        return template.format(**context)
    except KeyError:
        return template


def _extract_placeholders(template: str) -> Set[str]:
    fields: Set[str] = set()
    if not template:
        return fields
    for _, field_name, _, _ in _FORMATTER.parse(template):
        if field_name:
            fields.add(field_name)
    return fields


def _has_missing_fields(fields: Set[str], context: Dict[str, Any]) -> bool:
    if not fields:
        return False
    for field in fields:
        value = context.get(field)
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
    return False


def render_answer(
    entity: str,
    rows: Iterable[Dict[str, Any]] | None,
    *,
    identifiers: Dict[str, Any] | None = None,
    aggregates: Dict[str, Any] | None = None,
) -> str:
    templates = _load_templates(entity)
    if not templates:
        return ""

    rows_list = list(rows or [])
    primary = rows_list[0] if rows_list else {}
    metric = (primary or {}).get("metric") or (aggregates or {}).get("metric")

    if metric and primary:
        template = templates.get(str(metric))
        if template:
            rendered = _render_from_template(template, primary)
            if rendered:
                return rendered

    row_template = templates.get("list_basic")
    fallback_template = templates.get("FALLBACK_row")
    row_placeholders = _extract_placeholders(row_template or "")
    fallback_placeholders = _extract_placeholders(fallback_template or "")

    if row_template or fallback_template:
        rendered_rows: List[str] = []
        for row in rows_list:
            row_context: Dict[str, Any] = {}
            for source in (identifiers or {}, row):
                if isinstance(source, dict):
                    row_context.update({k: v for k, v in source.items() if v is not None})
            template_to_use = row_template
            if _has_missing_fields(row_placeholders, row_context):
                template_to_use = fallback_template
            if template_to_use:
                if template_to_use is fallback_template and _has_missing_fields(
                    fallback_placeholders, row_context
                ):
                    continue
                rendered = _render_from_template(template_to_use, row_context)
                if rendered:
                    rendered_rows.append(rendered)
        if rendered_rows:
            return "\n".join(rendered_rows)
        if fallback_template:
            fallback_context: Dict[str, Any] = {}
            for source in (identifiers or {},):
                if isinstance(source, dict):
                    fallback_context.update({k: v for k, v in source.items() if v is not None})
            if not _has_missing_fields(fallback_placeholders, fallback_context):
                rendered = _render_from_template(fallback_template, fallback_context)
                if rendered:
                    return rendered

    context: Dict[str, Any] = {}
    for source in (identifiers or {}), primary:
        if isinstance(source, dict):
            context.update({k: v for k, v in source.items() if v is not None})

    if metric:
        fallback_key = f"{metric}__FALLBACK"
        template = templates.get(fallback_key)
        if template:
            rendered = _render_from_template(template, context)
            if rendered:
                return rendered

    for key, template in templates.items():
        if key.endswith("__FALLBACK"):
            rendered = _render_from_template(template, context)
            if rendered:
                return rendered

    return ""


__all__ = ["render_answer"]
