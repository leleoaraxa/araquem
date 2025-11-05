from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List

_TEMPLATE_DIR = Path("data/concepts")


_LIST_TEMPLATE_CONFIG = {
    "fiis_imoveis": {
        "row_template": "list_basic",
        "fallback_template": "FALLBACK_row",
        "required_fields": [
            "ticker",
            "asset_name",
            "asset_class",
            "asset_address",
            "total_area",
            "units_count",
            "vacancy_ratio",
            "assets_status",
        ],
    },
    "fiis_processos": {
        "row_template": "list_basic",
        "fallback_template": "FALLBACK_row",
        "required_fields": [
            "ticker",
            "process_number",
            "judgment",
            "instance",
            "initiation_date",
            "cause_amt",
            "loss_risk_pct",
            "main_facts",
        ],
    },
    "fiis_noticias": {
        "row_template": "list_basic",
        "fallback_template": "FALLBACK_row",
        "required_fields": [
            "title",
            "source",
            "url",
            "published_at",
        ],
    },
}


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

    list_cfg = _LIST_TEMPLATE_CONFIG.get(entity)
    if list_cfg:
        row_template_key = list_cfg.get("row_template")
        fallback_template_key = list_cfg.get("fallback_template")
        row_template = templates.get(row_template_key) if row_template_key else None
        fallback_template = templates.get(fallback_template_key) if fallback_template_key else None
        rendered_rows: List[str] = []
        required = set(list_cfg.get("required_fields") or [])
        for row in rows_list:
            row_context: Dict[str, Any] = {}
            for source in (identifiers or {}, row):
                if isinstance(source, dict):
                    row_context.update({k: v for k, v in source.items() if v is not None})
            missing_required = False
            if required:
                for field in required:
                    value = row_context.get(field)
                    if value is None or value == "":
                        missing_required = True
                        break
            template_to_use = fallback_template if missing_required else row_template
            if template_to_use:
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
