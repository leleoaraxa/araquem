# scripts/quality_push_cron.py
import os, sys, json, hashlib, time, pathlib
import httpx

API_URL = os.environ.get("API_URL", "http://localhost:8000")
TOKEN = os.environ.get("QUALITY_OPS_TOKEN", "")
GLOB = os.environ.get("QUALITY_SAMPLES_GLOB", "data/ops/quality/*.json")
SLEEP_BETWEEN = float(os.environ.get("QUALITY_PUSH_SLEEP", "0.2"))

def sha256(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def push(path: pathlib.Path) -> dict:
    with open(path, "rb") as f:
        data = json.load(f)
    r = httpx.post(
        f"{API_URL}/ops/quality/push",
        headers={"X-QUALITY-TOKEN": TOKEN, "Content-Type": "application/json"},
        json=data,
        timeout=30.0,
    )
    r.raise_for_status()
    return r.json()

def main():
    base = pathlib.Path(".")
    files = sorted(base.glob(GLOB))
    if not files:
        print("[warn] no files matched:", GLOB)
        sys.exit(0)
    accepted = 0
    for p in files:
        try:
            h = sha256(p)
            out = push(p)
            print(f"[ok] {p} ({h[:8]}): {json.dumps(out, ensure_ascii=False)}")
            accepted += 1
            time.sleep(SLEEP_BETWEEN)
        except Exception as e:
            print(f"[err] {p}: {e}")
    print(f"[done] total accepted={accepted}")

if __name__ == "__main__":
    main()
