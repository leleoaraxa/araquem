O que é:
- View com dados cadastrais oficiais dos FIIs (ticker, CNPJ, nomes de pregão e
  exibição, setor, tipo do fundo, gestor, administrador e informações de IPO).
- Base usada para identificar o fundo correto antes de consultar preços,
  dividendos ou indicadores.

Principais colunas:
- ticker: código negociado na B3.
- fii_cnpj: identificação legal do fundo.
- display_name e b3_name: nomes de exibição e de pregão.
- classification, sector, sub_sector: categorização oficial do fundo.
- management_type e target_market: tipo de gestão e público-alvo; is_exclusive
  indica fundos exclusivos.
- documentos e governança: admin_name/admin_cnpj, custodian_name, isin,
  ipo_date, website_url.
- pesos e escala: presença de campos com pesos em índices (IFIX/IFIL) e
  contagem de cotas/cotistas (shares_count, shareholders_count) para dar
  dimensão do fundo.

Como o Araquem usa:
- Resolver ambiguidades de ticker e validar a identidade do fundo antes de
  buscas numéricas.
- Responder perguntas de identificação ("qual o CNPJ do HGLG11?") ou de
  classificação ("o KNRI11 é tijolo ou papel?").
- Serve como ponto de partida para enriquecer respostas de overview e risco.
