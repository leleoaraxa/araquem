# Araquem — Catálogo de Entidades

## Estrutura declarativa

- `data/entities/<entidade>/entity.yaml`: contrato completo (identificadores, colunas, aggregations e apresentação).
- `data/entities/<entidade>/responses/<kind>.md.j2`: template de resposta alinhado a `presentation.kind` (summary, list ou table).
- `data/entities/<entidade>/view.sql.j2`: referência canônica da view consumida pelo builder (placeholder quando o SQL ainda está em outro repositório).
- `data/entities/<entidade>/templates.md`: respostas legadas formatadas via `render_answer` (mantidas para compatibilidade).

## 🧰 Developer Utilities (scripts/)

| Área            | Caminho                          | Descrição |
|-----------------|----------------------------------|------------|
| Qualidade       | `scripts/quality/`               | Push, diff e dashboards de qualidade |
| Observabilidade | `scripts/observability/`         | Métricas, alerts, dashboards e auditorias |
| Embeddings      | `scripts/embeddings/`            | Build e avaliação do índice RAG |
| Core            | `scripts/core/`                  | Comandos principais e manutenção de contratos |
| Maintenance     | `scripts/maintenance/`           | Ferramentas utilitárias e setup local |

## 🧪 Test Suites (tests/)

Estrutura por domínio:
- `core/`: pipeline base, cache, parâmetros
- `entities/`: validação das entidades YAML + SQL
- `planner/`: ontologia, explain e RAG
- `observability/`: dashboards e métricas Prometheus
- `quality/`: projeções, cron e gates
- `explain/`: fusão, re-rank e analytics
- `rag/`: métricas e integração RAG

## Entidades disponíveis

| Entidade | result_key | sql_view | presentation.kind |
| --- | --- | --- | --- |
| client_fiis_positions | `positions` | `client_fiis_positions` | `table` |
| fiis_cadastro | `cadastro_fii` | `fiis_cadastro` | `list` |
| fiis_dividendos | `dividendos_fii` | `fiis_dividendos` | `table` |
| fiis_financials_revenue_schedule | `financials_revenue` | `fiis_financials_revenue_schedule` | `table` |
| fiis_financials_risk | `financials_risk` | `fiis_financials_risk` | `summary` |
| fiis_financials_snapshot | `financials_snapshot` | `fiis_financials_snapshot` | `summary` |
| fiis_imoveis | `imoveis_fii` | `fiis_imoveis` | `list` |
| fiis_metrics | `fii_metrics` | `fiis_metrics` | `summary` |
| fiis_noticias | `noticias_fii` | `fiis_noticias` | `list` |
| fiis_precos | `precos_fii` | `fiis_precos` | `table` |
| fiis_processos | `processos_fii` | `fiis_processos` | `list` |
| fiis_rankings | `rankings_fii` | `fiis_rankings` | `table` |

> Todas as entidades operam com dados D-1 já consolidados na ingestão.

## Exemplos de perguntas suportadas

- "imóveis do HGLG11" → retorna os ativos do FII via `fiis_imoveis`.
- "status dos processos do HGRU11" → lista processos judiciais usando `fiis_processos`.
- "notícias do MXRF11" → traz matérias recentes através de `fiis_noticias`.

As intents continuam roteadas pelo planner via ontologia (`cadastro`, `precos`, `dividendos`, `rankings`, `metricas`, `noticias`), mantendo o contrato `/ask` inalterado.
