"""
Audit end-to-end do Planner com foco em roteamento single/multi ticker.

O script NÃO altera lógica: apenas chama Planner.explain para uma bateria
de perguntas e gera um JSONL + resumo em Markdown com logs estruturados.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.planner.planner import Planner  # noqa: E402
from app.planner.ticker_index import (  # noqa: E402
    extract_tickers_from_text,
    resolve_ticker_from_text,
)

ONTOLOGY_PATH = Path("data/ontology/entity.yaml")
JSONL_PATH = Path("data/diagnostics/planner_audit.jsonl")
MD_PATH = Path("docs/dev/diagnostics/PLANNER_FLOW_AUDIT.md")

QUESTIONS = [
    "Como está KNRI11 e XPLG11?",
    "Preço do KNRI11 e do XPLG11 hoje",
    "Dividendos de KNRI11 e XPLG11",
    "Quais são os imóveis do KNRI11 e XPLG11?",
    "Tem notícias do KNRI11 e do XPLG11?",
    "Como está KNRI11 agora?",
    "Preço do KNRI11 hoje",
    "Dividendos do KNRI11",
    "Imóveis do KNRI11",
    "Notícias do KNRI11",
    "Como está hoje?",
    "Quais são os melhores FIIs no ranking?",
    "Qual foi o valor do IPCA em março de 2025?",
    "Como está KNRI agora?",
    "Dividendos de XPLG",
]


@dataclass
class WarningFlags:
    regex_like_tokens: List[str] = field(default_factory=list)
    multiword_tokens: List[str] = field(default_factory=list)
    multi_ticker_downcast: bool = False
    bucket_filtered_entities: bool = False
    gate_apply_on_mismatch: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "regex_like_token_detected": bool(self.regex_like_tokens),
            "regex_like_tokens": self.regex_like_tokens,
            "multiword_token_detected": bool(self.multiword_tokens),
            "multiword_tokens": self.multiword_tokens,
            "multi_ticker_downcast": self.multi_ticker_downcast,
            "bucket_filtered_entities": self.bucket_filtered_entities,
            "gate_apply_on_mismatch": self.gate_apply_on_mismatch,
        }


def _regex_like(token: str) -> bool:
    return any(ch in token for ch in ["[", "]", "{", "}", "\\", "(", ")", "|", "+", "*", "?"])


def _extract_intent_entities(planner: Planner, intent_name: Optional[str]) -> List[str]:
    if not intent_name:
        return []
    for it in planner.onto.intents:
        if it.name == intent_name:
            return it.entities or []
    return []


def _base_top10(intent_scores: Dict[str, float], details: Dict[str, Any]) -> List[Dict[str, Any]]:
    ordered = sorted(intent_scores.items(), key=lambda kv: kv[1], reverse=True)[:10]
    result: List[Dict[str, Any]] = []
    for name, score in ordered:
        det = details.get(name, {})
        result.append(
            {
                "intent": name,
                "score": score,
                "token_includes": det.get("token_includes", []),
                "token_excludes": det.get("token_excludes", []),
                "phrase_includes": det.get("phrase_includes", []),
                "phrase_excludes": det.get("phrase_excludes", []),
                "anti_penalty": det.get("anti_penalty", 0.0),
            }
        )
    return result


def _final_top10(explain: Dict[str, Any]) -> List[Dict[str, Any]]:
    combined = explain.get("scoring", {}).get("combined", {}).get("intent") or []
    return combined[:10]


def _gate_block(explain: Dict[str, Any]) -> Dict[str, Any]:
    thr = explain.get("scoring", {}).get("thresholds_applied", {})
    return {
        "min_score": thr.get("min_score"),
        "min_gap": thr.get("min_gap"),
        "gap": thr.get("gap"),
        "accepted": thr.get("accepted"),
        "source": thr.get("source"),
    }


def _fusion_block(explain: Dict[str, Any]) -> Dict[str, Any]:
    fusion = explain.get("fusion", {}) or {}
    rag = explain.get("rag", {}) or {}
    return {
        "rag_enabled": fusion.get("enabled"),
        "rag_used": fusion.get("used"),
        "fusion_weight": fusion.get("weight"),
        "mode": fusion.get("mode"),
        "rag_entity_hints": rag.get("entity_hints"),
    }


def _detect_warnings(planner: Planner, payload: Dict[str, Any]) -> WarningFlags:
    flags = WarningFlags()
    regex_tokens: List[str] = []
    multiword_tokens: List[str] = []
    for intent in planner.onto.intents:
        for tok in intent.tokens_include or []:
            if _regex_like(tok):
                regex_tokens.append(tok)
            if " " in tok:
                multiword_tokens.append(tok)
    flags.regex_like_tokens = sorted(set(regex_tokens))[:30]
    flags.multiword_tokens = sorted(set(multiword_tokens))[:30]

    tickers = payload.get("tickers_found") or []
    resolved = payload.get("resolved_ticker")
    if len(tickers) > 1 and resolved:
        flags.multi_ticker_downcast = True

    chosen_intent = payload.get("chosen_intent")
    chosen_entity = payload.get("chosen_entity")
    bucket_entities = set(payload.get("bucket_entities") or [])
    intent_entities = set(_extract_intent_entities(planner, chosen_intent))
    if intent_entities and bucket_entities and not (intent_entities & bucket_entities):
        flags.bucket_filtered_entities = True
    if intent_entities and chosen_entity and chosen_entity not in bucket_entities:
        flags.bucket_filtered_entities = True

    gate_block = payload.get("gate_decision") or {}
    apply_on = gate_block.get("source")
    fusion = payload.get("fusion") or {}
    if fusion.get("rag_used") and apply_on == "base":
        flags.gate_apply_on_mismatch = True

    return flags


def _collect_payload(planner: Planner, question: str) -> Dict[str, Any]:
    explain = planner.explain(question)
    normalized = explain.get("normalized")
    tokens = explain.get("tokens") or []
    tokens_set = sorted(set(tokens))
    all_tickers = extract_tickers_from_text(question)
    resolved_single = resolve_ticker_from_text(question)
    bucket = explain.get("explain", {}).get("bucket", {}).get("selected")
    bucket_entities = explain.get("explain", {}).get("bucket", {}).get("entities", [])
    base_top10 = _base_top10(explain.get("intent_scores", {}), explain.get("details", {}))
    final_top10 = _final_top10(explain.get("explain", {}))
    gate = _gate_block(explain.get("explain", {}))
    fusion = _fusion_block(explain.get("explain", {}))
    chosen = explain.get("chosen", {}) or {}

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "raw_question": question,
        "normalized": normalized,
        "tokens": tokens,
        "tokens_set": tokens_set,
        "token_split": planner.onto.token_split,
        "normalize_steps": planner.onto.normalize,
        "resolved_ticker": resolved_single,
        "has_ticker": bool(resolved_single),
        "all_tickers_found": all_tickers,
        "bucket_selected": bucket,
        "bucket_entities": bucket_entities,
        "bucket_entities_count": len(bucket_entities or []),
        "top10_intents_base": base_top10,
        "top10_intents_final": final_top10,
        "fusion": fusion,
        "gate_decision": gate,
        "chosen_intent": chosen.get("intent"),
        "chosen_entity": chosen.get("entity"),
        "chosen_accepted": chosen.get("accepted"),
    }

    warnings = _detect_warnings(planner, payload)
    payload["warnings"] = warnings.to_dict()
    return payload


def _write_jsonl(payloads: List[Dict[str, Any]]) -> None:
    JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with JSONL_PATH.open("w", encoding="utf-8") as f:
        for item in payloads:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def _render_markdown(payloads: List[Dict[str, Any]]) -> str:
    lines = [
        "# Auditoria do Planner (roteamento single vs multi ticker)",
        "",
        "## Fluxo real do Planner",
        "- Normalização/tokenização conforme ontologia (steps e regex de split).",
        "- Extração de ticker via ticker_index (exact/prefix4) sem alterar score.",
        "- Bucket via data/ontology/bucket_rules.yaml seguido de filtro de entidades.",
        "- Scoring base por tokens/phrases + anti-penalty, fusão opcional com RAG, e gate por thresholds.",
        "",
        "## Casos com 1 ticker vs multi ticker",
    ]
    for item in payloads:
        lines.append(
            f"- **{item['raw_question']}** — tickers: {item['all_tickers_found']} → chosen: {item['chosen_intent']} / {item['chosen_entity']} (accepted={item['chosen_accepted']})"
        )
    lines.append("")
    lines.append("## Onde falha e por quê (com evidência)")
    for item in payloads:
        warn = item.get("warnings", {})
        if not any(warn.values()):
            continue
        lines.append(
            f"- {item['raw_question']}: warnings={warn} | bucket={item['bucket_selected']} | gate={item['gate_decision']}"
        )
    lines.append("")
    lines.append("## Hipóteses confirmadas/refutadas")
    lines.append(
        "- Regex-like tokens ou tokens multi-palavra marcados como suspeitos (match literal pode falhar)."
    )
    lines.append(
        "- Multi-ticker pode ser reduzido a booleano/1 ticker quando resolve_ticker_from_text retorna apenas o primeiro."
    )
    lines.append("")
    lines.append("## Próximos passos seguros (somente recomendações)")
    lines.append("- Revisar tokens include com caracteres de regex ou espaços (substituir por tokens atômicos).")
    lines.append("- Avaliar suporte explícito a múltiplos tickers no Planner (mantendo score).")
    lines.append("- Revisar regras de bucket para entidades esperadas que estejam sendo filtradas.")
    return "\n".join(lines)


def _write_markdown(payloads: List[Dict[str, Any]]) -> None:
    MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    MD_PATH.write_text(_render_markdown(payloads), encoding="utf-8")


def main() -> None:
    planner = Planner(str(ONTOLOGY_PATH))
    payloads = [_collect_payload(planner, q) for q in QUESTIONS]
    _write_jsonl(payloads)
    _write_markdown(payloads)
    print(json.dumps({"results": len(payloads), "jsonl": str(JSONL_PATH), "markdown": str(MD_PATH)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
