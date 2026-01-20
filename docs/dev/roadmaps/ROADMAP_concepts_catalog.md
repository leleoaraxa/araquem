# ROADMAP — concepts_catalog

## 1. Resumo executivo
Este roadmap define como introduzir a entidade **`concepts_catalog`** no Araquem seguindo o padrão de **`fiis_rankings`** e o contrato declarativo de catálogo/ontologia/quality/policies já existente. O objetivo é ter um catálogo estruturado de conceitos (derivado de `data/concepts/*.yaml` e `data/concepts/catalog.yaml`) que seja consultável como entidade determinística, com governança clara (schemas, ontologia, policies, quality, colisões). O plano não altera nada agora: lista arquivos a criar, pontos de integração e checks obrigatórios. Todas as mudanças futuras devem ser dirigidas por fontes declarativas (YAML/ontologia/policies) e pelos padrões já auditados em `fiis_rankings`. O foco é garantir integração completa (catálogo, contratos, quality, policies, ontologia e observabilidade), sem heurísticas hardcoded no runtime.

---

## 2. Baseline fiis_rankings: onde integra e para que serve (tabela)

| Arquivo (baseline) | Papel no sistema | O que `concepts_catalog` precisa espelhar |
| --- | --- | --- |
| `data/contracts/entities/fiis_rankings.schema.yaml` | Contrato do schema (colunas, tipos, nullable, tolerância). | Criar schema equivalente para `concepts_catalog` com colunas mínimas e tolerância (sem extras/faltas). |
| `data/entities/fiis_rankings/fiis_rankings.yaml` | Definição da entidade (id, sql_view, result_key, ask, colunas, apresentação). | Criar `concepts_catalog.yaml` com `id`, `result_key`, `sql_view`/view, `ask` (intents/keywords), colunas e apresentação. |
| `data/entities/fiis_rankings/hints.md` | Hints de entidade (quando usados por RAG/embeddings). | Decidir se `concepts_catalog` terá `hints.md` (ex.: para orientar roteamento ou contexto conceitual). |
| `data/ops/quality/payloads/fiis_rankings_suite.json` | Suite de QA de roteamento/intent (perguntas-alvo). | Criar suite de perguntas para `concepts_catalog` (perguntas conceituais e de catálogo). |
| `data/ops/quality/payloads/entities_sqlonly/fiis_rankings_suite.json` | Suite SQL-only (quando a entidade é determinística). | Criar suite SQL-only para `concepts_catalog` se a resposta for 100% determinística via SQL. |
| `data/ops/quality/projection_fiis_rankings.json` | Projection quality: must_have_columns e samples. | Criar `projection_concepts_catalog.json` se o padrão exigir projection para a nova entidade. |
| `scripts/dev/test_fiis_rankings_table_template.py` | Teste manual do template Jinja (table). | Criar script equivalente para validar template da nova entidade (se houver template). |
| `data/entities/catalog.yaml` | Catálogo oficial de entidades com paths e coverage. | Registrar `concepts_catalog` com paths + coverage (cache/rag/narrator/param_inference). |
| `data/ontology/entity.yaml` | Ontologia de intents e exemplos por entidade. | Adicionar intent/entidade `concepts_catalog` com tokens, frases, anti_tokens. |
| `data/ontology/ontology_manifest.yaml` | Manifesto/assinatura de ontologia para auditoria. | Atualizar hash/manifest após inserir a nova intent. |
| `data/ops/entities_consistency_report.yaml` | Checklist declarativo de consistência. | Incluir `concepts_catalog` com flags esperadas (schema, quality projection, policies). |
| `data/ops/param_inference.yaml` | Inferência temporal/agregações declarativas. | Incluir apenas se a entidade precisar de janelas/agg (provável **não**). |
| `data/ops/planner_thresholds.yaml` | Thresholds do planner por intent/entidade. | Definir thresholds para `concepts_catalog` (por analogia com entidades snapshot). |
| `data/ops/quality/routing_samples.json` | Amostras globais de roteamento. | Inserir perguntas para garantir roteamento para `concepts_catalog`. |
| `data/ops/quality_experimental/planner_rag_integration.json` | Checks RAG/Planner (quando relevante). | Adicionar amostra se `concepts_catalog` interagir com RAG/collections. |
| `data/policies/cache.yaml` | Política de cache por entidade. | Configurar TTL, scope e key_fields para `concepts_catalog`. |
| `data/policies/context.yaml` | Políticas de contexto/last_reference. | Definir se a entidade pode herdar contexto (provável **não**). |
| `data/policies/narrator.yaml` | Política do Narrator por entidade. | Definir `llm_enabled` (provável **false**) e limites. |
| `data/policies/quality.yaml` | Regras de qualidade (freshness, not_null, ranges). | Adicionar checks mínimos (not_null para chaves/colunas críticas). |
| `data/policies/rag.yaml` | Política de RAG por intent/entidade. | Definir se a entidade é elegível a RAG (provável **negada** para SQL-only). |
| `data/golden/m65_quality.json` + `data/golden/m65_quality.yaml` | Golden sets de roteamento/qualidade. | Adicionar exemplos de perguntas de `concepts_catalog` quando ampliar cobertura. |
| `docs/ARAQUEM_COVERAGE_MATRIX.md` | Matriz de cobertura oficial. | Registrar cobertura de `concepts_catalog` (categoria conceitual). |
| `docs/dev/ENTITIES_INVENTORY_2025.md` | Inventário de entidades. | Adicionar a nova entidade com objetivo e tipo. |
| `docs/dev/mapa_uso_entidades.md` | Mapa de templates/hints/uso. | Atualizar com templates/hints de `concepts_catalog` (se existirem). |
| `docs/dev/DOMAIN_FIIS_INVENTORY.md` + `docs/dev/DOMAIN_MAP_FIIS.yaml` | Inventário/Mapa de domínio. | Atualizar se a entidade ampliar o domínio FIIs/conceitos. |
| `docs/dev/entities/fiis_rankings.md` | Doc detalhada por entidade. | Criar doc equivalente **se** o padrão exigir para novas entidades. |
| `docs/qa/GUIA_ENTIDADES_ARAQUEM.md` | Guia QA com exemplos reais. | Adicionar `concepts_catalog` no mapa rápido + exemplos. |
| `reports/entities/entities_surface_report.json` + `reports/entities/entities_usage_report.json` | Relatórios de superfície/uso. | Validar após integração (nova entidade deve aparecer). |
| `reports/ontology/collision_report.json` | Relatório de colisões de tokens/phrases. | Re-rodar auditoria após adicionar a intent. |
| `scripts/ontology/audit_collisions.py` | Auditoria de colisões. | Garantir nova entidade não conflita com intents existentes. |
| `scripts/ontology/validate_and_hash.py` | Validação/manifesto da ontologia. | Re-gerar hashes e manifest após editar ontologia. |
| `tests/rag/test_context_builder.py` | Testes de RAG/context (se alterar políticas). | Ajustar somente se `concepts_catalog` interagir com RAG/context. |
| `docs/database/ddls/views.sql` | Padrões de naming SQL/view. | Seguir naming de view (ex.: `concepts_catalog`) se houver view SQL. |

---

## 3. Especificação da entidade `concepts_catalog`

### 3.1 Tipo esperado
- **Kind sugerido:** `snapshot` no catálogo (`data/entities/catalog.yaml`) para alinhar com entidades D-1/estáticas. 
- **Schema kind:** `view` (seguindo `fiis_rankings.schema.yaml`) se a entidade for exposta via view SQL. 
- **Fonte de verdade:** catálogo de conceitos declarativo (`data/concepts/catalog.yaml` + `data/concepts/*.yaml`).

### 3.2 Chave natural e colunas mínimas (contrato)
**Chave natural (sugerida):**
- `concept_id` + `domain` + `version` **ou** `concept_id` + `domain` + `source_file`.

**Colunas mínimas recomendadas (placeholder, sem SQL real):**
- `concept_id` (string, não nulo) — ID estável do conceito.
- `domain` (string, não nulo) — domínio (ex.: fiis, macro, risk, carteira).
- `section` (string, não nulo) — seção do catálogo (ex.: “Rankings e Popularidade”).
- `concept_type` (string, não nulo) — tipo do conceito (definição, métrica, processo, risco, etc.).
- `name` (string, não nulo) — título curto do conceito.
- `description` (string, não nulo) — descrição resumida.
- `source_file` (string, não nulo) — arquivo de origem (ex.: `data/concepts/concepts-fiis.yaml`).
- `source_path` (string, não nulo) — path completo do item no YAML (para auditabilidade).
- `version` (string, não nulo) — versão do catálogo/geração.
- `created_at` / `updated_at` (datetime, não nulo) — timestamps de geração (se padrão da entidade).

**Contrato esperado (placeholder):**
- `concept_id` deve ser único dentro de (`domain`, `version`).
- `source_file`/`source_path` devem permitir rastrear 1:1 com `data/concepts/*.yaml`.
- `tolerance` deve proibir colunas extras/faltantes (como `fiis_rankings`).

### 3.3 Conexão com `data/concepts/catalog.yaml`
- O pipeline **não deve usar heurísticas**: a fonte de verdade deve ser o YAML (`data/concepts/catalog.yaml` + `data/concepts/*.yaml`).
- O build step deve ser explícito (script/ETL declarativo) e gerar uma view ou tabela materializada **determinística**. 
- Responsável provável: módulo de ingest/build de conceitos (a definir), que lê `data/concepts/catalog.yaml`, resolve `sections` e produz linhas em `concepts_catalog`.

### 3.4 Exemplos de perguntas (para roteamento)
- “Quais conceitos existem na seção Rankings e Popularidade?”
- “Liste conceitos do domínio fiis sobre volatilidade.”
- “Explique o conceito de Sharpe e mostre o catálogo correspondente.”
- “Quais conceitos do catálogo tratam de macroeconomia?”

---

## 4. Checklist executável (passos numerados)

> Cada passo lista os **arquivos envolvidos** e o tipo de alteração esperada. **Não executar agora.**

1) **Definir contrato e entidade**
   - **Arquivos envolvidos (criar):**
     - `data/contracts/entities/concepts_catalog.schema.yaml`
     - `data/entities/concepts_catalog/concepts_catalog.yaml`
     - `data/entities/concepts_catalog/hints.md` (se for desejado para RAG/planner)
     - `data/entities/concepts_catalog/templates.md` + `data/entities/concepts_catalog/responses/*.md.j2` (se for padrão de resposta)
   - **Checklist:**
     - [ ] Schema com colunas mínimas e `tolerance` restritiva.
     - [ ] Entity YAML com `id`, `result_key`, `sql_view`, `ask` (intents/keywords/synonyms), `presentation`.

2) **Registrar a entidade no catálogo e ontologia**
   - **Arquivos envolvidos (to-change later):**
     - `data/entities/catalog.yaml`
     - `data/ontology/entity.yaml`
     - `data/ontology/ontology_manifest.yaml`
   - **Checklist:**
     - [ ] Adicionar `concepts_catalog` no catálogo (paths + coverage).
     - [ ] Adicionar intent com tokens/phrases/anti_tokens (sem não-ASCII, sem duplicatas).
     - [ ] Re-gerar hashes no manifesto (via `scripts/ontology/validate_and_hash.py`).

3) **Policies (cache/context/narrator/rag/quality)**
   - **Arquivos envolvidos (to-change later):**
     - `data/policies/cache.yaml`
     - `data/policies/context.yaml`
     - `data/policies/narrator.yaml`
     - `data/policies/rag.yaml`
     - `data/policies/quality.yaml`
   - **Checklist:**
     - [ ] Cache com TTL e `key_fields` compatíveis com a chave natural.
     - [ ] Contexto: definir se pode herdar entidade/ticker (provável **não**).
     - [ ] Narrator: manter `llm_enabled=false` se SQL-only.
     - [ ] RAG: negar intent se for determinístico; permitir somente se houver coleção textual.
     - [ ] Quality: adicionar `not_null` para chaves e campos essenciais.

4) **Ops/Planner/Quality suites**
   - **Arquivos envolvidos (criar):**
     - `data/ops/quality/payloads/concepts_catalog_suite.json`
     - `data/ops/quality/payloads/entities_sqlonly/concepts_catalog_suite.json` (se SQL-only)
     - `data/ops/quality/projection_concepts_catalog.json` (se houver projection)
   - **Arquivos envolvidos (to-change later):**
     - `data/ops/planner_thresholds.yaml`
     - `data/ops/quality/routing_samples.json`
     - `data/ops/quality_experimental/planner_rag_integration.json` (se for relevante)
   - **Checklist:**
     - [ ] Suite cobre perguntas de catálogo, domínio, seção, definição.
     - [ ] Projection valida `must_have_columns`.
     - [ ] Thresholds definidos por analogia com entidades snapshot.

5) **Roteamento e colisões**
   - **Arquivos envolvidos (to-change later):**
     - `data/ontology/entity.yaml`
     - `reports/ontology/collision_report.json`
     - `scripts/ontology/audit_collisions.py`
   - **Checklist:**
     - [ ] Rodar auditoria de colisões após definir tokens/phrases.
     - [ ] Adicionar anti_tokens para evitar conflito com entidades factuais.

6) **Docs e inventários**
   - **Arquivos envolvidos (to-change later):**
     - `docs/dev/ENTITIES_INVENTORY_2025.md`
     - `docs/ARAQUEM_COVERAGE_MATRIX.md`
     - `docs/dev/mapa_uso_entidades.md`
     - `docs/qa/GUIA_ENTIDADES_ARAQUEM.md`
     - `docs/dev/entities/concepts_catalog.md` (apenas se padrão para novas entidades)
   - **Checklist:**
     - [ ] Registrar entidade no inventário e mapa de cobertura.
     - [ ] Atualizar guia QA com exemplos e paths.

7) **Observabilidade e relatórios**
   - **Arquivos envolvidos (to-change later):**
     - `reports/entities/entities_surface_report.json`
     - `reports/entities/entities_usage_report.json`
   - **Checklist:**
     - [ ] Validar presença da entidade nos relatórios após integração.

---

## 5. Quality & Observability (suites, gates, colisões)

- **Suites mínimas:**
  - `concepts_catalog_suite.json` com perguntas sobre **domínio**, **seção** e **definição de conceitos**.
  - `entities_sqlonly/concepts_catalog_suite.json` se a entidade for determinística (SQL-only).
- **Projection quality:**
  - `projection_concepts_catalog.json` listando `must_have_columns` como `concept_id`, `domain`, `section`, `name`, `description`, `source_file`.
- **Quality gates:**
  - Atualizar `data/policies/quality.yaml` para `not_null` e ranges (se aplicável).
  - Atualizar `data/ops/planner_thresholds.yaml` (min_score/min_gap) por analogia com `fiis_rankings`.
- **Colisões:**
  - Rodar `scripts/ontology/audit_collisions.py` e revisar `reports/ontology/collision_report.json`.
  - Assegurar tokens/phrases não colidem com entidades factuais (ex.: `fiis_rankings`, `fiis_dividends`).

---

## 6. Critérios de aceite

- [ ] `concepts_catalog` registrado no catálogo e ontologia (paths corretos).
- [ ] Schema validado com colunas mínimas e tolerância restritiva.
- [ ] Suites de quality passando (routing + sqlonly, se aplicável).
- [ ] `collision_report` sem regressões ou conflitos não mitigados.
- [ ] Template de resposta (se existir) renderiza sem erro (script de teste dedicado).
- [ ] Pipeline de ingest/build determinístico e auditável (uso de `source_file`/`source_path`).

---

## 7. Plano de PRs (sequência sugerida)

1. **PR1 — Contratos + entidade base**
   - Criar schema, entity YAML, hints/templates (se aplicável).
2. **PR2 — Catálogo + ontologia + policies**
   - Registrar entidade no catálogo, ontologia e políticas (cache/context/narrator/rag/quality).
3. **PR3 — Quality suites + projections + thresholds**
   - Adicionar suites, projection, thresholds e samples de roteamento.
4. **PR4 — Pipeline/build do catálogo de conceitos**
   - Implementar geração determinística do catálogo (sem heurísticas) + view/tabela.
5. **PR5 — Docs e observabilidade**
   - Atualizar inventários, coverage matrix, guia QA e verificar relatórios.

