#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: scripts/experiments/run_shadow_experiment_v0.py
Purpose: Executar o experimento Shadow v0 do Narrator, disparando perguntas
         declaradas em data/ops/experiments/shadow_experiment_v0.yaml
         contra o endpoint /ask.

- Não altera payload do /ask (segue o contrato imutável).
- Usa client_id / conversation_id definidos por fluxo.
- Após a execução, os registros devem estar em:
    logs/narrator_shadow/narrator_shadow_YYYYMMDD.jsonl
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List

import requests
import yaml


def load_experiment(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de experimento não encontrado: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Conteúdo inválido em {path}, esperado mapeamento YAML.")
    return data


def iter_flows(exp: Dict[str, Any]) -> List[Dict[str, Any]]:
    flows = exp.get("flows") or []
    if not isinstance(flows, list):
        raise ValueError("Campo 'flows' deve ser uma lista.")
    return [f for f in flows if isinstance(f, dict)]


def post_question(
    api_url: str,
    question: str,
    client_id: str,
    conversation_id: str,
    nickname: str,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    payload = {
        "question": question,
        "conversation_id": conversation_id,
        "nickname": nickname,
        "client_id": client_id,
    }
    resp = requests.post(api_url, json=payload, timeout=timeout)
    try:
        data = resp.json()
    except Exception:
        data = {}
    return {
        "status_code": resp.status_code,
        "payload": payload,
        "response": data,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Executa o experimento Shadow v0 do Narrator."
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000/ask",
        help="URL do endpoint /ask (default: http://localhost:8000/ask)",
    )
    parser.add_argument(
        "--experiment",
        default="data/ops/experiments/shadow_experiment_v0.yaml",
        help="Caminho para o YAML de experimento.",
    )
    parser.add_argument(
        "--sleep-ms",
        type=int,
        default=200,
        help="Intervalo em ms entre perguntas (default: 200).",
    )
    args = parser.parse_args()

    exp_path = Path(args.experiment)
    exp = load_experiment(exp_path)
    flows = iter_flows(exp)

    print(f"[shadow-v0] Carregado experimento de {exp_path} com {len(flows)} fluxos.")
    print(f"[shadow-v0] Endpoint: {args.api_url}")

    sleep_s = max(args.sleep_ms, 0) / 1000.0

    for flow in flows:
        flow_id = flow.get("id") or "flow-unnamed"
        desc = flow.get("description") or ""
        client_id = flow.get("client_id") or "shadow-v0"
        conversation_id = flow.get("conversation_id") or f"{client_id}-{flow_id}"
        nickname = flow.get("nickname") or "shadow-experiment"
        questions = flow.get("questions") or []

        if not isinstance(questions, list) or not questions:
            print(f"[shadow-v0] Fluxo {flow_id} sem perguntas, ignorando.")
            continue

        print(f"\n[shadow-v0] Iniciando fluxo: {flow_id}")
        if desc:
            print(f"  descrição: {desc}")
        print(f"  client_id={client_id} conversation_id={conversation_id}")

        for idx, q in enumerate(questions, start=1):
            if not isinstance(q, str):
                continue

            print(f"  [{idx}/{len(questions)}] Q: {q}")
            result = post_question(
                api_url=args.api_url,
                question=q,
                client_id=client_id,
                conversation_id=conversation_id,
                nickname=nickname,
            )

            status = result["status_code"]
            resp = result["response"] or {}
            answer = resp.get("answer") or resp.get("legacy_answer") or ""
            meta = resp.get("meta") or {}

            print(f"      -> status={status}, answer[0:80]={answer[:80]!r}")

            # Opcional: se quiser inspecionar rapidamente a rota escolhida:
            intent = meta.get("intent") or meta.get("planner_intent")
            entity = meta.get("entity") or meta.get("planner_entity")
            if intent or entity:
                print(f"      -> route: intent={intent}, entity={entity}")

            time.sleep(sleep_s)

    print("\n[shadow-v0] Concluído. Verifique os arquivos em logs/narrator_shadow/.")


if __name__ == "__main__":
    main()
