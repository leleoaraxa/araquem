#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lint canônico do institutional_intent_map.

Valida:
- intent_id obrigatório e único
- concept_ref existente em concepts-institutional.yaml
- fallback.concept_ref existente
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
INTENT_MAP_PATH = REPO_ROOT / "data" / "contracts" / "responses" / "institutional_intent_map.yaml"
CONCEPTS_PATH = REPO_ROOT / "data" / "concepts" / "concepts-institutional.yaml"


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        return {}
    return data


def collect_concept_ids(data: Dict[str, Any], errors: List[str]) -> List[str]:
    concepts = data.get("concepts")
    if not isinstance(concepts, list):
        errors.append("concepts: expected a list in concepts-institutional.yaml")
        return []
    ids: List[str] = []
    for idx, item in enumerate(concepts):
        if not isinstance(item, dict):
            errors.append(f"concepts[{idx}]: expected an object")
            continue
        concept_id = item.get("id")
        if isinstance(concept_id, str) and concept_id.strip():
            ids.append(concept_id)
        else:
            errors.append(f"concepts[{idx}].id: expected a non-empty string")
    return ids


def validate_intent_map(data: Dict[str, Any], concept_ids: List[str], errors: List[str]) -> None:
    intent_map = data.get("intent_map")
    if not isinstance(intent_map, list):
        errors.append("intent_map: expected a list")
        return

    seen: Dict[str, int] = {}
    for idx, item in enumerate(intent_map):
        path_prefix = f"intent_map[{idx}]"
        if not isinstance(item, dict):
            errors.append(f"{path_prefix}: expected an object")
            continue
        intent_id = item.get("intent_id")
        if not isinstance(intent_id, str) or not intent_id.strip():
            errors.append(f"{path_prefix}.intent_id: required non-empty string")
        else:
            if intent_id in seen:
                first_idx = seen[intent_id]
                errors.append(
                    f"{path_prefix}.intent_id: duplicate '{intent_id}' (already in intent_map[{first_idx}].intent_id)"
                )
            else:
                seen[intent_id] = idx

        concept_ref = item.get("concept_ref")
        if not isinstance(concept_ref, str) or not concept_ref.strip():
            errors.append(f"{path_prefix}.concept_ref: required non-empty string")
        elif concept_ref not in concept_ids:
            errors.append(f"{path_prefix}.concept_ref: '{concept_ref}' not found in concepts-institutional.yaml")


def validate_fallback(data: Dict[str, Any], concept_ids: List[str], errors: List[str]) -> None:
    fallback = data.get("fallback")
    if not isinstance(fallback, dict):
        errors.append("fallback: expected an object")
        return
    concept_ref = fallback.get("concept_ref")
    if not isinstance(concept_ref, str) or not concept_ref.strip():
        errors.append("fallback.concept_ref: required non-empty string")
    elif concept_ref not in concept_ids:
        errors.append(f"fallback.concept_ref: '{concept_ref}' not found in concepts-institutional.yaml")


def main() -> int:
    errors: List[str] = []
    intent_map_data = load_yaml(INTENT_MAP_PATH)
    concepts_data = load_yaml(CONCEPTS_PATH)

    concept_ids = collect_concept_ids(concepts_data, errors)
    validate_intent_map(intent_map_data, concept_ids, errors)
    validate_fallback(intent_map_data, concept_ids, errors)

    if errors:
        print("FAIL")
        print("Erros:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
