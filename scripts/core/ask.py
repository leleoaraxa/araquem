#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: ask.py
Purpose: CLI wrapper para chamar a rota /ask do Araquem.
Compliance: Guardrails Araquem v2.1.1

Uso rápido:
  python scripts/core/ask.py "Qual o CNPJ do ABCD11?"

Com token:
  python scripts/core/ask.py "Qual o CNPJ do ABCD11?" --token %ARQ_API_TOKEN%

Com arquivo JSON:
  python scripts/core/ask.py --file data/samples/ask_sample.json

Opções:
  --url            URL do endpoint /ask (default: http://localhost:8000/ask)
  --conversation-id, --nickname, --client-id  (sobrescrevem o payload)
  --token          Bearer token para Authorization
  --timeout        Timeout em segundos (default: 30)
  --pretty         Imprime JSON formatado
"""

import argparse
import json
import os
import sys
import time
import uuid
from urllib import request, error

DEFAULT_URL = os.getenv("ARAQUEM_ASK_URL", "http://localhost:8000/ask")


def _build_payload(args) -> dict:
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Permite sobrescrever campos via flags
        if args.question is not None:
            data["question"] = args.question
        if args.conversation_id is not None:
            data["conversation_id"] = args.conversation_id
        if args.nickname is not None:
            data["nickname"] = args.nickname
        if args.client_id is not None:
            data["client_id"] = args.client_id
        return data

    # Sem arquivo: construir payload mínimo
    if args.question is None:
        print(
            "erro: informe a pergunta como argumento ou use --file <json>",
            file=sys.stderr,
        )
        sys.exit(2)

    payload = {
        "question": args.question,
        "conversation_id": args.conversation_id or f"cli-{uuid.uuid4()}",
        "nickname": args.nickname or os.getenv("ARAQUEM_NICKNAME", "Leleo"),
        "client_id": args.client_id or os.getenv("ARAQUEM_CLIENT_ID", "cli-local"),
    }
    return payload


def _post_json(
    url: str, payload: dict, token: str | None, timeout: float, pretty: bool
) -> int:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            if pretty:
                try:
                    print(json.dumps(json.loads(body), ensure_ascii=False, indent=2))
                except Exception:
                    print(body)
            else:
                print(body)
            return 0
    except error.HTTPError as e:
        # HTTP com corpo de erro JSON
        try:
            body = e.read().decode("utf-8", errors="replace")
            if pretty:
                try:
                    print(
                        json.dumps(json.loads(body), ensure_ascii=False, indent=2),
                        file=sys.stderr,
                    )
                except Exception:
                    print(body, file=sys.stderr)
            else:
                print(body, file=sys.stderr)
        except Exception:
            print(f"HTTP {e.code}: {e.reason}", file=sys.stderr)
        return 1
    except error.URLError as e:
        print(f"Falha ao conectar em {url}: {e.reason}", file=sys.stderr)
        return 2


def main():
    parser = argparse.ArgumentParser(
        description="CLI para chamar /ask do Araquem (NL->SQL)."
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="Pergunta em linguagem natural (ex.: 'Qual o CNPJ do ABCD11?').",
    )
    parser.add_argument(
        "--url", default=DEFAULT_URL, help=f"Endpoint /ask (default: {DEFAULT_URL})"
    )
    parser.add_argument(
        "--file", help="Caminho para arquivo JSON com o payload completo."
    )
    parser.add_argument(
        "--conversation-id",
        dest="conversation_id",
        help="conversation_id para o payload.",
    )
    parser.add_argument("--nickname", dest="nickname", help="nickname para o payload.")
    parser.add_argument(
        "--client-id", dest="client_id", help="client_id para o payload."
    )
    parser.add_argument("--token", help="Bearer token (Authorization).")
    parser.add_argument(
        "--timeout", type=float, default=30.0, help="Timeout em segundos (default: 30)."
    )
    parser.add_argument(
        "--pretty", action="store_true", help="Imprime a resposta em JSON indentado."
    )

    args = parser.parse_args()

    payload = _build_payload(args)
    # Sanidade mínima do contrato payload
    missing = [
        k
        for k in ("question", "conversation_id", "nickname", "client_id")
        if k not in payload
    ]
    if missing:
        print(f"payload inválido: faltam campos {missing}", file=sys.stderr)
        sys.exit(2)

    url = args.url
    token = args.token or os.getenv("QUALITY_OPS_TOKEN")
    code = _post_json(url, payload, token, args.timeout, args.pretty)
    sys.exit(code)


if __name__ == "__main__":
    main()
