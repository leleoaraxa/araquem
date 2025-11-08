#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Avaliação rápida do Narrator em modo local."""
from __future__ import annotations
import argparse, json
from app.narrator.narrator import Narrator

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload", required=True, help="arquivo JSON com 'executor_payload'")
    args = ap.parse_args()

    data = json.loads(open(args.payload, "r", encoding="utf-8").read())
    payload = data.get("executor_payload") or data
    question = payload.get("question","")
    facts = payload.get("facts",{})
    meta = payload.get("meta",{})
    meta.setdefault("intent", payload.get("intent"))
    meta.setdefault("entity", payload.get("entity"))

    n = Narrator()
    out = n.render(question=question, facts=facts, meta=meta)
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
