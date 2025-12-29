#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: quality_list_misses.py
Purpose: Listar perguntas que estão falhando nos quality gates de roteamento,
         gerando o arquivo JSON:
           data/ops/quality_experimental/routing_misses_via_ask.json

Este script é um alias fino em cima do `quality_diff_routing.py`, que é a
fonte da verdade para comparar o roteamento atual com o golden set
(data/ops/quality/routing_samples.json, Suite v2 com chave payloads).

Uso típico:

    python scripts/quality/quality_list_misses.py

Compliance: Guardrails Araquem v2.1.1
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DIFF_SCRIPT = ROOT / "scripts" / "quality" / "quality_diff_routing.py"


def main() -> int:
    if not DIFF_SCRIPT.exists():
        print(
            f"[error] quality_diff_routing.py não encontrado em {DIFF_SCRIPT}",
            file=sys.stderr,
        )
        return 1

    cmd = [sys.executable, str(DIFF_SCRIPT), *sys.argv[1:]]
    proc = subprocess.run(cmd, cwd=str(ROOT))
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
