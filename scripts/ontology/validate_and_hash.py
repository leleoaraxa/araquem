import argparse
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
ENTITIES_DIR = REPO_ROOT / "data" / "entities"
MANIFEST_PATH = REPO_ROOT / "data" / "ontology" / "ontology_manifest.yaml"
ONTOLOGY_PATH = REPO_ROOT / "data" / "ontology" / "entity.yaml"
MANIFEST_VERSION = "2025.0-prod"

REQUIRED_KEYS = {
    "id": str,
    "intent": str,
    "result_key": str,
    "tokens": list,
    "phrases": list,
    "anti_tokens": list,
    "columns": list,
}

COLLISION_RULES: Mapping[str, Sequence[str]] = {
    "fiis_financials_snapshot": [
        "fii_overview",
        "fiis_rankings",
        "fiis_precos",
        "fiis_dividendos",
        "fiis_yield_history",
    ],
    "fii_overview": [
        "fiis_financials_snapshot",
        "fiis_rankings",
        "fiis_precos",
        "fiis_dividendos",
        "fiis_yield_history",
    ],
    "fiis_rankings": [
        "fiis_financials_snapshot",
        "fii_overview",
        "fiis_precos",
        "fiis_dividendos",
        "fiis_yield_history",
    ],
    "fiis_precos": [
        "fiis_financials_snapshot",
        "fii_overview",
        "fiis_rankings",
        "fiis_dividendos",
        "fiis_yield_history",
    ],
    "fiis_dividendos": [
        "fiis_financials_snapshot",
        "fii_overview",
        "fiis_rankings",
        "fiis_precos",
        "fiis_yield_history",
    ],
    "fiis_yield_history": [
        "fiis_financials_snapshot",
        "fii_overview",
        "fiis_rankings",
        "fiis_precos",
        "fiis_dividendos",
    ],
}


class ValidationError(Exception):
    """Aggregate validation errors."""


class OntologyEntity:
    def __init__(self, raw: Mapping, source: Path):
        if not isinstance(raw, Mapping):
            raise ValidationError(f"Entity file {source} must contain a mapping at the root")
        self.raw = raw
        self.source = source
        self._validate_structure()
        self.id = str(raw["id"])
        self.intent = str(raw["intent"])
        self.result_key = str(raw["result_key"])
        self.tokens = self._ensure_str_list(raw["tokens"], "tokens")
        self.phrases = self._ensure_str_list(raw["phrases"], "phrases")
        self.anti_tokens = self._ensure_str_list(raw["anti_tokens"], "anti_tokens")
        self.columns = self._validate_columns(raw["columns"])
        self._validate_ascii()
        self._validate_internal_duplicates()

    def _validate_structure(self) -> None:
        errors: List[str] = []
        for key, expected_type in REQUIRED_KEYS.items():
            if key not in self.raw:
                errors.append(f"Missing required key '{key}' in {self.source}")
                continue
            if not isinstance(self.raw[key], expected_type):
                errors.append(
                    f"Key '{key}' in {self.source} must be of type {expected_type.__name__}"
                )
        if errors:
            raise ValidationError("\n".join(errors))

    def _ensure_str_list(self, value: Iterable, field: str) -> List[str]:
        items: List[str] = []
        for entry in value:
            if not isinstance(entry, str):
                raise ValidationError(
                    f"All entries in '{field}' for {self.source} must be strings"
                )
            items.append(entry)
        return items

    def _validate_columns(self, columns: Iterable[Mapping]) -> List[Mapping[str, str]]:
        validated: List[Mapping[str, str]] = []
        for column in columns:
            if not isinstance(column, Mapping):
                raise ValidationError(
                    f"Each column entry in {self.source} must be a mapping with a 'name' field"
                )
            if "name" not in column or not isinstance(column["name"], str):
                raise ValidationError(
                    f"Each column in {self.source} must include a string 'name' field"
                )
            validated.append(column)
        return validated

    def _validate_ascii(self) -> None:
        errors: List[str] = []
        for field_name, values in (
            ("tokens", self.tokens),
            ("phrases", self.phrases),
            ("anti_tokens", self.anti_tokens),
        ):
            non_ascii = [value for value in values if not value.isascii()]
            if non_ascii:
                joined = ", ".join(sorted(non_ascii))
                errors.append(
                    f"Field '{field_name}' in {self.source} contains non-ASCII entries: {joined}"
                )
        if errors:
            raise ValidationError("\n".join(errors))

    def _validate_internal_duplicates(self) -> None:
        errors: List[str] = []
        for field_name, values in (
            ("tokens", self.tokens),
            ("phrases", self.phrases),
            ("anti_tokens", self.anti_tokens),
        ):
            duplicates = find_duplicates(values)
            if duplicates:
                dup_display = ", ".join(sorted(duplicates))
                errors.append(
                    f"Field '{field_name}' in {self.source} contains duplicates: {dup_display}"
                )
        if errors:
            raise ValidationError("\n".join(errors))

    def list_hash(self, items: Sequence[str]) -> str:
        normalized = "\n".join(sorted(items))
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def tokens_hash(self) -> str:
        return self.list_hash(self.tokens)

    def phrases_hash(self) -> str:
        return self.list_hash(self.phrases)

    def anti_tokens_hash(self) -> str:
        return self.list_hash(self.anti_tokens)

    def entity_hash(self) -> str:
        payload_items = [self.id]
        payload_items.extend(sorted(self.tokens))
        payload_items.extend(sorted(self.phrases))
        payload_items.extend(sorted(self.anti_tokens))
        payload = "\n".join(payload_items)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def find_duplicates(items: Iterable[str]) -> List[str]:
    seen: Dict[str, int] = {}
    duplicates: List[str] = []
    for item in items:
        if item in seen:
            seen[item] += 1
        else:
            seen[item] = 1
    for item, count in seen.items():
        if count > 1:
            duplicates.append(item)
    return duplicates


def _select_intent(intents: Iterable[str], fallback_id: str) -> str:
    collected = list(intents)
    if collected:
        return sorted(collected)[0]
    return fallback_id


def load_ontology_tokens() -> Dict[str, Dict[str, set]]:
    if not ONTOLOGY_PATH.exists():
        raise ValidationError(f"Ontology definition not found at {ONTOLOGY_PATH}")
    with ONTOLOGY_PATH.open("r", encoding="utf-8") as handle:
        ontology_raw = yaml.safe_load(handle) or {}
    intents = ontology_raw.get("intents", []) or []
    anti_tokens_map: Dict[str, List[str]] = ontology_raw.get("anti_tokens", {}) or {}
    ontology: Dict[str, Dict[str, set]] = {}
    for intent in intents:
        intent_name = intent.get("name")
        if not intent_name:
            continue
        if intent_name == "ticker_query":
            continue
        token_section = intent.get("tokens", {}) or {}
        phrase_section = intent.get("phrases", {}) or {}
        tokens_include = token_section.get("include", []) or []
        tokens_exclude = token_section.get("exclude", []) or []
        phrases_include = phrase_section.get("include", []) or []
        phrases_exclude = phrase_section.get("exclude", []) or []
        for entity_id in intent.get("entities", []) or []:
            entity_data = ontology.setdefault(
                entity_id,
                {
                    "intents": set(),
                    "tokens": set(),
                    "phrases": set(),
                    "anti_tokens": set(),
                },
            )
            entity_data["intents"].add(intent_name)
            entity_data["tokens"].update(tokens_include)
            entity_data["phrases"].update(phrases_include)
            entity_data["anti_tokens"].update(tokens_exclude)
            entity_data["anti_tokens"].update(phrases_exclude)

    generic_anti_tokens = set(anti_tokens_map.get("generic", []) or [])
    for entity_id, entity_data in ontology.items():
        entity_data["anti_tokens"].update(generic_anti_tokens)
        entity_data["anti_tokens"].update(anti_tokens_map.get(entity_id, []) or [])

    for entity_id, specific_anti_tokens in anti_tokens_map.items():
        if entity_id == "generic":
            continue
        if entity_id not in ontology:
            ontology[entity_id] = {
                "intents": set(),
                "tokens": set(),
                "phrases": set(),
                "anti_tokens": generic_anti_tokens.union(specific_anti_tokens or []),
            }
    return ontology


def load_entities(ontology_tokens: Mapping[str, Dict[str, set]]) -> Dict[str, OntologyEntity]:
    errors: List[str] = []
    entities: Dict[str, OntologyEntity] = {}
    for entity_dir in sorted(ENTITIES_DIR.iterdir()):
        entity_path = entity_dir / "entity.yaml"
        if not entity_path.is_file():
            continue
        try:
            with entity_path.open("r", encoding="utf-8") as handle:
                raw = yaml.safe_load(handle)
        except Exception as exc:  # pylint: disable=broad-except
            errors.append(f"Failed to load {entity_path}: {exc}")
            continue
        if not isinstance(raw, MutableMapping):
            errors.append(f"Entity file {entity_path} must contain a mapping at the root")
            continue
        entity_id = raw.get("id")
        if not isinstance(entity_id, str):
            errors.append(f"Entity file {entity_path} must include a string 'id' field")
            continue
        ontology_entry = ontology_tokens.get(entity_id, {})
        merged_raw: Dict[str, object] = dict(raw)
        merged_raw.setdefault("intent", _select_intent(ontology_entry.get("intents", set()), entity_id))
        merged_raw.setdefault("tokens", list(ontology_entry.get("tokens", set())))
        merged_raw.setdefault("phrases", list(ontology_entry.get("phrases", set())))
        merged_raw.setdefault("anti_tokens", list(ontology_entry.get("anti_tokens", set())))
        try:
            entity = OntologyEntity(merged_raw, entity_path)
        except ValidationError as exc:
            errors.append(str(exc))
            continue
        if entity.id in entities:
            errors.append(
                f"Duplicate entity id '{entity.id}' found in {entity_path} and {entities[entity.id].source}"
            )
            continue
        entities[entity.id] = entity
    if errors:
        raise ValidationError("\n".join(errors))
    return entities


def validate_collisions(entities: Mapping[str, OntologyEntity]) -> None:
    errors: List[str] = []
    for entity_id, forbidden_peers in COLLISION_RULES.items():
        if entity_id not in entities:
            continue
        for peer_id in forbidden_peers:
            if peer_id not in entities:
                continue
            overlap = set(entities[entity_id].tokens).intersection(entities[peer_id].tokens)
            if overlap:
                joined = ", ".join(sorted(overlap))
                errors.append(
                    f"Collision between '{entity_id}' and '{peer_id}' on tokens: {joined}"
                )
        if errors:
            raise ValidationError("\n".join(errors))


def build_manifest(entities: Mapping[str, OntologyEntity], timestamp: str | None = None) -> Dict:
    entity_records = []
    entity_hashes: List[str] = []
    for entity_id in sorted(entities):
        entity = entities[entity_id]
        entity_records.append(
            {
                "id": entity.id,
                "tokens": entity.tokens_hash(),
                "phrases": entity.phrases_hash(),
                "anti_tokens": entity.anti_tokens_hash(),
                "entity_hash": entity.entity_hash(),
            }
        )
        entity_hashes.append(entity.entity_hash())
    manifest_timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    global_payload = "\n".join(sorted(entity_hashes))
    return {
        "version": MANIFEST_VERSION,
        "timestamp": manifest_timestamp,
        "entity_count": len(entity_records),
        "entities": entity_records,
        "ontology_global_hash": hashlib.sha256(global_payload.encode("utf-8")).hexdigest(),
    }


def write_manifest(manifest: Mapping) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(manifest, handle, sort_keys=False)


def load_manifest_from_disk() -> Mapping:
    if not MANIFEST_PATH.exists():
        raise ValidationError(f"Manifest file not found at {MANIFEST_PATH}")
    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def run_generation(check_only: bool = False) -> None:
    ontology_tokens = load_ontology_tokens()
    entities = load_entities(ontology_tokens)
    validate_collisions(entities)
    timestamp_override = None
    if check_only:
        existing_manifest = load_manifest_from_disk()
        timestamp_override = existing_manifest.get("timestamp")
    manifest = build_manifest(entities, timestamp=timestamp_override)
    if check_only:
        if not MANIFEST_PATH.exists():
            raise ValidationError("Manifest is missing. Please generate it before running --check.")
        if existing_manifest != manifest:
            raise ValidationError(
                "Manifest on disk is outdated. Please regenerate ontology_manifest.yaml."
            )
        return
    write_manifest(manifest)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate ontology integrity and produce deterministic hashes."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate ontology and ensure existing manifest matches the expected state.",
    )
    args = parser.parse_args()
    try:
        run_generation(check_only=args.check)
    except ValidationError as exc:
        print(f"Validation failed: {exc}")
        return 1
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Unexpected error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
