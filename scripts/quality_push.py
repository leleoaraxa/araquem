#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path

import httpx

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - runtime dependency check
    yaml = None

API = os.getenv("API_URL", "http://localhost:8000")
TOKEN = os.getenv("QUALITY_OPS_TOKEN", "araquem-secret-bust-2025")

def load_payload(path: str):
    suffix = Path(path).suffix.lower()
    if suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    if suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML não instalado – instale 'pyyaml' ou use .json")
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    raise ValueError(f"formato não suportado: '{suffix}' (use .json, .yaml ou .yml)")


def push(path: str):
    payload = load_payload(path)
    r = httpx.post(
        f"{API}/ops/quality/push",
        headers={"x-ops-token": TOKEN, "Content-Type": "application/json"},
        json=payload,
        timeout=30.0
    )
    r.raise_for_status()
    return r.json()

def main():
    if len(sys.argv) < 2:
        print(
            "usage: scripts/quality_push.py <payload.(json|yaml|yml)> "
            "[<payload.(json|yaml|yml)> ...]",
            file=sys.stderr,
        )
        sys.exit(2)
    total = 0
    for p in sys.argv[1:]:
        out = push(p)
        total += int(out.get("accepted") or 0)
        print(f"[ok] {p}: {json.dumps(out, ensure_ascii=False)}")
    print(f"[done] total accepted={total}")

if __name__ == "__main__":
    main()
