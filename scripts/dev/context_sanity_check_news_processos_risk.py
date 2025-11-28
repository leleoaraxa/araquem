#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: context_sanity_check_news_processos_risk.py
Purpose: Exercitar cenário de contexto multi-turno no /ask, validando herança
         de ticker via last_reference no fluxo:

1) "Quais são as últimas notícias do HGLG11?"
2) "Esse fundo está envolvido em algum processo?"
3) "E o risco dele hoje?"

Objetivo: inspecionar meta retornado pelo /ask, especialmente:
- meta.planner_entity / meta.planner_intent
- meta.aggregates (e aggregates.ticker)
- rows_total
- coerência entre as etapas

⚠️ Observações:
- Script externo, NÃO altera payload nem contrato do /ask.
- Envia somente {question, conversation_id, nickname, client_id}.
- Ideal rodar com API ativa.

Uso sugerido:

    python scripts/dev/context_sanity_check_news_processos_risk.py \
        --base-url http://localhost:8000 \
        --client-id dev-context-tester \
        --conversation-id context-demo-xyz
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
        description="Sanity check do contexto multi-turno (notícias -> processos -> risco)."
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
        help="nickname usado no payload do /ask",
    )

    args = parser.parse_args()

    conversation_id = args.conversation_id or f"context-demo-{uuid.uuid4()}"
    print(
        f"Usando client_id={args.client_id!r}, conversation_id={conversation_id!r}, "
        f"base_url={args.base_url!r}"
    )
    print()

    # 🔥 Cenário 2: Noticias → Processos → Risco (FII herdado)
    scenarios = [
        "Quais são as últimas notícias do HGLG11?",
        "Qunatos processos tem ele?",
        "E o risco dele?",
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

    ticker_step2 = ((answers[1].get("meta") or {}).get("aggregates") or {}).get(
        "ticker"
    )
    ticker_step3 = ((answers[2].get("meta") or {}).get("aggregates") or {}).get(
        "ticker"
    )

    print("Resumo de herança de ticker:")
    if ticker_step2 and ticker_step2 == ticker_step3:
        print(f"HERANÇA DE TICKER OK (ticker herdado: {ticker_step2})")
    else:
        print("HERANÇA DE TICKER FALHOU — ticker não propagou corretamente.")

    print("Context sanity check finalizado.\n")
    print(
        "Confira se nas perguntas 2 e 3 o meta.aggregates.ticker veio igual ao ticker da pergunta 1 "
        "(ex.: 'HGLG11'), conforme política de last_reference."
    )


if __name__ == "__main__":
    sys.exit(main())
