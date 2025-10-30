from __future__ import annotations
from typing import Dict, Any, List
import re, unicodedata
from .ontology_loader import load_ontology

def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def _normalize(text: str, steps: List[str]) -> str:
    out = text
    for step in steps:
        if step == "lower":
            out = out.lower()
        elif step == "strip_accents":
            out = _strip_accents(out)
    return out

def _tokenize(text: str, split_pat: str) -> List[str]:
    parts = re.split(split_pat, text)
    return [p for p in parts if p and not p.isspace()]

def _phrase_present(text: str, phrase: str) -> bool:
    return phrase in text

def _any_in(text: str, candidates: List[str]) -> bool:
    return any(c for c in candidates if c and c in text)

class Planner:
    def __init__(self, ontology_path: str):
        self.ontology_path = ontology_path
        self.onto = load_ontology(ontology_path)

    def reload(self):
        self.onto = load_ontology(self.ontology_path)

    def explain(self, question: str):
        norm = _normalize(question, self.onto.normalize)
        tokens = _tokenize(norm, self.onto.token_split)

        token_weight = float(self.onto.weights.get("token", 1.0))
        phrase_weight = float(self.onto.weights.get("phrase", 2.0))

        intent_scores = {}
        details = {}

        for it in self.onto.intents:
            score = 0.0
            include_hits = [t for t in it.tokens_include if t in tokens or t in norm]
            exclude_hits = [t for t in it.tokens_exclude if t in tokens or t in norm]
            score += token_weight * len(include_hits)
            score -= token_weight * len(exclude_hits)

            phrase_incl_hits = [p for p in it.phrases_include if _phrase_present(norm, p)]
            phrase_excl_hits = [p for p in it.phrases_exclude if _phrase_present(norm, p)]
            score += phrase_weight * len(phrase_incl_hits)
            score -= phrase_weight * len(phrase_excl_hits)

            anti_penalty = 0.0
            for _, toks in (self.onto.anti_tokens or {}).items():
                if _any_in(norm, toks):
                    anti_penalty += 0.5 * token_weight
            score -= anti_penalty

            intent_scores[it.name] = score
            details[it.name] = {
                "token_includes": include_hits,
                "token_excludes": exclude_hits,
                "phrase_includes": phrase_incl_hits,
                "phrase_excludes": phrase_excl_hits,
                "anti_penalty": anti_penalty,
                "entities": it.entities,
            }

        chosen_intent = None
        chosen_entity = None
        chosen_score = 0.0
        if intent_scores:
            chosen_intent = max(intent_scores, key=lambda k: intent_scores[k])
            chosen_score = intent_scores[chosen_intent]
            # escolhe a 1ª entidade dessa intenção (YAML decide)
            for it in self.onto.intents:
                if it.name == chosen_intent:
                    chosen_entity = it.entities[0] if it.entities else None
                    break

        return {
            "normalized": norm,
            "tokens": tokens,
            "intent_scores": intent_scores,
            "details": details,
            "chosen": {
                "intent": chosen_intent,
                "entity": chosen_entity,
                "score": chosen_score,
            },
        }
