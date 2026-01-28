# Auditoria de pontos de entrada — Entidades, Intents e Contratos (Araquem)

> **Escopo aplicado:** esta auditoria mapeia *pontos de entrada* e *fluxos de consumo* sem avaliar conteúdo de carteira/dados financeiros ou semântica de entidades SQL. Os domínios alvo (conceitos, institucional mínimo e suporte determinístico) são tratados apenas como **pontos de entrada existentes ou ausentes**, sem criação de novos artefatos.

---

## 0) Inventário de pontos de entrada (mapa bruto)

| path | tipo | papel | escreve / lê | impacto no /ask | evidência |
| --- | --- | --- | --- | --- | --- |
| `app/api/ask.py` | Python | Endpoint `/ask` → chama Planner/Orchestrator/Presenter/Narrator. | lê | **direto** (entrada principal) | `ask()` e wiring de Presenter/Narrator. |
| `app/planner/` | Python | Resolver intents + entidades a partir da ontologia. | lê | **direto** (roteamento) | `Planner` usa `load_ontology()` e calcula scores. |
| `app/orchestrator/` | Python | Carrega entity.yaml, thresholds, executa SQL e monta `meta` + RAG. | lê | **direto** (roteamento e execução) | `route_question()` e `build_rag_context()`. |
| `app/builder/sql_builder.py` | Python | Monta SQL a partir de entity.yaml. | lê | **direto** (execução) | `_load_entity_yaml()` + `build_select_for_entity`. |
| `app/formatter/rows.py` | Python | Render declarativo via `presentation.kind` + templates. | lê | **direto** (contratos de resposta) | `render_rows_template()`. |
| `app/templates_answer/` | Python | Template legado (template.md). | lê | **direto** (contrato de resposta fallback) | `render_answer()`. |
| `app/presenter/` | Python | Consolida facts, templates, Narrator e RAG. | lê | **direto** (contratos finais) | `present()` chama `render_answer()`/`render_rows_template()` + `Narrator.render()`. |
| `app/narrator/` | Python | Policy e modos (concept/data), uso de RAG. | lê | **direto** (narrativa) | `Narrator.render()` e `get_effective_policy()`. |
| `app/rag/` | Python | Leitura de embeddings + policy de RAG. | lê | **direto** (enriquecimento textual) | `build_context()` e `EmbeddingStore`. |
| `data/entities/**` | YAML/MD | Definição de entidades (entity.yaml, templates, responses, hints). | lê | **direto** (roteamento, SQL, apresentação) | lidas por planner/orchestrator/builder/formatter/templates. |
| `data/entities/catalog.yaml` | YAML | Catálogo/índice de entidades. | lê | **indireto** (governança/qualidade) | usado por scripts de cobertura. |
| `data/contracts/entities/**` | YAML | Contratos de saída tabular (schemas). | lê | **indireto** (qualidade/validadores) | validadores e report scripts. |
| `data/ontology/**` | YAML | Intents, buckets, anti_tokens, ticker index. | lê | **direto** (Planner). | carregado por `load_ontology()` e `TickerIndex`. |
| `data/policies/**` | YAML/MD | Policies (RAG, Narrator, cache, context, formatting etc.). | lê | **direto** (roteamento/comportamento) | `rag.yaml`, `narrator.yaml`, `cache.yaml`, `context.yaml`, `formatting.yaml`. |
| `data/concepts/**` | YAML | Conceitos/first-class *somente via embeddings*. | lê | **indireto** (RAG) | incluído em `data/embeddings/index.yaml`. |
| `data/embeddings/index.yaml` | YAML | Índice declarativo de documentos para embeddings. | lê | **indireto** (RAG) | usado pelo builder de embeddings. |
| `data/embeddings/store/**` | JSONL/JSON | Store de embeddings em runtime. | lê | **direto** (RAG) | consumido por `EmbeddingStore`. |
| `data/ops/planner_thresholds.yaml` | YAML | Thresholds de intents/entidades. | lê | **direto** (gate de roteamento) | consumido via `_load_thresholds`. |
| `data/ops/param_inference.yaml` | YAML | Param inference por intent. | lê | **direto** (inferencia de parâmetros) | usado pelo Orchestrator. |
| `scripts/embeddings/**` | Python | Geração e health check do RAG. | lê/escreve | **indireto** (RAG) | `embeddings_build.py` e `embeddings_health_check.py`. |
| `scripts/quality/**` | Python/SH | Suites de roteamento/contratos. | lê | **indireto** (governança) | `quality_gate_check.sh`, `quality_diff_routing.py`, etc. |
| `scripts/diagnostics/**` | Python | Auditorias e suites de /ask. | lê | **indireto** (diagnóstico) | `run_ask_suite.py`, `audit_planner_flow.py`. |

---

## 1) Entidades: onde nascem, onde são consumidas

### 1.1 Declaração (fonte de verdade)
- **Fonte primária:** `data/entities/<entity>/<entity>.yaml` — descreve SQL view, columns, presentation, identificadores e bloco `ask`. Lido por **Orchestrator** e **SQL Builder**.
- **Catálogo:** `data/entities/catalog.yaml` agrega paths, coverage e metadados por entidade. Usado por scripts de qualidade/coverage.
- **Contratos tabulares (schemas):** `data/contracts/entities/*.schema.yaml` com colunas, tipos e tolerâncias. Usados por validadores/suites (não pelo runtime).

### 1.2 Consumo (runtime)
- **Planner** consome apenas `data/ontology/entity.yaml` (intents e buckets) para escolher intent/entity. Não consome entity.yaml diretamente.
- **Orchestrator** carrega entity.yaml para extrair config (ask metrics, options, result_key) e disparar SQL via `build_select_for_entity()`.
- **SQL Builder** usa entity.yaml como contrato declarativo de SQL (colunas, filtros, métricas/aggregations).
- **Formatter/Presenter** usam `presentation.kind` e templates (`responses/*.md.j2`, `template.md`) para renderizar respostas determinísticas.

### 1.3 Duplicações e sobreposições
- **Ontologia vs entity.yaml:** termos/intents do `ask` em entity.yaml não são usados pelo Planner; o Planner usa apenas `data/ontology/entity.yaml`. Isso cria redundância sem governança unificada.
- **Entity YAML vs contracts:** `data/contracts/entities` define colunas, enquanto entity.yaml define columns de output e presentation — há duplicação sem validação runtime.
- **Narrator vs presenter/formatter:** o Narrator pode reescrever respostas já formatadas pelos templates, mas a policy busca reduzir LLM (LLM desabilitado para buckets A/B/C por padrão).

**Veredito:**
- **Fonte de verdade de execução:** `data/entities/<entity>/<entity>.yaml` + `data/ontology/entity.yaml`.
- **Derivados/indiretos:** `data/entities/catalog.yaml`, `data/contracts/entities`, reports em `data/ops/reports`, e documentação em `docs/dev/`.

---

## 2) Intents: definição, roteamento e colisões

### 2.1 Onde intents são definidas
- **Definição canônica:** `data/ontology/entity.yaml` define intents, tokens, phrases, anti_tokens e entidades elegíveis. Carregado pelo Planner.
- **Uso em entity.yaml:** `ask.intents` existe nos YAMLs de entidade, mas **não é consumido pelo Planner** — serve apenas como metadado local e texto (embeddings).

### 2.2 Onde intents são priorizadas / filtradas
- **Thresholds:** `data/ops/planner_thresholds.yaml` define `min_score`/`min_gap` por intent e entity; aplicado no Orchestrator.
- **Policies de RAG:** `data/policies/rag.yaml` define `routing.deny_intents` e `allow_intents`, bloqueando RAG por intent.
- **Policies de contexto:** `data/policies/context.yaml` permite/nega histórico por entidade (afeta resolution de contexto no /ask).

### 2.3 Onde intents são testadas / governadas
- **Quality suites** em `data/ops/quality/payloads/*_suite.json` e scripts em `scripts/diagnostics/run_ask_suite.py`.
- **Quality gate**: `scripts/quality/quality_gate_check.sh` executa validação de ontologia/contratos.

### 2.4 Intents ativas, órfãs e dead
- **Ativas:** todas as intents em `data/ontology/entity.yaml` são carregadas pelo Planner.
- **Órfã (sem uso em entity.ask):** `ticker_query` existe na ontologia, mas não aparece em `ask.intents` dos entity.yaml. **Status: POTENTIALLY_DEAD (metadata)**, pois não há evidência de consumo fora do Planner.
- **Dead intents:** não há evidência inequívoca de intents “nunca atingidas” sem execução real; apenas políticas podem bloquear RAG, não o Planner.

---

## 3) Contratos de resposta (response / template / narrator)

### 3.1 `data/entities/*/responses/**`
- **FIRST_CLASS_CONTRACT:** `presentation.kind` em entity.yaml + template `data/entities/<entity>/responses/<kind>.md.j2` renderizado por `render_rows_template()`.

### 3.2 Templates fallback (`data/entities/*/template.md`)
- **LEGACY_FALLBACK:** `app/templates_answer.render_answer()` busca `template.md`/`templates.md` para respostas determinísticas.

### 3.3 Narrator (LLM / rewrite)
- **RAG_ENRICHMENT:** quando `meta.rag.enabled` e policy permite `use_rag_in_prompt`, o Narrator incorpora chunks de RAG.
- **FIRST_CLASS_CONTRACT:** policy de Narrator (`data/policies/narrator.yaml`) decide se LLM pode operar, modo conceitual (concept/data) e guardrails.

### 3.4 Fallbacks
- **LEGACY_FALLBACK:** fallback textual determinístico quando template não existe ou está vazio.
- **POTENTIALLY_DEAD:** fallback legado em `data/concepts/*_templates.md` removido (não havia arquivos no repo).

---

## 4) RAG: papel real hoje

### 4.1 O que o RAG influencia no `/ask`
- Orchestrator sempre injeta `meta.rag` (com `enabled` true/false) via `build_rag_context()`.
- Narrator usa `meta.rag` para inserir contexto ou fallback conceitual dependendo da policy.

### 4.2 Dependência por entidade
- `data/policies/rag.yaml` define collections por entity (ex.: `history_*` → `concepts-macro`).
- `routing.deny_intents` bloqueia RAG para várias intents (incluindo quase todas as entidades SQL atuais), deixando RAG **efetivamente desligado** para a maior parte do tráfego.

### 4.3 Policies que bloqueiam
- `data/policies/rag.yaml` (deny_intents/allow_intents) é o gate principal.
- `data/policies/narrator.yaml` define `use_rag_in_prompt`, `prefer_concept_when_no_ticker`, `concept_with_data_when_rag`.

### 4.4 Documentos no store
- `data/embeddings/index.yaml` inclui `data/concepts/*.yaml`, `data/ontology/entity.yaml`, entity.yaml, hints, policies e projections.
- `data/embeddings/store/embeddings.jsonl` é o único artefato lido em runtime.

### 4.5 Classificação de uso
- **Essencial:** o store de embeddings quando `rag.yaml` permite (chunks usados pelo Narrator).
- **Complementar:** hints.md, policies e projections usados apenas como texto contextual em embeddings.
- **Irrelevante no runtime:** `data/concepts/*.yaml` diretamente (não lidos no /ask, apenas indexados).

---

## 5) Suporte e Institucional: o que já existe hoje

### 5.1 Institucional (about/privacidade/termos/limites/pricing)
- **Não encontrado** como entidade/intents first-class nem como templates determinísticos.
- **Parcial via conceitos:** há conteúdo sobre privacidade de carteira em `data/concepts/concepts-carteira.yaml` (apenas para embeddings).

### 5.2 Suporte determinístico (how-to core, acionado por “?” na UI)
- **Não encontrado** como entidade/intents first-class nem templates.
- **Possível via RAG:** não há coleções específicas de suporte no `rag.yaml`.

**Classificação:**
- **Conceitos:** existem como **RAG_ENRICHMENT** (não first-class).
- **Institucional:** **não existe**.
- **Suporte determinístico:** **não existe**.

---

## 6) Limpeza segura (executar)

### 6.1 Itens POTENTIALLY_DEAD
- Fallback legado de templates em `data/concepts/<entity>_templates.md`: não há arquivos e o caminho não é mais mantido.

### 6.2 Remoções executadas
- **Remoção do fallback legado para `data/concepts/*_templates.md`** em `app/templates_answer`.
- Evidência de não uso: inexistência de arquivos `data/concepts/*_templates.md` no repositório + fallback mantido apenas como compat legacy.

### 6.3 Risco avaliado
- **Risco baixo**: comportamento permanece inalterado para templates existentes (`data/entities/**/template.md`). Apenas remove uma busca de fallback que nunca encontraria arquivos.

---

## 7) Conclusão executiva

### 7.1 Quantos pontos de entrada reais existem hoje
- **Runtime (diretos):** ontologia, entidades, policies (rag/narrator/context/cache/formatting), embeddings store, planner/orchestrator/presenter/narrator.
- **Governança/diagnóstico:** catalog, contracts, ops/quality, scripts de diagnóstico/embeddings.

### 7.2 Onde há sobreposição
- **Ontologia vs entity.yaml (ask.*):** campos de tokens/keywords/anti_tokens em entity.yaml são redundantes para o Planner.
- **Entity.yaml vs contracts:** colunas e schema duplicados sem enforcement em runtime.
- **Narrator vs templates:** duas camadas com responsabilidade de “forma final” da resposta (LLM desligado por default mitiga conflito).

### 7.3 Onde há acoplamento frágil
- **RAG:** depende de `rag.yaml` + store gerado manualmente; se o index/store estiver stale, o narrador perde contexto sem erro crítico.
- **Policies:** ausência de `rag.yaml`/`narrator.yaml` desliga ou quebra features sem fallback explícito além do determinístico.

### 7.4 Onde *devemos* introduzir (sem implementar)
> Sem criar entidades novas, apenas indicando o *lugar correto* para criação futura.

- **Conceitos first-class:** `data/entities/<entity>.yaml` + `data/ontology/entity.yaml` + templates em `data/entities/<entity>/responses/` + policies (`rag.yaml`/`narrator.yaml`).
- **Institucional first-class:** mesmo conjunto acima (entidade + intent + template + policy), com possível coleção RAG dedicada em `data/embeddings/index.yaml`.
- **Suporte determinístico first-class:** entidade + intent + templates determinísticos, sem depender de RAG.

---

## Critério de sucesso: “Se eu quiser criar uma nova entidade conceitual first-class, quais arquivos eu toco — e só eles?”

1) **Ontologia**: adicionar intent e tokens em `data/ontology/entity.yaml`.
2) **Entidade**: criar `data/entities/<entity>/<entity>.yaml` (presentation + ask + sql_view). *(sem alterar SQL nesta auditoria)*
3) **Templates**: adicionar `data/entities/<entity>/responses/<kind>.md.j2` + `template.md` se necessário.
4) **Policies**: ajustar `data/policies/narrator.yaml` (modo conceitual) e `data/policies/rag.yaml` (coleções).
5) **Embeddings** (se usar RAG): adicionar o documento em `data/embeddings/index.yaml` e gerar o store via `scripts/embeddings/embeddings_build.py`.

