#!/bin/sh
set -e

echo "[init] iniciando ollama serve em background..."
ollama serve >/tmp/ollama-serve.log 2>&1 &
SERVE_PID=$!

echo "[init] aguardando daemon..."
until ollama ps >/dev/null 2>&1; do sleep 1; done

# 1) pull dos modelos base (embeddings + base LLM)
for m in ${OLLAMA_MODELS:-}; do
  if ollama show "$m" >/dev/null 2>&1; then
    echo "[init] modelo já presente: $m"
  else
    echo "[init] puxando modelo: $m"
    ollama pull "$m"
  fi
done

# 2) criação do modelo customizado sirios-narrator:latest
if ollama show sirios-narrator:latest >/dev/null 2>&1; then
  echo "[init] modelo já presente: sirios-narrator:latest"
else
  MF="${SIRIOS_MODEFILE:-/app/docker/Modelfile.sirios-narrator}"
  if [ -f "$MF" ]; then
    echo "[init] criando modelo sirios-narrator:latest a partir de $MF"
    ollama create sirios-narrator:latest -f "$MF"
  else
    echo "[init][WARN] Modelfile do sirios-narrator não encontrado em $MF"
  fi
fi

echo "[init] modelos prontos. mantendo o daemon em foreground..."
wait $SERVE_PID
