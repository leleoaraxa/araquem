## Descrição
Histórico mensal de dividendos por cota, preço de referência e dividend yield (DY) de cada FII.
Cada linha representa um mês de referência (`ref_month`) para um determinado `ticker`, com a soma
dos dividendos pagos no período, o preço de referência da cota e o DY mensal calculado
(`dividends_sum / price_ref`).

## Exemplos de perguntas
- "qual foi o DY mensal do HGLG11 em 2024-05?"
- "como está a evolução do DY do MXRF11 nos últimos 12 meses?"
- "quais FIIs tiveram maior DY médio nos últimos 6 meses?"
- "mostre o histórico de dividendos e DY do KNRI11."
- "liste os FIIs com DY consistente nos últimos 24 meses."

## Respostas usando templates
### table_basic
Tabela em Markdown com uma linha por combinação `{ticker, ref_month}`, contendo:

- **Ticker** (`ticker`)
- **Mês ref.** (`ref_month|date_br`)
- **Dividendos (R$)** (`dividends_sum|currency_br`)
- **Preço ref. (R$)** (`price_ref|currency_br`, ou `"-"` se nulo)
- **DY mensal** (`dy_monthly|percentage_br`, ou `"-"` se nulo)

A tabela é renderizada a partir do arquivo `responses/table.md.j2`.

### FALLBACK_row
Sem histórico de dividend yield para exibir para {ticker} no período informado.
