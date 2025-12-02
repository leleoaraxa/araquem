#!/usr/bin/env python3
import json
import requests
from pathlib import Path

QUALITY_FILE = Path("data/ops/quality/rag_overview_risk_macro.json")
API_URL = "http://localhost:8000/ask"


def run_sample(sample):
    payload = {
        "question": sample["question"],
        "conversation_id": f"ragtest-{sample['id']}",
        "nickname": "Leleo",
        "client_id": "ragtest",
    }
    r = requests.post(API_URL, json=payload, timeout=60)
    return r.status_code, r.text


def main():
    data = json.loads(QUALITY_FILE.read_text())
    samples = data["samples"]

    print(f"\n=== Running {len(samples)} RAG/Overview/Risk/Macro samples ===\n")

    for s in samples:
        print(f"[{s['id']}] {s['question']}")
        status, text = run_sample(s)
        print(f"  → status={status}")
        print(f"  → answer={text[:200].replace(chr(10), ' ')}...\n")


if __name__ == "__main__":
    main()
