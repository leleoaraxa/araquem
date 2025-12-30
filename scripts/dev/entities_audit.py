"""Audit script for entity surface and usage reports.

This script inspects entities under ``data/entities`` and writes two
JSON reports describing structural presence and textual references
across the repository. The script performs only read operations on the
project files and creates the requested output files.
"""

from __future__ import annotations

import argparse
from datetime import datetime, UTC
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

try:
    import yaml
except Exception as exc:  # pragma: no cover
    # YAML é dependência obrigatória para este script.
    print(
        f"[entities_audit] ERRO: não foi possível importar 'yaml' (PyYAML). Detalhes: {exc}",
        file=sys.stderr,
    )
    sys.exit(1)


def utc_now_iso() -> str:
    timestamp = datetime.now(UTC).isoformat()
    return timestamp


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_yaml_ids(catalog_path: Path) -> Set[str]:
    ids: Set[str] = set()
    if not catalog_path.exists() or yaml is None:
        return ids
    try:
        content = yaml.safe_load(
            catalog_path.read_text(encoding="utf-8", errors="ignore")
        )
    except Exception:
        return ids
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                if "id" in item and isinstance(item["id"], str):
                    ids.add(item["id"])
            elif isinstance(item, str):
                ids.add(item)
    elif isinstance(content, dict):
        ids.update(str(key) for key in content.keys())
    return ids


def find_catalog_line(path: Path, entity_id: str) -> Optional[int]:
    if not path.exists():
        return None
    try:
        for idx, line in enumerate(
            path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1
        ):
            if entity_id in line:
                return idx
    except Exception:
        return None
    return None


def collect_entity_ids(root: Path, catalog_path: Path) -> List[str]:
    dir_ids = {p.name for p in root.iterdir() if p.is_dir()}
    catalog_ids = load_yaml_ids(catalog_path)
    return sorted(dir_ids.union(catalog_ids))


def parse_entity_yaml(path: Path) -> bool:
    if not path.exists() or yaml is None:
        return False
    try:
        yaml.safe_load(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return False
    return True


def list_response_templates(responses_dir: Path) -> List[Dict[str, object]]:
    templates: List[Dict[str, object]] = []
    if not responses_dir.exists():
        return templates
    for file in sorted(responses_dir.glob("*.md.j2")):
        templates.append(
            {
                "filename": file.name,
                "path": str(file.as_posix()),
                "size_bytes": file.stat().st_size,
            }
        )
    return templates


def build_surface_entry(
    entity_id: str,
    root: Path,
    catalog_path: Path,
    catalog_ids: Set[str],
) -> Dict[str, object]:
    entity_dir = root / entity_id
    new_entity_yaml_path = entity_dir / f"{entity_id}.yaml"
    entity_yaml_path = (
        new_entity_yaml_path if new_entity_yaml_path.exists() else entity_dir / "entity.yaml"
    )
    responses_dir = entity_dir / "responses"
    schema_path = Path("data/contracts/entities") / f"{entity_id}.schema.yaml"
    hints_path = entity_dir / "hints.md"
    template_path = entity_dir / "template.md"
    legacy_template_path = entity_dir / "templates.md"
    template_exists = template_path.exists()
    legacy_template_exists = legacy_template_path.exists()
    selected_template_path: Optional[Path] = None
    if template_exists:
        selected_template_path = template_path
    elif legacy_template_exists:
        selected_template_path = legacy_template_path
    db_sample_path = Path("docs/database/samples") / f"{entity_id}.csv"

    projection_files = sorted(
        [
            p
            for p in Path("data/ops/quality").glob(f"projection_{entity_id}.json")
            if p.is_file()
        ]
    )

    entry = {
        "entity_id": entity_id,
        "dir_exists": entity_dir.exists(),
        "dir_path": str(entity_dir.as_posix()),
        "catalog": {
            "listed_in_catalog": entity_id in catalog_ids,
            "catalog_path": str(catalog_path.as_posix()),
            "catalog_line": find_catalog_line(catalog_path, entity_id),
        },
        "entity_yaml": {
            "exists": entity_yaml_path.exists(),
            "path": str(entity_yaml_path.as_posix()),
            "parse_ok": parse_entity_yaml(entity_yaml_path),
            "schema_path": str(schema_path.as_posix()),
            "schema_exists": schema_path.exists(),
        },
        "responses": {
            "dir_exists": responses_dir.exists(),
            "dir_path": str(responses_dir.as_posix()),
            "templates": list_response_templates(responses_dir),
        },
        "support_files": {
            "hints_md": {
                "exists": hints_path.exists(),
                "path": str(hints_path.as_posix()) if hints_path.exists() else None,
            },
            "template_md": {
                "exists": template_exists or legacy_template_exists,
                "path": (
                    str(selected_template_path.as_posix())
                    if selected_template_path
                    else None
                ),
                "canonical": template_exists,
                "legacy_fallback": (not template_exists) and legacy_template_exists,
            },
            "templates_md": {
                "exists": legacy_template_exists,
                "path": (
                    str(legacy_template_path.as_posix()) if legacy_template_exists else None
                ),
            },
        },
        "db_samples": {
            "csv_exists": db_sample_path.exists(),
            "path": str(db_sample_path.as_posix()) if db_sample_path.exists() else None,
        },
        "golden": {
            "in_projection_quality": len(projection_files) > 0,
            "projection_files": [str(p.as_posix()) for p in projection_files],
        },
    }

    tags: List[str] = []
    if entry["entity_yaml"]["schema_exists"]:
        tags.append("has_contract_schema")
    if not entry["entity_yaml"]["exists"]:
        tags.append("missing_entity_yaml")
    if entry["db_samples"]["csv_exists"]:
        tags.append("has_db_sample")
    if entry["golden"]["in_projection_quality"]:
        tags.append("has_projection")
    entry["tags"] = tags

    return entry


def scan_files_for_entity(entity_id: str, files: Iterable[Path]) -> Dict[str, object]:
    matched: List[str] = []
    for file_path in files:
        if not file_path.exists():
            continue
        try:
            if entity_id in read_text(file_path):
                matched.append(str(file_path.as_posix()))
        except Exception:
            continue
    return {"referenced": len(matched) > 0, "files": matched}


def glob_files(pattern: str) -> List[Path]:
    return [p for p in Path(".").glob(pattern) if p.is_file()]


def build_used_by(entity_id: str) -> Dict[str, object]:
    ontology_files = [
        Path("data/ontology/entity.yaml"),
        Path("data/ontology/bucket_rules.yaml"),
        Path("data/ontology/ontology_manifest.yaml"),
    ]
    planner_files = glob_files("app/planner/*.py")
    orchestrator_files = glob_files("app/orchestrator/*.py")
    builder_files = glob_files("app/builder/*.py")
    presenter_files = glob_files("app/presenter/*.py")
    narrator_files = (
        glob_files("app/narrator/*.py")
        + glob_files("data/concepts/*.yaml")
        + [
            Path("data/policies/narrator.yaml"),
            Path("data/policies/narrator_shadow.yaml"),
        ]
    )
    rag_files = glob_files("app/rag/*.py")
    context_files = [
        Path("app/context/context_manager.py"),
        Path("data/policies/context.yaml"),
    ]

    policies = {
        "rag_policy": scan_files_for_entity(
            entity_id, [Path("data/policies/rag.yaml")]
        ),
        "narrator_policy": scan_files_for_entity(
            entity_id, [Path("data/policies/narrator.yaml")]
        ),
        "context_policy": scan_files_for_entity(
            entity_id, [Path("data/policies/context.yaml")]
        ),
    }

    quality = {
        "projections": scan_files_for_entity(
            entity_id, glob_files("data/ops/quality/*.json")
        ),
        "golden_sets": scan_files_for_entity(
            entity_id, glob_files("data/golden/*.json")
        ),
        "experimental_sets": scan_files_for_entity(
            entity_id,
            glob_files("data/ops/quality_experimental/*.json")
            + glob_files("data/ops/quality_experimental/*.yaml"),
        ),
    }

    embeddings = {
        "index": scan_files_for_entity(entity_id, [Path("data/embeddings/index.yaml")]),
    }

    docs = scan_files_for_entity(
        entity_id,
        [
            Path("docs/dev/ENTITIES_INVENTORY_2025.md"),
            Path("docs/dev/DOMAIN_FIIS_INVENTORY.md"),
        ],
    )

    used_by = {
        "ontology": scan_files_for_entity(entity_id, ontology_files),
        "planner": scan_files_for_entity(entity_id, planner_files),
        "orchestrator": scan_files_for_entity(entity_id, orchestrator_files),
        "builder": scan_files_for_entity(entity_id, builder_files),
        "presenter": scan_files_for_entity(entity_id, presenter_files),
        "narrator": scan_files_for_entity(entity_id, narrator_files),
        "rag": scan_files_for_entity(entity_id, rag_files),
        "context": scan_files_for_entity(entity_id, context_files),
        "policies": policies,
        "quality": quality,
        "embeddings": embeddings,
        "docs": docs,
    }

    return used_by


def any_references(used_by: Dict[str, object]) -> bool:
    def _walk(node: object) -> bool:
        if isinstance(node, dict):
            if "referenced" in node and isinstance(node["referenced"], bool):
                if node["referenced"]:
                    return True
            for value in node.values():
                if _walk(value):
                    return True
        return False

    return _walk(used_by)


def build_suspicious_signals(
    surface_entry: Dict[str, object], used_by: Dict[str, object]
) -> List[str]:
    signals: List[str] = []
    entity_yaml = (
        surface_entry.get("entity_yaml", {}) if isinstance(surface_entry, dict) else {}
    )
    golden = surface_entry.get("golden", {}) if isinstance(surface_entry, dict) else {}

    if entity_yaml.get("schema_exists") and not used_by.get("ontology", {}).get(
        "referenced"
    ):
        signals.append("entity_has_schema_but_not_in_ontology")
    if golden.get("in_projection_quality") and not used_by.get("planner", {}).get(
        "referenced"
    ):
        signals.append("entity_has_projection_but_not_in_planner")
    if not any_references(used_by):
        signals.append("entity_not_referenced_anywhere")
    return signals


def classify_entity(used_by: Dict[str, object]) -> Dict[str, str]:
    is_core = any(
        used_by.get(key, {}).get("referenced")
        for key in ["ontology", "planner", "orchestrator", "builder", "presenter"]
    )
    support_signals = (
        used_by.get("quality", {}).get("projections", {}).get("referenced")
        or used_by.get("quality", {}).get("golden_sets", {}).get("referenced")
        or used_by.get("docs", {}).get("referenced")
    )
    experimental_only = (
        used_by.get("quality", {}).get("experimental_sets", {}).get("referenced")
    )

    lifecycle: str
    notes: str

    if is_core:
        lifecycle = "core"
        sources = [
            k
            for k in ["ontology", "planner", "orchestrator", "builder", "presenter"]
            if used_by.get(k, {}).get("referenced")
        ]
        notes = (
            "entity appears in " + ", ".join(sources)
            if sources
            else "entity marked as core"
        )
    elif support_signals:
        lifecycle = "support"
        components = []
        if used_by.get("quality", {}).get("projections", {}).get("referenced"):
            components.append("quality projections")
        if used_by.get("quality", {}).get("golden_sets", {}).get("referenced"):
            components.append("golden sets")
        if used_by.get("docs", {}).get("referenced"):
            components.append("docs")
        notes = (
            "appears in " + ", ".join(components)
            if components
            else "support usage detected"
        )
    elif experimental_only:
        lifecycle = "experimental"
        notes = "only used in quality experimental sets"
    else:
        lifecycle = "legacy"
        notes = "no strong references found; candidate for archive"

    return {"lifecycle": lifecycle, "notes": notes}


def write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def generate_surface_report(root: Path, out_path: Path) -> Dict[str, object]:
    catalog_path = root / "catalog.yaml"
    entities = collect_entity_ids(root, catalog_path)
    catalog_ids = load_yaml_ids(catalog_path)
    report_entities = [
        build_surface_entry(entity_id, root, catalog_path, catalog_ids)
        for entity_id in entities
    ]
    payload = {
        "generated_at": utc_now_iso(),
        "root": str(root.as_posix()),
        "entities": report_entities,
    }
    write_json(out_path, payload)
    return {entity["entity_id"]: entity for entity in report_entities}


def generate_usage_report(
    entities: List[str], surface_map: Dict[str, Dict[str, object]], out_path: Path
) -> None:
    report_entities: List[Dict[str, object]] = []
    for entity_id in entities:
        used_by = build_used_by(entity_id)
        signals = build_suspicious_signals(surface_map.get(entity_id, {}), used_by)
        classification = classify_entity(used_by)
        report_entities.append(
            {
                "entity_id": entity_id,
                "used_by": used_by,
                "suspicious_signals": signals,
                "classification": classification,
            }
        )
    payload = {"generated_at": utc_now_iso(), "entities": report_entities}
    write_json(out_path, payload)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate entity surface and usage reports"
    )
    parser.add_argument(
        "--root", default="data/entities", help="Root directory containing entities"
    )
    parser.add_argument(
        "--out-surface",
        required=True,
        dest="out_surface",
        help="Output path for surface report",
    )
    parser.add_argument(
        "--out-usage",
        required=True,
        dest="out_usage",
        help="Output path for usage report",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    root = Path(args.root)
    surface_out = Path(args.out_surface)
    usage_out = Path(args.out_usage)

    catalog_path = root / "catalog.yaml"
    entities = collect_entity_ids(root, catalog_path)
    surface_map = generate_surface_report(root, surface_out)
    generate_usage_report(entities, surface_map, usage_out)

    print(f"Surface report written to {surface_out}")
    print(f"Usage report written to {usage_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
