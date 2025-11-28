#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: context_sanity_check.py
Purpose: Exercitar cenário de contexto multi-turno no /ask, validando herança
         de ticker via last_reference (CNPJ -> Sharpe -> overview).

Fluxo padrão (mesmo client_id / conversation_id):

1) "CNPJ do HGLG11?"
2) "Esse fundo tem Sharpe bom?"
3) "E o overview dele?"

O objetivo é inspecionar o meta retornado pelo /ask, em especial:
- meta.planner_entity
- meta.aggregates (e, se presente, aggregates.ticker)

Uso sugerido:

    python scripts/dev/context_sanity_check.py \
        --base-url http://localhost:8000 \
        --client-id dev-context-tester \
        --conversation-id context-demo-001

⚠️ Pequenas observações:
- O script NÃO altera payload nem contrato do /ask: envia apenas
  {question, conversation_id, nickname, client_id}.
- Ele é um cliente externo, só lê o que o /ask já expõe em JSON.
- Ideal rodar com api já de pé (docker compose up -d api).
"""

import argparse
import json
import sys
import textwrap
import uuid
from typing import Any, Dict

import requests


def call_ask(
    base_url: str,
    question: str,
    client_id: str,
    conversation_id: str,
    nickname: str = "context-tester",
) -> Dict[str, Any]:
    url = base_url.rstrip("/") + "/ask"
    payload = {
        "question": question,
        "client_id": client_id,
        "conversation_id": conversation_id,
        "nickname": nickname,
    }

    print("=" * 80)
    print(f"QUESTION: {question}")
    print(f"POST {url}")
    print(f"payload: {json.dumps(payload, ensure_ascii=False)}")

    try:
        resp = requests.post(url, json=payload, timeout=30)
    except Exception as exc:
        print(f"[ERROR] HTTP request failed: {exc}")
        return {}

    print(f"HTTP {resp.status_code}")
    try:
        data = resp.json()
    except Exception as exc:
        print(f"[ERROR] Could not parse JSON: {exc}")
        print(resp.text[:1000])
        return {}

    # Pretty-print only key parts
    status = data.get("status") or {}
    results = data.get("results") or {}
    meta = data.get("meta") or {}

    planner_entity = meta.get("planner_entity") or results.get("entity")
    planner_intent = meta.get("planner_intent") or results.get("intent")
    aggregates = meta.get("aggregates") or {}

    result_entity = results.get("entity") or meta.get("entity")
    result_intent = results.get("intent") or meta.get("intent")

    ticker_from_agg = None
    if isinstance(aggregates, dict):
        ticker_from_agg = aggregates.get("ticker")

    print("\n--- META SNAPSHOT ---")
    print(f"status.reason        : {status.get('reason')}")
    print(f"meta.planner_intent  : {planner_intent}")
    print(f"meta.planner_entity  : {planner_entity}")
    print(f"meta.rows_total      : {meta.get('rows_total')}")
    print(f"meta.aggregates      : {json.dumps(aggregates, ensure_ascii=False)}")
    print(f"meta.aggregates.ticker (if any): {ticker_from_agg}")
    print(f"results.intent/entity: {result_intent} / {result_entity}")

    answer = data.get("answer")
    if answer:
        trimmed = textwrap.shorten(str(answer).replace("\n", " "), width=200)
        print(f"\n--- ANSWER (trimmed) ---\n{trimmed}")

    print("=" * 80)
    print()
    return data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sanity check do contexto multi-turno (CNPJ -> Sharpe -> overview)."
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL da API (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--client-id",
        default="dev-context-tester",
        help="client_id a ser usado no payload do /ask",
    )
    parser.add_argument(
        "--conversation-id",
        default=None,
        help="conversation_id a ser usado no payload; se vazio, gera um UUID",
    )
    parser.add_argument(
        "--nickname",
        default="context-tester",
        help="nickname a ser usado no payload do /ask",
    )

    args = parser.parse_args()

    conversation_id = args.conversation_id or f"context-demo-{uuid.uuid4()}"
    print(
        f"Usando client_id={args.client_id!r}, conversation_id={conversation_id!r}, "
        f"base_url={args.base_url!r}"
    )
    print()

    # Cenário padrão: HGLG11 em três etapas
    scenarios = [
        "CNPJ do HGLG11?",
        "Esse fundo tem Sharpe bom?",
        "E o overview dele?",
    ]

    answers = []
    for q in scenarios:
        answers.append(
            call_ask(
                base_url=args.base_url,
                question=q,
                client_id=args.client_id,
                conversation_id=conversation_id,
                nickname=args.nickname,
            )
        )

    ticker_second = ((answers[1].get("meta") or {}).get("aggregates") or {}).get("ticker")
    ticker_third = ((answers[2].get("meta") or {}).get("aggregates") or {}).get("ticker")

    print("Resumo de herança de ticker:")
    if ticker_second and ticker_second == ticker_third:
        print(f"HERANÇA DE TICKER OK (ticker herdado: {ticker_second})")
    else:
        print(
            "HERANÇA DE TICKER FALHOU (verifique meta.aggregates.ticker nas perguntas 2 e 3)"
        )

    print("Context sanity check finalizado.\n")
    print(
        "Agora confira se nas perguntas 2 e 3 o meta.aggregates.ticker veio preenchido "
        "com o mesmo ticker da pergunta 1 (ex.: 'HGLG11'), conforme política de last_reference."
    )


if __name__ == "__main__":
    sys.exit(main())
