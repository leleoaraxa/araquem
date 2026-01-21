concept_id: carteira.carteira_de_fiis_do_investidor
domain: carteira
section: 
concept_type: concept
name: Carteira de FIIs do investidor
description: Representa o conjunto de posições em fundos imobiliários de um investidor, com quantidades, valores e participantes (corretoras/custodiantes). É uma camada privada, ligada ao CPF/CNPJ do cliente.
aliases: minha carteira; posições em FIIs; wallet de FIIs
details_md: 
source_file: data/concepts/concepts-carteira.yaml
source_path: concepts[0]
version: dev-20260121

concept_id: carteira.concentracao_e_diversificacao
domain: carteira
section: 
concept_type: concept
name: Concentração e diversificação
description: Mede quanto cada FII representa do valor total da carteira e como os investimentos estão distribuídos entre setores, tipos de fundo e estratégias. Ajuda a evitar concentração excessiva em poucos ativos.
aliases: concentração por FII; diversificação da carteira
details_md: 
source_file: data/concepts/concepts-carteira.yaml
source_path: concepts[1]
version: dev-20260121

concept_id: carteira.principios_de_privacidade_e_seguranca_de_dados
domain: carteira
section: 
concept_type: concept
name: Princípios de privacidade e segurança de dados
description: Dados de carteira (cliente, documento, posições, valores) são tratados como informações sensíveis. A SIRIOS utiliza autenticação, controle de escopo e políticas de uso da IA para garantir que consultas sobre carteira só sejam respondidas quando o contexto de usuário autenticado permitir.
aliases: privacidade da carteira; dados pessoais da carteira
details_md: 
source_file: data/concepts/concepts-carteira.yaml
source_path: concepts[4]
version: dev-20260121

concept_id: carteira.projecoes_de_renda_e_objetivos_financeiros
domain: carteira
section: 
concept_type: concept
name: Projeções de renda e objetivos financeiros
description: A partir das posições atuais e de hipóteses de dividendos, é possível projetar cenários de renda futura e tempo estimado para atingir metas financeiras. Essa camada conecta carteira real, simuladores e objetivos do investidor.
aliases: simulação de renda com FIIs; liberdade financeira com FIIs
details_md: 
source_file: data/concepts/concepts-carteira.yaml
source_path: concepts[3]
version: dev-20260121

concept_id: carteira.risco_e_retorno_da_carteira
domain: carteira
section: 
concept_type: concept
name: Risco e retorno da carteira
description: A SIRIOS consolida indicadores de risco e retorno dos FIIs individuais para calcular métricas no nível da carteira: volatilidade, Sharpe, Treynor, drawdown e retorno acumulado. O objetivo é mostrar se, como conjunto, a carteira está eficiente.
aliases: risco da carteira; performance ajustada ao risco da carteira
details_md: 
source_file: data/concepts/concepts-carteira.yaml
source_path: concepts[2]
version: dev-20260121

concept_id: fiis.carteira.corretora
domain: fiis
section: carteira
concept_type: field
name: corretora
description: Participante responsável.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.carteira.concepts[5].corretora
version: dev-20260121

concept_id: fiis.carteira.data_posicao
domain: fiis
section: carteira
concept_type: field
name: data_posicao
description: Data da posição.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.carteira.concepts[1].data_posicao
version: dev-20260121

concept_id: fiis.carteira.identificador_cliente
domain: fiis
section: carteira
concept_type: field
name: identificador_cliente
description: CPF/CNPJ do investidor.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.carteira.concepts[0].identificador_cliente
version: dev-20260121

concept_id: fiis.carteira.preco_avaliacao
domain: fiis
section: carteira
concept_type: field
name: preco_avaliacao
description: Preço usado no cálculo da carteira.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.carteira.concepts[3].preco_avaliacao
version: dev-20260121

concept_id: fiis.carteira.quantidade
domain: fiis
section: carteira
concept_type: field
name: quantidade
description: Quantidade em custódia e disponível.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.carteira.concepts[2].quantidade
version: dev-20260121

concept_id: fiis.carteira.valor_posicao
domain: fiis
section: carteira
concept_type: field
name: valor_posicao
description: Valor total da posição.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.carteira.concepts[4].valor_posicao
version: dev-20260121

concept_id: fiis.dividendos.acumulados
domain: fiis
section: dividendos
concept_type: field
name: acumulados
description: Somatórios de 3, 6 e 12 meses.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.dividendos.concepts[3].acumulados
version: dev-20260121

concept_id: fiis.dividendos.data_com
domain: fiis
section: dividendos
concept_type: field
name: data_com
description: Determina quem tem direito ao dividendo.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.dividendos.concepts[2].data_com
version: dev-20260121

concept_id: fiis.dividendos.data_pagamento
domain: fiis
section: dividendos
concept_type: field
name: data_pagamento
description: Data do recebimento.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.dividendos.concepts[1].data_pagamento
version: dev-20260121

concept_id: fiis.dividendos.dividendo
domain: fiis
section: dividendos
concept_type: field
name: dividendo
description: Valor distribuído por cota.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.dividendos.concepts[0].dividendo
version: dev-20260121

concept_id: fiis.dividendos.dy
domain: fiis
section: dividendos
concept_type: field
name: dy
description: Dividend Yield: dividendo anualizado sobre preço.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.dividendos.concepts[4].dy
version: dev-20260121

concept_id: fiis.financials_snapshot.alavancagem
domain: fiis
section: financials_snapshot
concept_type: field
name: alavancagem
description: Indicadores de endividamento.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.financials_snapshot.concepts.estrutura_financeira[2].alavancagem
version: dev-20260121

concept_id: fiis.financials_snapshot.caixa
domain: fiis
section: financials_snapshot
concept_type: field
name: caixa
description: Disponibilidades do fundo.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.financials_snapshot.concepts.estrutura_financeira[0].caixa
version: dev-20260121

concept_id: fiis.financials_snapshot.cap_rate
domain: fiis
section: financials_snapshot
concept_type: field
name: cap_rate
description: Renda anual sobre valor da cota.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.financials_snapshot.concepts.valuation[4].cap_rate
version: dev-20260121

concept_id: fiis.financials_snapshot.crescimento_dividendos
domain: fiis
section: financials_snapshot
concept_type: field
name: crescimento_dividendos
description: Crescimento dos dividendos em 12/24/36 meses.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.financials_snapshot.concepts.crescimento[0].crescimento_dividendos
version: dev-20260121

concept_id: fiis.financials_snapshot.crescimento_receita
domain: fiis
section: financials_snapshot
concept_type: field
name: crescimento_receita
description: Crescimento de receita ou patrimônio.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.financials_snapshot.concepts.crescimento[1].crescimento_receita
version: dev-20260121

concept_id: fiis.financials_snapshot.dy
domain: fiis
section: financials_snapshot
concept_type: field
name: dy
description: Dividend Yield mensal e anual.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.financials_snapshot.concepts.renda[0].dy
version: dev-20260121

concept_id: fiis.financials_snapshot.enterprise_value
domain: fiis
section: financials_snapshot
concept_type: field
name: enterprise_value
description: Valor econômico considerando dívidas.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.financials_snapshot.concepts.valuation[1].enterprise_value
version: dev-20260121

concept_id: fiis.financials_snapshot.market_cap
domain: fiis
section: financials_snapshot
concept_type: field
name: market_cap
description: Valor de mercado.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.financials_snapshot.concepts.valuation[0].market_cap
version: dev-20260121

concept_id: fiis.financials_snapshot.passivos
domain: fiis
section: financials_snapshot
concept_type: field
name: passivos
description: Dívidas e obrigações.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.financials_snapshot.concepts.estrutura_financeira[1].passivos
version: dev-20260121

concept_id: fiis.financials_snapshot.payout
domain: fiis
section: financials_snapshot
concept_type: field
name: payout
description: Percentual de lucro distribuído.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.financials_snapshot.concepts.renda[2].payout
version: dev-20260121

concept_id: fiis.financials_snapshot.pvp
domain: fiis
section: financials_snapshot
concept_type: field
name: pvp
description: Preço dividido pelo valor patrimonial.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.financials_snapshot.concepts.valuation[3].pvp
version: dev-20260121

concept_id: fiis.financials_snapshot.reservas
domain: fiis
section: financials_snapshot
concept_type: field
name: reservas
description: Reservas de dividendos.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.financials_snapshot.concepts.estrutura_financeira[3].reservas
version: dev-20260121

concept_id: fiis.financials_snapshot.soma_12m
domain: fiis
section: financials_snapshot
concept_type: field
name: soma_12m
description: Total de proventos em 12 meses.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.financials_snapshot.concepts.renda[1].soma_12m
version: dev-20260121

concept_id: fiis.financials_snapshot.vpa
domain: fiis
section: financials_snapshot
concept_type: field
name: vpa
description: Valor patrimonial por cota.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.financials_snapshot.concepts.valuation[2].vpa
version: dev-20260121

concept_id: fiis.identidade_classificacao.cnpj
domain: fiis
section: identidade_classificacao
concept_type: field
name: cnpj
description: Registro legal do FII e do administrador.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.identidade_classificacao.concepts[1].cnpj
version: dev-20260121

concept_id: fiis.identidade_classificacao.gestao
domain: fiis
section: identidade_classificacao
concept_type: field
name: gestao
description: Gestão ativa ou passiva.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.identidade_classificacao.concepts[4].gestao
version: dev-20260121

concept_id: fiis.identidade_classificacao.governanca
domain: fiis
section: identidade_classificacao
concept_type: field
name: governanca
description: Administrador, gestor, custodiante e site oficial.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.identidade_classificacao.concepts[8].governanca
version: dev-20260121

concept_id: fiis.identidade_classificacao.ipo
domain: fiis
section: identidade_classificacao
concept_type: field
name: ipo
description: Data de início das negociações.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.identidade_classificacao.concepts[7].ipo
version: dev-20260121

concept_id: fiis.identidade_classificacao.isin
domain: fiis
section: identidade_classificacao
concept_type: field
name: isin
description: Código internacional de negociação.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.identidade_classificacao.concepts[6].isin
version: dev-20260121

concept_id: fiis.identidade_classificacao.nomes
domain: fiis
section: identidade_classificacao
concept_type: field
name: nomes
description: Nome de pregão e nome de exibição usados na B3.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.identidade_classificacao.concepts[2].nomes
version: dev-20260121

concept_id: fiis.identidade_classificacao.participacao_indices
domain: fiis
section: identidade_classificacao
concept_type: field
name: participacao_indices
description: Participação e pesos no IFIX/IFIL.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.identidade_classificacao.concepts[9].participacao_indices
version: dev-20260121

concept_id: fiis.identidade_classificacao.publico_alvo
domain: fiis
section: identidade_classificacao
concept_type: field
name: publico_alvo
description: Investidores em geral, qualificados etc.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.identidade_classificacao.concepts[5].publico_alvo
version: dev-20260121

concept_id: fiis.identidade_classificacao.setor_tipo
domain: fiis
section: identidade_classificacao
concept_type: field
name: setor_tipo
description: Classificação por setor, subsetor e tipo (tijolo, papel, híbrido, desenvolvimento).
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.identidade_classificacao.concepts[3].setor_tipo
version: dev-20260121

concept_id: fiis.identidade_classificacao.ticker
domain: fiis
section: identidade_classificacao
concept_type: field
name: ticker
description: Código oficial do fundo, ex.: HGLG11.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.identidade_classificacao.concepts[0].ticker
version: dev-20260121

concept_id: fiis.imoveis.area_total
domain: fiis
section: imoveis
concept_type: field
name: area_total
description: Área total ocupada.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.imoveis.concepts[3].area_total
version: dev-20260121

concept_id: fiis.imoveis.classe
domain: fiis
section: imoveis
concept_type: field
name: classe
description: Tipo (logístico, corporativo, shopping etc.).
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.imoveis.concepts[1].classe
version: dev-20260121

concept_id: fiis.imoveis.inadimplencia
domain: fiis
section: imoveis
concept_type: field
name: inadimplencia
description: Atrasos no pagamento.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.imoveis.concepts[6].inadimplencia
version: dev-20260121

concept_id: fiis.imoveis.localizacao
domain: fiis
section: imoveis
concept_type: field
name: localizacao
description: Cidade e estado.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.imoveis.concepts[2].localizacao
version: dev-20260121

concept_id: fiis.imoveis.nome_ativo
domain: fiis
section: imoveis
concept_type: field
name: nome_ativo
description: Nome do imóvel/ativo.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.imoveis.concepts[0].nome_ativo
version: dev-20260121

concept_id: fiis.imoveis.status
domain: fiis
section: imoveis
concept_type: field
name: status
description: Ativo, Inativo, etc.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.imoveis.concepts[7].status
version: dev-20260121

concept_id: fiis.imoveis.unidades
domain: fiis
section: imoveis
concept_type: field
name: unidades
description: Número de unidades.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.imoveis.concepts[4].unidades
version: dev-20260121

concept_id: fiis.imoveis.vacancia
domain: fiis
section: imoveis
concept_type: field
name: vacancia
description: Vacância física e financeira.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.imoveis.concepts[5].vacancia
version: dev-20260121

concept_id: fiis.macro.cdi
domain: fiis
section: macro
concept_type: field
name: cdi
description: Taxa DI.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.macro.concepts.macroindicadores[0].cdi
version: dev-20260121

concept_id: fiis.macro.dolar
domain: fiis
section: macro
concept_type: field
name: dolar
description: Compra, venda e variação.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.macro.concepts.moedas[0].dolar
version: dev-20260121

concept_id: fiis.macro.euro
domain: fiis
section: macro
concept_type: field
name: euro
description: Compra, venda e variação.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.macro.concepts.moedas[1].euro
version: dev-20260121

concept_id: fiis.macro.ibov
domain: fiis
section: macro
concept_type: field
name: ibov
description: Pontos e variação do Ibovespa.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.macro.concepts.indices_b3[0].ibov
version: dev-20260121

concept_id: fiis.macro.ifil
domain: fiis
section: macro
concept_type: field
name: ifil
description: Pontos e variação do IFIL.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.macro.concepts.indices_b3[2].ifil
version: dev-20260121

concept_id: fiis.macro.ifix
domain: fiis
section: macro
concept_type: field
name: ifix
description: Pontos e variação do IFIX.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.macro.concepts.indices_b3[1].ifix
version: dev-20260121

concept_id: fiis.macro.igpm
domain: fiis
section: macro
concept_type: field
name: igpm
description: Inflação medida pelo IGPM.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.macro.concepts.macroindicadores[3].igpm
version: dev-20260121

concept_id: fiis.macro.inpc
domain: fiis
section: macro
concept_type: field
name: inpc
description: Inflação medida pelo INPC.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.macro.concepts.macroindicadores[4].inpc
version: dev-20260121

concept_id: fiis.macro.ipca
domain: fiis
section: macro
concept_type: field
name: ipca
description: Inflação medida pelo IPCA.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.macro.concepts.macroindicadores[2].ipca
version: dev-20260121

concept_id: fiis.macro.selic
domain: fiis
section: macro
concept_type: field
name: selic
description: Taxa básica de juros.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.macro.concepts.macroindicadores[1].selic
version: dev-20260121

concept_id: fiis.noticias.data_publicacao
domain: fiis
section: noticias
concept_type: field
name: data_publicacao
description: Data da notícia.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.noticias.concepts[4].data_publicacao
version: dev-20260121

concept_id: fiis.noticias.fonte
domain: fiis
section: noticias
concept_type: field
name: fonte
description: Origem da notícia.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.noticias.concepts[0].fonte
version: dev-20260121

concept_id: fiis.noticias.resumo
domain: fiis
section: noticias
concept_type: field
name: resumo
description: Descrição curta do conteúdo.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.noticias.concepts[2].resumo
version: dev-20260121

concept_id: fiis.noticias.tags
domain: fiis
section: noticias
concept_type: field
name: tags
description: Classificação do tema.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.noticias.concepts[1].tags
version: dev-20260121

concept_id: fiis.noticias.tickers_mencionados
domain: fiis
section: noticias
concept_type: field
name: tickers_mencionados
description: FIIs impactados.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.noticias.concepts[3].tickers_mencionados
version: dev-20260121

concept_id: fiis.precos.ohlc
domain: fiis
section: precos
concept_type: field
name: ohlc
description: Abertura, máxima e mínima do dia.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.precos.concepts[1].ohlc
version: dev-20260121

concept_id: fiis.precos.preco_fechamento
domain: fiis
section: precos
concept_type: field
name: preco_fechamento
description: Preço de fechamento ajustado da cota.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.precos.concepts[0].preco_fechamento
version: dev-20260121

concept_id: fiis.precos.serie_historica
domain: fiis
section: precos
concept_type: field
name: serie_historica
description: Evolução da cota ao longo do tempo.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.precos.concepts[3].serie_historica
version: dev-20260121

concept_id: fiis.precos.variacao
domain: fiis
section: precos
concept_type: field
name: variacao
description: Variação diária em percentual e valor.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.precos.concepts[2].variacao
version: dev-20260121

concept_id: fiis.processos.fatos_principais
domain: fiis
section: processos
concept_type: field
name: fatos_principais
description: Resumo objetivo do caso.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.processos.concepts[5].fatos_principais
version: dev-20260121

concept_id: fiis.processos.impacto_potencial
domain: fiis
section: processos
concept_type: field
name: impacto_potencial
description: Possível efeito no fundo.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.processos.concepts[6].impacto_potencial
version: dev-20260121

concept_id: fiis.processos.instancia
domain: fiis
section: processos
concept_type: field
name: instancia
description: Grau do processo.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.processos.concepts[1].instancia
version: dev-20260121

concept_id: fiis.processos.julgamento
domain: fiis
section: processos
concept_type: field
name: julgamento
description: Fase atual.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.processos.concepts[2].julgamento
version: dev-20260121

concept_id: fiis.processos.numero_processo
domain: fiis
section: processos
concept_type: field
name: numero_processo
description: Identificador judicial.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.processos.concepts[0].numero_processo
version: dev-20260121

concept_id: fiis.processos.risco_perda
domain: fiis
section: processos
concept_type: field
name: risco_perda
description: Classificação do risco.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.processos.concepts[4].risco_perda
version: dev-20260121

concept_id: fiis.processos.valor_causa
domain: fiis
section: processos
concept_type: field
name: valor_causa
description: Montante envolvido.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.processos.concepts[3].valor_causa
version: dev-20260121

concept_id: fiis.rankings.movimentos
domain: fiis
section: rankings
concept_type: field
name: movimentos
description: Subidas e quedas na posição do FII ao longo do tempo.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.rankings.concepts[1].movimentos
version: dev-20260121

concept_id: fiis.rankings.posicao
domain: fiis
section: rankings
concept_type: field
name: posicao
description: Posição atual do FII em diferentes rankings (usuários, SIRIOS, IFIX, IFIL).
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.rankings.concepts[0].posicao
version: dev-20260121

concept_id: fiis.rankings.rankings_ifix_ifil
domain: fiis
section: rankings
concept_type: field
name: rankings_ifix_ifil
description: Posição do FII nos índices IFIX e IFIL, inclusive entrada e saída em rebalanceamentos.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.rankings.concepts[2].rankings_ifix_ifil
version: dev-20260121

concept_id: fiis.revenue_schedule.igpm
domain: fiis
section: revenue_schedule
concept_type: field
name: igpm
description: Receitas indexadas ao IGPM.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.revenue_schedule.concepts.indexadores[1].igpm
version: dev-20260121

concept_id: fiis.revenue_schedule.incc
domain: fiis
section: revenue_schedule
concept_type: field
name: incc
description: Receitas indexadas ao INCC.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.revenue_schedule.concepts.indexadores[3].incc
version: dev-20260121

concept_id: fiis.revenue_schedule.inpc
domain: fiis
section: revenue_schedule
concept_type: field
name: inpc
description: Receitas indexadas ao INPC.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.revenue_schedule.concepts.indexadores[2].inpc
version: dev-20260121

concept_id: fiis.revenue_schedule.ipca
domain: fiis
section: revenue_schedule
concept_type: field
name: ipca
description: Receitas indexadas ao IPCA.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.revenue_schedule.concepts.indexadores[0].ipca
version: dev-20260121

concept_id: fiis.revenue_schedule.janelas_padrao
domain: fiis
section: revenue_schedule
concept_type: field
name: janelas_padrao
description: Faixas apuradas: 0–3m, 3–6m, 6–9m, 9–12m, 12–15m, 15–18m, 18–21m, 21–24m, 24–27m, 27–30m, 30–33m, 33–36m, acima de 36m e indeterminado.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.revenue_schedule.concepts.janelas_padrao[0]
version: dev-20260121

concept_id: fiis.revenue_schedule.revenue_due_0_3m_pct
domain: fiis
section: revenue_schedule
concept_type: field
name: revenue_due_0_3m_pct
description: Receitas com vencimento em 0–3 meses.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.revenue_schedule.concepts.buckets[0].revenue_due_0_3m_pct
version: dev-20260121

concept_id: fiis.revenue_schedule.revenue_due_12_15m_pct
domain: fiis
section: revenue_schedule
concept_type: field
name: revenue_due_12_15m_pct
description: Receitas com vencimento em 12–15 meses.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.revenue_schedule.concepts.buckets[4].revenue_due_12_15m_pct
version: dev-20260121

concept_id: fiis.revenue_schedule.revenue_due_15_18m_pct
domain: fiis
section: revenue_schedule
concept_type: field
name: revenue_due_15_18m_pct
description: Receitas com vencimento em 15–18 meses.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.revenue_schedule.concepts.buckets[5].revenue_due_15_18m_pct
version: dev-20260121

concept_id: fiis.revenue_schedule.revenue_due_18_21m_pct
domain: fiis
section: revenue_schedule
concept_type: field
name: revenue_due_18_21m_pct
description: Receitas com vencimento em 18–21 meses.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.revenue_schedule.concepts.buckets[6].revenue_due_18_21m_pct
version: dev-20260121

concept_id: fiis.revenue_schedule.revenue_due_21_24m_pct
domain: fiis
section: revenue_schedule
concept_type: field
name: revenue_due_21_24m_pct
description: Receitas com vencimento em 21–24 meses.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.revenue_schedule.concepts.buckets[7].revenue_due_21_24m_pct
version: dev-20260121

concept_id: fiis.revenue_schedule.revenue_due_24_27m_pct
domain: fiis
section: revenue_schedule
concept_type: field
name: revenue_due_24_27m_pct
description: Receitas com vencimento em 24–27 meses.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.revenue_schedule.concepts.buckets[8].revenue_due_24_27m_pct
version: dev-20260121

concept_id: fiis.revenue_schedule.revenue_due_27_30m_pct
domain: fiis
section: revenue_schedule
concept_type: field
name: revenue_due_27_30m_pct
description: Receitas com vencimento em 27–30 meses.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.revenue_schedule.concepts.buckets[9].revenue_due_27_30m_pct
version: dev-20260121

concept_id: fiis.revenue_schedule.revenue_due_30_33m_pct
domain: fiis
section: revenue_schedule
concept_type: field
name: revenue_due_30_33m_pct
description: Receitas com vencimento em 30–33 meses.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.revenue_schedule.concepts.buckets[10].revenue_due_30_33m_pct
version: dev-20260121

concept_id: fiis.revenue_schedule.revenue_due_33_36m_pct
domain: fiis
section: revenue_schedule
concept_type: field
name: revenue_due_33_36m_pct
description: Receitas com vencimento em 33–36 meses.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.revenue_schedule.concepts.buckets[11].revenue_due_33_36m_pct
version: dev-20260121

concept_id: fiis.revenue_schedule.revenue_due_3_6m_pct
domain: fiis
section: revenue_schedule
concept_type: field
name: revenue_due_3_6m_pct
description: Receitas com vencimento em 3–6 meses.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.revenue_schedule.concepts.buckets[1].revenue_due_3_6m_pct
version: dev-20260121

concept_id: fiis.revenue_schedule.revenue_due_6_9m_pct
domain: fiis
section: revenue_schedule
concept_type: field
name: revenue_due_6_9m_pct
description: Receitas com vencimento em 6–9 meses.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.revenue_schedule.concepts.buckets[2].revenue_due_6_9m_pct
version: dev-20260121

concept_id: fiis.revenue_schedule.revenue_due_9_12m_pct
domain: fiis
section: revenue_schedule
concept_type: field
name: revenue_due_9_12m_pct
description: Receitas com vencimento em 9–12 meses.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.revenue_schedule.concepts.buckets[3].revenue_due_9_12m_pct
version: dev-20260121

concept_id: fiis.revenue_schedule.revenue_due_over_36m_pct
domain: fiis
section: revenue_schedule
concept_type: field
name: revenue_due_over_36m_pct
description: Receitas com vencimento acima de 36 meses.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.revenue_schedule.concepts.buckets[12].revenue_due_over_36m_pct
version: dev-20260121

concept_id: fiis.revenue_schedule.revenue_due_undetermined_pct
domain: fiis
section: revenue_schedule
concept_type: field
name: revenue_due_undetermined_pct
description: Receitas com vencimento indeterminado.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.revenue_schedule.concepts.buckets[13].revenue_due_undetermined_pct
version: dev-20260121

concept_id: fiis.risco.beta
domain: fiis
section: risco
concept_type: field
name: beta
description: Sensibilidade em relação ao IFIX.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.risco.concepts[5].beta
version: dev-20260121

concept_id: fiis.risco.jensen_alpha
domain: fiis
section: risco
concept_type: field
name: jensen_alpha
description: Retorno acima do esperado pelo CAPM.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.risco.concepts[4].jensen_alpha
version: dev-20260121

concept_id: fiis.risco.max_drawdown
domain: fiis
section: risco
concept_type: field
name: max_drawdown
description: Maior queda acumulada.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.risco.concepts[7].max_drawdown
version: dev-20260121

concept_id: fiis.risco.r2
domain: fiis
section: risco
concept_type: field
name: r2
description: Grau de explicação pelo índice de referência.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.risco.concepts[6].r2
version: dev-20260121

concept_id: fiis.risco.sharpe
domain: fiis
section: risco
concept_type: field
name: sharpe
description: Retorno acima do CDI dividido pela volatilidade.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.risco.concepts[1].sharpe
version: dev-20260121

concept_id: fiis.risco.sortino
domain: fiis
section: risco
concept_type: field
name: sortino
description: Sharpe que penaliza apenas quedas.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.risco.concepts[2].sortino
version: dev-20260121

concept_id: fiis.risco.treynor
domain: fiis
section: risco
concept_type: field
name: treynor
description: Retorno excedente dividido pelo beta.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.risco.concepts[3].treynor
version: dev-20260121

concept_id: fiis.risco.volatilidade
domain: fiis
section: risco
concept_type: field
name: volatilidade
description: Oscilação dos preços no tempo.
aliases: 
details_md: 
source_file: data/concepts/concepts-fiis.yaml
source_path: sections.risco.concepts[0].volatilidade
version: dev-20260121

concept_id: macro.contexto_macro_e_tomada_de_decisao_em_fiis
domain: macro
section: 
concept_type: concept
name: Contexto macro e tomada de decisão em FIIs
description: O contexto macroeconômico influencia diretamente FIIs por meio de taxa de juros, inflação, atividade econômica e câmbio. Na SIRIOS, o papel da camada macro é dar referência, não fazer previsão: mostrar se um FII ou carteira está entregando retorno compatível com CDI, SELIC e inflação.
aliases: cenário macro; macro e FIIs
details_md: 
source_file: data/concepts/concepts-macro.yaml
source_path: concepts[4]
version: dev-20260121

concept_id: macro.inflacao_e_indexadores
domain: macro
section: 
concept_type: concept
name: Inflação e indexadores
description: Índices de inflação como IPCA, IGPM, INPC e IPCA-15 impactam diretamente contratos de aluguel, recebíveis imobiliários e indexação de receitas dos FIIs. Na SIRIOS, esses indicadores são usados para analisar a proteção do fluxo de caixa contra a inflação e a exposição de cada fundo a diferentes indexadores.
aliases: IPCA; IGPM; INPC; índices de inflação
details_md: 
source_file: data/concepts/concepts-macro.yaml
source_path: concepts[2]
version: dev-20260121

concept_id: macro.moedas_e_exposicao_cambial
domain: macro
section: 
concept_type: concept
name: Moedas e exposição cambial
description: As cotações de dólar e euro em relação ao real importam para fundos que possuem ativos dolarizados, contratos atrelados ao câmbio ou exposição indireta a moedas estrangeiras. A SIRIOS utiliza essas séries para dar contexto a movimentos de preço e risco em fundos sensíveis ao câmbio.
aliases: dólar; euro; câmbio
details_md: 
source_file: data/concepts/concepts-macro.yaml
source_path: concepts[3]
version: dev-20260121

concept_id: macro.taxas_de_juros_e_indicadores_de_renda_fixa
domain: macro
section: 
concept_type: concept
name: Taxas de juros e indicadores de renda fixa
description: CDI e SELIC são utilizados como proxies de ativo livre de risco e linha de base para comparar o retorno de FIIs e carteiras. Também servem como referência para cálculo de Sharpe, Treynor e outras métricas de risco.
aliases: CDI; SELIC; taxa livre de risco
details_md: 
source_file: data/concepts/concepts-macro.yaml
source_path: concepts[1]
version: dev-20260121

concept_id: macro.indices_de_mercado_da_b3
domain: macro
section: 
concept_type: concept
name: Índices de mercado da B3
description: Índices como IBOV, IFIX e IFIL representam carteiras teóricas de ativos negociados na B3 e são usados como referência para avaliar o desempenho de FIIs e carteiras. No contexto da SIRIOS, esses índices ajudam a comparar retorno e risco dos fundos em relação ao mercado.
aliases: IBOV; IFIX; IFIL; índices de referência
details_md: 
source_file: data/concepts/concepts-macro.yaml
source_path: concepts[0]
version: dev-20260121

concept_id: macro.methodology
domain: macro
section: 
concept_type: methodology
name: methodology
description: 
aliases: 
details_md: Explicar como a SIRIOS acompanha indicadores macroeconômicos usados no contexto de FIIs: quais séries entram no sistema, como são coletadas e que limitações existem. O objetivo é oferecer contexto textual para RAG, sem prometer recomendações ou retornos financeiros.
source_file: data/concepts/concepts-macro-methodology.yaml
source_path: root
version: dev-20260121

concept_id: risk.alfa_de_jensen
domain: risk
section: 
concept_type: concept
name: Alfa de Jensen
description: Mostra quanto o fundo entregou acima (ou abaixo) do retorno esperado pelo modelo de precificação de ativos (CAPM), dado o seu beta. Indica se o gestor gerou valor além do que o risco de mercado explicaria.
aliases: alpha de Jensen; Jensen alpha
details_md: 
source_file: data/concepts/concepts-risk.yaml
source_path: concepts[4]
version: dev-20260121

concept_id: risk.beta_e_r2
domain: risk
section: 
concept_type: concept
name: Beta e R²
description: Beta mede a sensibilidade do fundo em relação a um índice de referência (ex.: IFIX). R² indica o quanto do comportamento do fundo é explicado por esse índice. Juntos, mostram o quanto o FII acompanha o mercado.
aliases: beta em relação ao índice; coeficiente de determinação
details_md: 
source_file: data/concepts/concepts-risk.yaml
source_path: concepts[7]
version: dev-20260121

concept_id: risk.fronteira_eficiente_e_carteiras
domain: risk
section: 
concept_type: concept
name: Fronteira eficiente e carteiras
description: A SIRIOS utiliza as métricas de risco e retorno para posicionar FIIs e carteiras em um plano risco versus retorno, aproximando-se do conceito de fronteira eficiente de Markowitz. A ideia é mostrar combinações de ativos que entregam o melhor retorno possível para cada nível de risco.
aliases: fronteira de Markowitz; eficiência risco-retorno
details_md: 
source_file: data/concepts/concepts-risk.yaml
source_path: concepts[8]
version: dev-20260121

concept_id: risk.maximo_drawdown_mdd
domain: risk
section: 
concept_type: concept
name: Máximo Drawdown (MDD)
description: Representa a maior queda acumulada entre um topo e um fundo em determinado período. Mostra o pior cenário de perda para quem entrou no topo e saiu no pior momento da janela.
aliases: max drawdown; queda máxima acumulada
details_md: 
source_file: data/concepts/concepts-risk.yaml
source_path: concepts[6]
version: dev-20260121

concept_id: risk.sharpe_ratio
domain: risk
section: 
concept_type: concept
name: Sharpe Ratio
description: Mede o retorno excedente do fundo em relação a um ativo livre de risco (tipicamente o CDI), dividido pela volatilidade. Avalia o quanto de retorno o investidor recebe para cada unidade de risco assumido.
aliases: índice de Sharpe
details_md: 
source_file: data/concepts/concepts-risk.yaml
source_path: concepts[2]
version: dev-20260121

concept_id: risk.sortino_ratio
domain: risk
section: 
concept_type: concept
name: Sortino Ratio
description: Versão do Sharpe que considera apenas a volatilidade negativa (quedas). Penaliza mais os movimentos para baixo do que os para cima.
aliases: índice de Sortino
details_md: 
source_file: data/concepts/concepts-risk.yaml
source_path: concepts[5]
version: dev-20260121

concept_id: risk.treynor_ratio
domain: risk
section: 
concept_type: concept
name: Treynor Ratio
description: Mede o retorno excedente do fundo em relação ao ativo livre de risco, dividido pelo beta. Foca no risco sistemático, isto é, aquele ligado ao mercado como um todo.
aliases: índice de Treynor
details_md: 
source_file: data/concepts/concepts-risk.yaml
source_path: concepts[3]
version: dev-20260121

concept_id: risk.visao_sirios_de_risco_em_fiis
domain: risk
section: 
concept_type: concept
name: Visão SIRIOS de risco em FIIs
description: A SIRIOS enxerga risco como a combinação entre oscilação de preços, retorno ajustado ao risco, comportamento em crises e dependência em relação ao mercado de referência. Os principais insumos são séries históricas de preços, dividendos e benchmarks (IFIX, CDI, outros índices).
aliases: risco em fundos imobiliários; análise quantitativa de risco
details_md: 
source_file: data/concepts/concepts-risk.yaml
source_path: concepts[0]
version: dev-20260121

concept_id: risk.volatilidade_historica
domain: risk
section: 
concept_type: concept
name: Volatilidade histórica
description: Mede o quanto o preço de um FII oscila em torno da sua média em um determinado período. Quanto maior a volatilidade, mais instável é o comportamento da cota no tempo.
aliases: volatilidade; volatility ratio
details_md: 
source_file: data/concepts/concepts-risk.yaml
source_path: concepts[1]
version: dev-20260121

concept_id: risk.methodology
domain: risk
section: 
concept_type: methodology
name: methodology
description: 
aliases: 
details_md: Métricas de risco da SIRIOS são calculadas com séries históricas de preços de FIIs, dividendos e benchmarks (IFIX, CDI/SELIC). O foco é medir risco historicamente observado, sem prometer performance futura. Todos os cálculos usam janelas explícitas (ex.: 12m, 24m) e deixam claro o benchmark utilizado.
source_file: data/concepts/concepts-risk-metrics-methodology.yaml
source_path: root
version: dev-20260121
