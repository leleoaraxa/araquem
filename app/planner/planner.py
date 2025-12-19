# app/planner/planner.py
from __future__ import annotations
from typing import Dict, Any, List
import re, unicodedata
import logging
import os
import time
from pathlib import Path
from functools import lru_cache

from .ontology_loader import load_ontology
from .ticker_index import resolve_ticker_from_text

# RAG: leitor de índice e hints
from app.rag.hints import entity_hints_from_rag
from app.rag.ollama_client import OllamaClient
from app.utils.filecache import cached_embedding_store, load_yaml_cached
from app.observability.instrumentation import counter, histogram

PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
_LOG = logging.getLogger("planner.explain")


@lru_cache(maxsize=1)
def _load_bucket_rules(path: str = "data/ontology/bucket_rules.yaml") -> Dict[str, Any]:
    """
    Carrega as regras de bucket a partir de YAML.

    Não aplica lógica de negócio; apenas retorna o dicionário cru com:
    - defaults
    - rules
    """
    try:
        return load_yaml_cached(path) or {}
    except Exception:
        _LOG.exception("Falha ao carregar bucket_rules de %s", path)
        return {}


def resolve_bucket(question: str, context: Dict[str, Any], ontology: Any) -> str:
    """
    Resolve o bucket (A/B/C/D) de forma 100% declarativa via YAML (bucket_rules).
    Quando nenhuma regra habilitada casa com a pergunta, retorna string vazia (modo neutro).
    """
    cfg = _load_bucket_rules()
    defaults = cfg.get("defaults") or {}
    rules = cfg.get("rules") or []

    if not isinstance(rules, list) or not rules:
        return ""

    # Normalização e tokenização consistentes com o Planner
    normalize_steps = defaults.get("normalize") or getattr(ontology, "normalize", [])
    split_pat = defaults.get("token_split") or getattr(ontology, "token_split", r"\b")

    norm = _normalize(question, normalize_steps)
    tokens = _tokenize(norm, split_pat)
    tokens_set = set(tokens)

    token_weight = float(defaults.get("token_weight", 1.0))
    phrase_weight = float(defaults.get("phrase_weight", 3.0))
    default_min_score = float(defaults.get("min_score", 1.0))

    best_bucket = ""
    best_score = 0.0

    for rule in rules:
        if not isinstance(rule, dict):
            continue

        if not rule.get("enabled", False):
            continue

        bucket = str(rule.get("bucket", "")).strip()
        if not bucket:
            continue

        min_score = float(rule.get("min_score", default_min_score))

        tokens_inc = rule.get("tokens_include") or []
        tokens_exc = rule.get("tokens_exclude") or []
        phrases_inc = rule.get("phrases_include") or []
        phrases_exc = rule.get("phrases_exclude") or []

        # Contagem de hits
        token_hits_inc = [t for t in tokens_inc if t in tokens_set]
        token_hits_exc = [t for t in tokens_exc if t in tokens_set]
        phrase_hits_inc = [p for p in phrases_inc if _phrase_present(norm, p)]
        phrase_hits_exc = [p for p in phrases_exc if _phrase_present(norm, p)]

        score = (
            token_weight * len(token_hits_inc)
            - token_weight * len(token_hits_exc)
            + phrase_weight * len(phrase_hits_inc)
            - phrase_weight * len(phrase_hits_exc)
        )

        if score >= min_score and score >= best_score:
            best_score = score
            best_bucket = bucket

    return best_bucket


def _require_key(cfg: Dict[str, Any], key: str, *, path: str) -> Any:
    if key not in cfg:
        raise ValueError(f"Configuração ausente: {path}.{key}")
    return cfg[key]


def _require_number(
    value: Any, *, key: str, path: str, allow_int: bool = True
) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{path}.{key} deve ser numérico, não booleano")
    if isinstance(value, (int, float)):
        if not allow_int and isinstance(value, int):
            raise ValueError(f"{path}.{key} deve ser float")
        if value < 0:
            raise ValueError(f"{path}.{key} não pode ser negativo")
        return float(value)
    raise ValueError(f"{path}.{key} deve ser numérico")


def _require_positive_int(value: Any, *, key: str, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{path}.{key} deve ser inteiro positivo")
    if value <= 0:
        raise ValueError(f"{path}.{key} deve ser > 0")
    return int(value)


_THRESHOLDS_CACHE: Dict[str, Any] | None = None


def _load_thresholds(path: str = "data/ops/planner_thresholds.yaml") -> Dict[str, Any]:
    global _THRESHOLDS_CACHE

    if _THRESHOLDS_CACHE is not None:
        return _THRESHOLDS_CACHE

    policy_path = Path(path)
    if not policy_path.exists():
        raise ValueError(f"Arquivo de thresholds ausente: {policy_path}")

    data = load_yaml_cached(str(policy_path))
    if not isinstance(data, dict):
        raise ValueError(f"Arquivo de thresholds inválido: {path}")

    planner = data.get("planner")
    if not isinstance(planner, dict):
        raise ValueError(f"Bloco 'planner' obrigatório em {path}")

    thresholds = planner.get("thresholds")
    rag = planner.get("rag")
    if not isinstance(thresholds, dict) or not isinstance(rag, dict):
        raise ValueError(f"Blocos 'thresholds' e 'rag' são obrigatórios em {path}")

    defaults = thresholds.get("defaults")
    if (
        not isinstance(defaults, dict)
        or "min_score" not in defaults
        or "min_gap" not in defaults
    ):
        raise ValueError("thresholds.defaults deve definir min_score e min_gap")
    _require_number(
        defaults.get("min_score"), key="min_score", path="thresholds.defaults"
    )
    _require_number(defaults.get("min_gap"), key="min_gap", path="thresholds.defaults")

    re_rank_cfg = rag.get("re_rank")
    if not isinstance(re_rank_cfg, dict):
        raise ValueError("Bloco rag.re_rank deve estar definido no YAML")

    _require_key(thresholds, "apply_on", path="thresholds")
    for key in ("enabled", "k", "min_score", "weight"):
        _require_key(rag, key, path="rag")
    for key in ("enabled", "mode", "weight"):
        _require_key(re_rank_cfg, key, path="rag.re_rank")

    # Validações mínimas de tipo/intervalo (sem regras de negócio).
    _require_positive_int(rag.get("k"), key="k", path="rag")
    _require_number(rag.get("min_score"), key="min_score", path="rag")
    _require_number(rag.get("weight"), key="weight", path="rag")
    _require_number(re_rank_cfg.get("weight"), key="weight", path="rag.re_rank")

    _THRESHOLDS_CACHE = {"planner": {"thresholds": thresholds, "rag": rag}}
    return _THRESHOLDS_CACHE


def _load_context_policy(path: str = "data/policies/context.yaml") -> Dict[str, Any]:
    """
    Carrega a política de contexto (se existir) para expor no explain do Planner.

    Importante:
      - NÃO altera roteamento, score ou thresholds.
      - Serve apenas para telemetria/observabilidade:
        informa se a entidade escolhida estaria apta a usar contexto,
        segundo data/policies/context.yaml.
    """
    policy_path = Path(path)
    if not policy_path.exists():
        _LOG.warning("Política de contexto ausente; contexto desabilitado")
        return {
            "context": {},
            "planner": {},
            "status": "missing",
        }

    try:
        data = load_yaml_cached(str(policy_path)) or {}
        if not isinstance(data, dict):
            raise ValueError("context.yaml deve ser um mapeamento")
        ctx = data.get("context") or {}
        planner_ctx = ctx.get("planner") or {}
        return {
            "context": ctx if isinstance(ctx, dict) else {},
            "planner": planner_ctx if isinstance(planner_ctx, dict) else {},
            "status": "ok",
        }
    except Exception as exc:
        # Defensivo: em caso de erro, consideramos contexto desabilitado e registramos o erro.
        _LOG.error("Falha ao carregar política de contexto", exc_info=True)
        return {
            "context": {},
            "planner": {},
            "status": "invalid",
            "error": str(exc),
        }


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


def _normalize_phrase(phrase: str, steps: List[str]) -> str:
    return _normalize(phrase, steps)


def _tokens_match_in_order(text_tokens: List[str], template_tokens: List[str]) -> bool:
    if not template_tokens:
        return True

    pos = 0
    for token in template_tokens:
        try:
            next_index = text_tokens.index(token, pos)
        except ValueError:
            return False
        pos = next_index + 1
    return True


def _phrase_matches_with_placeholders(
    norm_text: str,
    raw_phrase: str,
    *,
    has_ticker: bool,
    normalize_steps: List[str],
    token_split: str,
    text_tokens: List[str],
) -> bool:
    if not raw_phrase:
        return False

    contains_ticker = "<ticker>" in raw_phrase
    contains_no_ticker = "(sem ticker)" in raw_phrase

    if not contains_ticker and not contains_no_ticker:
        normalized_phrase = _normalize_phrase(raw_phrase, normalize_steps)
        return bool(normalized_phrase) and normalized_phrase in norm_text

    if contains_ticker and not has_ticker:
        return False
    if contains_no_ticker and has_ticker:
        return False

    template = raw_phrase.replace("<ticker>", " ").replace("(sem ticker)", " ")
    normalized_template = _normalize_phrase(template, normalize_steps)
    template_tokens = _tokenize(normalized_template, token_split)

    if not template_tokens and (contains_ticker or contains_no_ticker):
        return True

    return _tokens_match_in_order(text_tokens, template_tokens)


def _any_in(text: str, candidates: List[str]) -> bool:
    return any(c for c in candidates if c and c in text)


def _entities_for_bucket(ontology: Any, bucket: str) -> List[str]:
    """Retorna entidades elegíveis para o bucket, sem lógica de negócio inline."""

    all_entities: List[str] = []
    for it in getattr(ontology, "intents", []) or []:
        ents = getattr(it, "entities", None) or []
        for ent in ents:
            if ent and ent not in all_entities:
                all_entities.append(ent)

    buckets_map = getattr(ontology, "buckets", None)
    if not isinstance(buckets_map, dict):
        return all_entities

    if not bucket:
        return all_entities

    entities = buckets_map.get(bucket) or []
    if not isinstance(entities, list) or not entities:
        return all_entities

    return [str(e) for e in entities if e]


class Planner:
    def __init__(self, ontology_path: str):
        self.ontology_path = ontology_path
        self.onto = load_ontology(ontology_path)

    def reload(self):
        self.onto = load_ontology(self.ontology_path)

    def explain(self, question: str):
        norm = _normalize(question, self.onto.normalize)
        tokens = _tokenize(norm, self.onto.token_split)
        tokens_set = set(tokens)

        resolved_ticker = resolve_ticker_from_text(question)
        has_ticker = bool(resolved_ticker)

        bucket = resolve_bucket(question, {}, self.onto)
        bucket_entities = set(_entities_for_bucket(self.onto, bucket))

        try:
            _LOG.info(
                {
                    "planner_phase": "normalize_tokenize",
                    "raw_question": question,
                    "normalized": norm,
                    "tokens": tokens,
                    "token_split": self.onto.token_split,
                    "normalize_steps": self.onto.normalize,
                    "tokens_set_sample": list(sorted(tokens_set))[:30],
                    "resolved_ticker": resolved_ticker,
                    "has_ticker": has_ticker,
                }
            )
        except Exception:
            pass

        try:
            _LOG.info(
                {
                    "planner_phase": "bucket_resolve",
                    "raw_question": question,
                    "bucket": bucket,
                    "bucket_entities_count": len(bucket_entities),
                    "bucket_entities_sample": list(sorted(bucket_entities))[:50],
                }
            )
        except Exception:
            pass

        # pesos vêm 100% da ontologia validada (sem defaults embutidos no código)
        token_weight = float(self.onto.weights["token"])
        phrase_weight = float(self.onto.weights["phrase"])

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
        decision_path.append(
            {"stage": "bucketize", "type": "planner_bucket", "bucket": bucket}
        )
        token_score_items: List[Dict[str, Any]] = []
        phrase_score_items: List[Dict[str, Any]] = []
        anti_hits_items: List[Dict[str, Any]] = []
        intent_base_breakdown: List[Dict[str, Any]] = []

        # --- scoring base (como já havia) ---
        for it in self.onto.intents:
            score = 0.0
            include_hits = [
                t
                for t in it.tokens_include
                if (t == "<ticker>" and has_ticker)
                or (t == "(sem ticker)" and not has_ticker)
                or (t not in {"<ticker>", "(sem ticker)"} and (t in tokens_set))
            ]

            exclude_hits = [
                t
                for t in it.tokens_exclude
                if (t == "<ticker>" and has_ticker)
                or (t == "(sem ticker)" and not has_ticker)
                or (t not in {"<ticker>", "(sem ticker)"} and (t in tokens_set))
            ]
            score += token_weight * len(include_hits)
            score -= token_weight * len(exclude_hits)

            phrase_incl_hits = [
                p
                for p in it.phrases_include
                if _phrase_matches_with_placeholders(
                    norm,
                    p,
                    has_ticker=has_ticker,
                    normalize_steps=self.onto.normalize,
                    token_split=self.onto.token_split,
                    text_tokens=tokens,
                )
            ]
            phrase_excl_hits = [
                p
                for p in it.phrases_exclude
                if _phrase_matches_with_placeholders(
                    norm,
                    p,
                    has_ticker=has_ticker,
                    normalize_steps=self.onto.normalize,
                    token_split=self.onto.token_split,
                    text_tokens=tokens,
                )
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
                "entities": [e for e in it.entities if e in bucket_entities],
            }
            intent_base_breakdown.append(
                {
                    "intent": it.name,
                    "score": score,
                    "token_includes": include_hits,
                    "token_excludes": exclude_hits,
                    "phrase_includes": phrase_incl_hits,
                    "phrase_excludes": phrase_excl_hits,
                    "anti_penalty": anti_penalty,
                }
            )

        try:
            ordered_base_breakdown = sorted(
                intent_base_breakdown, key=lambda item: item["score"], reverse=True
            )
            _LOG.info(
                {
                    "planner_phase": "intent_base_scoring",
                    "raw_question": question,
                    "top_intents": ordered_base_breakdown[:10],
                }
            )
        except Exception:
            pass

        # --- configurações RAG ---
        cfg = _load_thresholds()
        planner_cfg = cfg["planner"]
        rag_cfg = planner_cfg["rag"]
        thresholds_cfg = planner_cfg["thresholds"]

        rag_enabled = bool(rag_cfg["enabled"])
        rag_k = int(rag_cfg["k"])
        rag_min_score = float(rag_cfg["min_score"])
        rag_weight = float(rag_cfg["weight"])
        rag_index_path = os.getenv(
            "RAG_INDEX_PATH", "data/embeddings/store/embeddings.jsonl"
        )
        # Re-rank (Preparação M7.4 — desligado por padrão)
        re_rank_cfg = rag_cfg["re_rank"]
        re_rank_enabled = bool(re_rank_cfg["enabled"])
        re_rank_mode = str(re_rank_cfg["mode"])
        re_rank_weight = float(re_rank_cfg["weight"])
        thr_apply_on = str(thresholds_cfg["apply_on"])
        # Compat: 'fused' deve usar o score final (pós-fusão) no gate
        if thr_apply_on == "fused":
            thr_apply_on = "final"

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
            # Intents podem ter N entidades; todas devem competir
            ents = [e for e in (it.entities or []) if e in bucket_entities]
            # Se não houver entidades, mantemos None (compat)
            intent_entities[it.name] = ents[0] if ents else None

            # Para métricas por intent, reportamos o melhor rag_signal entre suas entidades
            best_rag_signal_for_intent = 0.0

            for entity_name in ents or [None]:
                if entity_name is None:
                    rag_signal = 0.0
                else:
                    # defensivo: entity_name pode não ser str em casos extremos
                    key = str(entity_name).strip()
                    rag_signal = float(rag_entity_hints.get(key, 0.0))

                # Regra anti-penalização:
                # se o RAG foi usado globalmente, mas ESTA entidade não tem sinal (0),
                # não reduzimos o score base (evita "blend" derrubar o base).
                if rag_fusion_applied and rag_signal <= 0.0:
                    final_score = base
                elif rag_fusion_applied:
                    if re_rank_mode == "additive":
                        # additive: base + w*rag
                        final_score = base + fusion_weight * rag_signal
                    else:
                        # blend: base*(1-w) + rag*w
                        final_score = (
                            base * (1.0 - fusion_weight) + rag_signal * fusion_weight
                        )
                else:
                    final_score = base

                # Intents: guardamos o MAIOR final_score entre suas entidades
                prev_intent_final = fused_scores.get(it.name, None)
                if prev_intent_final is None or final_score > prev_intent_final:
                    fused_scores[it.name] = final_score

                # Entidades: agregamos por entidade
                if entity_name:
                    if (
                        entity_name not in entity_base_scores
                        or base > entity_base_scores[entity_name]
                    ):
                        entity_base_scores[entity_name] = base
                    if (
                        entity_name not in entity_combined_scores
                        or final_score > entity_combined_scores[entity_name]
                    ):
                        entity_combined_scores[entity_name] = final_score
                    entity_rag_scores[entity_name] = max(
                        entity_rag_scores.get(entity_name, 0.0),
                        rag_signal if rag_fusion_applied else 0.0,
                    )
                    best_rag_signal_for_intent = max(
                        best_rag_signal_for_intent, rag_signal
                    )

            # Para telemetria por intent (combined_intents), usamos o melhor combinado das suas entidades
            combined_intents.append(
                {
                    "name": it.name,
                    "base": base,
                    "rag": (best_rag_signal_for_intent if rag_fusion_applied else 0.0),
                    "combined": float(fused_scores.get(it.name, base)),
                    "winner": False,
                }
            )
            intent_rag_signals[it.name] = best_rag_signal_for_intent

        chosen_intent = None
        chosen_score = 0.0
        if fused_scores:
            chosen_intent = max(fused_scores, key=lambda key: fused_scores[key])
            chosen_score = float(fused_scores[chosen_intent])

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

        if chosen_intent is not None:
            chosen_entity = top_entity_name or intent_entities.get(chosen_intent)
        else:
            chosen_entity = None

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

        try:
            ordered_final_intents = sorted(
                combined_intents, key=lambda item: item["combined"], reverse=True
            )
            _LOG.info(
                {
                    "planner_phase": "intent_final_scoring",
                    "raw_question": question,
                    "rag_enabled": rag_enabled,
                    "rag_used": rag_used,
                    "fusion_weight": effective_weight,
                    "fusion_mode": re_rank_mode,
                    "top_intents": ordered_final_intents[:10],
                }
            )
        except Exception:
            pass

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
        meta_explain["bucket"] = {
            "selected": bucket,
            "entities": sorted(bucket_entities),
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

        try:
            _LOG.info(
                {
                    "planner_phase": "gate_decision",
                    "raw_question": question,
                    "min_score": min_score,
                    "min_gap": min_gap,
                    "gap": gap_used,
                    "apply_on": ("final" if gate_source_is_final else "base"),
                    "score_for_gate": score_for_gate,
                    "accepted": accepted,
                    "rag_enabled": rag_enabled,
                    "re_rank_enabled": re_rank_enabled,
                    "rag_used": rag_used,
                }
            )
        except Exception:
            pass

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

        # ------------------------------------------------------------------
        # Contexto conversacional — snapshot declarativo (NÃO altera rota)
        # ------------------------------------------------------------------
        # Fonte única: data/policies/context.yaml
        # Regras:
        #   - se context.enabled = false      -> entity_allowed_for_context = False
        #   - se planner.enabled = false     -> entity_allowed_for_context = False
        #   - se entidade estiver em denied  -> False
        #   - se allowed_entities vazio      -> True (whitelist vazia)
        #   - caso contrário                 -> True somente se entidade ∈ allowed
        ctx_policy_raw = _load_context_policy()
        ctx_cfg = ctx_policy_raw.get("context") or {}
        planner_ctx_cfg = ctx_policy_raw.get("planner") or {}

        ctx_enabled = bool(ctx_cfg.get("enabled", False))
        planner_ctx_enabled = bool(planner_ctx_cfg.get("enabled", True))

        allowed_entities = planner_ctx_cfg.get("allowed_entities") or []
        denied_entities = planner_ctx_cfg.get("denied_entities") or []

        entity_allowed_for_context = False
        if chosen_entity and ctx_enabled and planner_ctx_enabled:
            if chosen_entity in denied_entities:
                entity_allowed_for_context = False
            elif not allowed_entities:
                entity_allowed_for_context = True
            else:
                entity_allowed_for_context = chosen_entity in allowed_entities

        # Expõe o snapshot de contexto apenas em explain.* (telemetria)
        meta_explain["context"] = {
            "enabled": ctx_enabled,
            "planner_enabled": planner_ctx_enabled,
            "entity_allowed": entity_allowed_for_context,
            "entity": chosen_entity,
            "allowed_entities": allowed_entities,
            "denied_entities": denied_entities,
            "status": ctx_policy_raw.get("status"),
            "error": ctx_policy_raw.get("error"),
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
                # snapshot de contexto (somente leitura, não afeta decisão)
                "context_allowed": entity_allowed_for_context,
            },
            "explain": meta_explain,
        }
