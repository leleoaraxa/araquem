# app/planner/ontology_loader.py

from __future__ import annotations
import yaml
from dataclasses import dataclass
from typing import List, Dict, Any

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
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    intents: List[IntentDef] = []
    for it in raw.get("intents", []):
        intents.append(
            IntentDef(
                name=it.get("name"),
                tokens_include=_get(it, ["tokens","include"], []),
                tokens_exclude=_get(it, ["tokens","exclude"], []),
                phrases_include=_get(it, ["phrases","include"], []),
                phrases_exclude=_get(it, ["phrases","exclude"], []),
                entities=it.get("entities", []),
            )
        )
    anti = raw.get("anti_tokens", {}) or {}
    return Ontology(
        normalize=raw.get("normalize", []),
        token_split=_get(raw, ["tokenization","split"], r"\b"),
        weights=raw.get("weights", {"token":1.0, "phrase":2.0}),
        intents=intents,
        anti_tokens=anti,
    )
