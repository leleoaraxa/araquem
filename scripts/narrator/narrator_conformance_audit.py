#!/usr/bin/env python
"""Narrator/RAG conformance audit for Araquem.
This script validates narrator and RAG configurations against Guardrails Araquem
v2.2.0 without executing LLMs or mutating runtime assets. It inspects policies,
entity definitions, and templates to ensure deterministic compliance and emits a
JSON report summarizing any issues.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Issue:
    type: str
    entity: Optional[str] = None
    field: Optional[str] = None
    path: Optional[str] = None
    detail: Optional[str] = None
    component: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        data = {
            "type": self.type,
        }
        if self.entity:
            data["entity"] = self.entity
        if self.field:
            data["field"] = self.field
        if self.path:
            data["path"] = self.path
        if self.detail:
            data["detail"] = self.detail
        if self.component:
            data["component"] = self.component
        return data


def load_yaml(path: Path) -> Optional[dict]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except FileNotFoundError:
        return None
    except yaml.YAMLError:
        return None


def is_ascii(value: str) -> bool:
    try:
        value.encode("ascii")
    except UnicodeEncodeError:
        return False
    return True


def extract_template_fields(template_text: str) -> Set[str]:
    fields: Set[str] = set()
    token = ""
    i = 0
    length = len(template_text)
    while i < length:
        ch = template_text[i]
        if ch.isalpha() or ch == "_":
            token = ch
            i += 1
            while i < length and (
                template_text[i].isalnum() or template_text[i] == "_"
            ):
                token += template_text[i]
                i += 1
            if i < length and template_text[i] == ".":
                i += 1
                attr = ""
                while i < length and (
                    template_text[i].isalnum() or template_text[i] == "_"
                ):
                    attr += template_text[i]
                    i += 1
                if attr:
                    fields.add(attr)
            continue
        i += 1
    return fields


def load_entities(entity_root: Path) -> Dict[str, dict]:
    entities: Dict[str, dict] = {}
    for entity_dir in entity_root.iterdir():
        if not entity_dir.is_dir():
            continue
        entity_file = entity_dir / "entity.yaml"
        data = load_yaml(entity_file)
        if not data:
            continue
        entity_id = data.get("id") or entity_dir.name
        columns = {c.get("name") for c in data.get("columns", []) if c.get("name")}
        identifiers = {
            i.get("name") for i in data.get("identifiers", []) if i.get("name")
        }
        requires_identifiers = set()
        ask = data.get("ask") or {}
        if isinstance(ask, dict):
            requires_identifiers = {
                ident for ident in (ask.get("requires_identifiers") or []) if ident
            }
        templates_dir = entity_dir / "responses"
        template_paths: List[Path] = []
        if templates_dir.is_dir():
            template_paths = [p for p in templates_dir.glob("*.j2") if p.is_file()]
        entities[entity_id] = {
            "columns": columns,
            "identifiers": identifiers,
            "requires_identifiers": requires_identifiers,
            "templates": template_paths,
            "private": bool(data.get("private")),
        }
    return entities


def audit_context_entities(
    context_policy: dict, entities: Dict[str, dict]
) -> List[Issue]:
    issues: List[Issue] = []
    narrator_cfg = (context_policy.get("context") or {}).get("narrator") or {}
    allowed_entities = narrator_cfg.get("allowed_entities") or []
    for entity in allowed_entities:
        if entity not in entities:
            issues.append(
                Issue(
                    type="entity_missing_in_ontology",
                    entity=entity,
                    component="narrator",
                    detail="Entity listed in context.yaml but missing in ontology",
                )
            )
            continue
        templates = entities[entity].get("templates") or []
        if not templates:
            issues.append(
                Issue(
                    type="template_missing",
                    entity=entity,
                    component="narrator",
                    detail="No narrator template found for allowed entity",
                )
            )
        valid_fields = entities[entity].get("columns") or set()
        for template_path in templates:
            try:
                text = template_path.read_text(encoding="utf-8")
            except Exception:
                issues.append(
                    Issue(
                        type="template_unreadable",
                        entity=entity,
                        component="narrator",
                        path=str(template_path.relative_to(ROOT)),
                    )
                )
                continue
            referenced = extract_template_fields(text)
            for field in sorted(referenced):
                if field not in valid_fields:
                    issues.append(
                        Issue(
                            type="template_missing_field",
                            entity=entity,
                            field=field,
                            component="narrator",
                            path=str(template_path.relative_to(ROOT)),
                        )
                    )
    return issues


def audit_concept_mode(prompts_path: Path) -> List[Issue]:
    issues: List[Issue] = []
    concept_template = None
    prompts_py = prompts_path / "prompts.py"
    if prompts_py.is_file():
        try:
            content = prompts_py.read_text(encoding="utf-8")
            marker = '"concept": '
            if marker in content:
                concept_start = content.split(marker, 1)[1]
                concept_template = concept_start
        except Exception:
            issues.append(
                Issue(
                    type="concept_template_unreadable",
                    component="narrator",
                    path=str(prompts_py.relative_to(ROOT)),
                )
            )
    else:
        issues.append(
            Issue(
                type="prompts_module_missing",
                component="narrator",
                path=str(prompts_py.relative_to(ROOT)),
            )
        )
    if concept_template:
        placeholders = "{{" in concept_template or "}}" in concept_template
        if placeholders:
            issues.append(
                Issue(
                    type="concept_template_has_placeholders",
                    component="narrator",
                    detail="Concept mode template must not reference entity fields",
                )
            )
        if "ticker" in concept_template:
            issues.append(
                Issue(
                    type="concept_template_mentions_ticker",
                    component="narrator",
                    detail="Concept mode should not require or mention tickers",
                )
            )
    return issues


def audit_entity_mode_requirements(
    context_policy: dict, entities: Dict[str, dict]
) -> List[Issue]:
    issues: List[Issue] = []
    narrator_cfg = (context_policy.get("context") or {}).get("narrator") or {}
    allowed_entities = narrator_cfg.get("allowed_entities") or []
    for entity in allowed_entities:
        info = entities.get(entity)
        if not info:
            continue
        requires = info.get("requires_identifiers") or set()
        identifiers = info.get("identifiers") or set()
        if "ticker" in identifiers and "ticker" not in requires:
            issues.append(
                Issue(
                    type="entity_missing_ticker_requirement",
                    entity=entity,
                    component="narrator",
                    detail="Entity mode must require ticker identifier",
                )
            )
    return issues


def audit_shadow(
    narrator_policy: dict, shadow_policy: dict, entities: Dict[str, dict]
) -> List[Issue]:
    issues: List[Issue] = []
    narrator_cfg = narrator_policy.get("narrator") or {}
    if narrator_cfg.get("shadow"):
        redaction_cfg = (shadow_policy.get("narrator_shadow") or {}).get(
            "redaction"
        ) or {}
        mask_fields = redaction_cfg.get("mask_fields") or []
        if not mask_fields:
            issues.append(
                Issue(
                    type="shadow_redaction_missing",
                    component="narrator",
                    detail="Shadow enabled but no redaction mask fields configured",
                )
            )
        shadow_private = (shadow_policy.get("narrator_shadow") or {}).get(
            "private_entities"
        ) or []
        for entity, info in entities.items():
            if info.get("private") and entity not in shadow_private:
                issues.append(
                    Issue(
                        type="shadow_private_entity_not_listed",
                        entity=entity,
                        component="narrator",
                        detail="Private entity missing from shadow redaction allowlist",
                    )
                )
        sensitive_fields = {
            "cpf",
            "cnpj",
            "document_number",
            "document",
            "email",
            "phone",
        }
        for entity, info in entities.items():
            templates = info.get("templates") or []
            for template_path in templates:
                try:
                    text = template_path.read_text(encoding="utf-8")
                except Exception:
                    continue
                referenced = extract_template_fields(text)
                for field in referenced:
                    if field.lower() in sensitive_fields:
                        issues.append(
                            Issue(
                                type="shadow_sensitive_field_referenced",
                                entity=entity,
                                field=field,
                                component="narrator",
                                path=str(template_path.relative_to(ROOT)),
                            )
                        )
    return issues


def audit_llm_enabled(
    narrator_policy: dict,
    context_policy: dict,
    shadow_policy: dict,
    entities: Dict[str, dict],
) -> List[Issue]:
    issues: List[Issue] = []
    narrator_cfg = narrator_policy.get("narrator") or {}
    if narrator_cfg.get("llm_enabled"):
        context_narrator = (context_policy.get("context") or {}).get("narrator") or {}
        denied = set(context_narrator.get("denied_entities") or [])
        for entity, info in entities.items():
            if info.get("private") and entity not in denied:
                issues.append(
                    Issue(
                        type="private_entity_not_denied",
                        entity=entity,
                        component="narrator",
                        detail="LLM enabled but private entity not in denied list",
                    )
                )
        shadow_cfg = shadow_policy.get("narrator_shadow") if shadow_policy else None
        if not shadow_cfg:
            issues.append(
                Issue(
                    type="shadow_policy_missing",
                    component="narrator",
                    detail="LLM enabled but narrator_shadow policy missing",
                )
            )
    return issues


def audit_template_directories() -> List[Issue]:
    issues: List[Issue] = []
    prompts_dir = ROOT / "app" / "narrator" / "prompts"
    formatter_dir = ROOT / "app" / "narrator" / "formatter"
    if not prompts_dir.exists():
        issues.append(
            Issue(
                type="template_directory_missing",
                component="narrator",
                path=str(prompts_dir.relative_to(ROOT)),
            )
        )
    if not formatter_dir.exists():
        issues.append(
            Issue(
                type="template_directory_missing",
                component="narrator",
                path=str(formatter_dir.relative_to(ROOT)),
            )
        )
    return issues


def audit_rag_index(index_path: Path) -> List[Issue]:
    issues: List[Issue] = []
    if not index_path.is_file():
        issues.append(
            Issue(
                type="rag_index_missing",
                component="rag",
                path=str(index_path.relative_to(ROOT)),
            )
        )
        return issues
    embedding_length: Optional[int] = None
    chunk_id = 0
    try:
        for line in index_path.read_text(encoding="utf-8").splitlines():
            chunk_id += 1
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                issues.append(
                    Issue(
                        type="rag_index_invalid_json",
                        component="rag",
                        path=str(index_path.relative_to(ROOT)),
                        detail=f"Line {chunk_id} is not valid JSON",
                    )
                )
                continue
            text = record.get("text")
            embedding = record.get("embedding")
            metadata = record.get("metadata") or {}
            if not isinstance(text, str) or not text.strip():
                issues.append(
                    Issue(
                        type="rag_index_missing_text",
                        component="rag",
                        path=str(index_path.relative_to(ROOT)),
                        detail=f"Line {chunk_id} missing text",
                    )
                )
            elif not is_ascii(text):
                issues.append(
                    Issue(
                        type="rag_text_not_ascii",
                        component="rag",
                        path=str(index_path.relative_to(ROOT)),
                        detail=f"Line {chunk_id} text not ASCII",
                    )
                )
            if not isinstance(embedding, list) or not embedding:
                issues.append(
                    Issue(
                        type="rag_embedding_invalid",
                        component="rag",
                        path=str(index_path.relative_to(ROOT)),
                        detail=f"Line {chunk_id} missing embedding",
                    )
                )
            else:
                if not all(isinstance(v, (int, float)) for v in embedding):
                    issues.append(
                        Issue(
                            type="rag_embedding_non_numeric",
                            component="rag",
                            path=str(index_path.relative_to(ROOT)),
                            detail=f"Line {chunk_id} embedding has non-numeric values",
                        )
                    )
                if embedding_length is None:
                    embedding_length = len(embedding)
                elif embedding_length != len(embedding):
                    issues.append(
                        Issue(
                            type="rag_embedding_length_mismatch",
                            component="rag",
                            path=str(index_path.relative_to(ROOT)),
                            detail=f"Line {chunk_id} embedding length mismatch",
                        )
                    )
            if isinstance(metadata, dict):
                for key, value in metadata.items():
                    if isinstance(key, str) and not is_ascii(key):
                        issues.append(
                            Issue(
                                type="rag_metadata_not_ascii",
                                component="rag",
                                path=str(index_path.relative_to(ROOT)),
                                detail=f"Line {chunk_id} metadata key not ASCII",
                            )
                        )
                    if isinstance(value, str) and not is_ascii(value):
                        issues.append(
                            Issue(
                                type="rag_metadata_not_ascii",
                                component="rag",
                                path=str(index_path.relative_to(ROOT)),
                                detail=f"Line {chunk_id} metadata value not ASCII",
                            )
                        )
    except Exception as exc:
        issues.append(
            Issue(
                type="rag_index_unreadable",
                component="rag",
                path=str(index_path.relative_to(ROOT)),
                detail=str(exc),
            )
        )
    return issues


def audit_rag_hints(hints_dir: Path) -> List[Issue]:
    issues: List[Issue] = []
    if not hints_dir.exists():
        issues.append(
            Issue(
                type="rag_hints_missing",
                component="rag",
                path=str(hints_dir.relative_to(ROOT)),
            )
        )
        return issues
    if not hints_dir.is_dir():
        issues.append(
            Issue(
                type="rag_hints_not_directory",
                component="rag",
                path=str(hints_dir.relative_to(ROOT)),
            )
        )
        return issues
    for hint_file in hints_dir.rglob("*"):
        if hint_file.is_file():
            try:
                content = hint_file.read_text(encoding="utf-8")
                if not is_ascii(content):
                    issues.append(
                        Issue(
                            type="rag_hint_not_ascii",
                            component="rag",
                            path=str(hint_file.relative_to(ROOT)),
                        )
                    )
            except Exception:
                issues.append(
                    Issue(
                        type="rag_hint_unreadable",
                        component="rag",
                        path=str(hint_file.relative_to(ROOT)),
                    )
                )
    return issues


def audit_rag_policy(rag_policy: dict, entities: Dict[str, dict]) -> List[Issue]:
    issues: List[Issue] = []
    routing = rag_policy.get("routing") or {}
    deny = routing.get("deny_intents") or []
    allow = routing.get("allow_intents") or []
    known = set(entities.keys())
    for ent in deny + allow:
        if ent not in known:
            issues.append(
                Issue(
                    type="rag_policy_unknown_entity",
                    entity=ent,
                    component="rag",
                    detail="Entity listed in RAG policy not found in ontology",
                )
            )
    profiles = rag_policy.get("profiles") or {}
    for profile_name, profile_cfg in profiles.items():
        min_score = profile_cfg.get("min_score")
        if min_score is None or not isinstance(min_score, (int, float)):
            issues.append(
                Issue(
                    type="rag_profile_min_score_missing",
                    component="rag",
                    detail=f"Profile {profile_name} missing numeric min_score",
                )
            )
        elif not (0 < float(min_score) < 1):
            issues.append(
                Issue(
                    type="rag_profile_min_score_out_of_range",
                    component="rag",
                    detail=f"Profile {profile_name} min_score outside (0,1)",
                )
            )
    rag_entities = (rag_policy.get("rag") or {}).get("entities") or {}
    for ent_name, ent_cfg in rag_entities.items():
        if ent_name not in known:
            issues.append(
                Issue(
                    type="rag_policy_unknown_entity",
                    entity=ent_name,
                    component="rag",
                    detail="RAG entity not found in ontology",
                )
            )
        min_score = ent_cfg.get("min_score")
        if min_score is not None and not (0 < float(min_score) < 1):
            issues.append(
                Issue(
                    type="rag_entity_min_score_out_of_range",
                    entity=ent_name,
                    component="rag",
                )
            )
        max_chunks = ent_cfg.get("max_chunks")
        if max_chunks is not None and (
            not isinstance(max_chunks, int) or max_chunks <= 0
        ):
            issues.append(
                Issue(
                    type="rag_entity_max_chunks_invalid",
                    entity=ent_name,
                    component="rag",
                )
            )
    apply_on = rag_policy.get("apply_on")
    if not apply_on:
        issues.append(
            Issue(
                type="rag_apply_on_missing",
                component="rag",
                detail="RAG apply_on not configured to enforce planner arbitration",
            )
        )
    return issues


def audit_rag_chunk_overrides(index_path: Path) -> List[Issue]:
    issues: List[Issue] = []
    if not index_path.is_file():
        return issues
    try:
        for idx, line in enumerate(
            index_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "override_entity" in record:
                issues.append(
                    Issue(
                        type="rag_chunk_overrides_entity",
                        component="rag",
                        path=str(index_path.relative_to(ROOT)),
                        detail=f"Line {idx} contains override_entity",
                    )
                )
    except Exception:
        return issues
    return issues


def generate_report(
    narrator_ok: bool, rag_ok: bool, issues: List[Issue], report_path: Path
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).isoformat()
    report = {
        "timestamp": timestamp,
        "narrator_ok": narrator_ok,
        "rag_ok": rag_ok,
        "issues": [issue.to_dict() for issue in issues],
    }
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=True)


def main() -> int:
    narrator_policy_path = ROOT / "data" / "policies" / "narrator.yaml"
    context_policy_path = ROOT / "data" / "policies" / "context.yaml"
    shadow_policy_path = ROOT / "data" / "policies" / "narrator_shadow.yaml"
    rag_policy_path = ROOT / "data" / "policies" / "rag.yaml"
    rag_index_path = ROOT / "data" / "rag" / "index.jsonl"
    rag_hints_dir = ROOT / "data" / "rag" / "hints"

    narrator_policy = load_yaml(narrator_policy_path) or {}
    context_policy = load_yaml(context_policy_path) or {}
    shadow_policy = load_yaml(shadow_policy_path) or {}
    rag_policy = load_yaml(rag_policy_path) or {}

    entities = load_entities(ROOT / "data" / "entities")

    issues: List[Issue] = []
    issues.extend(audit_template_directories())
    issues.extend(audit_context_entities(context_policy, entities))
    issues.extend(audit_concept_mode(ROOT / "app" / "narrator"))
    issues.extend(audit_entity_mode_requirements(context_policy, entities))
    issues.extend(audit_shadow(narrator_policy, shadow_policy, entities))
    issues.extend(
        audit_llm_enabled(narrator_policy, context_policy, shadow_policy, entities)
    )

    issues.extend(audit_rag_policy(rag_policy, entities))
    issues.extend(audit_rag_index(rag_index_path))
    issues.extend(audit_rag_hints(rag_hints_dir))
    issues.extend(audit_rag_chunk_overrides(rag_index_path))

    narrator_ok = not any(issue.component == "narrator" for issue in issues)
    rag_ok = not any(issue.component == "rag" for issue in issues)

    report_path = ROOT / "reports" / "narrator" / "narrator_conformance.json"
    generate_report(narrator_ok, rag_ok, issues, report_path)

    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
