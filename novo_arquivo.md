# Resumo executivo

Templates auditados: 20

Entidades auditadas: 20

Falhas por severidade: CRITICAL 15 / HIGH 0 / MEDIUM 0 / LOW 0

## Matriz por entidade

| entity | template(s) | status | principais falhas | risco rewrite_only | filtros desconhecidos |
| --- | --- | --- | --- | --- | --- |
| carteira_enriquecida | table.md.j2 | FAIL | Sem guarda {% set rows = ... %} → quebra quando rows indefinido | RISCO | NÃO |
| client_fiis_dividends_evolution | table.md.j2 | FAIL | Sem guarda rows default | RISCO | NÃO |
| client_fiis_performance_vs_benchmark | table.md.j2 | FAIL | Sem guarda rows default | RISCO | NÃO |
| client_fiis_positions | table.md.j2 | FAIL | Sem guarda rows default | RISCO | NÃO |
| dividendos_yield | table.md.j2 | FAIL | Sem guarda rows default | RISCO | NÃO |
| fii_overview | table.md.j2 | FAIL | Sem guarda rows default | RISCO | NÃO |
| fiis_cadastro | list.md.j2 | FAIL | Sem guarda rows default | RISCO | NÃO |
| fiis_dividendos | table.md.j2 | FAIL | Sem guarda rows default | RISCO | NÃO |
| fiis_financials_revenue_schedule | table.md.j2 | FAIL | Sem guarda rows default | RISCO | NÃO |
| fiis_financials_risk | table.md.j2 | FAIL | Sem guarda rows default | RISCO | NÃO |
| fiis_financials_snapshot | table.md.j2 | PASS | Guarda rows e fallback condicional | OK | NÃO |
| fiis_imoveis | table.md.j2 | PASS | Guarda rows e fallback condicional | OK | NÃO |
| fiis_noticias | list.md.j2 | FAIL | Sem guarda rows default | RISCO | NÃO |
| fiis_precos | table.md.j2 | PASS | Guarda rows e hidratação segura com meta/aggregates | OK | NÃO |
| fiis_processos | list.md.j2 | PASS | Guarda rows e fallback condicional | OK | NÃO |
| fiis_rankings | table.md.j2 | PASS | Guarda rows e fallback condicional | OK | NÃO |
| fiis_yield_history | table.md.j2 | FAIL | Sem guarda rows default | RISCO | NÃO |
| history_b3_indexes | table.md.j2 | FAIL | Sem guarda rows default | RISCO | NÃO |
| history_currency_rates | table.md.j2 | FAIL | Sem guarda rows default | RISCO | NÃO |
| history_market_indicators | table.md.j2 | FAIL | Sem guarda rows default | RISCO | NÃO |
| macro_consolidada | table.md.j2 | FAIL | Sem guarda rows default | RISCO | NÃO |

## Falhas detalhadas

- **CRITICAL** – `data/entities/carteira_enriquecida/responses/table.md.j2` linhas 1–15: template inicia com `if rows` sem `{% set rows = rows if rows is defined else [] %}`, podendo quebrar quando `rows` indefinido em rewrite_only ou baseline vazio.
- **CRITICAL** – `data/entities/fiis_yield_history/responses/table.md.j2` linhas 1–19: mesma ausência de guarda `rows`, com acesso direto a `rows/subset` e `rows[0]`, arriscando exceção quando baseline não fornece `rows`.
- **CRITICAL** – `data/entities/history_currency_rates/responses/table.md.j2` linhas 1–19: falta de inicialização de `rows` e uso direto em `rows[0]` (latest), quebrando em respostas vazias ou rewrite_only.
- **CRITICAL** – `data/entities/history_market_indicators/responses/table.md.j2` linhas 1–13: idem, sem fallback `rows` e com `rows[0]` obrigatório.
- **CRITICAL** – `data/entities/history_b3_indexes/responses/table.md.j2` linhas 1–18: idem, ausência de guarda `rows` e uso de `rows[0]`.
- **CRITICAL** – `data/entities/fiis_cadastro/responses/list.md.j2` linhas 1–26: nenhum set defensivo para `rows`; bloco assume `rows` iterável, quebrando com undefined.
- **CRITICAL** – `data/entities/client_fiis_positions/responses/table.md.j2` linhas 1–15: ausência de guarda `rows`; acesso a `rows[0]` em branch true causa falha se baseline não preencheu `rows`.
- **CRITICAL** – `data/entities/client_fiis_performance_vs_benchmark/responses/table.md.j2` linhas 1–17: sem fallback `rows` e usa `rows[0]`, incompatível com rewrite_only e baseline vazio.
- **CRITICAL** – `data/entities/client_fiis_dividends_evolution/responses/table.md.j2` linhas 1–15: sem guarda `rows`; dicionário de meses e `rows[0]` assumem dados presentes.
- **CRITICAL** – `data/entities/fiis_dividendos/responses/table.md.j2` linhas 1–18: ausência de set `rows`; `subset[0]` acessado sem proteção.
- **CRITICAL** – `data/entities/fiis_financials_revenue_schedule/responses/table.md.j2` linhas 1–18: empty state apenas avalia `rows`, mas não inicializa; `rows[0]` usado diretamente.
- **CRITICAL** – `data/entities/fiis_financials_risk/responses/table.md.j2` linhas 1–14: verifica `rows` mas sem definir default; `rows[0]` acessado sem proteção quando `rows` indefinido.
- **CRITICAL** – `data/entities/dividendos_yield/responses/table.md.j2` linhas 1–19: sem guarda `rows`; `rows[0]` e fatia `rows[:12]` assumem presença de dados.
- **CRITICAL** – `data/entities/fiis_noticias/responses/list.md.j2` linhas 1–17: falta de inicialização de `rows`; grupo/loop falham se `rows` indefinido.
- **CRITICAL** – `data/entities/fii_overview/responses/table.md.j2` linhas 1–30: sem guarda `rows`; loops assumem dados e não protegem rewrite_only baseline vazio.
- **CRITICAL** – `data/entities/macro_consolidada/responses/table.md.j2` linhas 1–19: sem default `rows`; `rows[0]` usado no cabeçalho, quebrando com baseline vazio.

## Referências de conformidade (exemplos positivos)

- `fiis_precos` demonstra padrão correto: inicialização de `rows`, fallback condicionado a `meta.result_key`, e empty state seguro com `ticker_label` protegido.
- `fiis_imoveis` segue mesma resiliência, evitando sobrescrita quando `rows` já veio preenchido.

## Recomendações (sem patches)

- Adicionar guarda de resiliência (A1/A2) em todos os templates que falharam: incluir `{% set rows = rows if rows is defined else [] %}` no topo e hidratação condicional por `meta.result_key` apenas quando `not rows`. Prioridade alta para templates com `rows[0]` direto (históricos, macro, cadastros).
- Rever empty states pós-guardas: garantir que blocos `else` continuem operando após introduzir a guarda e não dependam de variáveis definidas apenas no branch populado.
- Validar rewrite_only nas entidades configuradas: alinhar templates falhos com políticas `rewrite_only` do Narrator (ex.: carteira_enriquecida, dividendos_yield, históricos) para evitar que baseline sem `rows` cause exceção na etapa de renderização.
