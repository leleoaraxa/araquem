## Descrição
Distribuição dos recebíveis do FII por faixas de vencimento e indexadores de correção.

## Exemplos de perguntas
- "quanto do HGLG11 vence em 12 meses?"
- "qual parcela do XPML11 está acima de 36 meses?"
- "qual a exposição do VISC11 a IPCA e IGPM?"

## Respostas usando templates
### list_basic
{ticker}: vencimentos — 0–3m {revenue_due_0_3m_pct|percent_br}, 9–12m {revenue_due_9_12m_pct|percent_br}, >36m {revenue_due_over_36m_pct|percent_br} | indexadores — IPCA {revenue_ipca_pct|percent_br}, IGPM {revenue_igpm_pct|percent_br}

### FALLBACK_row
Não encontrei estrutura de recebíveis para {ticker}.
