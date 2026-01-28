# BUCKET_MAP_AUDIT.md

## 0) Executive Summary (10–15 linhas)
1) **Bucket A/B/C (governance)** será fonte única em `data/ontology/entity.yaml`, onde há blocos `buckets` (entidades) e `intents[].bucket` (intents). (data/ontology/entity.yaml:L13-L44) (data/ontology/entity.yaml:L41-L120)
2) Hoje existe **duplicidade** com `data/ontology/bucket_rules.yaml`, que também define buckets A/B/C e está **desativado** (`enabled: false`). (data/ontology/bucket_rules.yaml:L19-L87)
3) O Planner resolve bucket via `resolve_bucket` e retorna **string vazia** quando não há regra habilitada, propagando bucket vazio para as camadas seguintes. (app/planner/planner.py:L40-L103)
4) O bucket é escrito no `explain` do Planner (`meta_explain["bucket"]`) e é propagado para `/ask`, ContextManager, Orchestrator e `plan_hash`. (app/planner/planner.py:L1286-L1321) (app/api/ask.py:L248-L268) (app/orchestrator/routing.py:L348-L470) (app/cache/rt_cache.py:L323-L370)
5) O ContextManager aplica TTL por bucket (`bucket_ttl`) com fallback para `max_age_turns` quando bucket está vazio/None. (data/policies/context.yaml:L63-L83) (app/context/context_manager.py:L586-L607)
6) O Narrator lê bucket de `meta["bucket"]`, aplica policy `narrator.buckets` e usa bucket como label de métricas. (app/narrator/narrator.py:L987-L1035) (app/narrator/narrator.py:L860-L938) (data/policies/narrator.yaml:L38-L55)
7) RAG **não é governado por bucket**; a nota em `rag.yaml` é drift/legado. Texto é outra dimensão (ex.: `compute.mode=concept`), fora de escopo aqui. (data/policies/rag.yaml:L51-L63) (app/planner/planner.py:L221-L266)
8) Há colisões semânticas: histogram **buckets** (observability), **buckets** de faixas de conceitos e **bucket** de privacidade no catálogo. (data/ops/observability.yaml:L74-L179) (data/concepts/concepts-fiis.yaml:L72-L90) (data/entities/catalog.yaml:L61-L66)
9) A convergência exige **reservar “bucket” apenas para D1** (A/B/C) e **renomear** demais usos (D2/D3/D4) no plano (sem código). (data/ops/observability.yaml:L74-L179) (data/entities/catalog.yaml:L61-L66)
10) Ações de convergência (sem código): (i) congelar A/B/C em `entity.yaml`, (ii) declarar “bucket” reservado, (iii) renomear usos D2/D3/D4, (iv) orientar consumidores a ler somente `entity.yaml`, (v) descontinuar `bucket_rules.yaml` no futuro. (data/ontology/entity.yaml:L13-L44) (data/ontology/bucket_rules.yaml:L19-L87)

**Evidências‑chave**
- Fonte única proposta: `buckets` e `intents[].bucket` em `entity.yaml`. (data/ontology/entity.yaml:L13-L44) (data/ontology/entity.yaml:L41-L44)
- Duplicidade: bucket_rules.yaml com A/B/C desativado. (data/ontology/bucket_rules.yaml:L19-L87)
- resolve_bucket retorna "" quando não há regra habilitada. (app/planner/planner.py:L40-L103)
- bucket propagado para explain → /ask → plan_hash. (app/planner/planner.py:L1286-L1321) (app/api/ask.py:L248-L268) (app/cache/rt_cache.py:L323-L370)
- Colisões semânticas (observability, conceitos, catálogo). (data/ops/observability.yaml:L74-L179) (data/concepts/concepts-fiis.yaml:L72-L90) (data/entities/catalog.yaml:L61-L66)

---

## 1) Glossário e domínios
**D1) bucket_governance_abc (A/B/C)**
- Definição oficial proposta: bucket A/B/C definido em `data/ontology/entity.yaml` (buckets e intents). (data/ontology/entity.yaml:L13-L44)

**D2) bucket_observability_histogram**
- “buckets” como faixas numéricas de histogramas (Prometheus). (data/ops/observability.yaml:L74-L179)

**D3) bucket_privacy_or_access**
- “bucket: carteira/privado” no catálogo de entidades (classificação de privacidade). (data/entities/catalog.yaml:L61-L66)

**D4) bucket_concepts_bands**
- “buckets” como faixas de vencimento/recebíveis em conceitos. (data/concepts/concepts-fiis.yaml:L72-L90)

**D5) bucket_other**
- “bucket” como agregação temporal/agrupamento técnico (ex.: analytics). (app/analytics/repository.py:L120-L203)

**Campos conflituosos encontrados (exemplos)**
- `buckets` em observability (histogram). (data/ops/observability.yaml:L74-L179)
- `bucket: carteira/privado` no catálogo. (data/entities/catalog.yaml:L61-L66)
- `buckets` em conceitos de receita. (data/concepts/concepts-fiis.yaml:L72-L90)
- `bucket_minute` em analytics. (app/analytics/repository.py:L120-L203)

**Evidências‑chave**
- Fonte A/B/C: `buckets` + `intents[].bucket`. (data/ontology/entity.yaml:L13-L44)
- Hist buckets: observability.yaml. (data/ops/observability.yaml:L74-L179)
- Bucket de privacidade: catalog.yaml. (data/entities/catalog.yaml:L61-L66)
- Buckets de conceitos: concepts-fiis.yaml. (data/concepts/concepts-fiis.yaml:L72-L90)

---

## 2) Fonte única: Prova e inventário em data/ontology/entity.yaml
**Provas**
- Bloco `buckets` (A/B/C) com entidades agrupadas. (data/ontology/entity.yaml:L13-L39)
- Campo `intents[].bucket` (ex.: `ticker_query` → A). (data/ontology/entity.yaml:L41-L44)

**Inventário (resumo por bucket, conforme YAML)**
- **Bucket A**: lista de entidades de FIIs (ex.: `fiis_quota_prices`, `fiis_rankings`, etc.). (data/ontology/entity.yaml:L14-L27)
- **Bucket B**: entidades de carteira do cliente. (data/ontology/entity.yaml:L28-L34)
- **Bucket C**: entidades macro/índices. (data/ontology/entity.yaml:L35-L38)


**Evidências‑chave**
- `buckets` A/B/C em entity.yaml. (data/ontology/entity.yaml:L13-L39)
- `intents[].bucket` presente (ex.: `ticker_query`). (data/ontology/entity.yaml:L41-L44)

---

## 3) Mapa de fluxo end‑to‑end (pergunta → bucket → efeitos)
**Planner → explain/meta → /ask → ContextManager → Orchestrator → plan_hash/cache → Narrator → RAG**
- **Planner resolve bucket** (D1) via `resolve_bucket` e retorna `""` quando não há regra habilitada. (app/planner/planner.py:L40-L103)
- **Planner escreve bucket** no explain (`meta_explain["bucket"]`). (app/planner/planner.py:L1286-L1321)
- **/ask lê bucket** de `planner.explain.bucket.selected` com fallback `""`. (app/api/ask.py:L248-L253)
- **/ask propaga bucket** em `meta` dos turnos (ContextManager) e para `resolve_last_reference(...)`. (app/api/ask.py:L257-L268) (app/api/ask.py:L371-L379)
- **ContextManager usa bucket** para TTL por bucket; fallback para `max_age_turns` quando bucket vazio/None. (app/context/context_manager.py:L586-L607)
- **Orchestrator lê bucket** do explain e passa para `build_plan_hash`. (app/orchestrator/routing.py:L357-L448)
- **Cache/plan_hash** inclui bucket (`str(bucket or "")`). (app/cache/rt_cache.py:L323-L370)
- **Narrator lê bucket** de `meta["bucket"]` e aplica policy por bucket; métricas usam `bucket_label`. (app/narrator/narrator.py:L987-L1035) (app/narrator/narrator.py:L860-L938)
- **RAG/rerank**: RAG não é governado por bucket; nota em policy é drift/legado. (data/policies/rag.yaml:L51-L63) (app/planner/planner.py:L221-L266)

**Evidências‑chave**
- resolve_bucket retorna string vazia em modo neutro. (app/planner/planner.py:L40-L103)
- bucket no explain do Planner. (app/planner/planner.py:L1286-L1321)
- bucket propagado no /ask e ContextManager. (app/api/ask.py:L248-L268) (app/api/ask.py:L371-L379)
- bucket no plan_hash. (app/cache/rt_cache.py:L323-L370)
- bucket em Narrator + métricas. (app/narrator/narrator.py:L860-L938) (app/narrator/narrator.py:L987-L1035)

---

## 4) Mapa de código (app/) — produtores/consumidores
**Tabela (app/)**
| Arquivo | Função/Classe | Papel | Domínio | Lê/Escreve | Evidência |
|---|---|---|---|---|---|
| app/planner/planner.py | resolve_bucket | Resolve bucket A/B/C | D1 | Escreve | (app/planner/planner.py:L40-L103) |
| app/planner/planner.py | meta_explain["bucket"] | Expõe bucket no explain | D1 | Escreve | (app/planner/planner.py:L1286-L1321) |
| app/planner/planner.py | _entities_for_bucket | Filtra entidades por bucket | D1 | Lê | (app/planner/planner.py:L453-L474) |
| app/planner/planner.py | _resolve_rerank_policy | Usa bucket como domain | D1 | Lê | (app/planner/planner.py:L221-L266) |
| app/orchestrator/routing.py | prepare_plan | Lê bucket do explain e propaga | D1 | Lê/Escreve | (app/orchestrator/routing.py:L357-L470) |
| app/cache/rt_cache.py | build_plan_hash | Inclui bucket no fingerprint | D1 | Lê | (app/cache/rt_cache.py:L323-L370) |
| app/api/ask.py | /ask flow | Lê bucket do explain e injeta em meta | D1 | Lê/Escreve | (app/api/ask.py:L248-L268) |
| app/context/context_manager.py | last_reference TTL | TTL por bucket + fallback | D1 | Lê | (app/context/context_manager.py:L586-L607) |
| app/narrator/narrator.py | render / render_global_post_sql | Lê bucket de meta e usa em métricas | D1 | Lê | (app/narrator/narrator.py:L987-L1035) (app/narrator/narrator.py:L860-L938) |
| app/narrator/prompts.py | build_bucket_d_global_prompt | Prompt global textual (nome legacy no código; não implica domínio de governança adicional) | D1 | Lê | (app/narrator/prompts.py:L490-L513) |
| app/observability/metrics.py | metrics labels | Bucket como label (métricas Narrator) | D1 | Lê | (app/observability/metrics.py:L44-L51) |
| app/analytics/repository.py | bucket_minute | Bucketing temporal (analytics) | D5 | Lê/Escreve | (app/analytics/repository.py:L120-L203) |

**Scripts/Docs (fora app/)**
- **Scripts D1**: build_coverage_report usa buckets da ontologia e policies por bucket. (scripts/quality/build_coverage_report.py:L75-L92) (scripts/quality/build_coverage_report.py:L280-L296)
- **Scripts D5**: cluster_routing_misses usa “bucket” como agrupamento de erros. (scripts/quality/cluster_routing_misses.py:L96-L103)
- **Docs D1/D4/D5**: ver inventário no Apêndice (files list). (docs/CHECKLIST-2025.0-prod.md:L40-L50) (docs/dev/entities/fiis_financials_snapshot.md:L17-L21)

**Evidências‑chave**
- resolve_bucket + explain bucket no Planner. (app/planner/planner.py:L40-L103) (app/planner/planner.py:L1286-L1321)
- Orchestrator/plan_hash com bucket. (app/orchestrator/routing.py:L357-L470) (app/cache/rt_cache.py:L323-L370)
- Narrator lê bucket e usa labels. (app/narrator/narrator.py:L987-L1035) (app/observability/metrics.py:L44-L51)
- Scripts com bucket (D1/D5). (scripts/quality/build_coverage_report.py:L75-L92)

---

## 5) Inventário em data/ (fora da ontologia)
**Arquivos em data/ com “bucket” (classificação D1..D5)**
1) `data/ontology/bucket_rules.yaml` → D1 (duplicado, deve ser descontinuado). (data/ontology/bucket_rules.yaml:L19-L87)
2) `data/policies/context.yaml` → D1 (bucket_ttl). (data/policies/context.yaml:L63-L83)
3) `data/policies/narrator.yaml` → D1 (buckets A/B/C). (data/policies/narrator.yaml:L38-L55)
4) `data/policies/rag.yaml` → D1 (nota legacy; RAG não é governado por bucket). (data/policies/rag.yaml:L51-L63)
5) `data/ops/reports/coverage_report_2025_0.json` → D1 (bucket por entidade). (data/ops/reports/coverage_report_2025_0.json:L289-L340)
6) `data/ops/observability.yaml` → D2 (histogram buckets). (data/ops/observability.yaml:L74-L179)
7) `data/entities/catalog.yaml` → D3 (bucket: carteira/privado). (data/entities/catalog.yaml:L61-L66)
8) `data/concepts/concepts-fiis.yaml` → D4 (buckets de faixas). (data/concepts/concepts-fiis.yaml:L72-L90)
9) `data/entities/fiis_financials_revenue_schedule/fiis_financials_revenue_schedule.yaml` → D4 (keywords “bucket/buckets”). (data/entities/fiis_financials_revenue_schedule/fiis_financials_revenue_schedule.yaml:L83-L90)
10) `data/entities/fiis_financials_revenue_schedule/hints.md` → D4 (buckets como faixas). (data/entities/fiis_financials_revenue_schedule/hints.md:L1-L10)
11) `data/entities/fiis_quota_prices/fiis_quota_prices.yaml` → D4/D5 (anti_tokens “bucket”, “bucket macro”). (data/entities/fiis_quota_prices/fiis_quota_prices.yaml:L92-L139)
12) `data/entities/fiis_financials_snapshot/fiis_financials_snapshot.yaml` → D4 (anti_tokens “bucket”). (data/entities/fiis_financials_snapshot/fiis_financials_snapshot.yaml:L125-L129)
13) `data/entities/fiis_news/fiis_news.yaml` → D4 (anti_tokens “bucket”). (data/entities/fiis_news/fiis_news.yaml:L74-L82)
14) `data/embeddings/store/embeddings.jsonl` → D4 (conteúdo derivado de concepts com “buckets”). (data/embeddings/store/embeddings.jsonl:L5-L5)

**Sugestões de renomeação (apenas nomes de campos) para NÃO‑D1**
- D2 (observability): `buckets` → `histogram_buckets`. (data/ops/observability.yaml:L74-L179)
- D3 (catalog): `bucket` → `access_scope` (ou `privacy_scope`). (data/entities/catalog.yaml:L61-L66)
- D4 (concepts): `buckets` → `maturity_bands` / `term_bands`. (data/concepts/concepts-fiis.yaml:L72-L90)
- D4/D5 (entity keywords/anti_tokens): usar termos específicos (ex.: `term_band`, `macro_scope`). (data/entities/fiis_quota_prices/fiis_quota_prices.yaml:L92-L139)

**Evidências‑chave**
- bucket_rules.yaml (duplicado). (data/ontology/bucket_rules.yaml:L19-L87)
- bucket_ttl em context.yaml. (data/policies/context.yaml:L63-L83)
- hist buckets em observability.yaml. (data/ops/observability.yaml:L74-L179)
- bucket de privacidade em catalog.yaml. (data/entities/catalog.yaml:L61-L66)
- buckets de conceitos em concepts-fiis.yaml. (data/concepts/concepts-fiis.yaml:L72-L90)

---

## 6) DRIFT REPORT (duplicidades e inconsistências)
**Duplicação #1 — bucket_rules.yaml vs fonte única (entity.yaml)**
- **Evidência de existência**: bucket_rules define A/B/C e está desativado. (data/ontology/bucket_rules.yaml:L19-L87)
- **Evidência de uso no runtime**: Planner carrega bucket_rules via `_load_bucket_rules` e resolve bucket por regras. (app/planner/planner.py:L24-L103)
- **Recomendação**: descontinuar/ignorar no futuro (sem alteração agora). (data/ontology/bucket_rules.yaml:L19-L87)

**Duplicação #2 — quaisquer outras “fontes” de bucket A/B/C**
- **Docs** que afirmam bucket A/B/C (não-fonte):
  - fiis_rankings bucket B. (docs/dev/entities/fiis_rankings.md:L160-L163)
  - fiis_legal_proceedings bucket A. (docs/dev/entities/fiis_legal_proceedings.md:L140-L143)
  - history_b3_indexes bucket C. (docs/dev/entities/history_b3_indexes.md:L62-L64)
  - fiis_registrations bucket B. (docs/dev/entities/fiis_registrations.md:L73-L77)
- **Reports** que materializam bucket (derivados): coverage report em data/ops. (data/ops/reports/coverage_report_2025_0.json:L289-L340)

**Colisões semânticas (não D1)**
- D2: histogram buckets em observability. (data/ops/observability.yaml:L74-L179)
- D3: bucket de privacidade em catálogo. (data/entities/catalog.yaml:L61-L66)
- D4: buckets como faixas de recebíveis. (data/concepts/concepts-fiis.yaml:L72-L90)
- D5: bucket temporal em analytics. (app/analytics/repository.py:L120-L203)

**Evidências‑chave**
- bucket_rules.yaml duplicado e desativado. (data/ontology/bucket_rules.yaml:L19-L87)
- Planner resolve bucket por rules. (app/planner/planner.py:L24-L103)
- Docs com bucket A/B/C. (docs/dev/entities/fiis_rankings.md:L160-L163)
- Colisões D2/D3/D4/D5. (data/ops/observability.yaml:L74-L179) (data/entities/catalog.yaml:L61-L66) (app/analytics/repository.py:L120-L203)

---

## 7) Plano de convergência (SEM CÓDIGO, passos sequenciais)
1) **Congelar definição A/B/C em `entity.yaml`** (buckets + intents). (data/ontology/entity.yaml:L13-L44)
   - Prós: fonte única explícita. Contras: exige disciplina para não replicar em docs/policies.
2) **Declarar “bucket” como termo reservado para D1** (A/B/C). (data/ontology/entity.yaml:L13-L44)
   - Implicação: toda ocorrência não‑D1 deve ser renomeada (apenas plano).
3) **Renomear usos não‑D1 (plano)**
   - D2: `buckets` → `histogram_buckets`. (data/ops/observability.yaml:L74-L179)
   - D3: `bucket` → `access_scope`. (data/entities/catalog.yaml:L61-L66)
   - D4: `buckets` → `maturity_bands` / `term_bands`. (data/concepts/concepts-fiis.yaml:L72-L90)
   - D5: `bucket_minute` → `time_bin`/`interval_bin` (plano). (app/analytics/repository.py:L120-L203)
4) **Consumidores D1 devem ler exclusivamente `entity.yaml`** (Planner/Orchestrator/Context/Narrator). **RAG não depende de bucket** (texto é outra dimensão). (app/planner/planner.py:L453-L503) (app/orchestrator/routing.py:L357-L470)
5) **bucket_rules.yaml**: declarar legado/descontinuar/arquivar no futuro (sem alteração agora). (data/ontology/bucket_rules.yaml:L19-L87)

**Evidências‑chave**
- Fonte única alvo: entity.yaml (buckets/intents). (data/ontology/entity.yaml:L13-L44)
- D2/D3/D4 exemplos para renomeação. (data/ops/observability.yaml:L74-L179) (data/entities/catalog.yaml:L61-L66) (data/concepts/concepts-fiis.yaml:L72-L90)
- Consumidores críticos (Planner/Orchestrator). (app/planner/planner.py:L453-L503) (app/orchestrator/routing.py:L357-L470)

---

## 8) Checklist de “fonte única” (critérios de aceite)
1) **Nenhum arquivo fora de `data/ontology/entity.yaml` define bucket A/B/C** (apenas referências derivadas). (data/ontology/entity.yaml:L13-L44)
2) **Nenhum arquivo usa o campo “bucket” com semântica não‑D1** (renomes concluídos). (data/ops/observability.yaml:L74-L179) (data/entities/catalog.yaml:L61-L66)
3) **Planner usa apenas `entity.yaml` para buckets**; `bucket_rules.yaml` está legado/ignorado. (app/planner/planner.py:L453-L503) (data/ontology/bucket_rules.yaml:L19-L87)
4) **`plan_hash` inclui bucket A/B/C apenas quando proveniente de `entity.yaml`**. (app/cache/rt_cache.py:L323-L370)
5) **ContextManager aplica TTL por bucket A/B/C sem depender de fontes duplicadas**. (app/context/context_manager.py:L586-L607) (data/policies/context.yaml:L63-L83)
6) **Narrator lê bucket apenas como D1 (A/B/C)**; **RAG não é governado por bucket**. (app/narrator/narrator.py:L860-L938) (app/planner/planner.py:L221-L266)
7) **Existe verificação automatizável** que falha se “bucket” aparecer fora de D1 (lint/quality), sem implementar agora. (scripts/quality/build_coverage_report.py:L75-L92)

**Checklist de convergência (resumo)**
- [ ] `entity.yaml` é a única fonte de bucket A/B/C. (data/ontology/entity.yaml:L13-L44)
- [ ] `bucket_rules.yaml` legado/ignorado (sem uso crítico). (app/planner/planner.py:L24-L103)
- [ ] “bucket” reservado a D1; todos os demais usos renomeados. (data/ops/observability.yaml:L74-L179) (data/entities/catalog.yaml:L61-L66)
- [ ] Relatórios/docs apenas descrevem (não definem) buckets. (docs/dev/entities/fiis_rankings.md:L160-L163)

**Evidências‑chave**
- `entity.yaml` contém buckets e intents. (data/ontology/entity.yaml:L13-L44)
- Planner ainda lê bucket_rules.yaml (legado). (app/planner/planner.py:L24-L103)
- D2/D3 colisões atuais. (data/ops/observability.yaml:L74-L179) (data/entities/catalog.yaml:L61-L66)
- Scripts/quality podem suportar lint futuro. (scripts/quality/build_coverage_report.py:L75-L92)

---

## Apêndice — comandos executados + outputs resumidos
**Comandos executados (obrigatórios)**
- `rg -n "(?i)\bbucket\b" app data scripts tests docs`
- `rg -n "bucket_rules\.yaml|resolve_bucket|_load_bucket_rules" app data`
- `rg -n "entity\.yaml" app/planner data/ontology` → **sem matches** (nenhum arquivo contém a string literal `entity.yaml` nesses diretórios).
- `rg -n "plan_hash|build_plan_hash|fingerprint\[" app`
- `rg -n "last_reference|bucket_ttl" app data/policies`
- `rg -n "narrator.*bucket|buckets:" app data/policies`
- `rg -n "histogram.*buckets|buckets:\s*\[" data/ops`
- `rg -n "concepts.*buckets|buckets:" data/concepts`
- `rg -l "(?i)\bbucket\b" app data scripts tests docs`

**Principais outputs (resumo)**
- Lista de arquivos com “bucket” (rg -l) usada para inventário de app/data/scripts/tests/docs. (listado no comando acima; ver seções 4 e 5)
- `bucket_rules.yaml` contém `enabled: false` em defaults e rules. (data/ontology/bucket_rules.yaml:L19-L87)
- `entity.yaml` contém buckets A/B/C e intents[].bucket. (data/ontology/entity.yaml:L13-L44)
- `build_plan_hash` inclui `bucket` como string vazia quando ausente. (app/cache/rt_cache.py:L323-L370)
- `bucket_ttl` e fallback em ContextManager. (data/policies/context.yaml:L63-L83) (app/context/context_manager.py:L586-L607)
