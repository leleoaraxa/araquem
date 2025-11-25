# app/planner/ontology_loader.py

from __future__ import annotations
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any

import yaml

LOGGER = logging.getLogger(__name__)

@dataclass
class IntentDef:
    name: str
    tokens_include: List[str]
    tokens_exclude: List[str]
    phrases_include: List[str]
    phrases_exclude: List[str]
    entities: List[str]

@dataclass
class Ontology:
    normalize: List[str]
    token_split: str
    weights: Dict[str, float]
    intents: List[IntentDef]
    anti_tokens: Dict[str, List[str]]

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

        intents.append(
            IntentDef(
                name=it.get("name"),
                tokens_include=_get(it, ["tokens", "include"], []),
                tokens_exclude=_get(it, ["tokens", "exclude"], []),
                phrases_include=_get(it, ["phrases", "include"], []),
                phrases_exclude=_get(it, ["phrases", "exclude"], []),
                entities=entities_block or [],
            )
        )

    anti_tokens = raw.get("anti_tokens", {}) or {}
    if anti_tokens is not None and not isinstance(anti_tokens, dict):
        LOGGER.error(
            "Arquivo de ontologia inválido: anti_tokens deve ser dict em %s", ontology_path
        )
        raise ValueError(f"Arquivo de ontologia inválido: {ontology_path}")

    tokenization = raw.get("tokenization")
    if tokenization is not None and not isinstance(tokenization, dict):
        LOGGER.error(
            "Arquivo de ontologia inválido: tokenization deve ser dict em %s",
            ontology_path,
        )
        raise ValueError(f"Arquivo de ontologia inválido: {ontology_path}")

    return Ontology(
        normalize=raw.get("normalize", []),
        token_split=_get(raw, ["tokenization", "split"], r"\b"),
        weights=raw.get("weights", {"token": 1.0, "phrase": 2.0}),
        intents=intents,
        anti_tokens=anti_tokens,
    )
