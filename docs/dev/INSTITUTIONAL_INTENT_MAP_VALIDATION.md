# Institutional Intent Map Validation

O arquivo `data/contracts/responses/institutional_intent_map.yaml` usa `intent_id` como chave canônica.
Qualquer validação de duplicidade deve considerar apenas `intent_id` (não existe campo `intent`).
O lint estático cruza `concept_ref` com `data/concepts/concepts-institutional.yaml`.

Validações aplicadas:
- `intent_id` obrigatório em cada entrada de `intent_map`.
- `intent_id` deve ser único.
- `concept_ref` precisa existir em `concepts[].id`.
- `fallback.concept_ref` também precisa existir.

Execução local:
- `python scripts/quality/validate_institutional_intent_map.py`

Teste manual (integração):
- `curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question":"O que é a SIRIOS?"}'`
  - Deve retornar 3 camadas (direta, complemento útil, conceito).
  - Mesmo com `llm_enabled` ligado, a resposta institucional não deve ser reescrita pelo Narrator.
