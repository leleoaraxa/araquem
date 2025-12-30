## Descrição
Distribuição dos recebíveis do FII por faixas de vencimento e indexadores de correção.

## Exemplos de perguntas
- "quanto do HGLG11 vence em 12 meses?"
- "qual parcela do XPML11 está acima de 36 meses?"
- "qual a exposição do VISC11 a IPCA e IGPM?"

## Respostas usando templates
### list_basic
{ticker}: vencimentos — 0–3m {revenue_due_0_3m_pct|percent_br}, 3–6m {revenue_due_3_6m_pct|percent_br}, 6–9m {revenue_due_6_9m_pct|percent_br}, 9–12m {revenue_due_9_12m_pct|percent_br}, 12–15m {revenue_due_12_15m_pct|percent_br}, 15–18m {revenue_due_15_18m_pct|percent_br}, 18–21m {revenue_due_18_21m_pct|percent_br}, 21–24m {revenue_due_21_24m_pct|percent_br}, 24–27m {revenue_due_24_27m_pct|percent_br}, 27–30m {revenue_due_27_30m_pct|percent_br}, 30–33m {revenue_due_30_33m_pct|percent_br}, 33–36m {revenue_due_33_36m_pct|percent_br}, >36m {revenue_due_over_36m_pct|percent_br}, indeterm. {revenue_due_undetermined_pct|percent_br} | indexadores — IPCA {revenue_ipca_pct|percent_br}, IGPM {revenue_igpm_pct|percent_br}, INPC {revenue_inpc_pct|percent_br}, INCC {revenue_incc_pct|percent_br}

### FALLBACK_row
Não encontrei estrutura de recebíveis para {ticker}.
