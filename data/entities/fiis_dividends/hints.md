O que é:
- Histórico de dividendos distribuídos por FII, com datas de pagamento e data
  com. Inclui valores por cota, sem métricas derivadas embutidas.

Principais colunas:
- ticker: identificador do fundo.
- payment_date e traded_until_date: determinam quando ocorre o pagamento e o
  último pregão com direito ao provento.
- dividend_amt: valor por cota em reais.
- created_at/updated_at: rastreabilidade do carregamento.

Como o Araquem usa:
- Responder perguntas sobre histórico de proventos e sazonalidade de pagamentos.
- Calcular médias ou somatórios em janelas padrão via agregações (ex.: 3, 6 ou
  12 meses) quando solicitado pelo usuário.
- Apoiar comparações entre fundos ("quem pagou mais em 12m?") e análises de
  estabilidade de renda.

Exemplos adicionais:
- "Dividendos que o KNRI11 pagou em janeiro de 2025"
- "Data de pagamento do provento do HGLG11"
