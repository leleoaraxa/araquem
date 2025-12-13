# Diagnóstico do fluxo /ask — "Existe processos para o ABCP11 e quais são?"

## 1. Resumo executivo
- O fluxo /ask seleciona a entidade `fiis_processos` com `result_key` inferida e executa SQL que retorna 4 linhas para `processos_fii`, porém a resposta final pode negar dados ou alucinar porque o pipeline depende de metadados frágeis (result_key/meta) e remove evidências antes do Narrator.
- O modo `rewrite_only` do Narrator descarta `rows`, `primary` e `aggregates`, obrigando a geração textual a confiar apenas em `rendered_text`; qualquer ausência/vazio desse campo provoca respostas vazias ou inventadas mesmo com `rows_total > 0`.
- Não existe validação pós-Narrator: respostas negativas ou genéricas são retornadas mesmo quando `results.processos_fii` está populado, como mostrado nas execuções reais A (vazia) e B (alucinação).

## 2. Fluxo técnico (/ask → answer)
1. `/ask` recebe o payload, chama o Planner e recupera `entity`/`intent`/`score`. Se `entity` existe, prossegue para orquestração e cache. 【F:app/api/ask.py†L65-L155】
2. `orchestrator.route_question` refaz o planejamento, aplica gates, extrai identificadores, constrói SQL, formata linhas e monta `meta.result_key`, `rows_total` e `compute.mode`. 【F:app/orchestrator/routing.py†L362-L740】
3. `/ask` deriva `result_key` como `meta.result_key` ou primeira chave de `results`, calcula `rows` e chama o Presenter com `results` e `meta` originais. 【F:app/api/ask.py†L292-L320】
4. `presenter.build_facts` escolhe `result_key` priorizando `meta.result_key` existente em `results`; caso contrário, usa o primeiro item de `results`. Retorna `facts.rows`/`primary`. 【F:app/presenter/presenter.py†L136-L184】
5. O Presenter monta baseline (`technical_answer` + `render_rows_template`) e, com policy `llm_enabled/rewrite_only`, remove `rows`, `primary`, `identifiers` e `aggregates` antes de invocar o Narrator. 【F:app/presenter/presenter.py†L299-L380】
6. O Narrator aplica `_default_text` priorizando `rendered_text`; se ausente, tenta `rows` (que já foram removidos em rewrite_only), caindo para mensagens vazias ou genéricas. Política efetiva controla `strategy` e não valida consistência com `rows_total`. 【F:app/narrator/narrator.py†L183-L201】
7. A resposta final do `/ask` inclui `answer` sem checagem pós-Narrator, mesmo que `rows_total > 0`. 【F:app/api/ask.py†L401-L520】

## 3. Auditoria por etapa
### 3.1 API `/ask`
- Seleção de `result_key` usa `meta.result_key` ou `next(iter(results))`, o que pode pegar chave errada quando `meta.result_key` diverge do payload real; se `results` não contém a chave, `rows` vira `[]` silenciosamente. 【F:app/api/ask.py†L292-L299】
- Caminho legacy converte qualquer dict em `results` mesmo sem `status/meta`, ocultando shape inválido e permitindo `rows=[]` com `status ok`. 【F:app/api/ask.py†L279-L291】

### 3.2 Planner
- Planner é chamado duas vezes (em `/ask` e no Orchestrator) sem compartilhamento de `meta.result_key`, abrindo janela para divergência entre `plan` e `orchestration.meta`. 【F:app/api/ask.py†L65-L77】【F:app/orchestrator/routing.py†L362-L379】
- Gates silenciosos retornam `results={}` com `status ok` e `rows_total=0`, induzindo o Presenter/Narrator a produzir respostas negativas mesmo quando a consulta deveria ser bloqueada explicitamente. 【F:app/orchestrator/routing.py†L392-L468】

### 3.3 Orchestrator / Routing
- `result_key` é definido a partir do `build_select_for_entity` e colocado em `meta`, mas `/ask` pode sobrescrever ao usar `next(iter(results))` se `meta.result_key` for `None` ou inválido. 【F:app/orchestrator/routing.py†L690-L770】【F:app/api/ask.py†L292-L299】
- Modo conceitual (`skip_sql`) gera `rows=[]` com `status ok`, preservando `meta.rows_total=0`, o que alimenta Narrator com ausência artificial de dados mesmo que caches SQL tivessem linhas. 【F:app/orchestrator/routing.py†L510-L737】
- Cache de métricas retorna `rows_formatted` sem validar colunas; `format_rows` não é chamado em hit, podendo deixar `rows` em shape inesperado para Presenter/Narrator. 【F:app/orchestrator/routing.py†L520-L684】

### 3.4 Executor / Formatter
- `format_rows` é bypassado em hits de cache, logo `rows` podem estar com colunas faltantes para o template e serem descartadas no Presenter. 【F:app/orchestrator/routing.py†L654-L684】

### 3.5 Presenter
- `build_facts` aceita `meta.result_key` mesmo que não exista em `results`; se ausente, pega primeira chave, podendo ignorar `processos_fii` quando vier em posição diferente. 【F:app/presenter/presenter.py†L136-L184】
- `render_rows_template` pode retornar string vazia; com `template_used=False`, `baseline_answer` vira `technical_answer` que pode ser genérico, mas em `rewrite_only` é removido antes do LLM, deixando apenas `facts_md` potencialmente vazio. 【F:app/presenter/presenter.py†L299-L325】【F:app/presenter/presenter.py†L370-L380】
- Em `rewrite_only`, `rows`, `primary`, `identifiers`, `aggregates` são removidos do `facts_wire`, eliminando evidência para o Narrator. 【F:app/presenter/presenter.py†L370-L380】

### 3.6 Narrator
- `_default_text` prioriza `rendered_text` e só usa `rows` se presentes; com `rewrite_only`, os dados são removidos e o Narrator cai para mensagem vazia/"Sem dados" mesmo com `rows_total > 0`. 【F:app/narrator/narrator.py†L183-L201】
- Não há validação de âncoras de processos (`has_process_anchor` inexistente); qualquer texto passado em `rendered_text` é aceito, permitindo narrativas extrapoladas. 【F:app/narrator/narrator.py†L183-L201】

### 3.7 Montagem final do `answer`
- `/ask` não revalida se `presenter_result.answer` condiz com `rows_total`; retorna `answer` mesmo quando contradiz `results`. 【F:app/api/ask.py†L401-L520】

## 4. Hipóteses ranqueadas (causas prováveis)
1. **Perda de evidência no rewrite_only**: `facts_wire` enviado ao Narrator não contém `rows`, restando apenas `rendered_text`. Se `render_rows_template` falha ou retorna vazio, o Narrator produz mensagem negativa (execução A). 【F:app/presenter/presenter.py†L370-L380】【F:app/narrator/narrator.py†L183-L201】
2. **Divergência de `result_key`**: diferença entre `meta.result_key`, `results` e fallback `next(iter(results))` pode selecionar chave errada ou esvaziar `rows`, levando a resposta de ausência. 【F:app/api/ask.py†L292-L299】【F:app/presenter/presenter.py†L136-L184】
3. **Narrativas extrapoladas**: com `rewrite_only` e ausência de checagem, o Narrator pode usar `_default_text` baseado em fragmentos de `rendered_text` ou prompts, gerando texto genérico (execução B). 【F:app/narrator/narrator.py†L183-L201】
4. **Planner duplicado sem coerência**: Planner roda duas vezes; se thresholds/gates diferirem ou cache alterar ordem das chaves, pode haver `rows_total>0` mas Narrator receber contexto inconsistente. 【F:app/api/ask.py†L65-L77】【F:app/orchestrator/routing.py†L362-L379】

## 5. 🔁 Diferença entre execução A (empty) e execução B (hallucinated)
- **Facts_wire e rendered_text**: Em A, apesar de `results.processos_fii` trazer 4 registros, o answer final afirma ausência de dados (indicando `facts_wire.rendered_text` vazio ou descartado). 【F:response_A.md†L6-L64】 Em B, a resposta traz narrativa genérica não baseada nos campos retornados, sugerindo que `rendered_text` foi usado sem validação. 【F:response_B.md†L6-L64】
- **Estratégia do Narrator**: Ambos usam policy `llm_enabled: true`, `rewrite_only: true`, `rag: false`, `compute_mode: data`; em A, a falta de `rendered_text` força fallback para `_default_text` → vazio; em B, texto genérico é aceito porque não há âncoras/validação. 【F:app/presenter/presenter.py†L370-L408】【F:app/narrator/narrator.py†L183-L201】
- **Âncoras**: Não existe checagem de âncoras de processos, permitindo que B gere narrativa extrapolada mesmo com dados estruturados. 【F:app/narrator/narrator.py†L183-L201】
- **Ponto de bifurcação**: a diferença ocorre na etapa Presenter→Narrator: se `render_rows_template` produz string vazia (A) ou genérica (B), o Narrator usa esse texto sem `rows`, levando a ausência total (A) ou alucinação (B). 【F:app/presenter/presenter.py†L299-L380】

## 6. Checks recomendados (somente leitura)
- Verificar em logs/shadow se `facts_wire.rendered_text` está vazio ou genérico nas execuções A/B.
- Conferir `meta.result_key` e ordem das chaves de `results` no payload recebido pelo Presenter.
- Confirmar se `render_rows_template` para `fiis_processos` retorna string não vazia e se colunas batem com o template.
- Inspecionar Narrator Shadow para `strategy`, `used`, `rewrite_only` e texto final usado.

## 7. Conclusão técnica (risco sistêmico)
O design `rewrite_only` remove evidências estruturadas antes do Narrator e não existe validação pós-geração. Isso permite tanto negar dados existentes quanto produzir narrativas desalinhadas, dependendo apenas do conteúdo de `rendered_text` ou de heurísticas do `_default_text`. Sem reforçar a coerência entre `rows_total` e `answer`, o pipeline continuará suscetível a respostas vazias ou alucinadas mesmo com `results.processos_fii` populado.
