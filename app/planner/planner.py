# app/planner/planner.py
from __future__ import annotations
from typing import Dict, Any, List
import re, unicodedata
import logging
import os
import time

from .ontology_loader import load_ontology

# RAG: leitor de índice e hints
from app.rag.hints import entity_hints_from_rag
from app.rag.ollama_client import OllamaClient
from app.utils.filecache import cached_embedding_store, load_yaml_cached
from app.observability.instrumentation import counter, histogram

PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
_LOG = logging.getLogger("planner.explain")

_THRESH_DEFAULTS = {
    "planner": {
        "thresholds": {
            "defaults": {"min_score": 1.0, "min_gap": 0.5},
            "intents": {},
            "entities": {},
            "apply_on": "base",
        },
        "rag": {
            "enabled": False,
            "k": 5,
            "min_score": 0.20,
            "weight": 0.35,
            "re_rank": {"enabled": False, "mode": "blend", "weight": 0.25},
        },
    }
}


def _load_thresholds(path: str = "data/ops/planner_thresholds.yaml") -> Dict[str, Any]:
    try:
        data = load_yaml_cached(path) or {}
        planner = data.get("planner") or {}
        thresholds = planner.get("thresholds") or dict(
            _THRESH_DEFAULTS["planner"]["thresholds"]
        )
        rag = planner.get("rag") or dict(_THRESH_DEFAULTS["planner"]["rag"])
        # Garantir chaves novas (defaults se ausentes)
        if "apply_on" not in thresholds:
            thresholds["apply_on"] = _THRESH_DEFAULTS["planner"]["thresholds"][
                "apply_on"
            ]
        if "re_rank" not in rag:
            rag["re_rank"] = dict(_THRESH_DEFAULTS["planner"]["rag"]["re_rank"])
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
        rag_cfg = _THRESH_DEFAULTS.get("planner", {}).get("rag") or {}
        cfg = _load_thresholds()
        planner_cfg = cfg.get("planner") or {}
        rag_cfg = planner_cfg.get("rag") or rag_cfg
        thresholds_cfg = planner_cfg.get("thresholds") or {}
        rag_enabled = bool(rag_cfg.get("enabled", False))
        rag_k = int(rag_cfg.get("k", 5))
        rag_min_score = float(rag_cfg.get("min_score", 0.20))
        rag_weight = float(
            rag_cfg.get("weight", 0.30)
        )  # só informativo quando re_rank desliga
        rag_index_path = os.getenv(
            "RAG_INDEX_PATH", "data/embeddings/store/embeddings.jsonl"
        )
        # Re-rank (Preparação M7.4 — desligado por padrão)
        re_rank_cfg = rag_cfg.get("re_rank") or {}
        re_rank_enabled = bool(re_rank_cfg.get("enabled", False))
        re_rank_mode = str(re_rank_cfg.get("mode", "blend"))
        re_rank_weight = float(re_rank_cfg.get("weight", 0.25))
        thr_apply_on = str(thresholds_cfg.get("apply_on", "base"))

        rag_entity_hints: Dict[str, float] = {}
        rag_error: Any = None
        rag_used = False
        rag_raw_results: List[Dict[str, Any]] = []
        rag_hits_count = 0
        rag_t0 = None

        if rag_enabled:
            from app.observability.metrics import emit_counter

            try:
                rag_t0 = time.perf_counter()
                store = cached_embedding_store(rag_index_path)
                embedder = OllamaClient()
                qvec = embedder.embed([question])[0]
                results = (
                    store.search_by_vector(qvec, k=rag_k, min_score=rag_min_score) or []
                )
                rag_raw_results = results
                rag_hits_count = len(results) if results else 0
                from app.rag.hints import entity_hints_from_rag

                rag_entity_hints = entity_hints_from_rag(results)
                rag_used = bool(rag_entity_hints)
                try:
                    emit_counter(
                        "sirios_rag_search_total",
                        outcome=("used" if rag_used else "skipped"),
                    )
                except Exception:
                    pass
            except Exception as e:
                rag_error = str(e)
                rag_entity_hints = {}
                rag_used = False
                try:
                    emit_counter("sirios_rag_search_total", outcome="error")
                except Exception:
                    pass

        # --- fusão linear base + RAG (apenas se hints disponíveis) ---
        combined_intents: List[Dict[str, Any]] = []
        entity_base_scores: Dict[str, float] = {}
        entity_combined_scores: Dict[str, float] = {}
        entity_rag_scores: Dict[str, float] = {}
        fused_scores: Dict[str, float] = {}
        intent_rag_signals: Dict[str, float] = {}
        intent_entities: Dict[str, Any] = {}

        # Fusão linear: prioriza peso do re_rank se habilitado; caso contrário usa peso do RAG
        fusion_weight = re_rank_weight if re_rank_enabled else rag_weight
        rag_fusion_applied = bool(rag_enabled and rag_used and (fusion_weight > 0.0))
        effective_weight = fusion_weight if rag_fusion_applied else 0.0

        for it in self.onto.intents:
            base = float(intent_scores.get(it.name, 0.0))
            entity_name = it.entities[0] if it.entities else None
            intent_entities[it.name] = entity_name

            rag_signal = (
                float(rag_entity_hints.get((entity_name or "").strip(), 0.0))
                if entity_name
                else 0.0
            )
            intent_rag_signals[it.name] = rag_signal

            if rag_fusion_applied:
                if re_rank_mode == "additive":
                    final_score = base + fusion_weight * rag_signal
                else:
                    final_score = (
                        base * (1.0 - fusion_weight) + rag_signal * fusion_weight
                    )
            else:
                final_score = base

            fused_scores[it.name] = final_score
            combined_intents.append(
                {
                    "name": it.name,
                    "base": base,
                    "rag": rag_signal if rag_fusion_applied else 0.0,
                    "combined": final_score,
                    "winner": False,
                }
            )

            if entity_name:
                prev_base = entity_base_scores.get(entity_name)
                if prev_base is None or base > prev_base:
                    entity_base_scores[entity_name] = base
                prev_combined = entity_combined_scores.get(entity_name)
                if prev_combined is None or final_score > prev_combined:
                    entity_combined_scores[entity_name] = final_score
                current_rag = entity_rag_scores.get(entity_name, 0.0)
                new_rag = rag_signal if rag_fusion_applied else 0.0
                entity_rag_scores[entity_name] = max(current_rag, new_rag)

        chosen_intent = None
        chosen_entity = None
        chosen_score = 0.0
        if fused_scores:
            chosen_intent = max(fused_scores, key=lambda key: fused_scores[key])
            chosen_score = float(fused_scores[chosen_intent])
            # usar o vencedor entre entidades (baseado em combined/base+rag)
            chosen_entity = top_entity_name or intent_entities.get(chosen_intent)

        ordered_combined = sorted(
            combined_intents, key=lambda item: item["combined"], reverse=True
        )
        top_intent_name = ordered_combined[0]["name"] if ordered_combined else None
        for item in ordered_combined:
            item["winner"] = bool(item["name"] == top_intent_name)

        combined_entities: List[Dict[str, Any]] = []
        for entity_name, base_val in entity_base_scores.items():
            combined_val = entity_combined_scores.get(entity_name, base_val)
            rag_val = entity_rag_scores.get(entity_name, 0.0)
            combined_entities.append(
                {
                    "name": entity_name,
                    "base": base_val,
                    "rag": rag_val if rag_fusion_applied else 0.0,
                    "combined": combined_val,
                    "winner": False,
                }
            )

        combined_entities = sorted(
            combined_entities, key=lambda item: item["combined"], reverse=True
        )
        top_entity_name = combined_entities[0]["name"] if combined_entities else None
        for item in combined_entities:
            item["winner"] = bool(item["name"] == top_entity_name)

        affected_entities = [
            item["name"]
            for item in combined_entities
            if abs(float(item["combined"]) - float(item["base"])) > 1e-9
        ]

        if rag_fusion_applied:
            decision_path.append(
                {
                    "stage": "fuse",
                    "type": "rag_integration",
                    "rag_weight": fusion_weight,
                }
            )
            decision_path.append(
                {
                    "stage": "fuse",
                    "type": "rag_fusion",
                    "weight": fusion_weight,
                    "affected": len(affected_entities),
                }
            )
        # --- top2 gap calculado sobre scores base e finais (telemetria M7.4) ---
        # gap_base: ordenado por score base
        ordered_base = sorted(intent_scores.items(), key=lambda kv: kv[1], reverse=True)
        gap_base = 0.0
        if len(ordered_base) >= 2:
            gap_base = float((ordered_base[0][1] or 0.0) - (ordered_base[1][1] or 0.0))
        elif len(ordered_base) == 1:
            gap_base = float(ordered_base[0][1] or 0.0)
        # gap_final: ordenado por score final (fused_scores)
        ordered_final = sorted(fused_scores.items(), key=lambda kv: kv[1], reverse=True)
        gap_final = 0.0
        if len(ordered_final) >= 2:
            gap_final = float(
                (ordered_final[0][1] or 0.0) - (ordered_final[1][1] or 0.0)
            )
        elif len(ordered_final) == 1:
            gap_final = float(ordered_final[0][1] or 0.0)

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
                    "min_score": rag_min_score,
                    "weight": rag_weight,
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

        # --- RAG Context Explain (somente explicativo; não altera roteamento) ---
        rag_context = None
        rag_latency_ms = None
        if rag_enabled and rag_used and rag_raw_results:
            # tokens "include" do intent vencedor (da ontologia) para barreira semântica
            winner_tokens = []
            for it in self.onto.intents:
                if it.name == chosen_intent:
                    winner_tokens = list(it.tokens_include or [])
                    break

            def _chunk_text(item: Dict[str, Any]) -> str:
                # Campos comuns: text/content/body
                for key in ("text", "content", "body"):
                    val = item.get(key)
                    if isinstance(val, str) and val.strip():
                        return val
                return ""

            def _chunk_doc_id(item: Dict[str, Any]) -> str:
                # Campos comuns: doc, id, doc_id, source
                for key in ("doc", "id", "doc_id", "source"):
                    val = item.get(key)
                    if isinstance(val, str) and val.strip():
                        return val
                return "unknown"

            # Seleção de snippets: precisa conter pelo menos 1 token do intent vencedor
            norm_tokens = [t.lower() for t in winner_tokens if t]
            filtered_snippets: List[str] = []
            matched_tokens: List[str] = []
            for item in rag_raw_results:
                txt = _chunk_text(item)
                if not txt:
                    continue
                low = txt.lower()
                hit_toks = [t for t in norm_tokens if t in low]
                if not hit_toks:
                    continue
                # corta o snippet ~240 chars, respeitando limite em palavra
                snippet = txt.strip()
                if len(snippet) > 240:
                    # tenta cortar no último espaço antes de 240
                    cut = snippet[:240]
                    sp = cut.rfind(" ")
                    snippet = cut if sp < 40 else cut[:sp]
                    snippet = snippet.rstrip() + "…"
                filtered_snippets.append(snippet)
                matched_tokens.extend(hit_toks)
                if len(filtered_snippets) >= 3:
                    break

            if filtered_snippets:
                top_doc = _chunk_doc_id(rag_raw_results[0])
                # Reason determinística (1 linha)
                uniq_matched = []
                for t in matched_tokens:
                    if t not in uniq_matched:
                        uniq_matched.append(t)
                reason_tokens = ", ".join(uniq_matched[:3]) if uniq_matched else ""
                rag_context = {
                    "top_doc": top_doc,
                    "snippets": filtered_snippets,
                    "reason": f"Contexto cita tokens do intent vencedor: {reason_tokens} para entity {chosen_entity}.",
                }
                if rag_t0 is not None:
                    rag_latency_ms = (time.perf_counter() - rag_t0) * 1000.0

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
                # Mantemos ambos para comparação no M7.4
                "intent_top2_gap_base": gap_base,
                "intent_top2_gap_final": gap_final,
            },
        }
        combined_block = {
            "intent": ordered_combined,
            "entity": combined_entities,
            "weight": effective_weight,
            "notes": (
                "additive=base+w*rag"
                if re_rank_mode == "additive"
                else "blend=base*(1-w)+rag*w"
            ),
        }
        # Expor final_combined por intent (M7.4)
        try:
            meta_explain["scoring"]["final_combined"] = [
                {"intent": name, "score": float(fused_scores.get(name, 0.0))}
                for name in [it["name"] for it in ordered_combined]
            ]
        except Exception:
            pass

        if rag_enabled:
            meta_explain["rag"] = {
                "enabled": True,
                "index_path": rag_index_path,
                "k": rag_k,
                "min_score": rag_min_score,
                "weight": rag_weight,
                "entity_hints": rag_entity_hints,
                "error": rag_error,
                "used": bool(rag_entity_hints),
                "re_rank": {
                    "enabled": re_rank_enabled,
                    "mode": re_rank_mode,
                    "weight": re_rank_weight,
                },
            }
            # scoring.rag_hint — lista [{entity, score}]
            meta_explain["scoring"]["rag_hint"] = [
                {"entity": k, "score": v}
                for k, v in sorted(
                    rag_entity_hints.items(), key=lambda kv: kv[1], reverse=True
                )
            ]
        else:
            meta_explain["rag"] = {
                "enabled": False,
                "re_rank": {
                    "enabled": re_rank_enabled,
                    "mode": re_rank_mode,
                    "weight": re_rank_weight,
                },
            }
        meta_explain["scoring"]["rag_signal"] = [
            {
                "intent": item["name"],
                "entity": intent_entities.get(item["name"]),
                "score": float(intent_rag_signals.get(item["name"], 0.0)),
            }
            for item in combined_intents
        ]
        if rag_context:
            meta_explain["rag_context"] = rag_context
        meta_explain["scoring"]["combined"] = combined_block
        meta_explain["fusion"] = {
            "enabled": bool(rag_enabled),
            "used": bool(rag_fusion_applied),
            "weight": effective_weight,
            "mode": re_rank_mode,
            "affected_entities": affected_entities,
            "error": rag_error,
        }

        # --- Métricas M7.3 (apenas quando rag_context foi emitido) ---
        if rag_context:
            lbl_intent = str(chosen_intent or "")
            lbl_entity = str(chosen_entity or "")
            try:
                counter(
                    "planner_rag_hits_total",
                    intent=lbl_intent,
                    entity=lbl_entity,
                    _value=float(rag_hits_count or 0),
                )
                counter(
                    "planner_rag_context_used_total",
                    intent=lbl_intent,
                    entity=lbl_entity,
                    _value=1.0,
                )
                if rag_latency_ms is not None:
                    histogram(
                        "planner_rag_context_latency_ms",
                        float(rag_latency_ms),
                        intent=lbl_intent,
                        entity=lbl_entity,
                    )
            except Exception:
                pass

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
        thr = thresholds_cfg or {}
        dfl = thr.get("defaults") or {"min_score": 1.0, "min_gap": 0.5}
        intent_thr = (thr.get("intents") or {}).get(chosen_intent or "", {})
        entity_thr = (thr.get("entities") or {}).get(chosen_entity or "", {})

        min_score = float(
            entity_thr.get("min_score", intent_thr.get("min_score", dfl["min_score"]))
        )
        min_gap = float(
            entity_thr.get("min_gap", intent_thr.get("min_gap", dfl["min_gap"]))
        )

        # Fonte do gate: base|final (apenas se re-rank estiver ligado)
        gate_source_is_final = bool(re_rank_enabled and (thr_apply_on == "final"))
        # score usado no gate: base do vencedor ou final do vencedor
        chosen_base_score = float(intent_scores.get(chosen_intent or "", 0.0))
        score_for_gate = (
            float(fused_scores.get(chosen_intent or "", 0.0))
            if gate_source_is_final
            else chosen_base_score
        )
        gap_used = float(gap_final if gate_source_is_final else gap_base)
        accepted = (score_for_gate >= min_score) and (gap_used >= min_gap)

        meta_explain["scoring"]["thresholds_applied"] = {
            "min_score": min_score,
            "min_gap": min_gap,
            "gap": gap_used,
            "accepted": accepted,
            "source": ("final" if gate_source_is_final else "base"),
        }

        # --------- Métricas M7.4: re-rank aplicado e gaps before/after ----------
        try:
            if re_rank_enabled:
                counter(
                    "planner_rerank_applied_total",
                    mode=re_rank_mode,
                    accepted=("true" if accepted else "false"),
                )
                # Mesmo se apply_on=base, coletamos os dois gaps para análise
                histogram("planner_decision_gap_before", float(gap_base))
                histogram("planner_decision_gap_after", float(gap_final))
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
                # status do gate (calculado pelos thresholds)
                "accepted": accepted,
            },
            "explain": meta_explain,
        }
