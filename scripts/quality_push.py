#!/usr/bin/env python3
import os, sys, json, httpx

API = os.getenv("API_URL", "http://localhost:8000")
TOKEN = os.getenv("QUALITY_OPS_TOKEN", "araquem-secret-bust-2025")

def push(path: str):
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
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
        print("usage: scripts/quality_push.py <json-file> [<json-file> ...]", file=sys.stderr)
        sys.exit(2)
    total = 0
    for p in sys.argv[1:]:
        out = push(p)
        total += int(out.get("accepted") or 0)
        print(f"[ok] {p}: {json.dumps(out, ensure_ascii=False)}")
    print(f"[done] total accepted={total}")

if __name__ == "__main__":
    main()
