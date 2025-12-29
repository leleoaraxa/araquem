"""Builds formal coverage reports cross-checking ontology, catalog, schemas and policies.

This script performs static checks only (no runtime calls) and writes two artifacts:
  - docs/dev/COVERAGE_REPORT_2025_0.md
  - data/ops/reports/coverage_report_2025_0.json

The output is fully derived from repository YAML files (no hardcoded entity lists) and
ordered deterministically to keep artifacts stable across runs.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Set, Tuple

import yaml


ROOT = Path(__file__).resolve().parents[2]
ONTOLOGY_PATH = ROOT / "data/ontology/entity.yaml"
CATALOG_PATH = ROOT / "data/entities/catalog.yaml"
CONTRACTS_DIR = ROOT / "data/contracts/entities"
POLICIES_DIR = ROOT / "data/policies"
PARAM_INFERENCE_PATH = ROOT / "data/ops/param_inference.yaml"

MARKDOWN_REPORT_PATH = ROOT / "docs/dev/COVERAGE_REPORT_2025_0.md"
JSON_REPORT_PATH = ROOT / "data/ops/reports/coverage_report_2025_0.json"


def load_yaml(path: Path) -> MutableMapping:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def sorted_unique(items: Iterable[str]) -> List[str]:
    return sorted({item for item in items if item is not None})


@dataclasses.dataclass
class Gap:
    priority: str  # P0, P1, P2
    message: str
    entity: Optional[str] = None
    intent: Optional[str] = None
    path: Optional[str] = None

    def as_dict(self) -> Dict[str, Optional[str]]:
        return {
            "priority": self.priority,
            "message": self.message,
            "entity": self.entity,
            "intent": self.intent,
            "path": self.path,
        }


def collect_ontology(path: Path) -> Tuple[Mapping[str, List[str]], Mapping[str, str], List[Mapping]]:
    data = load_yaml(path)
    bucket_map = data.get("buckets", {}) or {}
    entities_to_bucket: Dict[str, str] = {}
    for bucket, entities in bucket_map.items():
        for entity in entities or []:
            entities_to_bucket[entity] = bucket

    intents: List[Mapping] = data.get("intents", []) or []
    entity_to_intents: Dict[str, List[str]] = {}
    for intent in intents:
        for entity in intent.get("entities", []) or []:
            entity_to_intents.setdefault(entity, []).append(intent.get("name"))

    for entity, intent_names in entity_to_intents.items():
        entity_to_intents[entity] = sorted_unique(intent_names)

    return entity_to_intents, entities_to_bucket, intents


def collect_catalog(path: Path) -> Mapping[str, Mapping]:
    data = load_yaml(path)
    return data.get("entities", {}) or {}


def validate_paths(entity: str, catalog_entry: Mapping, gaps: List[Gap]) -> Dict[str, bool]:
    results = {"entity_yaml_exists": False, "schema_exists": False}
    paths = catalog_entry.get("paths", {}) or {}

    entity_yaml_path = paths.get("entity_yaml")
    schema_path = paths.get("schema")

    if entity_yaml_path:
        full_path = ROOT / entity_yaml_path
        results["entity_yaml_exists"] = full_path.exists()
        if not full_path.exists():
            gaps.append(
                Gap(
                    priority="P0",
                    entity=entity,
                    path=str(full_path),
                    message="Entity YAML path missing",
                )
            )

    if schema_path:
        full_path = ROOT / schema_path
        results["schema_exists"] = full_path.exists()
        if not full_path.exists():
            gaps.append(
                Gap(
                    priority="P0",
                    entity=entity,
                    path=str(full_path),
                    message="Schema path missing",
                )
            )

    return results


def detect_non_tabular_schema(schema_data: Mapping) -> bool:
    if "columns" not in schema_data:
        return True
    columns = schema_data.get("columns")
    if not isinstance(columns, list):
        return True
    return False


def validate_schema(entity: str, schema_path: Path, gaps: List[Gap]) -> Dict[str, object]:
    if not schema_path.exists():
        return {"status": "missing", "issues": ["schema file absent"], "ok": False}

    schema_data = load_yaml(schema_path)
    issues: List[str] = []

    if detect_non_tabular_schema(schema_data):
        issues.append("non-tabular schema (missing or invalid columns block)")

    if schema_data.get("entity") != entity:
        issues.append(f"entity field mismatch: {schema_data.get('entity')} != {entity}")

    if schema_data.get("name") != entity:
        issues.append(f"name field mismatch: {schema_data.get('name')} != {entity}")

    if schema_data.get("kind") != "view":
        issues.append(f"kind should be 'view' (found {schema_data.get('kind')})")

    description = schema_data.get("description")
    if description is None or str(description).strip() == "":
        issues.append("description missing or empty")

    columns = schema_data.get("columns", []) or []
    for column in columns if isinstance(columns, list) else []:
        if not isinstance(column, Mapping):
            issues.append("column entry is not a mapping")
            continue
        if "name" not in column or "type" not in column:
            issues.append(f"column missing name/type: {column}")

    if "properties" in schema_data or (schema_data.get("type") == "object" and "columns" not in schema_data):
        issues.append("schema appears to use JSON Schema format (properties/type), expected tabular")

    ok = len(issues) == 0
    if not ok:
        for issue in issues:
            gaps.append(
                Gap(
                    priority="P0",
                    entity=entity,
                    path=str(schema_path),
                    message=issue,
                )
            )

    return {"ok": ok, "issues": issues}


def read_policies() -> Mapping[str, MutableMapping]:
    return {
        "cache": load_yaml(POLICIES_DIR / "cache.yaml"),
        "rag": load_yaml(POLICIES_DIR / "rag.yaml"),
        "narrator": load_yaml(POLICIES_DIR / "narrator.yaml"),
        "context": load_yaml(POLICIES_DIR / "context.yaml"),
    }


def evaluate_cache(entity: str, flag: bool, cache_policy: Mapping, gaps: List[Gap]) -> str:
    policies = (cache_policy.get("policies") or {}) if cache_policy else {}
    has_policy = entity in policies
    if flag and not has_policy:
        gaps.append(
            Gap(priority="P1", entity=entity, message="cache_policy flag true but no cache rule defined")
        )
        return "flagged_missing_rule"
    if not flag and has_policy:
        return "rule_present_flag_false"
    return "ok" if (flag == has_policy or not flag) else "unknown"


def _rag_allowed_intents(intents: List[str], routing: Mapping) -> List[str]:
    allow_intents = routing.get("allow_intents") or []
    deny_intents = routing.get("deny_intents") or []
    if allow_intents:
        allowed = [intent for intent in intents if intent in allow_intents and intent not in deny_intents]
    else:
        allowed = [intent for intent in intents if intent not in deny_intents]
    return sorted_unique(allowed)


def evaluate_rag(entity: str, intents: List[str], flag: bool, rag_policy: Mapping, gaps: List[Gap]) -> Dict[str, object]:
    routing = rag_policy.get("routing") or {}
    rag_entities = (rag_policy.get("rag") or {}).get("entities", {})
    allowed_intents = _rag_allowed_intents(intents, routing)
    entity_configured = entity in rag_entities
    globally_denied = not routing.get("allow_intents") and not allowed_intents and bool(intents)

    status = "ok"
    notes: List[str] = []

    if flag:
        if globally_denied:
            status = "flagged_but_rag_disabled"
            notes.append("routing denies all intents (policy override: disabled)")
            gaps.append(
                Gap(
                    priority="P1",
                    entity=entity,
                    message="rag flag active but routing denies intents (policy override)",
                )
            )
        elif not allowed_intents:
            status = "flagged_without_allowed_intents"
            notes.append("no intents allowed for RAG")
            gaps.append(
                Gap(priority="P1", entity=entity, message="rag flag active but no intents allowed for RAG")
            )
        elif not entity_configured:
            status = "flagged_without_entity_config"
            notes.append("allowed intents but entity missing from rag.entities (using default)")
    else:
        if allowed_intents or entity_configured:
            status = "policy_present_flag_false"
            notes.append("RAG configuration exists while catalog flag is false")
            gaps.append(
                Gap(
                    priority="P2",
                    entity=entity,
                    message="catalog rag_policy=false but RAG configuration present",
                )
            )

    return {"status": status, "allowed_intents": allowed_intents, "notes": notes}


def evaluate_narrator(
    entity: str,
    bucket: Optional[str],
    intents: List[str],
    flag: bool,
    narrator_policy: Mapping,
    context_policy: Mapping,
    gaps: List[Gap],
) -> Dict[str, object]:
    narrator_entities = (narrator_policy.get("entities") or {}) if narrator_policy else {}
    bucket_rules = (narrator_policy.get("buckets") or {}) if narrator_policy else {}
    default_rule = narrator_policy.get("default") if narrator_policy else None
    context_narrator = (context_policy.get("context") or {}).get("narrator") or {}

    entity_rule = narrator_entities.get(entity)
    bucket_rule = bucket_rules.get(bucket) if bucket else None
    allowed_by_context = entity in (context_narrator.get("allowed_entities") or [])
    denied_by_context = entity in (context_narrator.get("denied_entities") or [])

    status = "ok"
    notes: List[str] = []

    if flag:
        if not entity_rule and not bucket_rule and not default_rule:
            status = "flagged_without_rule"
            gaps.append(Gap(priority="P1", entity=entity, message="narrator flag active but no narrator rule found"))
        if entity_rule and entity_rule.get("llm_enabled") is False:
            notes.append("narrator llm explicitly disabled for entity")
        if denied_by_context:
            status = "denied_by_context"
            notes.append("context policy denies narrator history for entity")
            gaps.append(
                Gap(priority="P1", entity=entity, message="narrator flag active but denied by context policy")
            )
    else:
        if entity_rule and entity_rule.get("llm_enabled"):
            status = "rule_present_flag_false"
            gaps.append(
                Gap(priority="P2", entity=entity, message="narrator rule enables llm while flag is false")
            )

    return {
        "status": status,
        "notes": notes,
        "llm_enabled": entity_rule.get("llm_enabled") if entity_rule else None,
        "context_allowed": allowed_by_context,
    }


def evaluate_param_inference(
    entity: str, intents: List[str], flag: bool, param_inference: Mapping, gaps: List[Gap]
) -> Dict[str, object]:
    intents_config = (param_inference.get("intents") or {}) if param_inference else {}
    configured_intents = [intent for intent in intents if intent in intents_config]
    missing_intents = [intent for intent in intents if intent not in intents_config]

    status = "ok"
    notes: List[str] = []

    if flag:
        if intents and not configured_intents:
            status = "flagged_missing_intents"
            notes.append("no intents configured for param inference")
            gaps.append(
                Gap(priority="P1", entity=entity, message="param_inference flag true but no intents configured")
            )
        elif missing_intents:
            status = "partial"
            notes.append(f"intents without param inference: {', '.join(sorted(missing_intents))}")
            gaps.append(
                Gap(
                    priority="P2",
                    entity=entity,
                    message="some intents missing param inference configuration",
                )
            )
    else:
        if configured_intents:
            status = "configured_flag_false"
            notes.append("param inference configuration exists while flag is false")
            gaps.append(
                Gap(priority="P2", entity=entity, message="param inference config present but flag is false")
            )

    return {
        "status": status,
        "configured_intents": sorted_unique(configured_intents),
        "missing_intents": sorted_unique(missing_intents),
        "notes": notes,
    }


def format_coverage_matrix_row(entity: str, record: Mapping) -> str:
    intents = ", ".join(record.get("intents", [])) or "—"
    cache = record.get("policies", {}).get("cache", "—")
    rag = record.get("policies", {}).get("rag", {}).get("status", "—")
    narrator = record.get("policies", {}).get("narrator", {}).get("status", "—")
    param_inf = record.get("policies", {}).get("param_inference", {}).get("status", "—")
    schema_ok = "ok" if record.get("schema", {}).get("ok") else "issues"
    notes = "; ".join(record.get("notes", [])) or ""
    return f"| {entity} | {intents} | {cache} | {rag} | {narrator} | {param_inf} | {schema_ok} | {notes} |"


def build_reports() -> Dict[str, object]:
    gaps: List[Gap] = []
    entity_to_intents, entities_to_bucket, intents_data = collect_ontology(ONTOLOGY_PATH)
    catalog = collect_catalog(CATALOG_PATH)
    policies = read_policies()
    param_inference = load_yaml(PARAM_INFERENCE_PATH)

    ontology_entities = set(entity_to_intents.keys()) | set(entities_to_bucket.keys())
    catalog_entities = set(catalog.keys())

    missing_from_catalog = ontology_entities - catalog_entities
    for entity in sorted(missing_from_catalog):
        gaps.append(
            Gap(priority="P1", entity=entity, message="Entity referenced in ontology is missing from catalog")
        )

    records: Dict[str, Dict[str, object]] = {}
    for entity in sorted(catalog.keys()):
        catalog_entry = catalog[entity] or {}
        intents = entity_to_intents.get(entity, [])
        bucket = entities_to_bucket.get(entity)

        path_checks = validate_paths(entity, catalog_entry, gaps)
        schema_path = catalog_entry.get("paths", {}).get("schema")
        schema_result: Dict[str, object]
        if schema_path:
            schema_result = validate_schema(entity, ROOT / schema_path, gaps)
        else:
            schema_result = {"ok": False, "issues": ["schema path missing in catalog"]}
            gaps.append(
                Gap(priority="P0", entity=entity, message="schema path missing in catalog entry")
            )

        coverage_flags = catalog_entry.get("coverage", {}) or {}
        cache_status = evaluate_cache(entity, coverage_flags.get("cache_policy", False), policies.get("cache"), gaps)
        rag_status = evaluate_rag(
            entity,
            intents,
            coverage_flags.get("rag_policy", False),
            policies.get("rag", {}),
            gaps,
        )
        narrator_status = evaluate_narrator(
            entity,
            bucket,
            intents,
            coverage_flags.get("narrator_policy", False),
            policies.get("narrator", {}),
            policies.get("context", {}),
            gaps,
        )
        param_status = evaluate_param_inference(
            entity, intents, coverage_flags.get("param_inference", False), param_inference, gaps
        )

        record = {
            "bucket": bucket,
            "intents": intents,
            "coverage_flags": coverage_flags,
            "paths": path_checks,
            "schema": schema_result,
            "policies": {
                "cache": cache_status,
                "rag": rag_status,
                "narrator": narrator_status,
                "param_inference": param_status,
            },
            "notes": catalog_entry.get("notes") or [],
        }
        records[entity] = record

    gaps_by_priority: Dict[str, List[Dict[str, Optional[str]]]] = {"P0": [], "P1": [], "P2": []}
    for gap in sorted(gaps, key=lambda g: (g.priority, g.entity or "", g.intent or "", g.message)):
        gaps_by_priority[gap.priority].append(gap.as_dict())

    appendix = {
        "catalog_entities": sorted(catalog.keys()),
        "ontology_intents": sorted(intent.get("name") for intent in intents_data if intent.get("name")),
        "ontology_entities": sorted(ontology_entities),
        "rag_denied_intents": sorted(policies.get("rag", {}).get("routing", {}).get("deny_intents", []) or []),
        "rag_allow_intents": sorted(policies.get("rag", {}).get("routing", {}).get("allow_intents", []) or []),
    }

    return {
        "records": records,
        "gaps": gaps_by_priority,
        "appendix": appendix,
    }


def write_json_report(report: Mapping) -> None:
    JSON_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with JSON_REPORT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)


def write_markdown_report(report: Mapping) -> None:
    records: Mapping[str, Mapping] = report["records"]
    gaps: Mapping[str, List[Mapping]] = report["gaps"]
    appendix: Mapping[str, List[str]] = report["appendix"]

    lines: List[str] = []
    lines.append("# Coverage Report 2025.0")
    lines.append("")
    lines.append("## Resumo executivo")
    lines.append("- Geração automática a partir de YAML (determinística, ordenação alfabética).")
    lines.append("- Escopo: Ontologia ↔ Catálogo ↔ Contracts ↔ Policies.")
    lines.append("- Prioridades: P0 (contrato), P1 (drift flags/policies), P2 (higiene).")
    lines.append("")

    lines.append("## Matriz de coverage por entidade")
    lines.append("| entidade | intents | cache | rag | narrator | param_inference | schema_ok | notes |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for entity in sorted(records.keys()):
        lines.append(format_coverage_matrix_row(entity, records[entity]))
    lines.append("")

    lines.append("## Gaps P0/P1/P2")
    for priority in ["P0", "P1", "P2"]:
        lines.append(f"### {priority}")
        if not gaps.get(priority):
            lines.append("- Nenhum.")
        else:
            for gap in gaps[priority]:
                scope = gap.get("entity") or gap.get("intent") or "-"
                path = f" ({gap.get('path')})" if gap.get("path") else ""
                lines.append(f"- {scope}: {gap.get('message')}{path}")
        lines.append("")

    lines.append("## Apêndice")
    lines.append("### Entidades no catálogo")
    lines.append(", ".join(appendix.get("catalog_entities", [])))
    lines.append("")

    lines.append("### Entidades na ontologia")
    lines.append(", ".join(appendix.get("ontology_entities", [])))
    lines.append("")

    lines.append("### Intents na ontologia")
    lines.append(", ".join(appendix.get("ontology_intents", [])))
    lines.append("")

    lines.append("### Policies RAG (routing)")
    lines.append(f"Allow intents: {', '.join(appendix.get('rag_allow_intents', [])) or '—'}")
    lines.append(f"Deny intents: {', '.join(appendix.get('rag_denied_intents', [])) or '—'}")
    lines.append("")

    MARKDOWN_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    MARKDOWN_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    report = build_reports()
    write_json_report(report)
    write_markdown_report(report)


if __name__ == "__main__":
    main()
