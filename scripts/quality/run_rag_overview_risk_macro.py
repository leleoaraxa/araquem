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
        "client_id": "66140994691",
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

        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            continue

        answer = payload.get("answer") if isinstance(payload, dict) else None
        if isinstance(answer, str) and answer.strip():
            continue

        status_block = payload.get("status") if isinstance(payload, dict) else {}
        meta_block = payload.get("meta") if isinstance(payload, dict) else {}
        gate_block = meta_block.get("gate") if isinstance(meta_block, dict) else {}

        print("  → answer is empty; diagnostics:")
        if isinstance(status_block, dict):
            print(f"     status.reason={status_block.get('reason')}")
            print(f"     status.message={status_block.get('message')}")
        if isinstance(gate_block, dict):
            print(f"     meta.gate.reason={gate_block.get('reason')}")
            for key in ["top2_gap", "min_gap", "min_score"]:
                if key in gate_block:
                    print(f"     meta.gate.{key}={gate_block.get(key)}")


if __name__ == "__main__":
    main()
