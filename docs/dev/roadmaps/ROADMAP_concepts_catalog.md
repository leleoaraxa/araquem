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

### 3.1 Tipo esperado e natureza dos dados

* **Natureza:** entidade **derivada de YAML do repositório** (conteúdo editorial/governado), não D-1.
* **Kind no catálogo (`data/entities/catalog.yaml`):** usar o tipo existente no projeto que melhor represente “derivado/estático”.

  * Se o catálogo só suportar `snapshot/view`, usar `snapshot` **com nota explícita**: `source=repo-yaml`.
* **Schema kind:** `view` (padrão do repositório para entidades SQL), independentemente de a origem ser view ou tabela; o requisito é haver uma relation consultável indicada por `sql_view`.
* **Fonte de verdade:** `data/concepts/catalog.yaml` (índice) + `data/concepts/*.yaml` (conteúdo).

### 3.2 Chave natural e colunas mínimas (contrato)

**Chave natural (fixar, sem ambiguidade):**

* `concept_id` + `version` (PK lógico / natural key)

**Campos mínimos (MVP) — placeholder, sem SQL real:**

* `concept_id` (string, **NOT NULL**) — ID estável do conceito (slug).
* `domain` (string, **NOT NULL**) — domínio (ex.: `fiis`, `macro`, `risk`, `carteira`).
* `section` (string, **NULLABLE**) — agrupamento humano (ex.: seção do glossário).

  * Regra: pode ser `NULL` quando não houver seção natural (ex.: root/methodology).
* `concept_type` (string, **NOT NULL**) — enum textual: `concept|field|metric|methodology`.
* `name` (string, **NOT NULL**) — título curto (ou nome do campo/métrica).
* `description` (string, **NULLABLE**) — resumo curto (1–3 linhas).
* `aliases` (json array, **NOT NULL**, default `[]`) — lista de aliases normalizada.
* `details_md` (string, **NULLABLE**) — texto longo (principalmente para `methodology`).
* `details_json` (jsonb, **NULLABLE**) — payload estruturado preservado (métricas, blocos, etc.).
* `source_file` (string, **NOT NULL**) — origem (ex.: `data/concepts/concepts-risk.yaml`).
* `source_path` (string, **NOT NULL**) — ponteiro determinístico no YAML (ex.: `terms[3]`, `sections.identidade.concepts.ticker`).
* `version` (string, **NOT NULL**) — bundle_id/build_id canônico do projeto (ex.: YYYYMMDDHHMM), usado para auditoria e cache.

**Invariantes de contrato (obrigatórios):**

* Unicidade: (`concept_id`, `version`) deve ser **único** (fail-closed no build).
* Auditabilidade: `source_file` + `source_path` devem permitir rastrear 1:1 o item no YAML.
* `tolerance` no schema deve ser **restritiva** (proibir colunas extras/faltantes), alinhado ao padrão `fiis_rankings`.

### 3.3 Conversão determinística (flatten) de `data/concepts/*` em linhas

A entidade `concepts_catalog` é derivada via um **build step determinístico** (sem heurísticas), que lê `data/concepts/catalog.yaml` (índice) e transforma os YAMLs em registros “flat” segundo regras fixas abaixo.

#### 3.3.1 Regra de `concept_id` (slug estável)

* `concept_id = "{domain}.{section_slug}.{name_slug}"` quando `section` existir e não estiver vazia
* caso contrário: `concept_id = "{domain}.{name_slug}"`
* `domain` vem do índice (`data/concepts/catalog.yaml`) para cada arquivo.
* `slugify`: lowercase, troca espaços por `_`, remove caracteres especiais de forma determinística.

#### 3.3.2 Padrões suportados (MVP)

**Padrão A — Lista de conceitos (`terms: [...]`)**

* Entrada típica: `terms: [ {name, aliases?, description?, ...}, ... ]`
* Para cada item `terms[i]`:

  * `concept_type="concept"`
  * `name=item.name` (obrigatório)
  * `description=item.description` (opcional)
  * `aliases=item.aliases || []`
  * `section=item.section || NULL` (somente se existir no YAML; sem inferência)
  * Se `section` não existir no item, deve permanecer `NULL` (não preencher valores default/root no MVP).
  * `source_path="terms[i]"`

**Padrão B — Glossário de campos por seção (`sections.<sec>.concepts.<field> = "<desc>"`)**

* Entrada típica: `sections: { <sec>: { concepts: { <field>: "<desc>" } } }`
* Para cada `section_name` e cada `field_name`:

  * `concept_type="field"`
  * `section=section_name`
  * `name=field_name`
  * `description=<desc string>`
  * `aliases=[]`
  * `source_path="sections.{section_name}.concepts.{field_name}"`

**Padrão C — Methodology/Métricas (arquivos `*-methodology.yaml`)**

* MVP (seguro): criar **1 linha** por arquivo como `methodology`, preservando estrutura em `details_json`.

  * `concept_type="methodology"`
  * `name`: usar campo `title` se existir; senão `"methodology"`
  * `description`: resumo curto se existir; senão `NULL`
  * `details_md`: texto longo se existir; senão `NULL`
  * `details_json`: subárvore relevante (ou YAML inteiro) para preservação
  * `source_path="root"`
* Expansão futura (não-MVP): gerar linhas `metric` **somente** se houver uma estrutura formal `metrics` claramente definida (lista/dict), sem inferência semântica.

#### 3.3.3 Validações (fail-closed)

O build step deve falhar (sem escrever output) se ocorrer qualquer um:

* Duplicidade de (`concept_id`, `version`)
* `name` ausente/vazio
* `aliases` presente e não-array
* No padrão B, valor do glossário não é string
* `source_file`/`source_path` ausentes
* `domain` ausente no índice (`catalog.yaml`) para o arquivo
* `domain` fora do conjunto permitido pelo índice (`catalog.yaml`)

### 3.4 Exemplos de perguntas (para roteamento)
- “Quais conceitos existem na seção Rankings e Popularidade?”
- “Liste conceitos do domínio fiis sobre volatilidade.”
- “Explique o conceito de Sharpe e mostre o catálogo correspondente.”
- “Quais conceitos do catálogo tratam de macroeconomia?”

---

## 4. Checklist executável (alinhado aos PRs)

> Este checklist segue estritamente a sequência PR1 → PR5.
> Cada item indica **arquivos a criar** e **arquivos a tocar depois** (*to-change later*).
> **Nenhuma alteração deve ser feita fora da PR correspondente.**

---

### PR1 — Contratos + entidade base + template

**Criar**

* `data/contracts/entities/concepts_catalog.schema.yaml`
* `data/entities/concepts_catalog/concepts_catalog.yaml`
* `data/entities/concepts_catalog/hints.md` *(se padrão do repo exigir)*
* Templates/responses table-kind (ex.: `responses/table.md.j2`, `responses/empty.md.j2`, se aplicável)

**Checklist**

* [ ] Schema com colunas mínimas (ver Seção 3.2) e `tolerance` restritiva (sem extras/faltas).
* [ ] Chave natural definida como (`concept_id`, `version`).
* [ ] Entity YAML com `id`, `result_key`, `sql_view` (placeholder), `presentation` e `ask` **mínimo** (sem tuning fino).
* [ ] Template table-kind renderiza colunas básicas (`domain`, `section`, `name`, `concept_type`, `description`) sem erro.

---

### PR2 — Pipeline determinístico de conversão (YAML → linhas)

**Criar**

* Script/build step de conversão de `data/concepts/catalog.yaml` + `data/concepts/*.yaml` em registros `concepts_catalog` (view/tabela/artefato derivado conforme padrão do repo).

**Checklist**

* [ ] Conversão implementa **apenas** os padrões definidos na Seção 3.3 (A, B e C-MVP).
* [ ] `concept_id` gerado por slug determinístico (sem heurísticas).
* [ ] `source_file` e `source_path` preenchidos para **todas** as linhas.
* [ ] Validações **fail-closed**:

  * duplicidade (`concept_id`, `version`)
  * `name` vazio
  * glossário com valor não-string
  * `domain` ausente no índice
* [ ] Output estável e reproduzível (mesmo input → mesmo output).

---

### PR3 — Quality suites + thresholds + amostras de roteamento

**Criar**

* `data/ops/quality/payloads/concepts_catalog_suite.json`
* `data/ops/quality/payloads/entities_sqlonly/concepts_catalog_suite.json` *(se SQL-only)*
* `data/ops/quality/projection_concepts_catalog.json` *(se padrão exigir projection)*

**To-change later**

* `data/ops/planner_thresholds.yaml`
* `data/ops/quality/routing_samples.json`

**Checklist**

* [ ] Suite cobre perguntas por **domínio**, **seção** e **definição**.
* [ ] Projection (se existir) valida `must_have_columns` mínimos.
* [ ] Thresholds definidos por analogia com entidades snapshot (sem relaxar gates).
* [ ] Suites passam localmente contra o output do PR2.

---

### PR4 — Ontologia + policies + colisões

**To-change later**

* `data/entities/catalog.yaml`
* `data/ontology/entity.yaml`
* `data/ontology/ontology_manifest.yaml`
* `data/policies/cache.yaml`
* `data/policies/context.yaml`
* `data/policies/narrator.yaml`
* `data/policies/rag.yaml`
* `data/policies/quality.yaml`

**Checklist**

* [ ] Entidade registrada no catálogo com coverage correto.
* [ ] Intent/entidade adicionada na ontologia com tokens/phrases **conservadores**.
* [ ] `anti_tokens` definidos para evitar colisão com entidades factuais.
* [ ] `llm_enabled=false` por padrão (SQL-only).
* [ ] Cache configurado com TTL e `key_fields` compatíveis com a chave natural.
* [ ] Auditoria de colisões rodada (`scripts/ontology/audit_collisions.py`) sem regressões.
* [ ] Manifesto de ontologia atualizado via `scripts/ontology/validate_and_hash.py`.

---

### PR5 — Docs, cobertura e observabilidade

**To-change later**

* `docs/ARAQUEM_COVERAGE_MATRIX.md`
* `docs/dev/ENTITIES_INVENTORY_2025.md`
* `docs/dev/mapa_uso_entidades.md`
* `docs/qa/GUIA_ENTIDADES_ARAQUEM.md`
* `docs/dev/entities/concepts_catalog.md` *(somente se padrão do repo exigir)*

**Checklist**

* [ ] Entidade aparece na matriz de cobertura e no inventário.
* [ ] Guia QA inclui exemplos reais de perguntas para `concepts_catalog`.
* [ ] Relatórios de superfície/uso (`reports/entities/*`) refletem a nova entidade.
* [ ] Nenhuma regressão detectada nos relatórios de ontologia ou planner.

---

### Regra de ouro (governança)

* **Nunca** pular PRs.
* Ontologia/policies **só entram após** existir output + suites passando.
* Qualquer mudança fora do checklist invalida o PR.

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

1. **PR1 — Contratos + entidade base + template**

   * Criar:

     * `data/contracts/entities/concepts_catalog.schema.yaml`
     * `data/entities/concepts_catalog/concepts_catalog.yaml`
     * `data/entities/concepts_catalog/hints.md` (se padrão do repo exigir)
     * templates/responses table-kind (se o padrão de entidades exigir para render)
   * Objetivo: registrar o contrato e a superfície de resposta, sem pipeline nem ontologia ainda.

2. **PR2 — Pipeline determinístico de conversão (YAML → linhas)**

   * Implementar o build step que lê `data/concepts/catalog.yaml` + `data/concepts/*.yaml` e produz `concepts_catalog` (view/tabela/artefato derivado conforme padrão do repo).
   * Incluir validações **fail-closed** e rastreabilidade (`source_file`, `source_path`).
   * Objetivo: produzir output estável e auditável antes de calibrar roteamento.

3. **PR3 — Quality suites + thresholds + amostras de roteamento**

   * Criar suites:

     * `data/ops/quality/payloads/concepts_catalog_suite.json`
     * `data/ops/quality/payloads/entities_sqlonly/concepts_catalog_suite.json` (se aplicável)
     * `data/ops/quality/projection_concepts_catalog.json` (se padrão exigir)
   * Atualizar (to-change):

     * `data/ops/planner_thresholds.yaml`
     * `data/ops/quality/routing_samples.json`
   * Objetivo: garantir roteamento + validação de colunas e estabilidade.

4. **PR4 — Ontologia + policies (cache/context/narrator/rag/quality) + colisões**

   * Atualizar (to-change):

     * `data/entities/catalog.yaml`
     * `data/ontology/entity.yaml` + `data/ontology/ontology_manifest.yaml`
     * `data/policies/cache.yaml`, `context.yaml`, `narrator.yaml`, `rag.yaml`, `quality.yaml`
   * Rodar auditoria de colisões (`scripts/ontology/audit_collisions.py`) e registrar mitigação via tokens/anti_tokens.
   * Objetivo: governança completa após existir output e suites.

5. **PR5 — Docs e observabilidade**

   * Atualizar inventários/cobertura/guias e validar presença nos relatórios:

     * `docs/ARAQUEM_COVERAGE_MATRIX.md`, `docs/dev/ENTITIES_INVENTORY_2025.md`, `docs/qa/GUIA_ENTIDADES_ARAQUEM.md`, etc.
     * `reports/entities/*` (validação pós-integração)
   * Objetivo: fechar documentação e rastreabilidade.



---

# CHECKLIST DE REVISÃO DE PR — `concepts_catalog`

> **Regra geral (vale para todos os PRs)**
>
> * ❌ Nenhum hardcode sem fonte declarativa (YAML/ontologia/policies).
> * ❌ Nenhuma heurística sem contrato explícito.
> * ✅ Diferenças pequenas, auditáveis e alinhadas ao roadmap.
> * ✅ Diferença “explicável”: todo campo novo sabe de onde vem e para que existe.

---

## PR1 — Contratos + entidade base + template

### 1. Schema (`data/contracts/entities/concepts_catalog.schema.yaml`)

**Revisar no diff:**

* [ ] Campos **exatamente** os definidos no roadmap (sem extras “por conveniência”).
* [ ] `tolerance` **restritiva** (extras/faltantes proibidos).
* [ ] `concept_id` e `version` marcados como **NOT NULL**.
* [ ] `section`, `description`, `details_md`, `details_json` **nullable** (conforme delta).
* [ ] Tipos coerentes (`string` vs `json` vs `jsonb`), sem ambiguidade.

**Falhas comuns a barrar**

* Coluna adicionada “porque pode ser útil”.
* `section` forçada como NOT NULL sem regra determinística.
* Campos implícitos (ex.: `created_at`) sem padrão global no projeto.

---

### 2. Entity YAML (`data/entities/concepts_catalog/concepts_catalog.yaml`)

**Revisar no diff:**

* [ ] `id` correto: `concepts_catalog`.
* [ ] `result_key` consistente com o schema.
* [ ] `sql_view` presente (mesmo que placeholder).
* [ ] `presentation` define colunas **existentes no schema**.
* [ ] `ask` mínimo: intents conservadores, **sem tuning agressivo**.
* [ ] Ordenação padrão definida (ex.: `domain`, `section`, `name`).

**Falhas comuns a barrar**

* `ask` muito permissivo (colide com entidades factuais).
* Coluna referenciada no template que não existe no schema.
* Dependência implícita de LLM.

---

### 3. Templates / responses

**Revisar no diff:**

* [ ] Template table-kind renderiza com **0 linhas**, **1 linha** e **N linhas**.
* [ ] Sem lógica condicional complexa (somente apresentação).
* [ ] `details_md`/`details_json` exibidos **somente** quando presentes.

**Falhas comuns a barrar**

* Template tentando “interpretar” conteúdo.
* Condicionais que mudam semântica da resposta.

---

## PR2 — Pipeline determinístico (YAML → linhas)

### 4. Conversão / build step

**Revisar no diff:**

* [ ] Fonte de verdade explícita: leitura de `data/concepts/catalog.yaml`.
* [ ] Padrões suportados **apenas** os definidos (A, B e C-MVP).
* [ ] `concept_id` gerado por slug determinístico (sem exceções).
* [ ] `source_file` e `source_path` preenchidos **para todas as linhas**.
* [ ] `aliases` sempre normalizado para array.
* [ ] `version` vindo de fonte única (build/bundle), não hardcoded.

**Validações obrigatórias (fail-closed)**

* [ ] Duplicidade (`concept_id`, `version`) → erro.
* [ ] `name` vazio → erro.
* [ ] Glossário com valor não-string → erro.
* [ ] Arquivo fora do índice → erro.

**Falhas comuns a barrar**

* `try/except` que ignora erro e continua.
* Inferência semântica (“se não tem section, assume X”).
* Transformação silenciosa de dados inválidos.

---

## PR3 — Quality suites + thresholds

### 5. Suites (`concepts_catalog_suite.json`)

**Revisar no diff:**

* [ ] Perguntas cobrem: domínio, seção, definição.
* [ ] Expectativas apontam **explicitamente** para `concepts_catalog`.
* [ ] Não dependem de ordem aleatória de linhas.

### 6. SQL-only suite (se aplicável)

* [ ] Nenhuma expectativa depende de LLM/narrator.
* [ ] Suite falha se coluna obrigatória faltar.

### 7. Thresholds / samples

* [ ] Thresholds alinhados a entidades snapshot (não relaxados).
* [ ] Samples adicionados **sem remover** cobertura existente.

**Falhas comuns a barrar**

* Suite “fraca” que sempre passa.
* Ajuste de threshold para “fazer passar”.

---

## PR4 — Ontologia + policies + colisões

### 8. Ontologia (`data/ontology/entity.yaml`)

**Revisar no diff:**

* [ ] Intent claramente conceitual (ex.: “conceitos”, “glossário”).
* [ ] Tokens/phrases **não colidem** com entidades factuais.
* [ ] `anti_tokens` explícitos para termos ambíguos.

### 9. Policies

**Cache**

* [ ] TTL compatível com conteúdo estático.
* [ ] `key_fields` compatíveis com (`concept_id`, `version`).

**Narrator**

* [ ] `llm_enabled=false` por padrão.

**RAG**

* [ ] Negado por padrão (SQL-only), salvo justificativa explícita.

**Quality**

* [ ] `not_null` aplicado às chaves e campos essenciais.

### 10. Colisões

* [ ] `scripts/ontology/audit_collisions.py` rodado.
* [ ] `collision_report` sem regressões não justificadas.

**Falhas comuns a barrar**

* Ajuste de tokens sem atualizar anti_tokens.
* Ativar RAG “porque é texto”.

---

## PR5 — Docs, cobertura e observabilidade

### 11. Documentação

**Revisar no diff:**

* [ ] Entidade aparece no inventário e coverage matrix.
* [ ] Doc da entidade (se existir) descreve **o contrato**, não implementação.

### 12. Relatórios

* [ ] `entities_surface_report` inclui `concepts_catalog`.
* [ ] `entities_usage_report` não mostra regressões inesperadas.

**Falhas comuns a barrar**

* Doc desalinhada do código.
* Atualizar docs sem evidência nos relatórios.

---

## Checklist final de aprovação (gate)

Antes de aprovar **qualquer PR**:

* [ ] PR respeita a ordem (não pula etapa).
* [ ] Tudo que está no diff está coberto por checklist.
* [ ] Não há lógica “escondida” fora de YAML/ontologia/policies.
* [ ] Dado gerado é reproduzível e auditável.
* [ ] O PR pode ser revertido isoladamente sem quebrar o pipeline.

---
