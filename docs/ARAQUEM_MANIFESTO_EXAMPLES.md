# **ARAQUEM — EXEMPLOS DE COMPORTAMENTO (v1.0)**

### *Casos reais para entender como o Araquem toma decisões*

---

# **1. Perguntas com ticker (dados factuais)**

## **1.1 Preço — fiis_precos**

### Pergunta

> “Qual o preço do HGLG11 hoje?”

### Fluxo do Araquem

* Tokens: `preço`, `HGLG11`
* Planner → `fiis_precos` (score alto)
* Builder gera SQL determinística
* Executor traz valor da view
* Narrator formata texto curto

### Resposta UX (ideal)

> **HGLG11 está sendo negociado a R$ 172,24.**
>
> Última atualização: D-1 (dados B3).

---

## **1.2 Dividendos — fiis_dividends**

### Pergunta

> “Qual foi o último dividendo do MXRF11?”

### Fluxo

* Intent: `fiis_dividends`
* SQL retorna as últimas linhas
* Narrator faz texto claro

### Resposta UX

> **O último dividendo do MXRF11 foi R$ 0,12**, pago em 15/10/2025.

---

## **1.3 Risco — fiis_financials_risk**

### Pergunta

> “O Sharpe do HGLG11 é bom?”

### Fluxo

* Tokens: `Sharpe`
* Entity → `fiis_financials_risk`
* SQL traz métricas
* Narrator explica em linguagem humana

### Resposta UX

> **O Sharpe do HGLG11 está em 0,87**, o que indica um bom equilíbrio entre retorno e volatilidade.
> Para FIIs, valores acima de ~0,5 já são considerados positivos.

---

# **2. Perguntas conceituais (sem dados / sem ticker)**

Essas perguntas **não** geram SQL.
São respondidas via:

* RAG (concepts-*.yaml)
* Narrator (texto)
* Sem números inventados

---

## **2.1 Indicadores de risco**

### Pergunta

> “O que significa Sharpe negativo?”

### Fluxo

* Tokens: `Sharpe`
* Sem ticker
* Planner escolhe conceitos → `concepts-risk`
* Narrator responde

### Resposta UX

> Um **Sharpe negativo** significa que o retorno do ativo ficou **abaixo do CDI**.
> Ou seja: **o risco não compensou**.

---

## **2.2 Inflação e FIIs**

### Pergunta

> “O que significa IPCA alto para os FIIs?”

### Fluxo correto

* Tokens: `IPCA`
* Sem ticker → pergunta macro
* Entidade ideal: `history_market_indicators` + `concepts-macro`
* Sem SQL se não pedir dado
* Narrator explica comportamento geral

### Resposta UX

> Um **IPCA alto tende a pressionar juros**, o que geralmente impacta:
>
> * FIIs de tijolo → podem sofrer com aumento de vacância e custo de capital
> * FIIs de papel → costumam se beneficiar, pois têm indexação ao IPCA
>
> É um cenário misto: depende da classe do fundo.

---

# **3. Perguntas híbridas (conceito + ticker)**

## **3.1 IPCA + receita indexada**

### Pergunta

> “Quanto do XPML11 está indexado ao IPCA?”

### Fluxo

* Tokens: `IPCA`, `XPML11`
* Entity: `fiis_financials_revenue_schedule`
* SQL + conceito
* Narrator explica

### Resposta UX

> **71% das receitas do XPML11 estão indexadas ao IPCA.**
> Isso tende a proteger o fundo em períodos de inflação mais alta.

---

# **4. Perguntas privadas (dados do cliente)**

## **4.1 Evolução dos dividendos**

### Pergunta

> “Minha renda mensal está crescendo?”

### Fluxo

* Entity: `client_fiis_dividends_evolution`
* SQL privada
* Narrator transforma em análise pessoal

### Resposta UX

> Sua renda mensal média dos últimos 12 meses está **6% maior** do que no período anterior.
> O crescimento vem principalmente de MXRF11 e CPTS11.

---

# **5. Ambiguidade resolvível (melhor caminho)**

## **5.1 Exemplo clássico**

### Pergunta

> “Como está o fundo KNRI11?”

Pode ser:

* `fiis_overview`
* `fiis_precos`
* `fiis_dividends`
* `fiis_financials_risk`

### Fluxo correto

* Planner detecta múltiplos intents válidos
* Gap baixo
* Deve acionar **UX de clarificação**:

### Resposta UX

> Você quer saber sobre:
>
> 1. Preço atual
> 2. Dividendos
> 3. Risco
> 4. Overview geral
>
> Qual deles?

---

# **6. Ambiguidade insolúvel (resposta segura)**

## Caso real

### Pergunta

> “Como interpretar uma notícia negativa sobre um FII?”

Nesse caso:

* Sem ticker
* Sem referência clara
* `fiis_noticias` exige ticker → SQL vazia
* RAG retorna conceitos
* Ideal: **não responder com dados falsos**
* Narrator sozinho não resolve sem o FII

### Resposta UX ideal

> Para te ajudar melhor, me diga **qual FII** está relacionado à notícia.

---

# **7. Quando não sei responder**

## Exemplo

> “Quanto o IFIX vai subir mês que vem?”

### Comportamento obrigatório

* Não prever
* Não inventar
* Não chutar

### Resposta UX

> Não faço previsões, mas posso te mostrar **como o IFIX tem se comportado** e quais fatores normalmente influenciam o índice. Quer ver?

---

# **8. Erros de contrato / Sem dados**

## Exemplo real

> “quantos processos o FII XPML11 tem?”

Suponha SQL retorna vazio.

### Resposta UX ideal

> Não encontrei processos judiciais registrados para o XPML11 no momento.
> (Fonte: base consolidada D-1)

---

# **9. Exemplos reais extraídos de data/golden/**

A seguir, alguns exemplos reais usados nos testes golden, que demonstram o comportamento ideal:

| Pergunta                                 | Entidade esperada      |
| ---------------------------------------- | ---------------------- |
| “cnpj do HGLG11”                         | `fiis_registrations`        |
| “dy do MXRF11 em 2024”                   | `fiis_yield_history`   |
| “como está o beta do XPLG11?”            | `fiis_financials_risk` |
| “último dividendo do KNCR11”             | `fiis_dividends`      |
| “quantos imóveis tem o HGLG11?”          | `fiis_real_estate`         |
| “posicao do CPTS11 no ranking da SIRIOS” | `fiis_rankings`        |
| “notícias do HGLG11”                     | `fiis_noticias`        |

---

# **10. Checklist final do comportamento ideal**

* [x] Não inventar nenhuma coluna SQL
* [x] Não inventar ticker
* [x] Não prever tendências
* [x] Não responder entidades privadas sem login
* [x] RAG só para entendimento conceitual
* [x] Narrator não altera números
* [x] Quando ambíguo, perguntar
* [x] Sempre entregar UX clara

---
