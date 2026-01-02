#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Avaliação rápida do Narrator em modo local.

Este script espera um arquivo JSON com um dos formatos:

1) Payload completo em "executor_payload":
   {
     "executor_payload": {
       "question": "...",
       "facts": { ... },
       "meta": { ... },
       "intent": "fiis_dividends",
       "entity": "fiis_dividends"
     }
   }

2) Payload direto na raiz:
   {
     "question": "...",
     "facts": { ... },
     "meta": { ... },
     "intent": "fiis_dividends",
     "entity": "fiis_dividends"
   }

O objetivo é alinhar o shape de "facts" com o contrato usado em runtime
(FactsPayload do presenter), sem quebrar casos antigos.
"""
from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from app.narrator.narrator import Narrator


def _load_payload(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    # Compat: alguns geradores aninham tudo em "executor_payload"
    if isinstance(raw, dict) and "executor_payload" in raw:
        payload = raw["executor_payload"]
        if not isinstance(payload, dict):
            raise ValueError("executor_payload deve ser um objeto JSON")
        return payload
    if not isinstance(raw, dict):
        raise ValueError("Payload raiz deve ser um objeto JSON")
    return raw


def _normalize_meta(payload: Dict[str, Any]) -> Dict[str, Any]:
    meta = payload.get("meta") or {}
    if not isinstance(meta, dict):
        meta = {}
    # Intenção/entidade podem vir soltas no payload
    intent = meta.get("intent") or payload.get("intent")
    entity = meta.get("entity") or payload.get("entity")
    if intent is not None:
        meta["intent"] = intent
    if entity is not None:
        meta["entity"] = entity
    return meta


def _normalize_facts(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza o dict de facts para algo compatível com o contrato
    usado em runtime (FactsPayload), mas sem ser estrito.

    Campos alvo:
      - result_key: str|None
      - rows: list[dict]
      - primary: dict
      - aggregates: dict
      - identifiers: dict
      - ticker: str|None
      - fund: str|None
    """
    facts = payload.get("facts") or {}
    if not isinstance(facts, dict):
        facts = {}

    # Base
    result_key = facts.get("result_key") or payload.get("result_key")
    rows = facts.get("rows") or payload.get("rows") or []
    if not isinstance(rows, list):
        rows = []
    rows = [r for r in rows if isinstance(r, dict)]

    primary = facts.get("primary")
    if not isinstance(primary, dict):
        primary = rows[0] if rows else {}

    aggregates = facts.get("aggregates") or payload.get("aggregates") or {}
    if not isinstance(aggregates, dict):
        aggregates = {}

    identifiers = facts.get("identifiers") or payload.get("identifiers") or {}
    if not isinstance(identifiers, dict):
        identifiers = {}

    ticker = (
        facts.get("ticker")
        or primary.get("ticker")
        or identifiers.get("ticker")
        or payload.get("ticker")
    )
    fund = facts.get("fund") or primary.get("fund") or payload.get("fund")

    normalized = {
        "result_key": result_key,
        "rows": rows,
        "primary": primary,
        "aggregates": aggregates,
        "identifiers": identifiers,
        "ticker": ticker,
        "fund": fund,
    }

    # Preserva campos extras que possam existir em facts originais
    for k, v in facts.items():
        if k not in normalized:
            normalized[k] = v

    return normalized


def main() -> None:
    ap = argparse.ArgumentParser(description="Avaliação local do Narrator.")
    ap.add_argument(
        "--payload",
        required=True,
        help="arquivo JSON com executor_payload ou payload direto",
    )
    args = ap.parse_args()

    payload = _load_payload(args.payload)

    question = payload.get("question") or ""
    meta = _normalize_meta(payload)
    facts = _normalize_facts(payload)

    n = Narrator()
    out = n.render(question=question, facts=facts, meta=meta)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
