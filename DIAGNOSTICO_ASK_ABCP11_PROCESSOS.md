# Diagnóstico do fluxo /ask — pergunta: "Existe processos para o ABCP11 e quais são?"

## Resumo executivo
- Planner roteou corretamente para `fiis_processos` com `result_key` `processos_fii` e retornou 4 linhas, porém a resposta final foi "Não encontrei registros para essa consulta."【F:response.md†L7-L69】【F:response.md†L103-L142】
- Presenter construiu `facts` com `rows` a partir de `results[result_key]`, mas o Narrator foi chamado em modo `rewrite_only` e removeu `rows`/`primary` do payload enviado ao LLM.【F:app/presenter/presenter.py†L265-L380】
- No Narrator, o texto baseline determinístico (`rendered_text`) foi usado como única evidência; a validação de âncoras exige números de processo e pode ter falhado, levando a fallback para baseline vazio ou `_default_text` → mensagem de ausência de dados.【F:app/narrator/narrator.py†L947-L981】【F:app/narrator/narrator.py†L1178-L1209】
- Não há RAG nem shadow; compute_mode "data" com `rewrite_only=true` para `fiis_processos` implica dependência total do campo `rendered_text`, que pode estar vazio por formatação/template.【F:response.md†L74-L115】【F:app/presenter/presenter.py†L299-L324】
- Divergência provável entre `results.processos_fii` (com dados) e `facts_wire` enviado ao Narrator (sem rows/identifiers) causa percepção de "zero evidência" e resposta negativa.【F:response.md†L7-L69】【F:app/presenter/presenter.py†L365-L380】

## Evidências do response.md
- `results.processos_fii`: 4 registros completos para ABCP11.【F:response.md†L7-L69】
- Planner: intent/entity `fiis_processos`, normalized question "existe processos para o abcp11 e quais sao", `result_key` `processos_fii`, `rows_total`: 4.【F:response.md†L103-L142】
- Narrator: `enabled=true`, `rewrite_only=true`, `rag.enabled=false`, `compute_mode=data`, `strategy=llm`. Latência ~35s.【F:response.md†L139-L182】
- Answer final: "Não encontrei registros para essa consulta."【F:response.md†L183-L184】

## Auditoria por etapa do pipeline

### 1) API / entrada HTTP
- **Contrato esperado:** `/ask` recebe `question`, `conversation_id`, `nickname`, `client_id` e delega a planner/orchestrator/presenter, retornando `status`, `results`, `meta`, `answer`.
- **Evidência:** Endpoint definido em `app/api/ask.py` (`@router.post("/ask")`) pega `AskPayload`, chama `planner.explain` e `orchestrator.route_question`, depois `present` para montar resposta.【F:app/api/ask.py†L57-L321】
- **Possível falha:** Linha 292-298 escolhe `result_key` como `meta.result_key` ou primeira chave; se meta for sobrescrita antes do presenter, rows podem ficar inconsistentes. 【F:app/api/ask.py†L292-L298】 Comentário: se `meta.result_key` viesse `None` ou divergente, presenter pode montar facts com chave errada, perdendo linhas.

### 2) Normalização / Planner
- **Contrato esperado:** normalizar pergunta, pontuar intents e escolher `fiis_processos` com `result_key` compatível.
- **Evidência:** Planner retorna `normalized` e `chosen` com `intent/entity=fiis_processos`, `result_key=processos_fii`, `rows_total=4`. 【F:response.md†L103-L142】
- **Possível falha:** Se thresholds/gate alterarem `result_key` ou bloquearam, meta poderia sinalizar `rows_total` incorreto; verificar `orchestrator.route_question` gate block. 【F:app/orchestrator/routing.py†L406-L468】 Comentário: gate aplica blocos por score/gap; para score 1.87 não bloqueou, mas se gatilho mudasse em produção poderia retornar meta ok com rows vazios.

### 3) Orchestrator / Routing
- **Contrato esperado:** construir SQL via `build_select_for_entity`, executar e armazenar em `results[result_key]`; meta inclui `result_key`, `aggregates`, `rag`.
- **Evidência:** `route_question` define `result_key` e `results = {result_key: final_rows}`; meta inclui `rows_total=len(final_rows)`, `rag` etc.【F:app/orchestrator/routing.py†L609-L770】
- **Possível falhas:**
  1. Cache path converte `orchestration_raw` não-estruturado em `{results: legacy_results}`; se algum caller devolvesse lista pura, `result_key` poderia cair como `None` e rows vazios.【F:app/api/ask.py†L279-L297】 Comentário: resultado do cache pode não carregar meta correta → presenter sem rows.
  2. `result_key = cached_result_key` quando `metrics_cache_hit`, mas cache armazena somente `result_key` e `rows`; se cache tiver payload antigo com chave diferente, rows não correspondem à entidade atual.【F:app/orchestrator/routing.py†L520-L684】 Comentário: risco de mismatch se rota for reutilizada.
  3. `meta['compute']['mode']` define "conceptual" quando `skip_sql`; em tal caso rows são list vazia mesmo com dados esperados. 【F:app/orchestrator/routing.py†L510-L738】 Comentário: se `requires_identifiers` estiver configurado e ticker não detectado, SQL é pulado → Narrator sem dados.

### 4) Executor (SQL)
- **Contrato esperado:** `PgExecutor.query` retorna lista de dicts; `format_rows` aplica colunas declarativas.
- **Evidência:** `route_question` chama `self._exec.query(sql, params)` e `format_rows(rows_raw, return_columns)`; resultado vai para `results[result_key]`.【F:app/orchestrator/routing.py†L608-L770】
- **Possível falha:** `format_rows` retorna `[]` silenciosamente se colunas/template não baterem com dados, mantendo `rows_total` zero apesar de dados na base. 【F:app/formatter/rows.py†L90-L118】 Comentário: inconsistência entre dados reais e rows expostos ao presenter.

### 5) Presenter / Formatter / Facts Payload
- **Contrato esperado:** `build_facts` pega `results[result_key]` e preenche `facts.rows` e `facts.primary`; presenter monta baseline (`render_answer`/`render_rows_template`) e injeta `facts_wire` no Narrator.
- **Evidência:** `facts.rows = results[result_key]` (lista) e `primary = rows[0]`. 【F:app/presenter/presenter.py†L137-L182】
- **Possíveis falhas (críticas):**
  1. `meta_result_key` validado apenas se presente em `results`; se `meta.result_key` divergir (`processos_fii` vs outro), `result_key` vira primeira chave e pode ser `None`, deixando `rows=[]`. 【F:app/presenter/presenter.py†L136-L151】 Comentário: qualquer inconsistência meta/results zera evidência.
  2. `facts_wire` para Narrator em rewrite-only remove `rows`, `primary`, `identifiers`, `aggregates`, mantendo só `rendered_text`. 【F:app/presenter/presenter.py†L365-L380】 Comentário: se `rendered_text` for vazio, Narrator recebe payload sem dados → fallback vazio.
  3. `render_rows_template` pode retornar string vazia se template YAML inexistente/mal formatado; então `baseline_answer` vira `technical_answer`, que pode ser vazio se `render_answer` não cobrir entidade `fiis_processos`. 【F:app/presenter/presenter.py†L299-L324】 Comentário: `facts_md` pode ser vazio, afetando rewrite-only anchors.
  4. `render_answer` (legacy) pode não conhecer campos específicos de processos, retornando ""; isso é o texto usado quando não há template. 【F:app/presenter/presenter.py†L299-L321】 Comentário: baseline vazio gera mensagem genérica no Narrator.
  5. `context_history_wire` só é populado se `context_manager` permitir; ausência não deve impactar evidência, mas meta para Narrator pode ficar incompleta. 【F:app/presenter/presenter.py†L255-L264】 Comentário: sem histórico, rewrite-only perde âncoras contextuais.

### 6) Narrator
- **Contrato esperado:** usar `facts`/`rendered_text` para gerar resposta; em `rewrite_only`, deve reescrever texto mantendo âncoras (número de processo).
- **Evidências:** narrator policy efetiva inclui `rewrite_only=true`; baseline `rendered_text` alimenta prompt; validação exige que saída contenha algum número da string `rendered_text` (`has_process_anchor`).【F:app/narrator/narrator.py†L1178-L1209】
- **Possíveis falhas:**
  1. `_default_text` retorna mensagem "Sem dados disponíveis" se `rendered_text` vazio e `rows` removidas, produzindo resposta negativa mesmo com dados. 【F:app/narrator/narrator.py†L184-L202】
  2. `has_process_anchor` verifica tokens numéricos em `rendered_text`; se o template condensar números (ex.: com pontos/hífens) ou truncar, âncoras não encontradas → fallback para baseline (possivelmente vazio). 【F:app/narrator/narrator.py†L1178-L1209】
  3. `rewrite_only` limpa `rows`/`primary`; se `rendered_text` vier vazio do presenter, LLM recebe prompt sem evidências e `_default_text` devolve mensagem de ausência. 【F:app/presenter/presenter.py†L365-L380】【F:app/narrator/narrator.py†L947-L981】
  4. `max_llm_rows`/`effective_enabled` controlam estratégia: se `max_llm_rows`=0 para entidade em policy, estratégia vira determinístico e `baseline_text` vazio gera fallback genérico. 【F:app/narrator/narrator.py†L789-L838】【F:app/narrator/narrator.py†L1007-L1120】 Comentário: verificar policy YAML para `fiis_processos`.

### 7) Montagem do answer final
- **Contrato esperado:** `presenter_result.answer` retorna texto final (Narrator ou baseline), repassado por `app/api/ask.py` em `payload_out['answer']`.
- **Evidência:** `answer` do response é exatamente `presenter_result.answer`; meta inclui `narrator` com `rewrite_only=true` e `strategy=llm`. 【F:app/api/ask.py†L401-L432】【F:response.md†L139-L184】
- **Possível falha:** Se Narrator devolve texto vazio ou fallback "Sem dados disponíveis", API não revalida contra `rows_total`; resposta negativa é retornada apesar de `rows_total=4`. 【F:app/api/ask.py†L401-L432】 Comentário: falta de checagem pós-narrator.

## Hipóteses ranqueadas
1. **Alta:** Payload para Narrator em `rewrite_only` removeu `rows` e dependeu de `rendered_text` vazio/sem âncoras, levando `_default_text` a responder ausência de dados.【F:app/presenter/presenter.py†L365-L380】【F:app/narrator/narrator.py†L184-L202】
2. **Alta:** Template/renderer para `fiis_processos` não produziu `rendered_text` contendo números de processo, falhando na validação de âncoras (`has_process_anchor`) e caindo em baseline vazio.【F:app/presenter/presenter.py†L299-L324】【F:app/narrator/narrator.py†L1178-L1209】
3. **Média:** `result_key` ou `rows` divergentes por cache/legacy path fizeram `facts.rows=[]` apesar de `results.processos_fii` existir no response; presenter escolhe chave errada silenciosamente.【F:app/api/ask.py†L279-L297】【F:app/presenter/presenter.py†L136-L151】
4. **Média:** Política do Narrator para `fiis_processos` pode ter `max_llm_rows=0` ou `llm_enabled=false` em produção, forçando estratégia determinística com baseline vazio e mensagem negativa.【F:app/narrator/narrator.py†L789-L838】【F:app/narrator/narrator.py†L1007-L1120】
5. **Baixa:** `format_rows` retornou vazio por incompatibilidade de colunas/decimal, mas meta `rows_total=4` indica formatação deveria ter dados; ainda assim, mismatch entre meta e fato pode existir em outras execuções.【F:app/formatter/rows.py†L90-L118】【F:response.md†L103-L142】

## Checks recomendados (sem alterar código)
- `python - <<'PY'` para imprimir `render_rows_template('fiis_processos', <rows>)` usando os dados de `response.md`, verificando se `rendered_text` sai vazio ou sem números de processo.
- `python - <<'PY'` para simular `build_facts` com `results={'processos_fii': ...}` e inspecionar `facts_wire` antes de Narrator quando `rewrite_only=true`.
- `cat data/policies/narrator.yaml | yq '.entities.fiis_processos'` para checar `llm_enabled`, `rewrite_only`, `max_llm_rows` e `empty_message` configurados.
- `python - <<'PY'` para validar `render_answer('fiis_processos', rows)` e ver se retorna string vazia.
- Ver logs do Narrator no momento (`grep -i "NARRATOR_FINAL_TEXT" tempo/*` ou observabilidade) para confirmar se estratégia foi `llm_skipped_no_evidence` ou falha de âncoras.
