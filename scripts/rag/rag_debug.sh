#!/usr/bin/env bash
set -euo pipefail

# Script de debug do RAG no Araquem.
# Uso:
#   scripts/rag_debug.sh "pergunta em linguagem natural"
#
# Exemplo:
#   scripts/rag_debug.sh "explique o risco do HGLG11"
#
# Depende:
#   - serviço API do Araquem rodando (compose.dev)
#   - curl + jq instalados no container/host

QUESTION="${1:-}"

if [ -z "$QUESTION" ]; then
  echo "Uso: $0 \"pergunta em linguagem natural\"" >&2
  exit 1
fi

ARAQUEM_URL="${ARAQUEM_URL:-http://localhost:8000}"

PAYLOAD=$(jq -n \
  --arg q "$QUESTION" \
  '{question: $q, conversation_id: "rag-debug", nickname: "rag-debug", client_id: "ops"}'
)

echo ">> Enviando pergunta para ${ARAQUEM_URL}/ask"
echo ">> Pergunta: \"$QUESTION\""
echo

RAW_RESPONSE=$(curl -sS -X POST \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  "${ARAQUEM_URL}/ask")

# Guarda resposta bruta em arquivo de apoio
mkdir -p /tmp/araquem
echo "$RAW_RESPONSE" > /tmp/araquem/rag_debug_last.json

echo "================= STATUS ================="
echo "$RAW_RESPONSE" | jq '.status'

echo
echo "================= META.RAG ==============="
echo "$RAW_RESPONSE" | jq '.meta.rag // "sem meta.rag"'

echo
echo "================= CHUNKS (resumo) ========"
echo "$RAW_RESPONSE" | jq '(.meta.rag.chunks // []) | map({id: .id, score: .score, source: .source})'

echo
echo "================= PRIMEIROS FACTS ========"
echo "$RAW_RESPONSE" | jq '.results | to_entries[0] // {} | {view: .key, rows_sample: (.value[0:3])}'

echo
echo "================= TEXTO FINAL (se houver narrator) =="
# Se você tiver um wrapper que já chama o Narrator, adapte aqui.
# Caso contrário, isso mostra só o resultado tabular.
echo "$RAW_RESPONSE" | jq '.meta.narrator // "narrator não integrado neste endpoint"'
