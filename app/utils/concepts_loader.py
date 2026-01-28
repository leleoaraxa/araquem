from __future__ import annotations

from typing import Any, Dict

from app.utils.filecache import load_yaml_cached


def load_concept_item(
    source: str,
    section_id: str,
    item_name: str,
) -> Dict[str, Any]:
    """Carrega item conceitual de forma determinística via seção + nome."""
    if not source or not section_id or not item_name:
        return {
            "source": source or None,
            "domain": None,
            "version": None,
            "section": None,
            "item": None,
        }

    data = load_yaml_cached(source)
    domain = data.get("domain") if isinstance(data, dict) else None
    version = data.get("version") if isinstance(data, dict) else None
    sections = data.get("sections") if isinstance(data, dict) else None

    if not isinstance(sections, list):
        return {
            "source": source,
            "domain": domain,
            "version": version,
            "section": None,
            "item": None,
        }

    for section in sections:
        if not isinstance(section, dict):
            continue
        if str(section.get("id") or "").strip() != section_id:
            continue
        items = section.get("items") or []
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            if str(item.get("name") or "").strip() == item_name:
                return {
                    "source": source,
                    "domain": domain,
                    "version": version,
                    "section": {
                        "id": section.get("id"),
                        "title": section.get("title"),
                    },
                    "item": item,
                }

    return {
        "source": source,
        "domain": domain,
        "version": version,
        "section": None,
        "item": None,
    }
