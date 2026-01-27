# app/planner/ontology_loader.py

from __future__ import annotations
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Mapping, Tuple

import yaml

LOGGER = logging.getLogger(__name__)

VALID_BUCKETS = {"A", "B", "C", "D"}
ROOT = Path(__file__).resolve().parents[2]


@dataclass
class IntentDef:
    name: str
    tokens_include: List[str]
    tokens_exclude: List[str]
    phrases_include: List[str]
    phrases_exclude: List[str]
    entities: List[str]
    bucket: Optional[str] = None


@dataclass
class Ontology:
    normalize: List[str]
    token_split: str
    weights: Dict[str, float]
    intents: List[IntentDef]
    anti_tokens: Dict[str, List[str]]
    bucket_index: Dict[str, Dict[str, List[str]]]


def _get(d: Dict[str, Any], path: List[str], default=None):
    cur = d
    for p in path:
        if cur is None:
            return default
        cur = cur.get(p)
    return cur if cur is not None else default


def load_ontology(path: str) -> Ontology:
    ontology_path = Path(path)

    if not ontology_path.exists():
        LOGGER.error("Arquivo de ontologia ausente: %s", ontology_path)
        raise ValueError(f"Arquivo de ontologia ausente: {ontology_path}")

    try:
        with ontology_path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except Exception:
        LOGGER.error(
            "Erro ao carregar arquivo de ontologia: %s", ontology_path, exc_info=True
        )
        raise

    if not isinstance(raw, dict):
        LOGGER.error(
            "Arquivo de ontologia inválido (esperado mapeamento): %s", ontology_path
        )
        raise ValueError(f"Arquivo de ontologia inválido: {ontology_path}")

    # --- normalize: se existir, precisa ser lista ---
    normalize_raw = raw.get("normalize", []) or []
    if not isinstance(normalize_raw, list):
        LOGGER.error(
            "Arquivo de ontologia inválido: bloco 'normalize' deve ser lista em %s",
            ontology_path,
        )
        raise ValueError(
            f"Arquivo de ontologia inválido: bloco 'normalize' deve ser lista em {ontology_path}"
        )

    # --- intents: bloco obrigatório, lista de dicts ---
    intents_raw = raw.get("intents")
    if intents_raw is None:
        LOGGER.error(
            "Arquivo de ontologia inválido: bloco 'intents' ausente em %s",
            ontology_path,
        )
        raise ValueError(
            f"Arquivo de ontologia inválido: bloco 'intents' ausente em {ontology_path}"
        )
    if not isinstance(intents_raw, list):
        LOGGER.error(
            "Arquivo de ontologia inválido: bloco 'intents' deve ser lista em %s",
            ontology_path,
        )
        raise ValueError(
            f"Arquivo de ontologia inválido: bloco 'intents' deve ser lista em {ontology_path}"
        )

    intents_raw = raw.get("intents", [])
    if intents_raw is None:
        intents_raw = []
    if not isinstance(intents_raw, list):
        LOGGER.error(
            "Arquivo de ontologia inválido: bloco 'intents' deve ser lista em %s",
            ontology_path,
        )
        raise ValueError(f"Arquivo de ontologia inválido: {ontology_path}")

    intents: List[IntentDef] = []
    for idx, it in enumerate(intents_raw):
        if not isinstance(it, dict):
            LOGGER.error(
                "Arquivo de ontologia inválido: intent %s não é dict em %s",
                idx,
                ontology_path,
            )
            raise ValueError(f"Arquivo de ontologia inválido: {ontology_path}")

        tokens_block = it.get("tokens")
        if tokens_block is not None and not isinstance(tokens_block, dict):
            LOGGER.error(
                "Arquivo de ontologia inválido: tokens de intent %s não são dict em %s",
                idx,
                ontology_path,
            )
            raise ValueError(f"Arquivo de ontologia inválido: {ontology_path}")

        phrases_block = it.get("phrases")
        if phrases_block is not None and not isinstance(phrases_block, dict):
            LOGGER.error(
                "Arquivo de ontologia inválido: phrases de intent %s não são dict em %s",
                idx,
                ontology_path,
            )
            raise ValueError(f"Arquivo de ontologia inválido: {ontology_path}")

        entities_block = it.get("entities", [])
        if entities_block is not None and not isinstance(entities_block, list):
            LOGGER.error(
                "Arquivo de ontologia inválido: entities de intent %s não são lista em %s",
                idx,
                ontology_path,
            )
            raise ValueError(f"Arquivo de ontologia inválido: {ontology_path}")

        bucket = it.get("bucket")
        if bucket is not None:
            if isinstance(bucket, bool) or not isinstance(bucket, str):
                LOGGER.error(
                    "Arquivo de ontologia inválido: bucket de intent %s deve ser string em %s",
                    idx,
                    ontology_path,
                )
                raise ValueError(f"Arquivo de ontologia inválido: {ontology_path}")
            bucket = bucket.strip()
            if bucket and bucket not in VALID_BUCKETS:
                LOGGER.error(
                    "Bucket inválido %s em intent %s (esperado A/B/C/D) em %s",
                    bucket,
                    it.get("name"),
                    ontology_path,
                )
                raise ValueError(f"Arquivo de ontologia inválido: {ontology_path}")

        intents.append(
            IntentDef(
                name=it.get("name"),
                tokens_include=_get(it, ["tokens", "include"], []),
                tokens_exclude=_get(it, ["tokens", "exclude"], []),
                phrases_include=_get(it, ["phrases", "include"], []),
                phrases_exclude=_get(it, ["phrases", "exclude"], []),
                entities=entities_block or [],
                bucket=bucket or None,
            )
        )

    anti_tokens = raw.get("anti_tokens", {}) or {}
    if anti_tokens is not None and not isinstance(anti_tokens, dict):
        LOGGER.error(
            "Arquivo de ontologia inválido: anti_tokens deve ser dict em %s",
            ontology_path,
        )
        raise ValueError(f"Arquivo de ontologia inválido: {ontology_path}")

    # --- tokenization: bloco obrigatório + split obrigatório ---
    tokenization = raw.get("tokenization")
    if not isinstance(tokenization, dict):
        LOGGER.error(
            "Arquivo de ontologia inválido: tokenization deve ser dict em %s",
            ontology_path,
        )
        raise ValueError(
            f"Arquivo de ontologia inválido: tokenization deve ser dict em {ontology_path}"
        )

    token_split = tokenization.get("split")
    if not isinstance(token_split, str) or not token_split.strip():
        LOGGER.error(
            "Arquivo de ontologia inválido: tokenization.split deve ser string não vazia em %s",
            ontology_path,
        )
        raise ValueError(
            f"Arquivo de ontologia inválido: tokenization.split deve ser string não vazia em {ontology_path}"
        )

    # --- weights: bloco obrigatório, com campos numéricos ---
    weights_raw = raw.get("weights")
    if not isinstance(weights_raw, dict):
        LOGGER.error(
            "Arquivo de ontologia inválido: bloco 'weights' deve ser dict em %s",
            ontology_path,
        )
        raise ValueError(
            f"Arquivo de ontologia inválido: bloco 'weights' deve ser dict em {ontology_path}"
        )

    weights: Dict[str, float] = {}
    for key in ("token", "phrase"):
        val = weights_raw.get(key)
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            LOGGER.error(
                "Arquivo de ontologia inválido: weights.%s deve ser numérico em %s",
                key,
                ontology_path,
            )
            raise ValueError(
                f"Arquivo de ontologia inválido: weights.{key} deve ser numérico em {ontology_path}"
            )
        if float(val) < 0:
            LOGGER.error(
                "Arquivo de ontologia inválido: weights.%s não pode ser negativo em %s",
                key,
                ontology_path,
            )
            raise ValueError(
                f"Arquivo de ontologia inválido: weights.{key} não pode ser negativo em {ontology_path}"
            )
        weights[key] = float(val)

    bucket_index = _build_bucket_index(intents)

    return Ontology(
        normalize=normalize_raw,
        token_split=token_split,
        weights=weights,
        intents=intents,
        anti_tokens=anti_tokens,
        bucket_index=bucket_index,
    )


def _entity_yaml_path(entity: str) -> Path:
    return ROOT / "data" / "entities" / entity / f"{entity}.yaml"


def _catalog_path() -> Path:
    return ROOT / "data" / "entities" / "catalog.yaml"


def _load_yaml(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _load_catalog_entities() -> Dict[str, Path]:
    catalog_path = _catalog_path()
    if not catalog_path.exists():
        raise ValueError(f"Catálogo de entidades ausente: {catalog_path}")
    catalog = _load_yaml(catalog_path)
    entities_cfg = catalog.get("entities")
    if not isinstance(entities_cfg, dict):
        raise ValueError(f"Catálogo inválido (entities ausente): {catalog_path}")
    entity_paths: Dict[str, Path] = {}
    for entity_name, entry in entities_cfg.items():
        if not isinstance(entry, dict):
            continue
        paths = entry.get("paths") or {}
        if not isinstance(paths, dict):
            continue
        entity_yaml = paths.get("entity_yaml")
        if not entity_yaml:
            raise ValueError(
                f"Entity YAML ausente no catálogo para {entity_name}: {catalog_path}"
            )
        entity_path = ROOT / entity_yaml
        if not entity_path.exists():
            raise ValueError(f"Entity YAML ausente: {entity_path}")
        entity_paths[str(entity_name)] = entity_path
    return entity_paths


def _build_bucket_index(intents: List[IntentDef]) -> Dict[str, Dict[str, List[str]]]:
    bucket_index: Dict[str, Dict[str, List[str]]] = {
        bucket: {"intents": [], "entities": []} for bucket in sorted(VALID_BUCKETS)
    }
    entity_paths = _load_catalog_entities()
    entity_bucket_map: Dict[str, str] = {}

    for entity_name, entity_path in entity_paths.items():
        entity_cfg = _load_yaml(entity_path)
        bucket = entity_cfg.get("bucket")
        if bucket is None:
            continue
        if isinstance(bucket, bool) or not isinstance(bucket, str):
            raise ValueError(
                f"Bucket inválido em {entity_path}: deve ser string A/B/C/D"
            )
        bucket = bucket.strip()
        if bucket and bucket not in VALID_BUCKETS:
            raise ValueError(f"Bucket inválido em {entity_path}: {bucket}")
        if not bucket:
            continue
        prev = entity_bucket_map.get(entity_name)
        if prev and prev != bucket:
            raise ValueError(
                f"Bucket duplicado para entity {entity_name}: {prev} vs {bucket}"
            )
        entity_bucket_map[entity_name] = bucket
        bucket_index[bucket]["entities"].append(entity_name)

    for intent in intents:
        intent_bucket = intent.bucket or ""
        intent_entity_names: List[str] = []
        for entity in intent.entities or []:
            if not isinstance(entity, str) or not entity.strip():
                continue
            entity_name = entity.strip()
            if entity_name not in entity_paths:
                raise ValueError(
                    f"Entity referenciada em intent ausente no catálogo: {entity_name}"
                )
            intent_entity_names.append(entity_name)
        entity_buckets = {
            entity_bucket_map.get(entity_name)
            for entity_name in intent_entity_names
            if entity_bucket_map.get(entity_name)
        }

        if intent_bucket:
            if any(b for b in entity_buckets if b and b != intent_bucket):
                raise ValueError(
                    f"Intent {intent.name} bucket={intent_bucket} conflita com buckets de entidades {sorted(entity_buckets)}"
                )
        else:
            entity_buckets = {b for b in entity_buckets if b}
            if len(entity_buckets) > 1:
                raise ValueError(
                    f"Intent {intent.name} possui entidades em buckets múltiplos: {sorted(entity_buckets)}"
                )
            if len(entity_buckets) == 1:
                intent_bucket = next(iter(entity_buckets))

        if intent_bucket:
            bucket_index[intent_bucket]["intents"].append(intent.name)

    for bucket in bucket_index.values():
        bucket["intents"] = sorted(set(bucket["intents"]))
        bucket["entities"] = sorted(set(bucket["entities"]))

    return bucket_index
