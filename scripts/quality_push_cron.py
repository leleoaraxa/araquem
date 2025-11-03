# scripts/quality_push_cron.py
import os, sys, json, hashlib, time, pathlib
import httpx

API_URL = os.environ.get("API_URL", "http://localhost:8000")
TOKEN = os.environ.get("QUALITY_OPS_TOKEN", "")
GLOB = os.environ.get("QUALITY_SAMPLES_GLOB", "data/ops/quality/*.json")
SLEEP_BETWEEN = float(os.environ.get("QUALITY_PUSH_SLEEP", "0.2"))
# Novo: header configurável e opção Authorization: Bearer
TOKEN_HEADER = os.environ.get("QUALITY_TOKEN_HEADER", "X-QUALITY-TOKEN").strip()
USE_BEARER = os.environ.get("QUALITY_AUTH_BEARER", "false").lower() in ("1","true","yes","on")

def sha256(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

ALLOWED_TYPES = {"routing", "projection"}


def load_payload(path: pathlib.Path):
    with open(path, "rb") as f:
        return json.load(f)


def push(path: pathlib.Path, data) -> dict:
    headers = {"Content-Type": "application/json"}
    if USE_BEARER:
        headers["Authorization"] = f"Bearer {TOKEN}"
    else:
        headers[TOKEN_HEADER] = TOKEN
    r = httpx.post(f"{API_URL}/ops/quality/push", headers=headers, json=data, timeout=30.0)

    r.raise_for_status()
    return r.json()

def main():
    base = pathlib.Path(".")
    files = sorted(base.glob(GLOB))
    if not files:
        print("[warn] no files matched:", GLOB)
        sys.exit(0)
    accepted = 0
    dry_run = "--dry-run" in sys.argv
    for p in files:
        try:
            data = load_payload(p)
            data_type = data.get("type") if isinstance(data, dict) else None
            if data_type not in ALLOWED_TYPES:
                print(f"[skip] {p} (unsupported or missing \"type\")")
                continue
            if dry_run:
                print(f"[post] {p}")
                accepted += 1
                continue
            h = sha256(p)
            out = push(p, data)
            print(f"[ok] {p} ({h[:8]}): {json.dumps(out, ensure_ascii=False)}")
            accepted += 1
            time.sleep(SLEEP_BETWEEN)
        except Exception as e:
            print(f"[err] {p}: {e}")
    print(f"[done] total accepted={accepted}")

if __name__ == "__main__":
    main()
