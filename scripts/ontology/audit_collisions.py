# scripts/ontology/audit_collisions.py

import json
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from scripts.ontology.validate_and_hash import (  # pylint: disable=wrong-import-position
    OntologyEntity,
    load_entities,
    load_ontology_tokens,
)

REPORT_PATH = REPO_ROOT / "reports" / "ontology" / "collision_report.json"

ENTITY_SCOPE: Tuple[str, ...] = (
    "fiis_precos",
    "fiis_dividends",
    "fiis_yield_history",
    "fiis_financials_risk",
    "fiis_financials_revenue_schedule",
    "fiis_financials_snapshot",
    "fiis_rankings",
    "fiis_real_estate",
    "fiis_noticias",
    "fiis_overview",
    "fiis_dividends_yields",
    "client_fiis_enriched_portfolio",
    "macro_consolidada",
    "history_market_indicators",
    "history_b3_indexes",
    "history_currency_rates",
)

PROHIBITED_TOKENS: Tuple[str, ...] = ()


class AuditError(Exception):
    """Raised when an audit precondition fails."""


def normalize_token(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return stripped.encode("ascii", "ignore").decode("ascii").lower().strip()


def find_duplicates(values: Iterable[str]) -> List[str]:
    seen: Dict[str, str] = {}
    duplicates: List[str] = []
    for entry in values:
        key = normalize_token(entry)
        if key in seen:
            duplicates.append(entry)
        else:
            seen[key] = entry
    return duplicates


def collect_accent_violations(values: Iterable[str]) -> List[str]:
    return [entry for entry in values if not entry.isascii()]


def load_scoped_entities() -> Dict[str, OntologyEntity]:
    ontology_tokens = load_ontology_tokens()
    all_entities = load_entities(ontology_tokens)
    scoped: Dict[str, OntologyEntity] = {}
    missing: List[str] = []
    for entity_id in ENTITY_SCOPE:
        entity = all_entities.get(entity_id)
        if entity is None:
            missing.append(entity_id)
            continue
        scoped[entity_id] = entity
    if missing:
        missing_display = ", ".join(missing)
        raise AuditError(f"Missing entity definitions for: {missing_display}")
    return scoped


def build_entity_index(entity: OntologyEntity) -> Dict[str, Set[str]]:
    tokens = set(normalize_token(token) for token in entity.tokens)
    phrases = set(normalize_token(phrase) for phrase in entity.phrases)
    anti_tokens = set(normalize_token(anti) for anti in entity.anti_tokens)
    return {"tokens": tokens, "phrases": phrases, "anti_tokens": anti_tokens}


def detect_conflicts(
    indexes: Mapping[str, Dict[str, Set[str]]],
) -> Tuple[Dict[str, Dict[str, List[str]]], int, Dict[str, List[str]]]:
    conflicts: Dict[str, Dict[str, List[str]]] = defaultdict(dict)
    missing_anti_tokens: Dict[str, List[str]] = defaultdict(list)
    total_conflicts = 0

    entity_ids = sorted(indexes)
    for i, left_id in enumerate(entity_ids):
        left = indexes[left_id]
        left_search = left["tokens"].union(left["phrases"])
        for right_id in entity_ids[i + 1 :]:
            right = indexes[right_id]
            right_search = right["tokens"].union(right["phrases"])
            overlap = sorted(left_search.intersection(right_search))
            if not overlap:
                continue
            conflicts[left_id][right_id] = overlap
            conflicts[right_id][left_id] = overlap
            total_conflicts += len(overlap)
            for token in overlap:
                if token not in left["anti_tokens"]:
                    missing_anti_tokens[left_id].append(token)
                if token not in right["anti_tokens"]:
                    missing_anti_tokens[right_id].append(token)
    return conflicts, total_conflicts, missing_anti_tokens


def audit_entities(entities: Mapping[str, OntologyEntity]) -> Dict:
    indexes: Dict[str, Dict[str, Set[str]]] = {}
    accent_violations: Dict[str, List[str]] = {}
    duplicates: Dict[str, List[str]] = {}
    prohibited_hits: Dict[str, List[str]] = {}

    for entity_id, entity in entities.items():
        indexes[entity_id] = build_entity_index(entity)
        accent_list = (
            collect_accent_violations(entity.tokens)
            + collect_accent_violations(entity.phrases)
            + collect_accent_violations(entity.anti_tokens)
        )
        if accent_list:
            accent_violations[entity_id] = sorted(set(accent_list))
        dup_list = (
            find_duplicates(entity.tokens)
            + find_duplicates(entity.phrases)
            + find_duplicates(entity.anti_tokens)
        )
        if dup_list:
            duplicates[entity_id] = sorted(set(dup_list))
        if PROHIBITED_TOKENS:
            hits = [
                token
                for token in entity.tokens + entity.phrases
                if normalize_token(token) in PROHIBITED_TOKENS
            ]
            if hits:
                prohibited_hits[entity_id] = sorted(set(hits))

    conflicts, total_conflicts, missing_anti_tokens = detect_conflicts(indexes)

    entity_reports: Dict[str, MutableMapping] = {}
    for entity_id in entities:
        entity_reports[entity_id] = {
            "invalid_tokens": sorted(set(duplicates.get(entity_id, []))),
            "conflicts_with": conflicts.get(entity_id, {}),
            "accent_violations": accent_violations.get(entity_id, []),
            "missing_anti_tokens": sorted(set(missing_anti_tokens.get(entity_id, []))),
            "prohibited_tokens": sorted(set(prohibited_hits.get(entity_id, []))),
        }
    return {
        "entities": entity_reports,
        "total_conflicts": total_conflicts,
        "total_entities": len(entities),
        "needs_fix": any(
            entity_reports[entity_id]["conflicts_with"]
            or entity_reports[entity_id]["accent_violations"]
            or entity_reports[entity_id]["invalid_tokens"]
            or entity_reports[entity_id]["prohibited_tokens"]
            or entity_reports[entity_id]["missing_anti_tokens"]
            for entity_id in entity_reports
        ),
    }


def write_report(report: Mapping) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    payload = {
        "timestamp": timestamp,
        "entities": report["entities"],
        "summary": {
            "total_entities": report["total_entities"],
            "total_conflicts": report["total_conflicts"],
            "needs_fix": report["needs_fix"],
        },
    }
    with REPORT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2, sort_keys=False)
        handle.write("\n")


def main() -> int:
    try:
        entities = load_scoped_entities()
        report = audit_entities(entities)
        write_report(report)
    except AuditError as exc:
        print(f"Audit failed: {exc}")
        return 1
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Unexpected error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
