#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: hash_guard.py
Purpose: Calcular hashes de referência para detectar drift em ontologia e golden sets.
Compliance: Guardrails Araquem v2.1.1
"""

import hashlib
import json
import sys
from pathlib import Path

TARGETS = [
    ("data/ontology", "data/ontology/.hash"),
    ("data/golden", "data/golden/.hash"),
]


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_files(dir_path: Path):
    for p in sorted(dir_path.rglob("*")):
        if p.is_file() and p.name != ".hash":
            yield p


def build_hash_index(dir_path: Path) -> dict:
    index = {}
    for p in collect_files(dir_path):
        rel = p.relative_to(dir_path).as_posix()
        index[rel] = sha256_of_file(p)
    # hash agregado (árvore)
    tree = hashlib.sha256(
        "\n".join(f"{k}:{index[k]}" for k in sorted(index.keys())).encode("utf-8")
    ).hexdigest()
    return {"files": index, "tree": tree}


def main():
    results = {}
    for src, out in TARGETS:
        src_path = Path(src)
        out_path = Path(out)
        if not src_path.exists():
            continue
        payload = build_hash_index(src_path)
        out_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        results[src] = payload["tree"]
    print(json.dumps({"ok": True, "trees": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
