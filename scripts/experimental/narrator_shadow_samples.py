import json
import requests

BASE_URL = "http://localhost:8000/ask"
SAMPLES_PATH = "data/ops/quality_experimental/narrator_shadow_samples.json"

with open(SAMPLES_PATH, "r", encoding="utf-8") as f:
    payload = json.load(f)

for sample in payload.get("samples", []):
    q = sample["question"]
    sample_id = sample["id"]

    body = {
        "question": q,
        "conversation_id": f"shadow-{sample_id}",
        "nickname": "narrator-shadow",
        "client_id": None,
    }

    print(f"\n=== {sample_id} :: {q}")
    resp = requests.post(BASE_URL, json=body, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    meta = data.get("meta", {}) or {}
    narrator_meta = meta.get("narrator") or meta.get("narrator_meta") or {}

    print("  entity:", meta.get("entity"))
    print("  narrator.strategy:", narrator_meta.get("strategy"))
    print("  narrator.enabled:", narrator_meta.get("enabled"))
    print("  narrator.shadow:", narrator_meta.get("shadow"))
    print("  narrator.latency_ms:", narrator_meta.get("latency_ms"))
