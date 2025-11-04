from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List

_TEMPLATE_DIR = Path("data/concepts")


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
