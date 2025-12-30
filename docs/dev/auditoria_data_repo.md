# Auditoria do repositório `data/` (Araquem)

Data/hora da auditoria: Tue Dec 30 17:09:08 UTC 2025
Branch/commit: `work @ 8f04f40189804e38f28c2a535b89419a7306b914`

## A) Visão geral

- Entidades em `data/entities`: **22** pastas
- Arquivos `responses/*.md.j2`: **22**

### Sumário executivo (achados principais)

1. Todas as 22 entidades possuem YAML principal (`data/entities/<entity>/<entity>.yaml`) e contrato em `data/contracts`; **6 não possuem `hints.md`** e **9 não possuem `template.md`**, impactando sinal de RAG e a camada “template-first”.
2. `hints.md` é consumido apenas via **RAG/embeddings → planner** (prefixo `entity-*`); não há uso direto em formatter/presenter.
3. A ausência de `template.md` faz a camada “render_answer/template-first” não produzir texto (fallback), deixando **formatter + Narrator** como únicas fontes de saída textual.
4. Responses Jinja cobrem todas as entidades; a maioria trata vazios (`empty_message`), porém há falta de padronização em:
   - resumo/cabeçalho humano
   - filtros (date/currency/percent)
   - consistência de multi-ticker
5. Políticas em `data/policies` são carregadas em runtime (cache, narrator, context, rag, formatting). Arquivos de “quality/codex/llm_prompts” aparecem como referenciais/offline (não runtime).
6. `data/ops` é usado em runtime para thresholds do planner/orchestrator e inferência de parâmetros; conteúdo de quality/experimental é offline (scripts).
7. `data/concepts` aparece como fallback legado para templates; sem uso direto no runtime de perguntas/respostas.
8. `data/raw/indicators/catalog.md` e afins atuam como fonte de conhecimento para embeddings/RAG (sem ingestão ativa detectada).
9. `data/golden` é utilizado como artefato de testes/benchmarks (manifestos/relatórios/embeddings), sem chamadas runtime detectadas.
10. `data/ontology/ticker_index.yaml` é usado para resolução/validação de tickers no planner/orchestrator, mas não há job/rota de atualização automática identificada.

---

## B) Inventário de entidades (cobertura de arquivos)

| entity_id | `{entity}.yaml` | `hints.md` | `template.md` | `responses/*.md.j2` | contrato (data/contracts) | docs (docs/dev/entities) | Observação |
|---|---|---|---|---|---|---|---|
| carteira_enriquecida | sim | sim | **não** | table | sim | sim | falta `template.md` |
| client_fiis_dividends_evolution | sim | sim | **não** | table | sim | sim | falta `template.md` |
| client_fiis_performance_vs_benchmark | sim | sim | **não** | table | sim | sim | falta `template.md` |
| client_fiis_performance_vs_benchmark_summary | sim | sim | **não** | table | sim | sim | falta `template.md` |
| client_fiis_positions | sim | **não** | sim | table | sim | sim | falta `hints.md` |
| dividendos_yield | sim | sim | **não** | table | sim | sim | falta `template.md` |
| fii_overview | sim | sim | **não** | table | sim | sim | falta `template.md` |
| fiis_cadastro | sim | sim | sim | list | sim | sim | completa |
| fiis_dividendos | sim | sim | sim | table | sim | sim | completa |
| fiis_financials_revenue_schedule | sim | sim | sim | table | sim | sim | completa |
| fiis_financials_risk | sim | sim | sim | table | sim | sim | completa |
| fiis_financials_snapshot | sim | **não** | sim | table | sim | sim | falta `hints.md` |
| fiis_imoveis | sim | **não** | sim | table | sim | sim | falta `hints.md` |
| fiis_noticias | sim | **não** | sim | list | sim | sim | falta `hints.md` |
| fiis_precos | sim | sim | sim | table | sim | sim | completa |
| fiis_processos | sim | **não** | sim | list | sim | sim | falta `hints.md` |
| fiis_rankings | sim | **não** | sim | table | sim | sim | falta `hints.md` |
| fiis_yield_history | sim | sim | **não** | table | sim | sim | falta `template.md` |
| history_b3_indexes | sim | sim | sim | table | sim | sim | completa |
| history_currency_rates | sim | sim | sim | table | sim | sim | completa |
| history_market_indicators | sim | sim | sim | table | sim | sim | completa |
| macro_consolidada | sim | sim | **não** | table | sim | sim | falta `template.md` |

---

## C) Auditoria de `hints.md`

### Cobertura
- **Com `hints.md` (16):** carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_performance_vs_benchmark_summary, dividendos_yield, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_precos, fiis_yield_history, history_b3_indexes, history_currency_rates, history_market_indicators, macro_consolidada.
- **Sem `hints.md` (6):** client_fiis_positions, fiis_financials_snapshot, fiis_imoveis, fiis_noticias, fiis_processos, fiis_rankings.

### Uso real (pipeline)
- `hints.md` entra como **fonte de embeddings** (doc_id `entity-*-hints`) e é consumido pelo planner via fusão de scores (RAG → entity hints).
- Não foi identificado consumo direto em formatter/presenter.

### Gap de padronização
- Estruturas variam (em geral “O que é” / “Perguntas típicas”), mas sem seção explícita de:
  - limites (“não responder”, “escopo”)
  - linguagem e exemplos canônicos
- Ausência em 6 entidades reduz sinal específico por entidade no rerank/fusão.

---

## D) Auditoria de `template.md` (camada “template-first”)

### Cobertura
- **Com `template.md` (14):** fiis_precos, fiis_financials_revenue_schedule, fiis_dividendos, fiis_cadastro, fiis_rankings, fiis_processos, history_currency_rates, fiis_financials_snapshot, client_fiis_positions, history_b3_indexes, fiis_imoveis, fiis_financials_risk, history_market_indicators, fiis_noticias.
- **Sem `template.md` (8):** carteira_enriquecida, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_performance_vs_benchmark_summary, dividendos_yield, fii_overview, fiis_yield_history, macro_consolidada.

### Comportamento quando não existe
- Quando `template.md` não existe, a camada “template-first” deixa de produzir texto e a resposta depende do renderer de rows/Jinja e/ou Narrator (se habilitado por policy).

### Observações
- Os `template.md` existentes trazem descrição/exemplos, mas não há evidência de múltiplos “keys”/variações por template (dependendo do parser, pode limitar reuso).
- Falta padronização entre entidades (o que dificulta escala e automação).

---

## E) Auditoria de `responses/*.md.j2`

### Kinds
- `table.md.j2`: maioria
- `list.md.j2`: `fiis_cadastro`, `fiis_processos`, `fiis_noticias`

### Padronização (pontos bons)
- Tratamento de vazio (`empty_message`) presente na maioria.
- Multi-ticker: agrupamento por ticker em entidades como `fiis_precos`, `fiis_cadastro`, `fiis_imoveis` quando suportado.
- Filtros humanizados aparecem em algumas respostas (date/currency/percent), mas não de forma uniforme.

### Riscos / gaps
- Falta de resumo/cabeçalho humano em várias respostas (especialmente macro/risco) → baixa “escaneabilidade”.
- Entidades privadas dependem de `private:true` + policies; não há redaction adicional nos templates.

---

## F) `data/policies` e `data/ops` → consumidores (visão operacional)

### `data/policies` (runtime)
- `cache.yaml`: políticas de cache/privacidade por entidade
- `narrator.yaml`: enable/disable de LLM por entidade/bucket
- `context.yaml`: gerenciamento de histórico
- `rag.yaml`: regras de RAG/rerank/fusão
- `narrator_shadow.yaml`: sampling/redaction do shadow
- `formatting.yaml`: filtros e formatação do formatter

### `data/ops` (runtime)
- `planner_thresholds.yaml`: thresholds de roteamento
- `param_inference.yaml`: defaults/bindings para parâmetros (agg/window etc.)

### Offline
- `data/ops/quality*` e `data/ops/quality_experimental*`: scripts de qualidade (não runtime)

---

## G) `data/concepts`, `data/raw`, `data/golden`

- `data/concepts`: fallback legado para templates; baixo uso operacional no runtime atual.
- `data/raw`: fonte documental para embeddings (ex.: indicators catalog), sem ingestão ativa detectada.
- `data/golden`: artefatos de benchmark/testes e manifestos de qualidade/RAG; sem leitura runtime detectada.

---

## H) `data/contracts`

- Cobertura completa: **22** schemas `.schema.yaml` para **22** entidades.
- Estrutura geral consistente (colunas, ordering, presentation, sample_questions).
- Observação: contratos não “garantem” presença de `hints.md`/`template.md`, então a qualidade final ainda depende desses arquivos por entidade.

---

## I) `data/ontology`

### Uso em runtime
- `data/ontology/entity.yaml`: intents/buckets/normas para o planner
- `data/ontology/bucket_rules.yaml`: regras de bucket
- `data/ontology/ticker_index.yaml`: resolução/normalização de ticker em runtime

### ticker_index.yaml — pontos de atenção
- Não foi identificada rotina/rota/job de atualização automática.
- Ele é usado como lista canônica em runtime para resolução; sem atualização documentada, há risco de obsolescência.

---

## J) Recomendações priorizadas (baseadas no diagnóstico acima)

### P0 (prioridade máxima)
1. Criar `template.md` para as **8 entidades** sem arquivo, evitando que a camada “template-first” não produza texto.
2. Adicionar `hints.md` padronizado nas **6 entidades** que não possuem, para cobertura uniforme do sinal de RAG por entidade.
3. Documentar e implementar rotina de atualização do `data/ontology/ticker_index.yaml` (cron/job), com rastreabilidade de fonte.

### P1 (qualidade e segurança)
4. Revisar templates Jinja para incluir resumos/cabeçalhos humanos e padronizar filtros (date/currency/percent), principalmente em macro/risco.
5. Revisar `narrator_shadow.yaml` para cobrir todas as entidades privadas (atuais e futuras) e alinhar com `private:true`.
6. Refinar `rag.yaml` por entidade para tornar o uso de RAG mais seletivo e previsível.

### P2 (maturidade e automação)
7. Criar validação pré-deploy cruzando `data/contracts` vs `{entity}.yaml` vs `responses` (colunas/presentation).
8. Consolidar decisão sobre `data/concepts` (manter como legado documentado vs remover fallback).
9. Marcar formalmente `data/golden`/`data/ops/quality*` como offline/benchmarks para evitar limpeza acidental.
