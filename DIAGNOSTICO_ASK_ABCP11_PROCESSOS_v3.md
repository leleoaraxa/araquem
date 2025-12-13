# Diagnóstico /ask — "Existe processos para o ABCP11 e quais são?" (v3)

## 1. Resumo executivo
- O fluxo `/ask` roda Planner duas vezes e pode divergir no `result_key`: a API escolhe `meta.result_key` ou a primeira chave de `results`, sem validar existência, levando a `rows=[]` silenciosos. 【F:app/api/ask.py†L292-L299】
- O Orchestrator retorna `results.processos_fii` com `rows_total` populado, mas caches/gates permitem payloads vazios com `status ok`, e o Presenter aceita `result_key` inexistente. 【F:app/orchestrator/routing.py†L362-L468】【F:app/presenter/presenter.py†L136-L184】
- Em `rewrite_only`, o Presenter remove `rows`, `primary`, `identifiers`, `aggregates` e envia apenas `rendered_text` ao Narrator; se este campo estiver vazio ou genérico, o Narrator gera resposta negativa ou alucinada sem validação contra `rows_total`. 【F:app/presenter/presenter.py†L370-L408】【F:app/narrator/narrator.py†L183-L201】
- A resposta final retorna `answer` sem checar coerência com `results/rows_total`, permitindo contradições como na execução A (`rows_total=4`, answer nega dados) e na B (narrativa genérica). 【F:app/api/ask.py†L401-L520】【F:response_A.md†L6-L64】【F:response_B.md†L6-L64】

## 2. Fluxo técnico completo (/ask → answer)
1. API `/ask` chama o Planner (`explain`) e registra intent/entity/score. 【F:app/api/ask.py†L65-L103】
2. `_fetch` aciona `orchestrator.route_question`, que refaz o planejamento, aplica gates e prepara `result_key`, `rows_total` e `compute`. 【F:app/orchestrator/routing.py†L362-L468】【F:app/orchestrator/routing.py†L654-L740】
3. A API monta `results` (ou caminho legacy), define `result_key = meta.result_key` ou `next(iter(results))` e extrai `rows` sem validar correspondência. 【F:app/api/ask.py†L279-L299】
4. Presenter `build_facts` repete a escolha de `result_key`: usa `meta.result_key` apenas se existir em `results`, senão a primeira chave; devolve `facts.rows`, `primary`. 【F:app/presenter/presenter.py†L136-L184】
5. Baseline: `render_answer` + `render_rows_template` produzem `baseline_answer`; `facts_md` = template ou resposta técnica. 【F:app/presenter/presenter.py†L299-L325】
6. Narrator (policy efetiva: `llm_enabled=true`, `rewrite_only=true`, `rag=false`, `compute_mode=data`) recebe `facts_wire`; em `rewrite_only`, o Presenter preenche `rendered_text=facts_md` e remove dados estruturados. 【F:app/presenter/presenter.py†L370-L408】
7. Narrator usa `_default_text` priorizando `rendered_text`; se vazio, tenta `rows` (removidos), depois mensagens genéricas, sem checar âncoras ou `rows_total`. 【F:app/narrator/narrator.py†L183-L201】
8. `/ask` retorna `answer` do Presenter sem validação pós-Narrator, junto de `results` e `rows_total`. 【F:app/api/ask.py†L401-L520】

## 3. Auditoria por etapa (evidências)
### 3.1 API `/ask`
- Seleção de `result_key` e `rows` usa `meta.result_key` ou primeira chave de `results` mesmo que inexistente, podendo zerar linhas silenciosamente. 【F:app/api/ask.py†L292-L299】
- Caminho legacy aceita qualquer dict como `results` e marca `status ok`, mascarando shapes incorretos. 【F:app/api/ask.py†L279-L291】
- Não há validação entre `rows_total` e `answer` na montagem final; apenas repassa o texto do Presenter. 【F:app/api/ask.py†L401-L432】

### 3.2 Planner
- Executado duas vezes (API e Orchestrator) sem compartilhar `result_key`/meta, permitindo divergência entre plano e execução. 【F:app/api/ask.py†L65-L77】【F:app/orchestrator/routing.py†L362-L379】
- Gates por threshold devolvem `results={}` com `status ok` e `rows_total=0`, sem erro explícito, induzindo respostas negativas. 【F:app/orchestrator/routing.py†L392-L468】

### 3.3 Orchestrator / Routing
- Define `result_key` e `rows_total` após SQL/cache; mas a API pode sobrescrever ao usar `next(iter(results))` se `meta.result_key` for `None`. 【F:app/orchestrator/routing.py†L717-L740】【F:app/api/ask.py†L292-L299】
- `skip_sql` (compute concept) retorna `rows_formatted=[]` com `status ok`, alimentando Narrator com ausência artificial de dados. 【F:app/orchestrator/routing.py†L654-L680】
- Em hits de cache, `format_rows` é bypassado; colunas faltantes podem quebrar template e zerar `rendered_text`. 【F:app/orchestrator/routing.py†L654-L684】

### 3.4 Executor / Formatter
- Dependência de `format_rows`; quando bypassado pelo cache, `rows` chegam brutos e podem não encaixar no template usado para `rendered_text`. 【F:app/orchestrator/routing.py†L654-L684】

### 3.5 Presenter
- `build_facts` aceita `meta.result_key` inexistente e faz fallback para primeira chave, podendo ignorar `processos_fii`. 【F:app/presenter/presenter.py†L136-L184】
- `render_rows_template` pode retornar vazio; em `rewrite_only`, `facts_wire` leva apenas `rendered_text` (vazio) e descarta `rows`/`primary`/`aggregates`, eliminando evidência para o LLM. 【F:app/presenter/presenter.py†L299-L380】
- Narrator recebe `facts_wire` com `strategy llm` e `rewrite_only`, definindo `final_answer` apenas pelo texto gerado. 【F:app/presenter/presenter.py†L341-L408】

### 3.6 Narrator
- `_default_text` prioriza `rendered_text`; se vazio e sem `rows` (removidos), retorna mensagem genérica "Sem dados", mesmo com `rows_total>0`. 【F:app/narrator/narrator.py†L183-L201】
- Não há validação de âncoras de processos; qualquer texto em `rendered_text` vira base para narrativa, permitindo alucinações. 【F:app/narrator/narrator.py†L183-L201】

### 3.7 Resposta final
- `/ask` retorna `answer` do Presenter sem revalidar contra `rows_total` ou `results`, permitindo contradições explícitas (dados presentes vs. resposta vazia). 【F:app/api/ask.py†L401-L520】

## 4. Hipóteses ranqueadas (causas)
1. **Perda de evidência em `rewrite_only`**: `facts_wire` sem `rows/primary` depende apenas de `rendered_text`; se vazio, Narrator produz resposta negativa. 【F:app/presenter/presenter.py†L370-L380】【F:app/narrator/narrator.py†L183-L201】
2. **Divergência de `result_key`**: API/Presenter podem selecionar chave errada ou inexistente, zerando `rows` apesar de `results.processos_fii` válido. 【F:app/api/ask.py†L292-L299】【F:app/presenter/presenter.py†L136-L184】
3. **Narrativa sem lastro**: Com `rewrite_only` e ausência de validação, qualquer `rendered_text` genérico gera resposta alucinada. 【F:app/presenter/presenter.py†L370-L408】【F:app/narrator/narrator.py†L183-L201】
4. **Planner duplicado e gates silenciosos**: Segunda execução e bloqueios retornam payload vazio com `status ok`, criando inconsistência entre `rows_total` e expectativa. 【F:app/orchestrator/routing.py†L362-L468】

## 5. 🔁 Diferença entre execução A (empty) e execução B (hallucinated)
- **Dados estruturados**: Ambas execuções trazem `results.processos_fii` com 4 registros e `rows_total>0`. 【F:response_A.md†L6-L64】【F:response_B.md†L6-L64】
- **Facts_wire/rendered_text**: Em A, o answer final afirma inexistência de dados, indicando que `facts_wire.rendered_text` estava vazio ou descartado após `rewrite_only`; em B, o Narrator produziu narrativa genérica, mostrando uso de `rendered_text` sem âncoras. 【F:response_A.md†L6-L64】【F:response_B.md†L6-L64】【F:app/presenter/presenter.py†L370-L408】
- **Estratégia efetiva**: Policy `llm_enabled=true`, `rewrite_only=true`, `rag=false`, `compute_mode=data` mantém LLM ativo mas sem dados estruturados; `_default_text` aceita texto vazio ou genérico. 【F:app/presenter/presenter.py†L370-L408】【F:app/narrator/narrator.py†L183-L201】
- **Bifurcação**: O ponto crítico é Presenter→Narrator: se `render_rows_template` retorna vazio (A), o Narrator devolve "sem dados"; se retorna texto genérico (B), ele é reescrito como narrativa alucinada. 【F:app/presenter/presenter.py†L299-L380】【F:app/narrator/narrator.py†L183-L201】

## 6. Riscos sistêmicos
- Contradições entre `results` e `answer` permanecerão para qualquer entidade em `rewrite_only`, pois não há checagem de consistência pós-Narrator. 【F:app/api/ask.py†L401-L520】
- Cache e gates podem devolver `rows_total=0` com `status ok`, disparando respostas negativas mesmo após SQL válido. 【F:app/orchestrator/routing.py†L392-L468】【F:app/orchestrator/routing.py†L654-L680】
- Ausência de validação de âncoras permite alucinações sempre que `rendered_text` não for derivado diretamente das linhas. 【F:app/narrator/narrator.py†L183-L201】

## 7. Conclusão técnica
O fluxo `/ask` para `fiis_processos` perde evidência em dois pontos: (1) seleção frágil de `result_key` que pode zerar `rows` e (2) política `rewrite_only` que remove `rows` antes do Narrator. Sem validação final entre `rows_total` e `answer`, o sistema retorna respostas vazias (execução A) ou narrativas genéricas (execução B) mesmo com dados válidos em `results.processos_fii`. 【F:app/api/ask.py†L292-L299】【F:app/presenter/presenter.py†L370-L408】【F:app/narrator/narrator.py†L183-L201】【F:response_A.md†L6-L64】【F:response_B.md†L6-L64】
