#!/usr/bin/env python3
import os, json, uuid, httpx
from pathlib import Path

API = os.getenv("API_URL", "http://localhost:8000")
CID = os.getenv("QUALITY_CONVERSATION_ID", "ops-quality")
NICK = os.getenv("QUALITY_NICK", "ops")
CLIENT = os.getenv("QUALITY_CLIENT", "ops")
SRC = Path("data/ops/quality/routing_samples.json")
OUT = Path("data/ops/quality/routing_misses_via_ask.json")


def pick(d, *paths, default=None):
    """pega o primeiro caminho existente em dicts aninhados"""
    for path in paths:
        cur = d
        ok = True
        for k in path:
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                ok = False
                break
        if ok:
            return cur
    return default


def ask(q: str):
    payload = {
        "question": q,
        "conversation_id": CID,
        "nickname": NICK,
        "client_id": CLIENT,
    }
    r = httpx.post(f"{API}/ask", json=payload, timeout=60.0)
    r.raise_for_status()
    j = r.json()

    # tenta extrair pelos caminhos mostrados nos seus exemplos
    intent = pick(
        j, ("meta", "planner", "chosen", "intent"), ("planner_intent",), default=None
    )
    entity = pick(
        j, ("meta", "planner", "chosen", "entity"), ("planner_entity",), default=None
    )
    # opcional: score e explain para debug
    score = pick(
        j, ("meta", "planner", "chosen", "score"), ("planner_score",), default=None
    )
    return intent, entity, score, j


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    samples = data["samples"]
    misses = []
    for i, s in enumerate(samples, start=1):
        intent, entity, score, resp = ask(s["question"])
        ok = (intent == s["expected_intent"]) and (entity == s["expected_entity"])
        if not ok:
            misses.append(
                {
                    "idx": i,
                    "question": s["question"],
                    "expected_intent": s["expected_intent"],
                    "expected_entity": s["expected_entity"],
                    "got_intent": intent,
                    "got_entity": entity,
                    "score": score,
                    # pegue um resumo curto do explain para inspeção rápida:
                    "normalized": pick(
                        resp, ("meta", "planner", "normalized"), default=None
                    ),
                    "tokens": pick(resp, ("meta", "planner", "tokens"), default=None),
                    "intent_scores": pick(
                        resp, ("meta", "planner", "intent_scores"), default=None
                    ),
                    "thresholds": pick(
                        resp,
                        ("meta", "planner", "explain", "scoring", "thresholds_applied"),
                        default=None,
                    ),
                }
            )
    if misses:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(
            json.dumps(misses, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"❌ Misses: {len(misses)}  → salvos em {OUT}")
        for m in misses:
            print(
                f"[#{m['idx']:03d}] {m['question']}\n"
                f"    exp : {m['expected_intent']} / {m['expected_entity']}\n"
                f"    got : {m['got_intent']} / {m['got_entity']} (score={m['score']})\n"
            )
    else:
        print("✅ Sem misses.")


if __name__ == "__main__":
    main()
