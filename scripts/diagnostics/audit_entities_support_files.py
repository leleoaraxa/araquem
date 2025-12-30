#!/usr/bin/env python3
"""Audit support files for data entities.

Validates presence of YAML, responses, template, and hints files for each entity
under ``data/entities``. Exits with status 1 if any requirement fails.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List


def discover_entities(root: Path) -> List[Path]:
    if not root.exists():
        raise FileNotFoundError(f"Entities root not found: {root}")
    return sorted([path for path in root.iterdir() if path.is_dir()])


def audit_entity(entity_dir: Path) -> List[str]:
    entity_id = entity_dir.name
    errors: List[str] = []

    yaml_path = entity_dir / f"{entity_id}.yaml"
    if not yaml_path.exists():
        errors.append(f"missing YAML: {yaml_path.relative_to(entity_dir)}")

    responses_dir = entity_dir / "responses"
    response_templates = list(responses_dir.glob("*.md.j2")) if responses_dir.exists() else []
    if not response_templates:
        errors.append("missing responses/*.md.j2")

    template_path = entity_dir / "template.md"
    if not template_path.exists():
        errors.append("missing template.md (singular)")

    plural_templates = list(entity_dir.glob("templates.md"))
    if plural_templates:
        errors.append("found deprecated templates.md (template.md is canonical; remove legacy file)")

    hints_path = entity_dir / "hints.md"
    if not hints_path.exists():
        errors.append("missing hints.md")

    return errors


def print_report(results: Dict[str, List[str]]) -> None:
    total = len(results)
    failures = {entity: errs for entity, errs in results.items() if errs}
    successes = total - len(failures)

    print("Auditoria de entidades em data/entities\n")
    for entity, errors in results.items():
        if errors:
            joined = "; ".join(errors)
            print(f"[FAIL] {entity}: {joined}")
        else:
            print(f"[OK]   {entity}")

    print("\nResumo:")
    print(f"- Entidades avaliadas: {total}")
    print(f"- Sem falhas: {successes}")
    print(f"- Com falhas: {len(failures)}")

    if failures:
        print("\nFalhas detalhadas:")
        for entity, errors in failures.items():
            for err in errors:
                print(f"  - {entity}: {err}")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    entities_root = repo_root / "data" / "entities"

    try:
        entity_dirs = discover_entities(entities_root)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    results: Dict[str, List[str]] = {}
    for entity_dir in entity_dirs:
        results[entity_dir.name] = audit_entity(entity_dir)

    print_report(results)

    has_failures = any(results.values())
    return 1 if has_failures else 0


if __name__ == "__main__":
    sys.exit(main())
