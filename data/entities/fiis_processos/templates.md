## Descrição
Processos judiciais relevantes para cada FII, com número, fase e valores envolvidos.

## Exemplos de perguntas
- "o VISC11 tem processos em andamento?"
- "qual o risco de perda do HGLG11 em ações judiciais?"
- "há causas relevantes envolvendo MXRF11?"

## Respostas usando templates
### list_basic
{ticker}: proc {process_number} — {judgment}/{instance} — início {initiation_date|date_br} — risco {loss_risk_pct|percent_br} — causa {cause_amt|currency_br} — fatos: {main_facts}.

### FALLBACK_row
Dados de processos do {ticker} não disponíveis no momento.
