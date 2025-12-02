#!/usr/bin/env python3
"""
Script: embeddings_health_check.py
Purpose: Verificar saúde básica do índice de embeddings gerado, sem acoplamento ao runtime.
Compliance: Guardrails Araquem v2.2.0
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable, List, Tuple


def _load_manifest(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data


def _iter_embeddings(path: Path) -> Iterable[Tuple[int, List[float]]]:
    with path.open("r", encoding="utf-8") as fh:
        for idx, line in enumerate(fh):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                yield idx, []
                continue
            emb = rec.get("embedding")
            yield idx, emb if isinstance(emb, list) else []


def _is_zero_or_nan_vector(vec: List[float]) -> bool:
    if not vec:
        return True
    has_value = False
    for v in vec:
        if isinstance(v, (int, float)):
            if math.isnan(v):
                return True
            if v != 0:
                has_value = True
        else:
            return True
    return not has_value


def _expected_total_from_manifest(manifest: dict) -> int | None:
    docs = manifest.get("docs") or []
    if not isinstance(docs, list):
        return None
    total = 0
    for doc in docs:
        try:
            total += int(doc.get("chunks", 0))
        except Exception:
            return None
    return total


def health_check(manifest_path: Path, embeddings_path: Path) -> int:
    manifest = _load_manifest(manifest_path)
    expected_total = _expected_total_from_manifest(manifest)

    dim_expected = manifest.get("vector_dimension")
    dim_detected = None
    total = 0
    wrong_dim = 0
    zero_or_nan = 0

    for idx, vec in _iter_embeddings(embeddings_path):
        total += 1
        if vec and dim_detected is None:
            dim_detected = len(vec)
        dim_now = len(vec) if isinstance(vec, list) else 0
        if dim_expected and dim_now not in (0, dim_expected):
            wrong_dim += 1
        if dim_expected is None and dim_detected and dim_now not in (0, dim_detected):
            wrong_dim += 1
        if _is_zero_or_nan_vector(vec):
            zero_or_nan += 1

    dim_report = dim_expected or dim_detected or "unknown"
    fail_reasons = []
    if expected_total is not None and expected_total != total:
        fail_reasons.append(
            f"count mismatch (manifest={expected_total} vs embeddings={total})"
        )
    if wrong_dim:
        fail_reasons.append(f"{wrong_dim} vectors with unexpected dimension")
    if zero_or_nan:
        fail_reasons.append(f"{zero_or_nan} vectors empty/zero/nan")

    if fail_reasons:
        print(f"FAIL: vectors={total} dim={dim_report} -> {', '.join(fail_reasons)}")
        return 1

    print(f"OK: vectors={total} dim={dim_report}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Health-check básico dos embeddings")
    parser.add_argument(
        "--manifest",
        default="data/embeddings/store/manifest.json",
        help="Caminho para o manifest.json gerado",
    )
    parser.add_argument(
        "--embeddings",
        default="data/embeddings/store/embeddings.jsonl",
        help="Caminho para o embeddings.jsonl gerado",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    embeddings_path = Path(args.embeddings)

    if not manifest_path.exists():
        print(f"FAIL: manifest não encontrado em {manifest_path}")
        raise SystemExit(1)
    if not embeddings_path.exists():
        print(f"FAIL: embeddings não encontrado em {embeddings_path}")
        raise SystemExit(1)

    raise SystemExit(health_check(manifest_path, embeddings_path))
