# Auditoria do repositório `data/` (Araquem)

Data/hora da auditoria: Tue Dec 30 17:57:22 UTC 2025
Branch/commit: `work @ 5e15018dc71d5fa66629f0cc42b23d0ce5737b82`

## A) Visão geral

- Entidades em `data/entities`: **22** pastas
- Arquivos `responses/*.md.j2`: **22**

### Sumário executivo (achados principais)

1. Todas as 22 entidades possuem YAML principal (`data/entities/<entity>/<entity>.yaml`) e contrato em `data/contracts`; `hints.md` e `template.md` estão presentes em **22/22** pastas, padronizados no singular (`template.md`) sem `templates.md` remanescentes (runtime mantém fallback para `templates.md` e `data/concepts/*_templates.md` por compatibilidade).
2. `hints.md` é consumido apenas via **RAG/embeddings → planner** (prefixo `entity-*`); não há uso direto em formatter/presenter.
3. A camada “render_answer/template-first” agora tem fallback textual em todas as entidades via `template.md`, reduzindo a dependência de Narrator quando o renderer de rows/Jinja não cobre casos de texto livre.
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
| client_fiis_enriched_portfolio | sim | sim | sim | table | sim | sim | completa |
| client_fiis_dividends_evolution | sim | sim | sim | table | sim | sim | completa |
| client_fiis_performance_vs_benchmark | sim | sim | sim | table | sim | sim | completa |
| client_fiis_performance_vs_benchmark_summary | sim | sim | sim | table | sim | sim | completa |
| client_fiis_positions | sim | sim | sim | table | sim | sim | completa |
| dividendos_yield | sim | sim | sim | table | sim | sim | completa |
| fii_overview | sim | sim | sim | table | sim | sim | completa |
| fiis_cadastro | sim | sim | sim | list | sim | sim | completa |
| fiis_dividendos | sim | sim | sim | table | sim | sim | completa |
| fiis_financials_revenue_schedule | sim | sim | sim | table | sim | sim | completa |
| fiis_financials_risk | sim | sim | sim | table | sim | sim | completa |
| fiis_financials_snapshot | sim | sim | sim | table | sim | sim | completa |
| fiis_imoveis | sim | sim | sim | table | sim | sim | completa |
| fiis_noticias | sim | sim | sim | list | sim | sim | completa |
| fiis_precos | sim | sim | sim | table | sim | sim | completa |
| fiis_processos | sim | sim | sim | list | sim | sim | completa |
| fiis_rankings | sim | sim | sim | table | sim | sim | completa |
| fiis_yield_history | sim | sim | sim | table | sim | sim | completa |
| history_b3_indexes | sim | sim | sim | table | sim | sim | completa |
| history_currency_rates | sim | sim | sim | table | sim | sim | completa |
| history_market_indicators | sim | sim | sim | table | sim | sim | completa |
| macro_consolidada | sim | sim | sim | table | sim | sim | completa |

---

## C) Auditoria de `hints.md`

### Cobertura
- **Cobertura completa (22/22):** client_fiis_enriched_portfolio, client_fiis_dividends_evolution, client_fiis_performance_vs_benchmark, client_fiis_performance_vs_benchmark_summary, client_fiis_positions, dividendos_yield, fii_overview, fiis_cadastro, fiis_dividendos, fiis_financials_revenue_schedule, fiis_financials_risk, fiis_financials_snapshot, fiis_imoveis, fiis_noticias, fiis_precos, fiis_processos, fiis_rankings, fiis_yield_history, history_b3_indexes, history_currency_rates, history_market_indicators, macro_consolidada (inclui novos `hints.md` para as seis entidades que não possuíam).

### Uso real (pipeline)
- `hints.md` entra como **fonte de embeddings** (doc_id `entity-*-hints`) e é consumido pelo planner via fusão de scores (RAG → entity hints).
- Não foi identificado consumo direto em formatter/presenter.

### Gap de padronização
- Base mínima padronizada agora cobre 22/22 entidades (com seções de limites e campos nas adições recentes).
- Conteúdo legado ainda varia em profundidade, exemplos e linguagem; pode ser harmonizado para reforçar sinal específico por entidade.

---

## D) Auditoria de `template.md` (camada “template-first”)

### Cobertura
- **Cobertura completa (22/22):** todas as entidades possuem `template.md` (singular); não restam `templates.md` no repositório, mas o runtime mantém fallback para `templates.md` (compat) e `data/concepts/*_templates.md` (legado).

### Comportamento quando não existe
- Com `template.md` padronizado em 22/22, a camada “template-first” mantém fallback textual; remover o arquivo voltaria a deixar a resposta dependente apenas do renderer de rows/Jinja e/ou Narrator (se habilitado por policy). Há compatibilidade explícita com `templates.md` e `data/concepts/*_templates.md`, mas o formato canônico é `template.md`.

### Observações
- Os `template.md` preservam descrições/exemplos atuais; não há evidência de múltiplos “keys”/variações por template (dependendo do parser, pode limitar reuso).
- A linguagem e a granularidade variam entre entidades; harmonização futura pode facilitar automação.

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
1. Documentar e implementar rotina de atualização do `data/ontology/ticker_index.yaml` (cron/job), com rastreabilidade de fonte.

### P1 (qualidade e segurança)
1. Revisar templates Jinja para incluir resumos/cabeçalhos humanos e padronizar filtros (date/currency/percent), principalmente em macro/risco.
2. Revisar `narrator_shadow.yaml` para cobrir todas as entidades privadas (atuais e futuras) e alinhar com `private:true`.
3. Refinar `rag.yaml` por entidade para tornar o uso de RAG mais seletivo e previsível.

### P2 (maturidade e automação)
1. Criar validação pré-deploy cruzando `data/contracts` vs `{entity}.yaml` vs `responses` (colunas/presentation).
2. Consolidar decisão sobre `data/concepts` (manter como legado documentado vs remover fallback).
3. Marcar formalmente `data/golden`/`data/ops/quality*` como offline/benchmarks para evitar limpeza acidental.

---

## K) Validação

- Suporte de checagem local para `template.md` e `hints.md` em todas as entidades: `python scripts/diagnostics/audit_entities_support_files.py`
