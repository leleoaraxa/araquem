# app/planner/planner.py

from __future__ import annotations
from typing import Dict, Any, List
import re, unicodedata
import logging

from .ontology_loader import load_ontology

PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
_LOG = logging.getLogger("planner.explain")

def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def _normalize(text: str, steps: List[str]) -> str:
    out = text
    for step in steps:
        if step == "lower":
            out = out.lower()
        elif step == "strip_accents":
            out = _strip_accents(out)
        elif step == "strip_punct":
            out = PUNCT_RE.sub(" ", out)
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
        decision_path: List[Dict[str, Any]] = [
            {
                "stage": "tokenize",
                "type": "normalization",
                "value": norm,
                "result": tokens[:],
            }
        ]
        token_score_items: List[Dict[str, Any]] = []
        phrase_score_items: List[Dict[str, Any]] = []
        anti_hits_items: List[Dict[str, Any]] = []


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

            # construir sinais (por intenção avaliada)
            for tk in include_hits:
                token_score_items.append({"token": tk, "weight": token_weight, "hits": 1, "intent": it.name})
            for tk in exclude_hits:
                token_score_items.append({"token": tk, "weight": -token_weight, "hits": 1, "intent": it.name})
            for ph in phrase_incl_hits:
                phrase_score_items.append({"phrase": ph, "weight": phrase_weight, "hits": 1, "intent": it.name})
            for ph in phrase_excl_hits:
                phrase_score_items.append({"phrase": ph, "weight": -phrase_weight, "hits": 1, "intent": it.name})
            if anti_penalty > 0:
                anti_hits_items.append({"term_group": "anti_tokens", "penalty": anti_penalty, "intent": it.name})

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

        # stages finais na trilha de decisão
        decision_path.append({
            "stage": "rank",
            "type": "intent_scoring",
            "intent": chosen_intent,
            "score": chosen_score
        })
        if chosen_entity:
            decision_path.append({
                "stage": "route",
                "type": "entity_select",
                "entity": chosen_entity,
                "score_after": chosen_score
            })

        # sumarização de pesos (apenas agregação — sem heurística)
        token_sum = float(sum(item["weight"] for item in token_score_items))
        phrase_sum = float(sum(item["weight"] for item in phrase_score_items))
        anti_sum = float(sum(item.get("penalty", 0.0) for item in anti_hits_items))
        weights_summary = {
            "token_sum": token_sum,
            "phrase_sum": phrase_sum,
            "anti_sum": anti_sum,
            "total": token_sum + phrase_sum - anti_sum
        }

        meta_explain = {
            "signals": {
                "token_scores": token_score_items,
                "phrase_scores": phrase_score_items,
                "anti_hits": anti_hits_items,
                "normalizations": [
                    {"step": s, "applied": True} for s in self.onto.normalize
                ],
                "weights_summary": weights_summary
            },
            "decision_path": decision_path,
            "scoring": {
                "intent": [{"name": chosen_intent, "score": chosen_score, "winner": True}] if chosen_intent else [],
                "entity": [{"name": chosen_entity, "score": chosen_score, "winner": True}] if chosen_entity else [],
            }
        }

        # log estruturado (JSON) – leve; sem dados sensíveis
        try:
            _LOG.info({
                "planner_phase": "explain",
                "decision_depth": len(decision_path),
                "signal_weights": weights_summary,
                "intent_top": chosen_intent,
                "intent_score": float(chosen_score),
                "entity_top": chosen_entity
            })
        except Exception:
            pass

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
            # bloco hierárquico para M6.4
            "explain": meta_explain,
        }
