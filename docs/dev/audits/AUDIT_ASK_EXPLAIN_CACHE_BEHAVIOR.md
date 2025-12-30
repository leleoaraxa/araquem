## O que o código faz

- `app/api/ask.py` processa todas as requisições com `planner.explain(...)` independentemente do parâmetro `explain`; o parâmetro só ativa métricas/analytics adicionais e inclui o bloco `explain` no payload de resposta quando `True`. 【F:app/api/ask.py†L54-L76】【F:app/api/ask.py†L337-L395】
- O cache de resposta é tentado quando a estratégia da entidade permite (`read_through`, TTL>0 e entidade pública). O `cache_key` é construído por `make_plan_cache_key(build_id, scope, entity, plan_hash)` sem considerar `explain`, e a leitura ocorre antes de qualquer branch de `explain`. 【F:app/api/ask.py†L168-L248】
- O cache só é gravado quando não houve hit, o status é `ok`, há `result_key` com linhas, a payload é cacheável e há TTL. Esse fluxo é igual para `explain=True` e `False`; não há bypass explícito ou alteração de key/TTL baseada em `explain`. 【F:app/api/ask.py†L302-L336】
- As respostas de erro (`unroutable`/`gated`) nunca são cacheadas e retornam sem escrever. Isso é independente do parâmetro `explain`. 【F:app/api/ask.py†L249-L302】

## Como medir com o runner

Execute duas vezes a mesma suíte, com os mesmos `conversation_id` e `client_id`, para comparar hits:

- Com explain (default):
  - `python scripts/diagnostics/run_ask_suite.py --suite client_fiis_performance_vs_benchmark_summary --base-url http://localhost:8000 --conversation-id TEST123 --client-id CLIENTX`
  - Repetir o mesmo comando para observar `cache_hit_response`.
- Sem explain:
  - `python scripts/diagnostics/run_ask_suite.py --suite client_fiis_performance_vs_benchmark_summary --no-explain --base-url http://localhost:8000 --conversation-id TEST123 --client-id CLIENTX`
  - Repetir o mesmo comando para observar `cache_hit_response` refletindo o cache real.

## Conclusão binária

**explain=true bypass cache de resposta? NÃO.** A leitura e escrita de cache não usam o parâmetro `explain` para alterar key, TTL, ou forçar bypass; o fluxo de cache é igual para ambos os modos. 【F:app/api/ask.py†L168-L336】
