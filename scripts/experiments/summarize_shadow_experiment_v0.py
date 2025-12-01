#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: scripts/experiments/summarize_shadow_experiment_v0.py
Purpose: Ler os arquivos JSONL do shadow do Narrator e gerar um resumo
         por fluxo (client_id / conversation_id) e por estratégia do Narrator.

Entrada esperada: arquivos em logs/narrator_shadow/narrator_shadow_*.jsonl,
onde cada linha é um JSON com campos:
  - timestamp
  - request.{question, client_id, conversation_id}
  - routing.{intent, entity, planner_score}
  - narrator.{enabled, shadow, model, strategy, latency_ms, error, ...}
  - presenter.{answer_final, answer_baseline, rows_used, ...}
  - shadow.{sampled, reason, ...}
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Tuple


def load_lines(path: Path, limit: int | None = None) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                out.append(obj)
            if limit is not None and len(out) >= limit:
                break
    return out


def pick_latest_log(log_dir: Path) -> Path | None:
    pattern = str(log_dir / "narrator_shadow_*.jsonl")
    candidates = glob.glob(pattern)
    if not candidates:
        return None
    # escolhe o arquivo mais recente por mtime
    latest = max(candidates, key=os.path.getmtime)
    return Path(latest)


def summarize(records: List[Dict[str, Any]]) -> None:
    if not records:
        print("Nenhum registro encontrado.")
        return

    total = len(records)
    print(f"Total de registros lidos: {total}")

    by_client: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    by_conv: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    strategies = Counter()
    errors = Counter()
    timeouts = 0
    latencies: List[float] = []

    for r in records:
        req = r.get("request") or {}
        narr = r.get("narrator") or {}
        client_id = str(req.get("client_id") or "unknown")
        conv_id = str(req.get("conversation_id") or "unknown")

        by_client[client_id].append(r)
        by_conv[(client_id, conv_id)].append(r)

        strat = narr.get("strategy") or "none"
        strategies[strat] += 1

        err = narr.get("error")
        if err:
            errors[str(err)] += 1
            if "TimeoutError" in str(err) or "timed out" in str(err):
                timeouts += 1

        lat = narr.get("latency_ms")
        if isinstance(lat, (int, float)):
            latencies.append(float(lat))

    # Resumo global
    print("\n=== Visão Global do Narrator ===")
    print("Estratégias usadas (strategy → contagem):")
    for s, c in strategies.most_common():
        print(f"  - {s}: {c}")

    print("\nErros distintos do Narrator (error → contagem):")
    for e, c in errors.most_common():
        print(f"  - {e}: {c}")

    if latencies:
        print("\nLatência do Narrator (ms):")
        print(f"  - média: {mean(latencies):.1f}")
        print(f"  - min:   {min(latencies):.1f}")
        print(f"  - max:   {max(latencies):.1f}")
        print(f"  - timeouts detectados (via error): {timeouts}")
    else:
        print("\nNenhuma latência registrada em narrator.latency_ms.")

    # Resumo por fluxo (client_id + conversation_id)
    print("\n=== Fluxos (client_id / conversation_id) ===")
    for (client_id, conv_id), recs in sorted(by_conv.items()):
        qs = [((r.get("request") or {}).get("question") or "") for r in recs]
        intents = [
            (r.get("routing") or {}).get("intent")
            or (r.get("presenter") or {}).get("intent")
            for r in recs
        ]
        entities = [
            (r.get("routing") or {}).get("entity")
            or (r.get("presenter") or {}).get("entity")
            for r in recs
        ]
        strat_local = Counter(
            ((r.get("narrator") or {}).get("strategy") or "none") for r in recs
        )
        errs_local = Counter(
            str((r.get("narrator") or {}).get("error") or "")
            for r in recs
            if (r.get("narrator") or {}).get("error")
        )

        print(f"\nFluxo: client_id={client_id}, conversation_id={conv_id}")
        print(f"  Perguntas: {len(recs)}")
        print("  Strategies neste fluxo:")
        for s, c in strat_local.most_common():
            print(f"    - {s}: {c}")
        if errs_local:
            print("  Erros neste fluxo:")
            for e, c in errs_local.most_common():
                print(f"    - {e}: {c}")

        # Mostra um pequeno preview das perguntas e intents
        print("  Amostra de perguntas:")
        for q, it, en in list(zip(qs, intents, entities))[:4]:
            q_preview = (q[:70] + "...") if len(q) > 70 else q
            print(f"    • {q_preview}  → intent={it}, entity={en}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resumo do experimento Shadow v0 (Narrator) a partir dos logs JSONL."
    )
    parser.add_argument(
        "--log-dir",
        default="logs/narrator_shadow",
        help="Diretório onde estão os arquivos narrator_shadow_*.jsonl",
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Arquivo específico de log JSONL. Se não informado, pega o mais recente em --log-dir.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limite máximo de registros a ler (para testes). Default: sem limite.",
    )
    args = parser.parse_args()

    log_dir = Path(args.log_dir)
    if args.file:
        log_path = Path(args.file)
    else:
        log_path = pick_latest_log(log_dir) if log_dir.exists() else None

    if not log_path or not log_path.exists():
        print(f"Nenhum arquivo narrator_shadow_*.jsonl encontrado em {log_dir}")
        return

    print(f"Lendo registros de: {log_path}")
    records = load_lines(log_path, limit=args.limit)
    summarize(records)


if __name__ == "__main__":
    main()
