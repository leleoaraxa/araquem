#!/usr/bin/env bash
set -euo pipefail

FILE="${1:-}"
if [ -z "$FILE" ]; then
  echo "Uso: $0 data/quality/rag_golden_set.json [--no-rag]" >&2
  exit 1
fi

SECOND_ARG="${2:-}"
if [ "$SECOND_ARG" = "--no-rag" ] || [ "$SECOND_ARG" = "--disable-rag" ]; then
  RAG_FLAG="--no-rag"
else
  RAG_FLAG=""
fi

echo ">> Lendo perguntas de: $FILE"
TOTAL=$(jq 'length' "$FILE")
echo ">> Total de perguntas: $TOTAL"
echo

for row in $(jq -c '.[]' "$FILE"); do
  ID=$(echo "$row" | jq -r '.id')
  Q=$(echo "$row"  | jq -r '.question')
  EXPECT_INTENT=$(echo "$row" | jq -r '.expected_intent')
  EXPECT_RAG=$(echo "$row"    | jq -r '.expect_rag')

  echo "=================================================="
  echo "ID: $ID"
  echo "Pergunta: $Q"
  echo "Esperado -> intent: $EXPECT_INTENT | RAG: $EXPECT_RAG"
  echo "--------------------------------------------------"

  # Reutiliza o script já existente
  scripts/rag/rag_debug.sh "$Q" $RAG_FLAG

  echo
done
