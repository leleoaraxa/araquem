# Concepts Validation Report

## Resumo

- Gate 1 (integridade estrutural): **OK**
- Gate 2 (schema): **FAIL**
- Gate 3 (regressão semântica): **FAIL**

## Tabela por arquivo

| arquivo | sections | items | text_chars | delta_items | delta_text_chars | status | notas |
| --- | --- | --- | --- | --- | --- | --- | --- |
| data/concepts/concepts-carteira.yaml | 1 | 5 | 2676 | 0.0% | 0.0% | FAIL | items.id não presente (checagem de unicidade N/A) |
| data/concepts/concepts-fiis.yaml | 12 | 64 | 4937 | 0.0% | 0.0% | FAIL | items.id não presente (checagem de unicidade N/A) |
| data/concepts/concepts-institutional-policies.yaml | 1 | 3 | 733 | 0.0% | 0.0% | OK | items.id não presente (checagem de unicidade N/A) |
| data/concepts/concepts-institutional-privacy.yaml | 1 | 3 | 587 | 0.0% | 0.0% | OK | items.id não presente (checagem de unicidade N/A) |
| data/concepts/concepts-institutional-product-positioning.yaml | 1 | 5 | 821 | 0.0% | 0.0% | OK | items.id não presente (checagem de unicidade N/A) |
| data/concepts/concepts-institutional-terms.yaml | 1 | 13 | 1433 | 0.0% | 0.0% | OK | items.id não presente (checagem de unicidade N/A) |
| data/concepts/concepts-institutional.yaml | 1 | 6 | 2032 | 0.0% | 0.0% | OK | items.id não presente (checagem de unicidade N/A) |
| data/concepts/concepts-macro-methodology.yaml | 4 | 9 | 3152 | 0.0% | 0.0% | OK | items.id não presente (checagem de unicidade N/A) |
| data/concepts/concepts-macro.yaml | 1 | 5 | 2859 | 0.0% | 0.0% | OK | items.id não presente (checagem de unicidade N/A) |
| data/concepts/concepts-risk-metrics-methodology.yaml | 3 | 9 | 2794 | 0.0% | 0.0% | FAIL | items.id não presente (checagem de unicidade N/A) |
| data/concepts/concepts-risk.yaml | 1 | 9 | 4656 | 0.0% | 0.0% | OK | items.id não presente (checagem de unicidade N/A) |
| data/concepts/concepts-support-errors.yaml | 1 | 4 | 645 | 0.0% | 0.0% | OK | items.id não presente (checagem de unicidade N/A) |
| data/concepts/concepts-support-howto.yaml | 1 | 3 | 639 | 0.0% | 0.0% | OK | items.id não presente (checagem de unicidade N/A) |
| data/concepts/concepts-support-plans.yaml | 1 | 3 | 542 | 0.0% | 0.0% | OK | items.id não presente (checagem de unicidade N/A) |
| data/concepts/concepts-support-troubleshooting.yaml | 1 | 6 | 1219 | 0.0% | 0.0% | OK | items.id não presente (checagem de unicidade N/A) |
| data/concepts/concepts-support.yaml | 1 | 5 | 1356 | 0.0% | 0.0% | OK | items.id não presente (checagem de unicidade N/A) |

## Problemas encontrados

- **Gate 2** [FAIL] data/concepts/concepts-carteira.yaml (linha 29): Unexpected item key: typical_metrics — `- name: "Concentração e diversificação"`. Sugestão: Remover chaves fora do schema canônico.
- **Gate 2** [FAIL] data/concepts/concepts-risk-metrics-methodology.yaml (linha 21): Field 'interpretation' must be a list of strings. — `- name: "Volatilidade"`. Sugestão: Ajustar o campo para lista de strings.
- **Gate 2** [FAIL] data/concepts/concepts-risk-metrics-methodology.yaml (linha 30): Field 'interpretation' must be a list of strings. — `- name: "Max Drawdown"`. Sugestão: Ajustar o campo para lista de strings.
- **Gate 2** [FAIL] data/concepts/concepts-risk-metrics-methodology.yaml (linha 38): Field 'interpretation' must be a list of strings. — `- name: "Sharpe"`. Sugestão: Ajustar o campo para lista de strings.
- **Gate 2** [FAIL] data/concepts/concepts-risk-metrics-methodology.yaml (linha 46): Field 'interpretation' must be a list of strings. — `- name: "Sortino"`. Sugestão: Ajustar o campo para lista de strings.
- **Gate 2** [FAIL] data/concepts/concepts-risk-metrics-methodology.yaml (linha 54): Field 'interpretation' must be a list of strings. — `- name: "Treynor"`. Sugestão: Ajustar o campo para lista de strings.
- **Gate 2** [FAIL] data/concepts/concepts-risk-metrics-methodology.yaml (linha 62): Field 'interpretation' must be a list of strings. — `- name: "Alfa de Jensen"`. Sugestão: Ajustar o campo para lista de strings.
- **Gate 2** [FAIL] data/concepts/concepts-risk-metrics-methodology.yaml (linha 71): Field 'interpretation' must be a list of strings. — `- name: "Beta e R²"`. Sugestão: Ajustar o campo para lista de strings.
- **Gate 3** [FAIL] data/concepts/concepts-fiis.yaml (linha 44): Item missing body/definition content. — `title: "Dividendos e Renda"`. Sugestão: Adicionar description/definition/usage ou notas úteis.
- **Gate 3** [FAIL] data/concepts/concepts-fiis.yaml (linha 58): Item missing body/definition content. — `title: "Indicadores Financeiros e Valuation"`. Sugestão: Adicionar description/definition/usage ou notas úteis.
- **Gate 3** [FAIL] data/concepts/concepts-fiis.yaml (linha 82): Item missing body/definition content. — `- name: "Estrutura financeira"`. Sugestão: Adicionar description/definition/usage ou notas úteis.
- **Gate 3** [FAIL] data/concepts/concepts-fiis.yaml (linha 93): Item missing body/definition content. — `- name: "Crescimento"`. Sugestão: Adicionar description/definition/usage ou notas úteis.
- **Gate 3** [FAIL] data/concepts/concepts-fiis.yaml (linha 123): Item missing body/definition content. — `- name: "Buckets"`. Sugestão: Adicionar description/definition/usage ou notas úteis.
- **Gate 3** [FAIL] data/concepts/concepts-fiis.yaml (linha 121): Item missing body/definition content. — `title: "Recebíveis e Indexadores"`. Sugestão: Adicionar description/definition/usage ou notas úteis.
- **Gate 3** [FAIL] data/concepts/concepts-fiis.yaml (linha 242): Item missing body/definition content. — `- name: "Índices da B3"`. Sugestão: Adicionar description/definition/usage ou notas úteis.
- **Gate 3** [FAIL] data/concepts/concepts-fiis.yaml (linha 250): Item missing body/definition content. — `- name: "Moedas"`. Sugestão: Adicionar description/definition/usage ou notas úteis.
- **Gate 3** [FAIL] data/concepts/concepts-fiis.yaml (linha 256): Item missing body/definition content. — `- name: "Macroindicadores"`. Sugestão: Adicionar description/definition/usage ou notas úteis.

## Saída do script

```text
validate_concepts_schema.py summary:
Gate 1: OK
Gate 2: FAIL
Gate 3: FAIL
Issues: 17
```
