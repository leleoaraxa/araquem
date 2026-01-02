# Guia SIRIOS do Domínio de FIIs – V1

> Este guia explica **como a SIRIOS enxerga e organiza o universo de Fundos
> Imobiliários (FIIs)**.
> Não é um manual de tela, e sim o mapa conceitual que sustenta as análises
> da SIRIOS e as respostas da nossa IA.

---

## 1. Como a SIRIOS enxerga um FII

Fundos de Investimento Imobiliário (FIIs) reúnem capital de vários investidores para
aplicar em ativos ligados ao mercado imobiliário: prédios corporativos, galpões
logísticos, shoppings, recebíveis (CRIs/CRAs), FIIs de fundos, entre outros.

Na SIRIOS, cada FII é identificado por um **ticker** (por exemplo, `HGLG11`, `MXRF11`),
e todo o domínio é construído para responder, de forma objetiva, perguntas como:

- **Quem é esse fundo?** (cadastro, classificação, governança)
- **Quanto ele vale hoje?** (preço, market cap, P/VP)
- **Quanto ele paga de renda?** (dividendos, yield, payout)
- **Quais são os riscos?** (volatilidade, Sharpe, Treynor, processos)
- **O que tem dentro dele?** (imóveis, recebíveis, indexadores)
- **Como isso impacta a minha carteira?** (posições de FIIs do investidor)

Para organizar tudo isso, a SIRIOS separa o domínio em **entidades de dados** e
**intents** (tipos de pergunta que a IA reconhece).

---

## 2. Mapa de dados do universo de FIIs na SIRIOS

Hoje o domínio de FIIs na SIRIOS é dividido em blocos:

1. **Identidade e classificação** – quem é o fundo, CNPJ, administrador, setor, tipo.
2. **Preço e histórico de cotas** – evolução diária da cota e variações.
3. **Dividendos e renda** – histórico de proventos pagos por cota.
4. **Indicadores financeiros e valuation** – DY, P/VP, caixa, passivos, cap rate etc.
5. **Riscos quantitativos** – volatilidade, Sharpe, Treynor, Jensen, Sortino, MDD, beta, R².
6. **Recebíveis e indexadores** – agenda de receitas e exposição a índices de inflação.
7. **Imóveis e portfólio físico** – ativos, localização, vacância, área, status.
8. **Processos judiciais** – ações relevantes e riscos legais.
9. **Notícias e eventos** – matérias recentes ligadas aos FIIs.
10. **Rankings e popularidade** – presença em listas da SIRIOS, usuários, IFIX, IFIL.
11. **Contexto de mercado e macroeconomia** – índices B3, moedas, IPCA, CDI, SELIC etc.
12. **Sua carteira de FIIs** – posições individuais do investidor (camada privada).

Os capítulos seguintes detalham cada bloco, sempre com foco em como isso te ajuda
a tomar decisões melhores.

---

## 3. Identidade do Fundo e Classificação (`fiis_registrations`)

**O que representa**
É a “identidade oficial” do fundo dentro da SIRIOS: tudo que define quem ele é.

**Principais informações:**

- Ticker (ex.: `HGLG11`)
- CNPJ do fundo e do administrador
- Nome de pregão / nome de exibição
- Classificação: setor, subsetor, tipo (tijolo, papel, híbrido, desenvolvimento etc.)
- Tipo de gestão (ativa, passiva) e público-alvo
- ISIN, data de IPO
- Administrador, gestor, custodiante
- Participação em índices (IFIX, IFIL) e respectivos pesos
- Número de cotas e número de cotistas
- Site oficial e dados básicos de governança

**Como isso te ajuda**

- Responder rapidamente *“que fundo é esse?”*
- Comparar perfis (setor, tipo, gestão) entre FIIs.
- Ser o ponto de amarração com todas as outras visões (preço, dividendos, risco etc.).

---

## 4. Preço e Renda: Cotas e Dividendos

### 4.1 Evolução de Preço da Cota (`fiis_precos`)

**O que representa**
Histórico diário de preço das cotas de cada FII.

**Principais dados:**

- Data de negociação
- Preço de fechamento (ajustado)
- Abertura, máxima, mínima
- Variação diária em % e em R$

**Perguntas típicas**

- *“Quanto fechou o HGLG11 ontem?”*
- *“Como se comportou o MXRF11 no último mês?”*

### 4.2 Histórico de Dividendos (`fiis_dividends`)

**O que representa**
Linha do tempo dos proventos pagos por cota.

**Principais dados:**

- Data de pagamento
- Valor do dividendo por cota
- Data-com
- Acúmulos em janelas (3, 6, 12 meses) usados em outros indicadores

**Perguntas típicas**

- *“Qual foi o último dividendo do KNRI11?”*
- *“Quanto o MXRF11 pagou em 12 meses?”*

Combinar **preço** e **dividendos** é a base para métricas como Dividend Yield (DY).

---

## 5. Indicadores Financeiros e Valuation (`fiis_financials_snapshot`)

**O que representa**
Um raio-X D-1 do fundo, com foco em renda, valuation e estrutura financeira.

**Principais grupos de métricas**

- **Renda e dividendos**
  - DY mensal e anual
  - Soma de proventos em 12 meses
  - Último dividendo e data de pagamento
  - Dividend Payout Ratio

- **Valuation**
  - Market Cap
  - Enterprise Value (EV)
  - Patrimônio líquido (PL)
  - Valor patrimonial por cota (VPA)
  - Preço / Valor patrimonial (P/VP)
  - Cap Rate

- **Crescimento**
  - Crescimento de dividendos em 12/24/36 meses
  - Crescimento de receita ou patrimônio em janelas definidas

- **Estrutura de capital**
  - Caixa total
  - Passivos totais
  - Indicadores de alavancagem
  - Reservas de dividendos (quando disponíveis)

**Como isso te ajuda**

- Avaliar a **qualidade financeira** de um FII.
- Comparar valuation entre fundos de um mesmo segmento.
- Responder perguntas como:
  - *“Qual o DY e o P/VP do VISC11?”*
  - *“Esse fundo está muito alavancado?”*

---

## 6. Risco Quantitativo e Fronteira da Eficiência (`fiis_financials_risk`)

### 6.1 Visão SIRIOS de risco em FIIs

Risco, para a SIRIOS, é a combinação entre:

- **Oscilação dos preços** (volatilidade);
- **Retorno por unidade de risco** (Sharpe, Treynor, Sortino);
- **Comportamento em crises** (máximo drawdown);
- **Dependência em relação ao mercado** (beta, R²).

As métricas são calculadas a partir de séries de preços, dividendos e benchmarks
como IFIX e CDI.

### 6.2 Métricas-chave de risco

- **Volatility Ratio** – mostra o quanto o preço oscila em torno da média.
- **Sharpe Ratio** – retorno acima do ativo livre de risco (ex.: CDI) dividido pela
  volatilidade.
- **Treynor Ratio** – retorno excedente dividido pelo beta (risco sistemático).
- **Alfa de Jensen** – quanto o fundo entregou acima do que o CAPM esperaria,
  dado o risco.
- **Beta** – sensibilidade em relação ao índice de referência (ex.: IFIX).
- **Sortino Ratio** – versão do Sharpe que considera apenas volatilidade negativa.
- **Max Drawdown (MDD)** – maior queda acumulada em um período.
- **R²** – quanto do comportamento do fundo é explicado pelo índice de referência.

### 6.3 Fronteira eficiente na prática

A partir desses dados, a SIRIOS consegue:

- Posicionar **FIIs isolados** no plano risco × retorno;
- Calcular **carteiras simuladas** e avaliar eficiência em relação à fronteira;
- Colocar **sua carteira real** no mesmo mapa, para mostrar se ela está mais
  agressiva ou conservadora em comparação a outras combinações possíveis.

O objetivo é dar contexto quantitativo, não prometer retorno.

---

## 7. Recebíveis e Indexadores de Receita (`fiis_financials_revenue_schedule`)

**O que representa**
A agenda de receitas futuras do fundo e como elas estão indexadas.

**Principais informações**

- Percentual da receita contratada que vence em:
  - 0–3 meses, 3–6 meses, …, acima de 36 meses
  - Prazo indeterminado
- Percentual indexado a:
  - IGPM, IPCA, INPC, INCC, entre outros

**Como isso te ajuda**

- Enxergar **concentração de vencimentos** no curto, médio e longo prazo.
- Entender a **sensibilidade da renda** a diferentes índices de inflação.
- Avaliar previsibilidade de fluxo de caixa.

---

## 8. Imóveis e Portfólio Físico (`fiis_real_estate`)

**O que representa**
A lista de ativos físicos do fundo.

**Principais dados**

- Nome do ativo
- Classe (logístico, corporativo, shopping, lajes etc.)
- Endereço / cidade / estado
- Área total
- Número de unidades
- Vacância física e financeira
- Inadimplência
- Status (ocupado, em desenvolvimento, vendido etc.)

**Perguntas típicas**

- *“Quais imóveis estão dentro do HGLG11?”*
- *“Esse fundo está concentrado em qual região?”*
- *“Quantos ativos têm vacância acima de 30%?”*

---

## 9. Notícias e Risco Qualitativo (`fiis_news`, `fiis_processos`)

### 9.1 Notícias de FIIs (`fiis_news`)

**O que representa**
Noticiário D-1 relacionado ao universo de FIIs.

- Fonte (ex.: Valor, InfoMoney)
- Título e resumo
- Tags / categorias
- URL e imagem
- Data de publicação
- Ticker(s) impactados, quando houver

Ajuda a responder:

- *“Quais as últimas notícias sobre o HGLG11?”*
- *“O que saiu hoje sobre IFIX?”*

### 9.2 Processos judiciais (`fiis_processos`)

**O que representa**
Processos relevantes associados ao fundo.

**Principais pontos**

- Número do processo e instância
- Fase de julgamento / andamento
- Data de início
- Valor da causa
- Risco de perda (possível, provável, remoto)
- Fatos principais
- Análise de impacto potencial

Complementa a visão de risco:

- *“Esse FII tem processos relevantes em aberto?”*
- *“Qual o risco de perda e o possível impacto?”*

---

## 10. Rankings e Sinais de Popularidade (`fiis_rankings`)

**O que representa**
Presença do FII em rankings da SIRIOS, dos usuários e de índices como IFIX/IFIL.

**Indicadores principais**

- Quantas vezes o fundo aparece em diferentes listas
- Movimentos líquidos (subindo ou caindo nos rankings)

**Como isso te ajuda**

- Enxergar **popularidade e momentum** de cada FII.
- Apoiar perguntas como:
  - *“Quais são os FIIs mais buscados hoje?”*
  - *“Esse fundo está ganhando ou perdendo espaço?”*

---

## 11. Contexto de Mercado e Macroeconomia

### 11.1 Índices da B3 (`history_b3_indexes`)

Série D-1 com:

- Pontos e variações de **IBOV, IFIX e IFIL**.

Base para:

- Comparar FIIs com os principais índices da B3.
- Calcular betas e indicadores de risco.

### 11.2 Moedas (`history_currency_rates`)

Cotações D-1 de:

- Dólar (compra / venda, variação)
- Euro (compra / venda, variação)

Úteis para fundos com ativos dolarizados ou operações ligadas a câmbio.

### 11.3 Indicadores macroeconômicos (`history_market_indicators`)

Série D-1 de indicadores como:

- CDI, SELIC
- IPCA, IGPM, INPC, IPCA-15
- Outros índices de inflação e taxa de juros

Servem como **linha de base** para:

- Comparar dividend yield de FIIs com CDI/SELIC;
- Avaliar indexação de receitas;
- Explicar movimentos de mercado em narrativas.

---

## 12. Sua Carteira de FIIs (`client_fiis_positions`)

**O que representa**
A visão da SIRIOS sobre **as suas posições em FIIs** – uma camada privada,
ligada ao seu CPF/CNPJ.

**Principais dados**

- Identificador do cliente (CPF/CNPJ ou equivalente)
- Data da posição
- Ticker e nome do FII
- Quantidade em custódia e disponível
- Preço utilizado para avaliação
- Valor da posição e variação no período
- Participante / corretora

**Princípios de privacidade**

- Esses dados são **pessoais e sensíveis**.
- A SIRIOS trabalha com controles de segurança, autenticação e limites de exposição
  definidos pelo produto.
- A IA só usa essa camada dentro do contexto certo (você autenticado).

**Perguntas típicas**

- *“Quantas cotas tenho de MXRF11?”*
- *“Qual é o valor total da minha carteira de FIIs hoje?”*
- *“Quais fundos representam mais de 10% da minha carteira?”*

---

## 13. Como a IA da SIRIOS conversa com esse domínio

De forma simplificada:

1. **Você faz uma pergunta em linguagem natural.**
2. A IA identifica a **intent** (ex.: `fiis_dividends`, `fiis_financials_risk`) e
   a **entidade** mais adequada.
3. O sistema consulta as tabelas e views correspondentes, inferindo:
   - Ticker(s);
   - Janelas de tempo;
   - Agregações compatíveis com a pergunta.
4. Os dados estruturados voltam para a camada de **Narrativa (Narrator)**, que:
   - Transforma números em texto claro, em português;
   - Usa os conceitos deste guia para explicar o que cada métrica significa;
   - Pode acionar RAG (busca em textos) para enriquecer com notícias, documentos
     e glossários quando fizer sentido.

Este guia é a referência para que **produto, dados, IA e experiência do investidor**
falem a mesma língua quando o assunto é FIIs na SIRIOS.
