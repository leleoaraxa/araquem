#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build deterministic concepts_catalog records from data/concepts/*.yaml."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "data" / "concepts" / "catalog.yaml"
DEFAULT_JSONL = (
    REPO_ROOT
    / "data"
    / "entities"
    / "concepts_catalog"
    / "concepts_catalog.jsonl"
)
DEFAULT_CSV = (
    REPO_ROOT / "data" / "entities" / "concepts_catalog" / "concepts_catalog.csv"
)
DEFAULT_MD = (
    REPO_ROOT
    / "data"
    / "entities"
    / "concepts_catalog"
    / "concepts_catalog_embeddings.md"
)

SCHEMA_COLUMNS = [
    "concept_id",
    "domain",
    "section",
    "concept_type",
    "name",
    "description",
    "aliases",
    "details_md",
    "details_json",
    "source_file",
    "source_path",
    "version",
]


@dataclass(frozen=True)
class CatalogEntry:
    path: Path
    domain: str


def _slugify(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    normalized = unicodedata.normalize("NFKD", raw)
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    lowered = stripped.lower()
    spaced = re.sub(r"\s+", "_", lowered)
    cleaned = re.sub(r"[^a-z0-9_]", "", spaced)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned


def _require_non_empty_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} ausente ou vazio.")
    return value.strip()


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo YAML não encontrado: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Esperado YAML dict em {path}")
    return payload


def _load_build_id() -> str:
    build_id = os.getenv("BUILD_ID")
    if not build_id:
        raise RuntimeError("BUILD_ID ausente (version não pode ser hardcoded).")
    return build_id.strip()


def _parse_catalog(path: Path) -> List[CatalogEntry]:
    data = _load_yaml(path)
    items = data.get("concepts")
    if not isinstance(items, list) or not items:
        raise ValueError("catalog.yaml inválido: 'concepts' ausente ou vazio.")
    seen: set[str] = set()
    entries: List[CatalogEntry] = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"catalog.yaml: entrada {idx} inválida (esperado dict).")
        file_path = item.get("file")
        domain = item.get("domain")
        if not isinstance(file_path, str) or not file_path.strip():
            raise ValueError(f"catalog.yaml: 'file' ausente na entrada {idx}.")
        if not isinstance(domain, str) or not domain.strip():
            raise ValueError(f"catalog.yaml: 'domain' ausente na entrada {idx}.")
        file_path = file_path.strip()
        domain = domain.strip()
        if not _slugify(domain):
            raise ValueError(
                f"catalog.yaml: domain inválido para slugify na entrada {idx}."
            )
        if file_path in seen:
            raise ValueError(f"catalog.yaml: arquivo duplicado: {file_path}")
        seen.add(file_path)
        entries.append(
            CatalogEntry(
                path=REPO_ROOT / file_path,
                domain=domain,
            )
        )
    concepts_dir = path.parent
    expected = {REPO_ROOT / item for item in seen}
    actual = {
        p
        for p in concepts_dir.glob("*.yaml")
        if p.is_file() and p.name != "catalog.yaml"
    }
    extra_files = sorted(str(p.relative_to(REPO_ROOT)) for p in actual - expected)
    if extra_files:
        raise ValueError(
            "Arquivos não listados em catalog.yaml: " + ", ".join(extra_files)
        )
    return entries


def _normalize_aliases(aliases: Any) -> List[Any]:
    if aliases is None:
        return []
    if not isinstance(aliases, list):
        raise ValueError("aliases presente e não-array.")
    for idx, item in enumerate(aliases):
        if not isinstance(item, str):
            raise ValueError(f"aliases[{idx}] inválido (esperado string).")
    return list(aliases)


def _build_concept_id(domain: str, section: Optional[str], name: str) -> str:
    domain_part = _slugify(domain)
    if not domain_part:
        raise ValueError("domain inválido para slugify.")
    name_part = _slugify(name)
    if not name_part:
        raise ValueError("name inválido para slugify.")
    if section and section.strip():
        section_part = _slugify(section)
        if not section_part:
            raise ValueError("section inválida para slugify.")
        return f"{domain_part}.{section_part}.{name_part}"
    return f"{domain_part}.{name_part}"


def _iter_terms(
    items: List[Any],
    list_key: str,
    domain: str,
    source_file: str,
    version: str,
) -> Iterator[Dict[str, Any]]:
    for idx, entry in enumerate(items):
        if not isinstance(entry, dict):
            raise ValueError(f"{source_file}:{list_key}[{idx}] inválido (dict esperado).")
        name = _require_non_empty_str(entry.get("name"), "name")
        description = entry.get("description")
        if description is not None and not isinstance(description, str):
            raise ValueError(f"{source_file}:{list_key}[{idx}].description inválida.")
        aliases = _normalize_aliases(entry.get("aliases"))
        section = entry.get("section")
        if section is not None and not isinstance(section, str):
            raise ValueError(f"{source_file}:{list_key}[{idx}].section inválida.")
        details_md = entry.get("details_md")
        if details_md is not None and not isinstance(details_md, str):
            raise ValueError(f"{source_file}:{list_key}[{idx}].details_md inválido.")
        extras = {
            key: value
            for key, value in entry.items()
            if key not in {"name", "description", "aliases", "section", "details_md"}
        }
        details_json = extras or None
        source_path = f"{list_key}[{idx}]"
        yield {
            "concept_id": _build_concept_id(domain, section, name),
            "domain": domain,
            "section": section.strip() if isinstance(section, str) and section.strip() else None,
            "concept_type": "concept",
            "name": name,
            "description": description.strip() if isinstance(description, str) else None,
            "aliases": aliases,
            "details_md": details_md.strip() if isinstance(details_md, str) else None,
            "details_json": details_json,
            "source_file": source_file,
            "source_path": source_path,
            "version": version,
        }


def _iter_section_concepts(
    concepts: Any,
    base_path: str,
    source_file: str,
) -> Iterator[Tuple[str, str, str]]:
    if isinstance(concepts, dict):
        for key, value in concepts.items():
            if isinstance(value, str):
                yield key, value, f"{base_path}.{key}"
            elif isinstance(value, list):
                if all(isinstance(item, str) for item in value):
                    for idx, item in enumerate(value):
                        yield (
                            key,
                            item,
                            f"{base_path}.{key}[{idx}]",
                        )
                elif all(isinstance(item, dict) and len(item) == 1 for item in value):
                    for idx, item in enumerate(value):
                        field_name, description = next(iter(item.items()))
                        if not isinstance(description, str):
                            raise ValueError(
                                f"{source_file}:{base_path}.{key}[{idx}].{field_name} não é string."
                            )
                        yield (
                            field_name,
                            description,
                            f"{base_path}.{key}[{idx}].{field_name}",
                        )
                else:
                    raise ValueError(
                        f"{source_file}:{base_path}.{key} inválido (lista com tipos mistos)."
                    )
            else:
                raise ValueError(
                    f"{source_file}:{base_path}.{key} inválido (esperado string ou list)."
                )
    elif isinstance(concepts, list):
        for idx, item in enumerate(concepts):
            if not isinstance(item, dict) or len(item) != 1:
                raise ValueError(
                    f"{source_file}:{base_path}[{idx}] inválido (dict 1 chave esperado)."
                )
            field_name, description = next(iter(item.items()))
            if not isinstance(description, str):
                raise ValueError(
                    f"{source_file}:{base_path}[{idx}].{field_name} não é string."
                )
            yield field_name, description, f"{base_path}[{idx}].{field_name}"
    else:
        raise ValueError(f"{source_file}:{base_path} inválido (dict/list esperado).")


def _iter_sections(
    sections: Dict[str, Any],
    domain: str,
    source_file: str,
    version: str,
) -> Iterator[Dict[str, Any]]:
    for section_key, section_payload in sections.items():
        if not isinstance(section_payload, dict):
            raise ValueError(
                f"{source_file}:sections.{section_key} inválido (dict esperado)."
            )
        if "concepts" not in section_payload:
            raise ValueError(
                f"{source_file}:sections.{section_key}.concepts ausente."
            )
        concepts = section_payload.get("concepts")
        base_path = f"sections.{section_key}.concepts"
        for field_name, description, source_path in _iter_section_concepts(
            concepts, base_path, source_file
        ):
            name = _require_non_empty_str(field_name, "name")
            section = _require_non_empty_str(section_key, "section")
            yield {
                "concept_id": _build_concept_id(domain, section, name),
                "domain": domain,
                "section": section,
                "concept_type": "field",
                "name": name,
                "description": description.strip(),
                "aliases": [],
                "details_md": None,
                "details_json": None,
                "source_file": source_file,
                "source_path": source_path,
                "version": version,
            }


def _extract_long_text(payload: Dict[str, Any]) -> Optional[str]:
    direct_keys = ["details_md", "details", "long_text", "abordagem_geral"]
    for key in direct_keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    methodology = payload.get("methodology")
    if isinstance(methodology, str) and methodology.strip():
        return methodology.strip()
    if isinstance(methodology, dict):
        proposito = methodology.get("proposito")
        if isinstance(proposito, str) and proposito.strip():
            return proposito.strip()
    return None


def _extract_summary(payload: Dict[str, Any]) -> Optional[str]:
    for key in ["summary", "resumo", "abstract"]:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _iter_methodology(
    payload: Dict[str, Any],
    domain: str,
    source_file: str,
    version: str,
) -> Iterator[Dict[str, Any]]:
    name = payload.get("title") or payload.get("name") or "methodology"
    name = _require_non_empty_str(name, "name")
    details_md = _extract_long_text(payload)
    description = _extract_summary(payload)
    yield {
        "concept_id": _build_concept_id(domain, None, name),
        "domain": domain,
        "section": None,
        "concept_type": "methodology",
        "name": name,
        "description": description,
        "aliases": [],
        "details_md": details_md,
        "details_json": payload,
        "source_file": source_file,
        "source_path": "root",
        "version": version,
    }


def _validate_row(row: Dict[str, Any]) -> None:
    for field in SCHEMA_COLUMNS:
        if field not in row:
            raise ValueError(f"Campo ausente: {field}")
    if not row.get("source_file"):
        raise ValueError("source_file ausente.")
    if not row.get("source_path"):
        raise ValueError("source_path ausente.")
    if not row.get("name"):
        raise ValueError("name ausente ou vazio.")
    aliases = row.get("aliases")
    if not isinstance(aliases, list):
        raise ValueError("aliases presente e não-array.")


def _serialize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {key: row.get(key) for key in SCHEMA_COLUMNS}


def _write_jsonl(rows: Iterable[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def _write_csv(rows: Iterable[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCHEMA_COLUMNS)
        writer.writeheader()
        for row in rows:
            record: Dict[str, Any] = {}
            for field in SCHEMA_COLUMNS:
                value = row.get(field)
                if isinstance(value, (dict, list)):
                    record[field] = json.dumps(value, ensure_ascii=False, sort_keys=True)
                elif value is None:
                    record[field] = ""
                else:
                    record[field] = value
            writer.writerow(record)


def _clean_text(value: Optional[Any]) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("Valor não-string fornecido para serialização textual.")
    return re.sub(r"\s+", " ", value).strip()


def _format_aliases(aliases: Any) -> str:
    if not aliases:
        return ""
    if not isinstance(aliases, list):
        raise ValueError("aliases presente e não-array.")
    for item in aliases:
        if not isinstance(item, str):
            raise ValueError("aliases contém item não-string.")
    return "; ".join(_clean_text(item) for item in aliases if item.strip())


def _write_md(rows: Iterable[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for idx, row in enumerate(rows):
            if idx:
                handle.write("\n")
            handle.write(f"concept_id: {_clean_text(row.get('concept_id'))}\n")
            handle.write(f"domain: {_clean_text(row.get('domain'))}\n")
            handle.write(f"section: {_clean_text(row.get('section'))}\n")
            handle.write(f"concept_type: {_clean_text(row.get('concept_type'))}\n")
            handle.write(f"name: {_clean_text(row.get('name'))}\n")
            handle.write(f"description: {_clean_text(row.get('description'))}\n")
            handle.write(f"aliases: {_format_aliases(row.get('aliases'))}\n")
            handle.write(f"details_md: {_clean_text(row.get('details_md'))}\n")
            source_file = _clean_text(row.get("source_file"))
            source_path = _clean_text(row.get("source_path"))
            handle.write(f"source_file: {source_file}\n")
            handle.write(f"source_path: {source_path}\n")
            handle.write(f"version: {_clean_text(row.get('version'))}\n")


def build_catalog(
    catalog_entries: List[CatalogEntry],
    version: str,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for entry in catalog_entries:
        payload = _load_yaml(entry.path)
        source_file = str(entry.path.relative_to(REPO_ROOT).as_posix())
        if source_file.endswith("-methodology.yaml"):
            rows.extend(
                _iter_methodology(payload, entry.domain, source_file, version)
            )
            continue
        has_terms = "terms" in payload
        has_concepts = "concepts" in payload
        has_sections = "sections" in payload
        if has_sections and (has_terms or has_concepts):
            raise ValueError(
                f"{source_file}: padrões conflitantes ('sections' e lista)."
            )
        if has_sections:
            sections = payload.get("sections")
            if not isinstance(sections, dict):
                raise ValueError(f"{source_file}: sections inválido (dict esperado).")
            rows.extend(_iter_sections(sections, entry.domain, source_file, version))
        elif has_terms or has_concepts:
            list_key = "terms" if has_terms else "concepts"
            items = payload.get(list_key)
            if not isinstance(items, list):
                raise ValueError(
                    f"{source_file}: {list_key} inválido (list esperado)."
                )
            rows.extend(_iter_terms(items, list_key, entry.domain, source_file, version))
        else:
            raise ValueError(f"{source_file}: padrão não suportado.")
    return rows


def _sort_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def _key(row: Dict[str, Any]) -> Tuple[str, str, str, str, str]:
        return (
            row.get("domain") or "",
            row.get("section") or "",
            row.get("concept_type") or "",
            row.get("name") or "",
            row.get("concept_id") or "",
        )

    return sorted(rows, key=_key)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build deterministic concepts_catalog artifacts."
    )
    parser.add_argument("--catalog", default=str(CATALOG_PATH))
    parser.add_argument("--out-jsonl", default=str(DEFAULT_JSONL))
    parser.add_argument("--out-csv", default=str(DEFAULT_CSV))
    parser.add_argument("--out-md", default=str(DEFAULT_MD))
    args = parser.parse_args()

    version = _load_build_id()
    catalog_entries = _parse_catalog(Path(args.catalog))
    rows = _sort_rows(build_catalog(catalog_entries, version))

    seen: set[Tuple[str, str]] = set()
    for row in rows:
        _validate_row(row)
        pair = (row["concept_id"], row["version"])
        if pair in seen:
            raise ValueError(f"Duplicidade de (concept_id, version): {pair}")
        seen.add(pair)

    serialized = [_serialize_row(r) for r in rows]
    _write_jsonl(serialized, Path(args.out_jsonl))
    _write_csv(serialized, Path(args.out_csv))
    _write_md(serialized, Path(args.out_md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
