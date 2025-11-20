# NARRATOR_FLOW_AUDIT — Araquem (M12/M13)

## 1. Escopo deste documento

- Focar exclusivamente em:
  - Narrator (camada de expressão)
  - Integração com RAG (context_builder, hints, concepts)
  - Caminho de dados: `results` → `facts` → `prompt/render` → `answer`


## 2. Arquivos e componentes relevantes

### 2.1. Configuração

| Componente                  | Caminho                                    | Responsabilidade principal                                      |
|----------------------------|--------------------------------------------|-----------------------------------------------------------------|
| Narrator policy            | `data/policies/narrator.yaml`              | Define habilitação do LLM, modelo, estilo e regras por entidade (preferência conceitual, fallback de RAG, limites de linhas). |
| RAG policy                 | `data/policies/rag.yaml`                   | Controla roteamento de intents para RAG, coleções por entidade, limites de chunks e perfis de ranking. |
| Quality policy (relevante) | `data/policies/quality.yaml`               | Estabelece metas de qualidade e checagens de dados para entidades (freshness, faixas aceitas), usadas como referência operacional. |

> Preencha o caminho real e descreva, em 1 linha, a responsabilidade de cada arquivo, baseado no conteúdo real do repositório.

### 2.2. Código Narrator

| Componente         | Caminho                         | Responsa                                                        |
|--------------------|---------------------------------|-----------------------------------------------------------------|
| Narrator core      | `app/narrator/narrator.py`      | Implementa decisão policy-driven entre renderização determinística e LLM, além de saneamento de fatos e escolha de modo conceitual. |
| Prompts Narrator   | `app/narrator/prompts.py`       | Define SYSTEM_PROMPT, templates de apresentação, few-shots e renderizadores determinísticos por entidade. |

### 2.3. Código RAG

| Componente         | Caminho                         | Responsa                                                        |
|--------------------|---------------------------------|-----------------------------------------------------------------|
| Context builder    | `app/rag/context_builder.py`    | Monta contexto de RAG (chunks, política aplicada) seguindo políticas de roteamento e coleções. |
| Cliente Ollama     | `app/rag/ollama_client.py`      | Fornece operações de embedding e geração de texto via API do Ollama (vetores e generate). |
| Rota debug RAG     | `app/api/ops/rag_debug.py`      | Endpoint `/ops/rag_debug` para executar fluxo completo com opção de desabilitar RAG e observar metadados do Narrator. |

### 2.4. Orquestração / Entrada

| Componente         | Caminho                         | Responsa                                                        |
|--------------------|---------------------------------|-----------------------------------------------------------------|
| API `/ask`         | `app/api/ask.py`                | Recebe pergunta, aciona planner, orquestrador, presenter e retorna resposta final; prepara flags do Narrator. |
| Orchestrator       | `app/orchestrator/routing.py`   | Roteia pergunta para SQL, aplica gates, monta meta (incluindo RAG) e devolve `results`. |
| Planner            | `app/planner/planner.py`        | Determina intent/entity via ontologia, aplica fusão com hints de RAG e thresholds. |

> Em “Responsa”, descreva em linguagem natural o que cada arquivo faz, usando o código como fonte.

---

## 3. Fluxo de alto nível (pergunta → resposta)

### 3.1. Sequência principal (nomes reais)

Descrever, em ordem, o caminho que uma pergunta segue até virar texto:

1. **Entrada HTTP**
   - Arquivo: `app/api/ask.py`
   - Função: `ask`
   - Responsa: Recebe payload `AskPayload`, chama `planner.explain`, aplica cache/read-through, obtém `orchestrator.route_question` e encaminha para `present` junto com flags do Narrator; devolve JSON com `results`, `meta` e `answer`.

2. **Planner / Orchestrator**
   - Arquivo: `app/orchestrator/routing.py`
   - Funções envolvidas:
     - `Orchestrator.route_question`
     - `extract_identifiers`
   - Responsa: Valida gate de score/gap, extrai tickers, infere parâmetros, busca/caching de métricas, executa SQL (via builder/executor), formata linhas, anexa `requested_metrics`, monta `meta` (incluindo `rag` via `build_rag_context`) e `results` para o presenter.

3. **Executor / Formatter**
   - Arquivo(s): `app/orchestrator/routing.py` (chama `build_select_for_entity`, `PgExecutor.query`, `format_rows`)
   - Funções: `build_select_for_entity`, `PgExecutor.query`, `format_rows`
   - Responsa: Constrói SELECT conforme entidade e parâmetros inferidos, executa no banco e formata para lista de dicts (`rows`) que povoam `results` e `meta.rows_total`.

4. **Narrator**
   - Arquivo: `app/narrator/narrator.py`
   - Descrever:
     - `render` é chamado pelo presenter com `question`, `facts` e `meta`, ajustando modo conceitual e RAG antes de renderizar.
     - `render_narrative(...)` é invocado primeiro para gerar texto determinístico especializado; depois `build_prompt(...)` é chamado apenas se política permitir uso de LLM.
     - Decisão entre renderer determinístico vs LLM depende de `llm_enabled`, `max_llm_rows` e presença de cliente LLM; quando LLM acionado, baseline é usado como fallback e prompt inclui FACTS/RAG/metadata.

5. **RAG (quando acionado)**
   - Arquivo: `app/rag/context_builder.py`
   - Função: `build_context`
   - Responsa: Verifica política `rag.yaml` para intent/entity, resolve coleções e limites, gera embeddings da pergunta, busca no índice e retorna dict com `enabled`, `chunks`, `used_collections` e `policy` para `meta['rag']`.

6. **Resposta final**
   - Descrever brevemente como o texto final é devolvido pela API `/ask`.
   - `present` escolhe entre Narrator (quando habilitado) ou baseline (`render_answer`); `ask` insere `presenter_result.answer` em `answer` do payload JSON e inclui `narrator` em `meta`.

---

## 4. Caminho de dados: FACTS, RAG_CONTEXT e PROMPT

### 4.1. FACTS (dados numéricos e estruturados)

- `facts` é montado em `app/presenter/presenter.py` pela função `build_facts`, combinando `plan.chosen`, `orchestrator_results` e `identifiers`/`aggregates`; define `rows`, `primary`, `result_key`, `requested_metrics`, `ticker` e `fund`.
- Exemplo de estrutura real para `fiis_financials_risk`, baseado no código:
  ```json
  {
    "result_key": "fiis_financials_risk",
    "primary": { "ticker": "...", "volatility_ratio": "...", "sharpe_ratio": "...", "treynor_ratio": "...", "jensen_alpha": 0, "beta_index": 0.0, "sortino_ratio": "...", "max_drawdown": 0.0, "r_squared": 0.0 },
    "rows": [ { "ticker": "...", "volatility_ratio": "...", "sharpe_ratio": "...", "treynor_ratio": "...", "jensen_alpha": 0, "beta_index": 0.0, "sortino_ratio": "...", "max_drawdown": 0.0, "r_squared": 0.0 } ]
  }
  ```

Indicar onde facts é passado para:

- `render_narrative(meta, facts, policy)`
- `build_prompt(question, facts, meta, style, rag)`

`present` chama `narrator.render(question, facts.dict(), meta_for_narrator)`, e `narrator.render` repassa `render_meta`/`effective_facts` para `render_narrative`; depois de sanitizar, envia `prompt_facts`/`prompt_meta` a `build_prompt` quando LLM é usado.



4.2. RAG_CONTEXT (rag → prompt)

- `meta['rag']` é preenchido pelo `Orchestrator` via `build_rag_context` (outra chamada no presenter com `load_rag_policy` para shadow/local).
- `narrator.render` lê `meta['rag']`, respeita `rag_debug_disable` e passa o contexto saneado para `build_prompt`.
- `app/narrator/prompts.py` usa `_prepare_rag_payload(rag)` para limitar a 5 snippets, truncar cada texto e retornar `{enabled, source, snippets}`; o resultado entra em `[RAG_CONTEXT]` do prompt como JSON ou mensagem de ausência.


4.3. SYSTEM_PROMPT / prompt final

- SYSTEM_PROMPT está definido em `app/narrator/prompts.py` na constante `SYSTEM_PROMPT`.
- `build_prompt(...)` concatena, nesta ordem:
  - `SYSTEM_PROMPT`
  - `[ESTILO]`, `[APRESENTACAO]`, `[INTENT]`, `[ENTITY]`
  - `[PERGUNTA]`
  - `[FACTS]` em JSON com fallback_message opcional
  - `[RAG_CONTEXT]` em JSON (ou texto padrão se não houver)
  - "Instruções adicionais" com template escolhido (summary/list/table)
  - Few-shot correspondente (quando existir)
  - Fecho instruindo a entregar apenas o texto final



---

5. Regras de decisão do Narrator

5.1. Determinístico vs LLM

- `Narrator._should_use_llm` retorna verdadeiro somente quando `llm_enabled` da policy é true, `max_llm_rows` > 0 e `len(facts.rows)` <= `max_llm_rows`.
- `render` sempre calcula `deterministic_text` via `render_narrative` e baseline via `build_narrator_text`/_default_text; se Narrator estiver desabilitado ou cliente LLM indisponível ou `_should_use_llm` for falso, retorna baseline (com erro/logs indicando motivo).
- Flags da policy influenciam:
  - `llm_enabled`/`shadow`: habilitam execução efetiva ou apenas shadow.
  - `entities.*.prefer_concept_when_no_ticker`: ativa `concept_mode`, limpando `rows/primary` e sinalizando `meta['narrator_mode']`.
  - `entities.*.rag_fallback_when_no_rows` e `concept_with_data_when_rag`: trocam baseline para melhor chunk de RAG em ausência de dados ou combinam conceito com dados.
  - `max_llm_rows`: bloqueia LLM se número de linhas exceder limite.


5.2. Renderers específicos por entidade

Preencher uma tabela com base no render_narrative real:

Entidade / result_key | Função renderer | Observações
--- | --- | ---
client_fiis_positions | `_render_client_fiis_positions` | Lista posições com valores aproximados e total.
fiis_processos | `_render_fiis_processos` | Descreve processos com risco, valores e resumo.
fiis_financials_revenue_schedule | `_render_fiis_financials_revenue_schedule` | Resume prazos de receita com percentuais e comentários.
fiis_financials_risk | `_render_fiis_financials_risk` | Lista métricas de risco; vazio em modo conceito.
fiis_financials_snapshot | `_render_fiis_financials_snapshot` | Destaca caixa, market cap, yield e alavancagem.
fiis_imoveis | `_render_fiis_imoveis` | Detalha imóveis com localidade e vacância.
* (outros) | `_fallback_render` | Mensagem padrão com contagem e linhas formatadas.



---

6. Redundâncias e riscos identificados

- O `SYSTEM_PROMPT` repete instruções de não copiar RAG e de priorizar métricas já presentes em templates/few-shot, gerando sobreposição com conceitos das coleções `concepts-risk`.
- `present` constrói `rag_context` localmente (via `load_rag_policy`) e o `Orchestrator` também monta `meta['rag']`, criando dois caminhos paralelos de RAG no mesmo fluxo.
- `facts.rendered_text` é explicitamente proibido no SYSTEM_PROMPT, mas ainda é calculado no Narrator (baseline), podendo ser ignorado pelo modelo caso o prompt seja extenso.
- `RAG_CONTEXT` inclui snippets textuais que, embora truncados, podem ser reproduzidos caso o modelo ignore a proibição de copiar trechos.


---

7. Próximos passos (apenas descrição, sem refatoração)

- O tamanho do prompt pode crescer devido à combinação de FACTS em JSON, RAG_CONTEXT e few-shots, podendo afetar limites de tokens monitorados pela policy.
- Há sobreposição entre instruções do SYSTEM_PROMPT e conteúdos conceituais das coleções de RAG, exigindo cuidado para evitar repetições na resposta.
- Fluxo duplo de construção de RAG (Orchestrator e Presenter) aumenta complexidade de depuração em cenários de shadow/disable.

