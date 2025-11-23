# LLM Prompt Policies — Araquem v2.1.1

## Narrator (Llama 3.1 local via Ollama)

- Modelo alvo: `llama3.1:latest` (via Ollama, configurado em `data/policies/narrator.yaml`).
- Prompt do Narrator é **minimalista**, em PT-BR, com foco em:
  - respostas curtas (até 2–3 parágrafos),
  - tom executivo e neutro,
  - uso exclusivo de números presentes em FACTS,
  - uso do RAG apenas para contexto conceitual.
- Em caso de erro do LLM ou ausência total de evidência (sem rows e sem chunks de RAG),
  o fail-safe canônico é: “Não sei responder com segurança agora. Exemplos de perguntas válidas: 'cnpj do MCCI11', 'preço do MXRF11 hoje'.”


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
- **Privacidade/PII**: Para entidades `private: true` (ex.: `client_fiis_positions`), **ignore qualquer PII no texto do usuário**. Os parâmetros sensíveis (ex.: `document_number`) **devem vir apenas do payload seguro**. **Nunca** ecoe números de documentos na resposta.
- **Logs/telemetria:** Não registre PII em logs, traces ou mensagens de erro. Oculte/mascare qualquer identificador sensível.
- Citar fontes usadas: id/score dos chunks.
- Respeitar templates/formatos definidos pela entidade quando existirem.
- Se faltar evidência: “Não encontrei evidências suficientes…”.

> Desambiguação obrigatória: pedidos de dado bruto D-1 (por exemplo, preço, dividendo, posição, cadastro) devem ser roteados para a entidade tabular correspondente. Pedidos analíticos/estatísticos/“no período” permanecem indisponíveis: análises compute-on-read desativadas temporariamente; projeto opera apenas com 11 D-1.
**Saída (JSON):**
{
  "answer": "…",
  "sources": [{"id":"chunk-123","score":0.78}]
}

## Fail-safe (fora do domínio / sem contexto)
Responder: “Não sei com segurança. **Exemplos de perguntas válidas**: 'cnpj do MCCI11', 'preço do MXRF11 hoje'.”
