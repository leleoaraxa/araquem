#!/usr/bin/env bash
set -euo pipefail
python /app/scripts/embeddings/rag_retrieval_eval.py \
  --eval data/ops/quality/rag_eval_set.json \
  --k 10 \
  --index data/embeddings/store/embeddings.jsonl \
  --api-url http://api:8000
echo "[rag-eval-cron] metrics registered"
