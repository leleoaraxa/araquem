# PROMPT_NEW_ENTITIES — Guia Operacional (Araquem M8.x, Guardrails v2.2.0)

Use este prompt **dentro do repositório** sempre que uma nova entidade precisar nascer ou sofrer ajustes estruturais. Ele deve instruir o Codex a produzir **arquivos completos** (ou patches) já prontos para commit, cobrindo 100% das peças declarativas do ecossistema Araquem.

-------------------------------------------------------------------------------
REGRAS ABSOLUTAS
-------------------------------------------------------------------------------
- **Sem pastas novas.** Sempre usar a topologia já existente.
- **Payload do `/ask` é imutável** (`question`, `conversation_id`, `nickname`, `client_id`). Nenhum parâmetro novo.
- **Zero heurística/hardcode em código.** Toda lógica deve vir de YAML, ontologia ou SQL já disponível. Nada de try/catch em import.
- **Compute-on-read e composições** seguem padrões existentes; não criar lógica Python.
- **Guardrails v2.2.0:** respeitar políticas de RAG/Narrator, contexto, cache, privacidade (entidades `client_*` sempre usam `document_number` seguro), e negar LLM onde padrão é determinístico.
- **Somente arquivos produzidos.** A resposta do Codex deve trazer o conteúdo integral ou diffs prontos para aplicar, sem texto solto.

-------------------------------------------------------------------------------
ESCOPO A SER ANALISADO (sempre)
-------------------------------------------------------------------------------
1) **Entidade base**
- `data/entities/<entity>/entity.yaml`
- `data/contracts/entities/<entity>.schema.yaml`
- `data/entities/<entity>/template.md` (documentação, nunca .j2 nem Jinja)
- `data/entities/<entity>/responses/*.md.j2` (tabelas/listas/summary com Jinja)
- `data/entities/<entity>/hints.md` (se existir; criar se novo)

2) **Catálogo, ontologia e políticas**
- `data/entities/catalog.yaml`
- `data/ontology/entity.yaml`
- `data/policies/*.yaml` (quality, rag, narrator, context, cache, etc.)
- `data/ops/entities_consistency_report.yaml`

3) **Quality, planner e parâmetros**
- `data/ops/quality/routing_samples.json`
- `data/ops/quality/projection_*.json`
- `data/ops/param_inference.yaml`
- `data/ops/planner_thresholds.yaml`

4) **RAG e conceitos**
- `data/rag/golden/rag_golden_set.json` (se for coleção textual)
- `data/rag/concepts/concepts-*.yaml` (se precisar atrelar a coleção já existente)

5) **Amostras e documentação**
- `docs/database/samples/<entity>.csv` (se fornecido)
- `docs/dev/ENTITIES_INVENTORY_2025.md`, `docs/ARAQUEM_STATUS_2025.md`, `docs/CHECKLIST-2025.0-prod.md`, `docs/GUARDRAILS_ARAQUEM_v2.2.0.md`

-------------------------------------------------------------------------------
PASSO A PASSO PARA CRIAR/ATUALIZAR ENTIDADE
-------------------------------------------------------------------------------
1) **Reconhecer o tipo**: snapshot D-1, histórico (metrics), compute-on-read, composite/view, macro/index/currency, risco, overview, client/privada, single-row, lista/tabela, agregações, multi-ticker ou single-ticker, janelas temporais.

2) **Basear-se em padrões existentes equivalentes.** Referências canônicas: `fiis_*`, `history_*`, `fii_overview`, `client_*`. Copiar decisões (campos, estruturas, políticas) do tipo mais próximo.

3) **Criar `data/entities/<entity>/entity.yaml`**
- Campos mínimos reais observados no repo: `id`, `result_key` (quando necessário), `sql_view` ou `sql` compute-on-read, `private` (true para `client_*` ou entidades PII), `description` (PT-BR), `options` (ex.: `supports_multi_ticker`), `identifiers` (lista com nome/descrição), `default_date_field` (quando temporal), `columns` (nome, alias e descrição). Não inventar tipos aqui.
- Blocos opcionais conforme padrões: `presentation` (kind summary/table e empty_message), `ask` (intents, requires_identifiers, keywords, phrase_includes, synonyms, weights, sample_questions), `params` (required/bindings para private), `order_by_whitelist`, `aggregations` (enabled + defaults), `responses` (mapa com kind/template). Use vocabulário e filtros já existentes (`currency_br`, `percent_br`, `number_br`, `int_br`, `float_br`, `date_br`, etc.).
- Para entidades privadas com `document_number`: `private: true`, incluir identifier + binding seguro, e `requires_identifiers`/`params.required` mapeando `context.client_id` (LGPD: ignorar PII do texto livre).
- Compute-on-read: usar bloco `sql` com parâmetros nomeados já usados em outras entidades; jamais criar Python.
- Single-row/overview: manter `aggregations.enabled: false` e `presentation.kind` adequado.

4) **Criar `data/contracts/entities/<entity>.schema.yaml`**
- Espelhar todas as colunas do entity (nomes e cardinalidade). Tipos válidos: `string`, `number`, `integer`, `boolean`, `string` com `format: date|date-time`. Definir `required` para chaves naturais e campos essenciais. Seguir estilo dos schemas atuais.

5) **Criar templates da entidade**
- `data/entities/<entity>/template.md`: documento de referência (Descrição, Exemplos de perguntas, Respostas usando templates). **Nunca** usar Jinja nem extensão .j2.
- `data/entities/<entity>/responses/`: criar pelo menos um template Jinja (`table.md.j2`, `summary.md.j2`, `list_basic.md.j2`, etc.) conforme o tipo da entidade. Tratar `rows` vazios com `empty_message` e preencher nulos com `"-"` ou filtros existentes. Multi-data por data: usar namespace para agrupar como em `client_fiis_positions`.
- `data/entities/<entity>/hints.md`: perguntas reais para ajudar o Planner (inclua sempre para entidades novas).

6) **Catalogar** (`data/entities/catalog.yaml`)
- Adicionar entrada com `title` PT-BR, `kind` (snapshot/historical/metrics/composite/macro/index/currency/client/etc.), `paths` (`entity_yaml`, `schema`, `quality_projection` se existir ou `null`), `coverage` (`cache_policy`, `rag_policy`, `narrator_policy`, `param_inference`), `identifiers.natural_keys`, `notes` (explicitar privacidade, RAG deny, etc.). Cobertura de RAG/narrator deve refletir as políticas reais (deny também conta como presença na cobertura de RAG).

7) **Ontologia** (`data/ontology/entity.yaml`)
- Incluir bloco `intents` com tokens/phrases include/exclude, entities mapeadas e domínios coerentes. Seguir pesos/tokens existentes (`normalize`, `tokenization`, `weights` já declarados). Respeitar exclusões de PII (não mencionar CPF/CNPJ em tokens de entidades públicas).

8) **Políticas**
- `data/policies/quality.yaml`: adicionar dataset com `freshness` (se aplicável), `not_null`, `accepted_range` coerentes com dados reais. Basear-se em CSV amostra ou ranges de entidades similares.
- `data/ops/quality/projection_<entity>.json`: criar projeção com `type: projection`, `entity`, `result_key` (quando usado), `must_have_columns`, `samples` de roteamento/QA.
- `data/ops/quality/routing_samples.json`: adicionar perguntas de roteamento para a nova intent, especialmente para garantir Planner correto.
- `data/ops/planner_thresholds.yaml`: incluir thresholds da intent e entity seguindo famílias (objetivas 1.0/0.20; soltas 0.8/0.10; risco com gap 0). Nunca afrouxar além dos padrões existentes.
- `data/ops/param_inference.yaml`:
  - Entidades históricas: definir `default_agg`, `default_window`, `windows_allowed`, `agg_keywords`, `window_keywords` conforme domínio.
  - Snapshots/composite sem janela: `inference: false` ou apenas `default_agg` list com limites.
  - Entidades privadas: `inference: false`, `required` e `bindings` (`document_number: context.client_id`).
  - Agregações: `defaults.list.limit/order` quando necessário.

9) **RAG e Narrator**
- `data/policies/rag.yaml`: manter deny para intents determinísticas. Só habilitar se já houver coleção existente (não criar novas). Se negar, adicionar intent a `routing.deny_intents`; se habilitar, apontar para collections existentes (`concepts-*` ou coleções RAG já listadas) e perfil adequado (default/macro/risk).
- `data/policies/narrator.yaml`: padrão é `llm_enabled: false`. Só adicionar override se já houver precedentes; manter `max_llm_rows: 0`, `strict_mode` conforme equivalente. Privadas e numéricas ficam desligadas.
- `data/policies/context.yaml`: atualizar `planner.allowed_entities` / `denied_entities` e bloco `entities` se a nova entidade puder herdar contexto (ticker/ref_date) ou se deve ser bloqueada (privadas, macro). Respeitar compute-on-read seguro.
- `data/policies/cache.yaml` (se aplicável): garantir inclusão/exclusão conforme análogo.

10) **Consistência operacional**
- `data/ops/entities_consistency_report.yaml`: marcar `has_schema`, `has_quality_projection`, `in_quality_policy`, `in_cache_policy`, `in_rag_policy` (true mesmo se deny), `in_narrator_policy`, `has_ontology_intent`, `has_param_inference`. Adicionar notas sobre privacidade, RAG negado, binding de documento, etc.

11) **Amostras e documentação auxiliar**
- `docs/database/samples/<entity>.csv`: criar se fornecida amostra; usar header/tipos reais para descrever colunas no entity e ranges de quality.
- `data/rag/golden/rag_golden_set.json`: se entidade entrar em RAG textual, adicionar exemplos de perguntas/respostas canônicas.
- `data/rag/concepts/concepts-*.yaml`: só usar coleções existentes; se precisar mapear para conceito, adicionar termos na coleção correspondente (macro/risk/fiis) sem criar novas.
- `docs/dev/ENTITIES_INVENTORY_2025.md` e `docs/ARAQUEM_STATUS_2025.md`: atualizar listagem/estado da entidade se for obrigatória no inventário.
- `docs/CHECKLIST-2025.0-prod.md`: marcar itens cumpridos para nova entidade.

-------------------------------------------------------------------------------
CASUÍSTICA ESPECÍFICA
-------------------------------------------------------------------------------
- **Entidade privada (`client_*` ou PII)**: `private: true`; identifiers incluem `document_number`; `ask.requires_identifiers` e `params.required` devem ter `document_number`; `param_inference` com `bindings.document_number: context.client_id`; RAG e Narrator negados (mantém cobertura com deny); notas no catalog e consistency explicando LGPD.
- **Multi-ticker**: `options.supports_multi_ticker: true`; `ask.requires_identifiers` inclui `ticker`; considerar `aggregations.enabled: true` com defaults list limit/order.
- **Single-row/overview**: `aggregations.enabled: false`; responses `summary` ou `list_basic`; `presentation.kind` summary.
- **Lista/tabela**: responses `table.md.j2` com cabeçalho e mensagem de vazio; usar filtros BR; agrupar por datas se necessário.
- **Agregações**: manter `aggregations.defaults.list.limit/order`; no param_inference, defina `default_agg`/keywords.
- **Janelas temporais**: obrigatórias para históricos; definir `default_window` e keywords coerentes.
- **RAG deny**: adicionar intent em `rag.routing.deny_intents`; catalog coverage.rag_policy: true; consistency `in_rag_policy: true` com nota.
- **Narrator off**: não incluir em `narrator.entities` (usa default off) ou incluir explicitamente com `llm_enabled: false` se outras entradas similares assim o fazem.
- **Contexto**: se entidade deve herdar último ticker/data, incluir em `context.planner.allowed_entities` e `context.entities.<entity>` com flags `use_referenced_ticker`/`use_last_entity`. Privadas/macros geralmente ficam em denied.
- **`metrics_synonyms` / métricas de tracking**: se a entidade expõe métricas novas, adicionar sinônimos nas seções adequadas do `entity.yaml` e considerar ranges de quality.
- **Golden set/roteamento**: adicionar exemplos que validem o intent e o template.

-------------------------------------------------------------------------------
VALIDAÇÃO FINAL (antes de responder)
-------------------------------------------------------------------------------
- Todos os YAMLs bem-formados; caminhos corretos.
- `entity.yaml` ↔ `schema.yaml` ↔ `catalog.yaml` ↔ `entities_consistency_report.yaml` alinhados.
- `param_inference` e `planner_thresholds` contemplam a intent.
- `quality_projection` e `quality.yaml` coerentes com colunas/ranges reais.
- Templates: `template.md` sem Jinja; responses .j2 com filtros corretos e tratamento de vazio.
- RAG/Narrator/context/cache configurados (deny ou allow) seguindo precedentes.
- Privacidade assegurada (`document_number` só via contexto seguro).
- Amostras/golden/concepts atualizados quando aplicável.

-------------------------------------------------------------------------------
SAÍDA OBRIGATÓRIA DO CODEX
-------------------------------------------------------------------------------
Entregar apenas arquivos/diffs prontos para commit para todos os itens afetados, incluindo (quando aplicável):
- `data/entities/<entity>/entity.yaml`
- `data/entities/<entity>/template.md`
- `data/entities/<entity>/responses/*.md.j2`
- `data/entities/<entity>/hints.md`
- `data/contracts/entities/<entity>.schema.yaml`
- `data/entities/catalog.yaml`
- `data/ontology/entity.yaml`
- `data/policies/quality.yaml`
- `data/ops/quality/projection_<entity>.json`
- `data/ops/quality/routing_samples.json`
- `data/ops/param_inference.yaml`
- `data/ops/planner_thresholds.yaml`
- `data/ops/entities_consistency_report.yaml`
- `data/policies/rag.yaml` (deny/allow conforme padrão) e `data/policies/narrator.yaml` (override se necessário)
- `data/policies/context.yaml` / `data/policies/cache.yaml` se houver impacto
- `data/rag/golden/rag_golden_set.json` e `data/rag/concepts/concepts-*.yaml` quando aplicável
- `docs/database/samples/<entity>.csv` e demais docs/inventário/checklist relevantes
