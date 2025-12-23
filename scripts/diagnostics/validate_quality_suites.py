#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validador rápido do contrato Suite v2 para arquivos *_suite.json.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from typing import List

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.diagnostics.suite_contracts import SuiteValidationError, load_suite_file


def _resolve_suite_paths(args: argparse.Namespace) -> List[str]:
    suite_paths: List[str] = []
    base_dir = args.suite_dir.rstrip("/")
    if args.suite_path:
        suite_paths.append(args.suite_path)
    elif args.suite:
        suite_paths.append(os.path.join(base_dir, f"{args.suite}_suite.json"))
    else:
        pattern = os.path.join(base_dir, args.suite_glob)
        suite_paths.extend(sorted(glob.glob(pattern)))
    return suite_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Valida contratos Suite v2 para *_suite.json")
    parser.add_argument(
        "--suite-dir",
        default="data/ops/quality/payloads",
        help="Diretório onde ficam as suites (default=data/ops/quality/payloads)",
    )
    parser.add_argument(
        "--suite-glob", default="*_suite.json", help="Glob para descobrir suites (default='*_suite.json')"
    )
    parser.add_argument("--suite", help="Nome lógico da suite (ex.: fiis_cadastro)")
    parser.add_argument("--suite-path", help="Caminho completo para um *_suite.json específico")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    suite_paths = _resolve_suite_paths(args)
    if not suite_paths:
        raise SystemExit("Nenhuma suite encontrada para validar.")

    errors = 0
    for path in suite_paths:
        try:
            load_suite_file(path)
            print(f"[ok] {path}")
        except SuiteValidationError as exc:
            errors += 1
            print(f"[error] {path}: {exc}")

    print(f"[summary] validated={len(suite_paths)} errors={errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
