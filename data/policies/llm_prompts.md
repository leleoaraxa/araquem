# LLM Prompt Policies — Araquem v2.1.1

## Planner-Explain (análise de intenção)
**Objetivo:** justificar a escolha de intent/entity com evidências.
**Regras:**
- Liste tokens e phrases acionadas e seus pesos/contagens (se disponíveis).
- Mostre top-3 intents com score e `min_gap` entre top-1 e top-2.
- Nunca invente dado; se ambíguo, sinalize e sugira pergunta de desambiguação.
**Saída (JSON):**
{
  "top_intents": [{"name":"cadastro","score":0.92}, {"name":"precos","score":0.61}],
  "min_gap": 0.31,
  "evidence": {"tokens":["cnpj","administrador"], "phrases":["cnpj do"]},
  "notes": "…"
}

## RAG-Answer (resposta com contexto)
**Objetivo:** responder em PT-BR curto usando **apenas** o contexto fornecido.
**Regras:**
- Citar fontes usadas: id/score dos chunks.
- Respeitar templates/formatos definidos pela entidade quando existirem.
- Se faltar evidência: “Não encontrei evidências suficientes…”.
**Saída (JSON):**
{
  "answer": "…",
  "sources": [{"id":"chunk-123","score":0.78}]
}

## Fail-safe (fora do domínio / sem contexto)
Responder: “Não sei com segurança. Exemplos: 'cnpj do MCCI11', 'preço do MXRF11 hoje'.”
