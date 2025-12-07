# Entidade `fiis_financials_risk`

## 1. Visão geral

`fiis_financials_risk` concentra indicadores de risco e retorno ajustado dos FIIs (volatilidade, Sharpe, Treynor, alfa de Jensen, beta, Sortino, max drawdown, R²), em base D-1 por fundo.

Perguntas típicas:
- “Qual o Sharpe do HGLG11?”
- “Beta do XPLG11 em relação ao IFIX.”
- “Max drawdown do MXRF11.”
- “Quais FIIs estão mais voláteis?”

## 2. Origem dos dados e contrato

- **View/Tabela base**: `fiis_financials_risk`.
- **Chave lógica**: `ticker`.
- **Granularidade temporal**: indicadores consolidados D-1.

Campos principais (do contrato `fiis_financials_risk.schema.yaml`):
- `ticker` — código do FII.
- Indicadores: `volatility_ratio`, `sharpe_ratio`, `treynor_ratio`, `jensen_alpha`, `beta_index`, `sortino_ratio`, `max_drawdown`, `r_squared`.
- Metadados: `created_at`, `updated_at`.

## 3. Identificadores

- **ticker**: obrigatório; visão suporta múltiplos tickers.

## 4. Grupos de colunas

- **Risco/Retorno**: `volatility_ratio`, `sharpe_ratio`, `treynor_ratio`, `sortino_ratio`.
- **Sensibilidade**: `beta_index`, `r_squared`.
- **Drawdown**: `max_drawdown`, `jensen_alpha` (alfa de Jensen).
- **Metadados**: `created_at`, `updated_at`.

## 5. Exemplos de perguntas que devem cair em `fiis_financials_risk`

- “Sharpe do HGLG11.”
- “Beta do XPLG11 em relação ao IFIX.”
- “Max drawdown do MXRF11.”
- “Qual FII tem maior volatilidade?”
- “Coeficiente de determinação do CPTS11.”

## 6. Observações

- Indicadores são calculados conforme contrato; valores ausentes podem aparecer para fundos sem histórico suficiente.
- Perguntas de preço ou dividendos devem ir para entidades específicas de preços/dividendos.
