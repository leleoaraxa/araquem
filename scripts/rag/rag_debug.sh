#!/usr/bin/env bash
set -euo pipefail

# Script de debug do RAG no Araquem.
# Uso:
#   scripts/rag_debug.sh "pergunta em linguagem natural"
#   scripts/rag_debug.sh "pergunta em linguagem natural" --no-rag
#
# Exemplo:
#   scripts/rag_debug.sh "explique o risco do HGLG11"
#   scripts/rag_debug.sh "explique o risco do HGLG11" --no-rag
#
# Depende:
#   - serviço API do Araquem rodando (compose.dev)
#   - curl + jq instalados no container/host
#   - variável QUALITY_OPS_TOKEN (opcional; default só pra dev)

QUESTION="${1:-}"

if [ -z "$QUESTION" ]; then
  echo "Uso: $0 \"pergunta em linguagem natural\" [--no-rag]" >&2
  exit 1
fi

# Segundo argumento opcional: --no-rag → disable_rag=true
SECOND_ARG="${2:-}"
if [ "$SECOND_ARG" = "--no-rag" ] || [ "$SECOND_ARG" = "--disable-rag" ]; then
  DISABLE_RAG=true
else
  DISABLE_RAG=false
fi

ARAQUEM_URL="${ARAQUEM_URL:-http://localhost:8000}"

# Mesmo default do backend (apenas para DEV)
TOKEN="${QUALITY_OPS_TOKEN:-araquem-secret-bust-2025}"

PAYLOAD=$(jq -n \
  --arg q "$QUESTION" \
  --argjson disable_rag "$DISABLE_RAG" \
  '{
    question: $q,
    conversation_id: "rag-debug",
    nickname: "rag-debug",
    client_id: "ops",
    disable_rag: $disable_rag
  }'
)

echo ">> Enviando pergunta para ${ARAQUEM_URL}/ops/rag_debug"
echo ">> Pergunta: \"$QUESTION\""
echo ">> disable_rag: ${DISABLE_RAG}"
echo ">> X-Ops-Token: $( [ -n "$TOKEN" ] && echo 'definido' || echo 'NÃO DEFINIDO' )"
echo

RAW_RESPONSE=$(curl -sS -X POST \
  -H "Content-Type: application/json" \
  -H "X-Ops-Token: ${TOKEN}" \
  -d "$PAYLOAD" \
  "${ARAQUEM_URL}/ops/rag_debug")

# Guarda resposta bruta em arquivo de apoio
mkdir -p /tmp/araquem
if [ "$DISABLE_RAG" = true ]; then
  OUTFILE="/tmp/araquem/rag_debug_last_no_rag.json"
else
  OUTFILE="/tmp/araquem/rag_debug_last_with_rag.json"
fi
echo "$RAW_RESPONSE" > "$OUTFILE"

echo ">> Resposta salva em: $OUTFILE"
echo

echo "================= STATUS ================="
echo "$RAW_RESPONSE" | jq '.status'

echo
echo "================= META.RAG ==============="
echo "$RAW_RESPONSE" | jq '.meta.rag // "sem meta.rag"'

echo
echo "================= META.INTENT/ENTITY ====="
echo "$RAW_RESPONSE" | jq '{intent: .meta.intent, entity: .meta.entity}'

echo
echo "================= RAG – PROFILE & COLLECTIONS ====="
echo "$RAW_RESPONSE" | jq '{
  profile: (.meta.rag.profile // "n/a"),
  used_collections: (.meta.rag.used_collections // []),
  k: (.meta.rag.k // "n/a")
}'

echo
echo "================= CHUNKS (resumo) ========"
echo "$RAW_RESPONSE" | jq '(.meta.rag.chunks // []) | map({id: .id, score: .score, source: .source})'

echo
echo "================= PRIMEIROS FACTS ========"
echo "$RAW_RESPONSE" | jq '.results | to_entries[0] // {} | {view: .key, rows_sample: (.value[0:3])}'

echo
echo "================= TEXTO FINAL (answer) == "
echo "$RAW_RESPONSE" | jq '.answer // "sem answer (narrator desabilitado ou erro)"'

echo
echo "================= META.NARRATOR ========="
echo "$RAW_RESPONSE" | jq '.meta.narrator // "meta.narrator ausente"'
