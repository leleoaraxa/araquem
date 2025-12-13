# PATCH NOTES — ASK ABCP11 PROCESSOS (Hotfix)

## Resumo
- Fortalecida seleção determinística de `result_key` com diagnóstico em meta e logs quando a chave informada não existe.
- Ajustado wiring em `rewrite_only` para preservar evidências compactas (rows_compact/anchors) e baseline não vazio.
- Validação pós-Narrator garante âncoras quando há linhas: respostas vazias, negativas ou sem lastro voltam para o baseline determinístico.
- Testes de reprodução usando `response_A.md` e `response_B.md` cobrindo ausência e narrativa sem âncoras.

## Arquivos alterados
- `app/api/ask.py`
- `app/presenter/presenter.py`
- `tests/test_ask_processos_rewrite_only_coherence.py`

## Rationale
- `response_A/B` mostraram `rows_total>0` mas respostas negativas/genéricas; o hotfix assegura coerência entre evidência e texto final, evitando deriva em rewrite_only e corrigindo inconsistências de `result_key`.

## Como validar
1) Rodar testes automatizados:
   - `pytest tests/test_ask_processos_rewrite_only_coherence.py`
2) Repro manual:
   - Carregar `response_A.md` e `response_B.md` como payloads simulados e chamar o Presenter com Narrator em `rewrite_only=true`.
   - Esperado: ambas retornam baseline determinístico contendo números de processo; nenhuma mensagem de “sem dados” com `rows_total>0`.
