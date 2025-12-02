O que é:
- View com dados cadastrais oficiais dos FIIs (ticker, CNPJ, nomes de pregão e
  exibição, setor, tipo do fundo, gestor, administrador e informações de IPO).
- Base usada para identificar o fundo correto antes de consultar preços,
  dividendos ou indicadores.

Principais colunas:
- ticker: código negociado na B3.
- cnpj: identificação legal do fundo e do administrador.
- setor_tipo: classificação por setor, subsetor e tipo (tijolo, papel, híbrido,
  desenvolvimento).
- gestao: se o fundo é de gestão ativa ou passiva.
- governanca: administrador, gestor, custodiante e site oficial.

Como o Araquem usa:
- Resolver ambiguidades de ticker e validar a identidade do fundo antes de
  buscas numéricas.
- Responder perguntas de identificação ("qual o CNPJ do HGLG11?") ou de
  classificação ("o KNRI11 é tijolo ou papel?").
- Serve como ponto de partida para enriquecer respostas de overview e risco.
