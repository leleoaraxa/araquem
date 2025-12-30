# client_fiis_positions — Hints

## O que é
Coletânea de sinais sobre a posição consolidada de FIIs por cliente, útil para contextualizar holdings, variação e composição de carteira sem revelar dados sensíveis.

### Perguntas típicas
- Como está distribuída a carteira de FIIs por setor ou classe de ativo?
- Quais posições aumentaram ou reduziram desde o último período de referência?
- Existe concentração relevante em um único FII ou em poucos emissores?
- Há posições sem liquidez recente ou que mereçam revisão?
- Como as posições se comparam a um benchmark ou carteira alvo?
- Há eventos futuros (ex.: subscrições) que impactem as posições atuais?

### Limites
- Não inferir dados ausentes ou extrapolar datas sem referência.
- Respeitar privacidade: não expor informações pessoais ou identificadores do cliente.
- Não inventar tickers ou códigos de negociação inexistentes.
- Manter o escopo restrito às posições de FIIs e suas características.

### Campos/colunas
- Identificador/ticker do FII e nome do fundo.
- Datas de referência e períodos de apuração das posições.
- Quantidade, preço médio e participação percentual na carteira.
- Indicadores de variação, aporte ou resgate por período.
- Fonte ou sistema de origem dos dados consolidados.
- Observações sobre liquidez, eventos ou restrições relevantes.
