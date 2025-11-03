# app/planner/planner.py
from __future__ import annotations
from typing import Dict, Any, List
import re, unicodedata
import logging
import os, json
from pathlib import Path

try:
    import yaml
except Exception:
    yaml = None

from .ontology_loader import load_ontology

# RAG: leitor de índice e hints
from app.rag.index_reader import EmbeddingStore
from app.rag.hints import entity_hints_from_rag
from app.rag.ollama_client import OllamaClient

PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
_LOG = logging.getLogger("planner.explain")

_THRESH_DEFAULTS = {
    "planner": {
        "thresholds": {
            "defaults": {"min_score": 1.0, "min_gap": 0.5},
            "intents": {},
            "entities": {},
        },
        "rag": {"enabled": False, "k": 5, "min_score": 0.20, "weight": 0.35},
    }
}


def _load_thresholds(path: str = "data/ops/planner_thresholds.yaml") -> Dict[str, Any]:
    if yaml is None:
        return _THRESH_DEFAULTS
    p = Path(path)
    if not p.exists():
        return _THRESH_DEFAULTS
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        planner = data.get("planner") or {}
        thresholds = (
            planner.get("thresholds") or _THRESH_DEFAULTS["planner"]["thresholds"]
        )
        rag = planner.get("rag") or _THRESH_DEFAULTS["planner"]["rag"]
        return {"planner": {"thresholds": thresholds, "rag": rag}}
    except Exception:
        return _THRESH_DEFAULTS


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


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

        intent_scores: Dict[str, float] = {}
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

        # --- scoring base (como já havia) ---
        for it in self.onto.intents:
            score = 0.0
            include_hits = [t for t in it.tokens_include if t in tokens or t in norm]
            exclude_hits = [t for t in it.tokens_exclude if t in tokens or t in norm]
            score += token_weight * len(include_hits)
            score -= token_weight * len(exclude_hits)

            phrase_incl_hits = [
                p for p in it.phrases_include if _phrase_present(norm, p)
            ]
            phrase_excl_hits = [
                p for p in it.phrases_exclude if _phrase_present(norm, p)
            ]
            score += phrase_weight * len(phrase_incl_hits)
            score -= phrase_weight * len(phrase_excl_hits)

            anti_penalty = 0.0
            for _, toks in (self.onto.anti_tokens or {}).items():
                if _any_in(norm, toks):
                    anti_penalty += 0.5 * token_weight
            score -= anti_penalty

            for tk in include_hits:
                token_score_items.append(
                    {"token": tk, "weight": token_weight, "hits": 1, "intent": it.name}
                )
            for tk in exclude_hits:
                token_score_items.append(
                    {"token": tk, "weight": -token_weight, "hits": 1, "intent": it.name}
                )
            for ph in phrase_incl_hits:
                phrase_score_items.append(
                    {
                        "phrase": ph,
                        "weight": phrase_weight,
                        "hits": 1,
                        "intent": it.name,
                    }
                )
            for ph in phrase_excl_hits:
                phrase_score_items.append(
                    {
                        "phrase": ph,
                        "weight": -phrase_weight,
                        "hits": 1,
                        "intent": it.name,
                    }
                )
            if anti_penalty > 0:
                anti_hits_items.append(
                    {
                        "term_group": "anti_tokens",
                        "penalty": anti_penalty,
                        "intent": it.name,
                    }
                )

            intent_scores[it.name] = score
            details[it.name] = {
                "token_includes": include_hits,
                "token_excludes": exclude_hits,
                "phrase_includes": phrase_incl_hits,
                "phrase_excludes": phrase_excl_hits,
                "anti_penalty": anti_penalty,
                "entities": it.entities,
            }

        # --- configurações RAG ---
        cfg = _load_thresholds()
        rag_cfg = (cfg.get("planner") or {}).get("rag") or {}
        rag_enabled = bool(rag_cfg.get("enabled", False))
        rag_k = int(rag_cfg.get("k", 5))
        rag_min = float(rag_cfg.get("min_score", 0.20))
        rag_w = float(rag_cfg.get("weight", 0.35))
        rag_index_path = os.getenv(
            "RAG_INDEX_PATH", "data/embeddings/store/embeddings.jsonl"
        )

        rag_results = []
        rag_entity_hints: Dict[str, float] = {}
        rag_error = None

        if rag_enabled:
            try:
                store = EmbeddingStore(rag_index_path)
                embedder = OllamaClient(
                    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                    model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
                )
                # Embedding explícito + busca vetorial (modo B)
                qvec = embedder.embed([question])[0]
                rag_results = store.search_by_vector(qvec, k=rag_k) or []
                # cutoff mínimo
                rag_results = [
                    r for r in rag_results if float(r.get("score") or 0.0) >= rag_min
                ]
                rag_entity_hints = entity_hints_from_rag(
                    rag_results
                )  # ex.: {"fiis_cadastro": 0.83, ...}
            except Exception as e:
                rag_error = repr(e)
                rag_results = []
                rag_entity_hints = {}

        # --- decisão base (mantém) ---
        chosen_intent = None
        chosen_entity = None
        chosen_score = 0.0
        if intent_scores:
            chosen_intent = max(intent_scores, key=lambda k: intent_scores[k])
            chosen_score = float(intent_scores[chosen_intent])
            for it in self.onto.intents:
                if it.name == chosen_intent:
                    chosen_entity = it.entities[0] if it.entities else None
                    break

        # --- score COMPOSTO (base + RAG) mantendo contrato ---
        combined_scores: Dict[str, Dict[str, Any]] = {}
        if intent_scores:
            for it in self.onto.intents:
                base = float(intent_scores.get(it.name, 0.0))
                ent = it.entities[0] if it.entities else None
                rag_sig = float(rag_entity_hints.get((ent or "").strip(), 0.0))
                combined = (
                    (1.0 - rag_w) * base + (rag_w) * rag_sig if rag_enabled else base
                )
                combined_scores[it.name] = {
                    "base": base,
                    "rag": rag_sig,
                    "combined": combined,
                    "entity": ent,
                }

            # escolhe pela pontuação combinada (ou base, se rag desabilitado)
            best = max(combined_scores.items(), key=lambda kv: kv[1]["combined"])
            chosen_intent = best[0]
            chosen_score = float(best[1]["combined"] or 0.0)
            chosen_entity = best[1]["entity"]

        # estágio de fusão para trilha (após definição do chosen_* acima)
        if rag_enabled:
            decision_path.append(
                {"stage": "fuse", "type": "rag_integration", "rag_weight": rag_w}
            )
        # --- top2 gap calculado sobre scores base (telemetria M6.5) ---
        ordered = sorted(intent_scores.items(), key=lambda kv: kv[1], reverse=True)
        top2_gap = 0.0
        if len(ordered) >= 2:
            top2_gap = float((ordered[0][1] or 0.0) - (ordered[1][1] or 0.0))
        elif len(ordered) == 1:
            top2_gap = float(ordered[0][1] or 0.0)

        # --- trilha de decisão ---
        decision_path.append(
            {
                "stage": "rank",
                "type": "intent_scoring",
                "intent": chosen_intent,
                "score": chosen_score,
            }
        )
        if chosen_entity:
            decision_path.append(
                {
                    "stage": "route",
                    "type": "entity_select",
                    "entity": chosen_entity,
                    "score_after": chosen_score,
                }
            )
        if rag_enabled:
            decision_path.append(
                {
                    "stage": "rag",
                    "type": "entity_hints",
                    "k": rag_k,
                    "min_score": rag_min,
                    "weight": rag_w,
                    "hints_keys": sorted(list(rag_entity_hints.keys())),
                }
            )

        # --- sumarização de pesos (como já havia) ---
        token_sum = float(sum(item["weight"] for item in token_score_items))
        phrase_sum = float(sum(item["weight"] for item in phrase_score_items))
        anti_sum = float(sum(item.get("penalty", 0.0) for item in anti_hits_items))
        weights_summary = {
            "token_sum": token_sum,
            "phrase_sum": phrase_sum,
            "anti_sum": anti_sum,
            "total": token_sum + phrase_sum - anti_sum,
        }

        # --- explain (mantém + adiciona bloco RAG e combined) ---
        meta_explain: Dict[str, Any] = {
            "signals": {
                "token_scores": token_score_items,
                "phrase_scores": phrase_score_items,
                "anti_hits": anti_hits_items,
                "normalizations": [
                    {"step": s, "applied": True} for s in self.onto.normalize
                ],
                "weights_summary": weights_summary,
            },
            "decision_path": decision_path,
            "scoring": {
                "intent": (
                    [{"name": chosen_intent, "score": chosen_score, "winner": True}]
                    if chosen_intent
                    else []
                ),
                "entity": (
                    [{"name": chosen_entity, "score": chosen_score, "winner": True}]
                    if chosen_entity
                    else []
                ),
                "intent_top2_gap": top2_gap,
            },
        }
        if rag_enabled:
            # signals.rag_hits — preview priorizando docs de entidade (visual only)
            def _hit_row(r):
                return {
                    "doc_id": r.get("doc_id"),
                    "score": float(r.get("score") or 0.0),
                    "chunk_id": r.get("chunk_id"),
                }

            _ents = [
                r for r in rag_results if str(r.get("doc_id", "")).startswith("entity-")
            ]
            _others = [
                r
                for r in rag_results
                if not str(r.get("doc_id", "")).startswith("entity-")
            ]
            _preview = (_ents + _others)[: min(len(rag_results), rag_k)]
            meta_explain["signals"]["rag_hits"] = [_hit_row(r) for r in _preview]

            meta_explain["rag"] = {
                "enabled": True,
                "index_path": rag_index_path,
                "weight": rag_w,
                "k": rag_k,
                "min_score": rag_min,
                "entity_hints": rag_entity_hints,
                "results_preview": [
                    {
                        "doc_id": r.get("doc_id"),
                        "score": float(r.get("score") or 0.0),
                        "chunk_id": r.get("chunk_id"),
                    }
                    for r in (rag_results[: min(len(rag_results), 10)])
                ],
                "error": rag_error,
            }
            # scoring.rag_hint — lista [{entity, score}]
            meta_explain["scoring"]["rag_hint"] = [
                {"entity": k, "score": v}
                for k, v in sorted(
                    rag_entity_hints.items(), key=lambda kv: kv[1], reverse=True
                )
            ]
            meta_explain["scoring"]["combined"] = {
                name: {
                    "base": vals["base"],
                    "rag": vals["rag"],
                    "combined": vals["combined"],
                    "entity": vals["entity"],
                }
                for name, vals in combined_scores.items()
            }

        # --- log estruturado leve ---
        try:
            _LOG.info(
                {
                    "planner_phase": "explain",
                    "decision_depth": len(decision_path),
                    "signal_weights": weights_summary,
                    "intent_top": chosen_intent,
                    "intent_score": float(chosen_score),
                    "entity_top": chosen_entity,
                    "rag_enabled": rag_enabled,
                }
            )
        except Exception:
            pass

        # imediatamente antes do return:
        thr = (cfg.get("planner") or {}).get("thresholds") or {}
        dfl = thr.get("defaults") or {"min_score": 1.0, "min_gap": 0.5}
        intent_thr = (thr.get("intents") or {}).get(chosen_intent or "", {})
        entity_thr = (thr.get("entities") or {}).get(chosen_entity or "", {})

        min_score = float(
            entity_thr.get("min_score", intent_thr.get("min_score", dfl["min_score"]))
        )
        min_gap = float(
            entity_thr.get("min_gap", intent_thr.get("min_gap", dfl["min_gap"]))
        )

        ordered = sorted(intent_scores.items(), key=lambda kv: kv[1], reverse=True)
        gap = float(
            (ordered[0][1] - ordered[1][1])
            if len(ordered) >= 2
            else ordered[0][1] if ordered else 0.0
        )
        accepted = (float(chosen_score) >= min_score) and (gap >= min_gap)

        meta_explain["scoring"]["thresholds_applied"] = {
            "min_score": min_score,
            "min_gap": min_gap,
            "gap": gap,
            "accepted": accepted,
        }

        return {
            "normalized": norm,
            "tokens": tokens,
            "intent_scores": intent_scores,
            "details": details,
            "chosen": {
                "intent": chosen_intent,
                "entity": chosen_entity,
                "score": chosen_score,
                # status do gate (calculado pelos thresholds)
                "accepted": accepted,
            },
            "explain": meta_explain,
        }
