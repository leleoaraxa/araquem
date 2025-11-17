# scripts/quality/quality_eval_narrator_batch.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Executor em lote para o quality_eval_narrator.

Objetivo:
    - Permitir rodar vários payloads de uma vez;
    - Reaproveitar o script existente `quality_eval_narrator.py` como
      "fonte da verdade" (sem duplicar lógica);
    - Gerar um resumo simples no stdout e, opcionalmente, um arquivo
      JSONL com os resultados consolidados.

Uso típico:

    python scripts/quality/quality_eval_narrator_batch.py \
        tmp/narrator_exec_*.json

    python scripts/quality/quality_eval_narrator_batch.py \
        tmp/narrator_exec_fiis_*.json \
        --out data/ops/quality/narrator_lote_20251117.jsonl
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "quality" / "quality_eval_narrator.py"


def _run_single(payload_path: Path) -> Dict[str, Any]:
    """Invoca o quality_eval_narrator.py para um único payload."""

    if not SCRIPT_PATH.exists():
        raise RuntimeError(f"quality_eval_narrator.py não encontrado em {SCRIPT_PATH}")

    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--payload",
        str(payload_path),
    ]

    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(ROOT),
    )

    if proc.returncode != 0:
        raise RuntimeError(
            f"Falha ao executar {cmd!r} (rc={proc.returncode}): {proc.stderr}"
        )

    try:
        data = json.loads(proc.stdout.strip() or "{}")
    except json.JSONDecodeError as exc:  # pragma: no cover - caminho excepcional
        raise RuntimeError(
            f"Saída não é JSON válido para payload {payload_path}: {exc}\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        ) from exc

    return data


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Executor em lote para quality_eval_narrator.py"
    )
    parser.add_argument(
        "payloads",
        nargs="+",
        help="Caminhos dos arquivos de payload (JSON) a serem avaliados.",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Arquivo de saída em formato JSONL com os resultados consolidados (opcional).",
    )

    args = parser.parse_args(argv)

    payload_paths = [Path(p) for p in args.payloads]
    for p in payload_paths:
        if not p.exists():
            parser.error(f"Payload não encontrado: {p}")

    out_fp = None
    if args.out:
        out_fp = Path(args.out).expanduser().resolve()
        out_fp.parent.mkdir(parents=True, exist_ok=True)
        f = out_fp.open("w", encoding="utf-8")
    else:
        f = None

    results: List[Dict[str, Any]] = []

    print(f"Rodando Narrator em lote para {len(payload_paths)} payload(s)...\n")

    for payload in payload_paths:
        rel = payload if not payload.is_absolute() else payload.relative_to(ROOT)
        print(f"▶ Payload: {rel}")

        data = _run_single(payload)
        text = (data.get("text") or "").strip()
        error = data.get("error")

        print(f"   - enabled={data.get('enabled')} shadow={data.get('shadow')}")
        print(
            f"   - tokens_in={data.get('tokens', {}).get('in')} "
            f"tokens_out={data.get('tokens', {}).get('out')}"
        )
        print(f"   - latency_ms={data.get('latency_ms'):.1f}")
        print(f"   - error={error or 'none'}")
        print(f"   - text_preview={text[:120].replace('\\n', ' ')}")
        print()

        record = {"payload": str(rel), "result": data}
        results.append(record)
        if f is not None:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    if f is not None:
        f.close()
        print(f"\nResultados salvos em: {out_fp}")

    print("\nConcluído.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
