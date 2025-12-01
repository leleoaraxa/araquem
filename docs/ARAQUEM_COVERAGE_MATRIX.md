# **👉 ARAQUEM_COVERAGE_MATRIX.md**

**“Mapa completo do que o Araquem sabe responder, como responde, quando responde e o que NÃO deve responder.”**

Esse arquivo vira:

* base dos testes (quality)
* base de revisão do Planner
* base do Narrator
* base de UX
* base de auditoria contínua
* base para roadmap de expansão

E serve também para entender riscos, lacunas, métricas e abrangência do produto.

Ele ficará em:

`docs/ARAQUEM_COVERAGE_MATRIX.md`

Abaixo está a **versão completa e finalizada**, pronta para commit.

---

# 🟦 **ARAQUEM — COVERAGE MATRIX (v1.0)**

## *Mapeamento oficial de cobertura: perguntas → entidades → comportamento → modo Narrator*

---


# **0. Objetivo**

Este documento responde:

* *“O Araquem cobre o quê?”*
* *“Como ele responde cada tipo de pergunta?”*
* *“Quais entidades suportam quais cenários?”*
* *“Onde há gaps?”*
* *“Onde o Narrator deve atuar e onde deve ficar quieto?”*
* *“Como os testes devem validar isso?”*

É uma matriz de governança técnica, de produto e de UX.

---


# **1. Visão Geral das Categorias de Perguntas**

Toda pergunta recebida cai sempre em **uma** das categorias abaixo:

| Categoria                     | Característica               | Exemplos                      | Resposta via           |
| ----------------------------- | ---------------------------- | ----------------------------- | ---------------------- |
| **A. Conceitual**             | Sem ticker, foco em conceito | “O que é Sharpe?”             | concepts + Narrator    |
| **B. Factual com ticker**     | Ticker explícito             | “DY do HGLG11”                | entidade + Narrator    |
| **C. Follow-up contextual**   | Sem ticker, mas com contexto | “E o risco?”                  | context + entidade     |
| **D. Privada (carteira)**     | Pergunta “para mim”          | “Estou ganhando da inflação?” | entidades client_*     |
| **E. Notícia**                | Palavra-chave do domínio     | “notícia do XPML11”           | fiis_noticias          |
| **F. Ambígua/perigosa**       | Rec, melhor, comprar/vender  | “Qual fundo é melhor?”        | fallback seguro        |
| **G. Meta (sobre o Araquem)** | Como funciona                | “O que você sabe fazer?”      | resposta institucional |

---


# **2. Matriz de Cobertura por Entidade**

Abaixo a matriz **oficial**, consolidada com base:

* entities/*.yaml
* ontology/entity.yaml
* concepts/*.yaml
* dados reais
* qualidade baseline

---

## **2.1. Entidades de FIIs (públicas)**

### **📌 fii_overview**

**Tipo:** 1x1
**Cobertura:** Dados cadastrais
**Perguntas:**

* resumo do HGLG11
* overview do KNRI11
* o que é o MXRF11?
  **Narrator:** interpretação curta
  **Gaps:** não cobre preços / dividendos

---

### **📌 fiis_cadastro**

Mesma natureza do overview (dados cadastrais).
**Usado como fallback técnico interno.**

---

### **📌 fiis_dividendos**

**Tipo:** 1xN
**Cobertura:** histórico de dividendos
**Perguntas:**

* dividendos do HGLG11
* quanto pagou mês a mês
* últimos dividendos
  **Narrator:**
* explicar tendências
* variações
* destaque de estabilidade

---

### **📌 fiis_precos**

**Tipo:** 1xN
**Cobertura:** histórico de cotações
**Perguntas:**

* preço do HGLG11 hoje
* gráfico 12 meses
* variação diária
  **Narrator:**
* explicar tendência
* contextualizar com IFIX

---

### **📌 fiis_yield_history**

**Tipo:** 1xN
**Cobertura:** yield mensal
**Perguntas:**

* DY do HGLG11
* histórico de rendimento
  **Narrator:**
* relação preço × dividendos

---

### **📌 fiis_financials_snapshot**

**Tipo:** 1x1
**Cobertura:** dados financeiros
**Perguntas:**

* patrimônio
* captação
* receitas
  **Narrator:**
* interpretar saúde financeira

---

### **📌 fiis_financials_risk**

**Tipo:** 1x1
**Cobertura:** métricas de risco
**Perguntas:**

* volatilidade
* Sharpe
* Beta
* Sortino
  **Narrator:**
* explicar cada risco
* relacionar com comportamento

---

### **📌 fiis_financials_revenue_schedule**

**Tipo:** 1x1
**Cobertura:** calendário de receitas futuras
**Perguntas:**

* % indexado ao IPCA
* vencimentos
* indexadores
  **Narrator:**
* explicar composição de indexadores

**Importante:** IPCA *conceitual* deve cair em concepts-macro, não nesta entidade.

---

### **📌 fiis_imoveis**

**Tipo:** 1xN
**Cobertura:** imóveis reais
**Perguntas:**

* imóveis do fundo
* estados
* tipos
  **Narrator:**
* interpretar exposição setorial

---

### **📌 fiis_processos**

**Tipo:** 1xN
**Cobertura:** processos judiciais
**Perguntas:**

* processos do fundo
* risco jurídico
  **Narrator:**
* explicar possíveis impactos

---

### **📌 fiis_rankings**

**Tipo:** 1x1
**Cobertura:** ranking SIRIOS / IFIX / liquidez
**Perguntas:**

* posição do HGLG11
* evolução no ranking
  **Narrator:**
* traduz tendências

---

### **📌 fiis_noticias**

**Tipo:** 1xN
**Cobertura:** notícias relacionadas ao FII
**Perguntas:**

* notícias do HGLG11
* notícias negativas
* fatos relevantes
  **Narrator:**
* contextualizar sem inventar
* destacar sentimento sem opinião
* nunca fazer previsão

---

## **2.2. Entidades Históricas/Índices**

### **📌 history_b3_indexes**

**Cobertura:** IFIX, IFIL, IBOV etc
**Perguntas:**

* desempenho do IFIX
* últimos meses
  **Narrator:** interpretar movimento do índice

---

### **📌 history_currency_rates**

**Cobertura:** moedas
**Perguntas:**

* dólar hoje
* euro mensal
  **Narrator:** contexto macro complementar

---

### **📌 history_market_indicators**

**Cobertura:** CDI, SELIC, IPCA, spreads
**Perguntas:**

* IPCA do mês
* CDI atual
* inflação
  **Narrator:** explicação macro

### ❗ IPCA “conceitual” → concepts-macro

### ❗ IPCA “de um FII” → revenue_schedule

### ❗ IPCA “da carteira” → client_performance_vs_benchmark

---

## **2.3. Entidades da carteira (privadas)**

### **📌 client_fiis_positions**

**Cobertura:** carteira atual
**Perguntas:**

* meus fiis
* quanto tenho em MXRF11
  **Narrator:** leitura geral

---

### **📌 client_fiis_dividends_evolution**

**Cobertura:** evolução da renda mensal
**Perguntas:**

* minha renda está crescendo?
* dividendos no tempo
  **Narrator:** análise de tendência

---

### **📌 client_fiis_performance_vs_benchmark**

**Cobertura:** carteira vs IFIX / IFIL / CDI
**Perguntas:**

* estou ganhando do IFIX?
* minha carteira melhorou?
  **Narrator:** comparação e explicação

---

## **2.4. Conceituais (data/concepts)**

### **📌 concepts-fiis**

* O que é FII
* Tipos de FII
* Vacância
* Gestão ativa/passiva

### **📌 concepts-risk**

* Sharpe
* Beta
* Volatilidade
* MDD

### **📌 concepts-macro**

* IPCA
* Juros
* Índices
* Inflação alta → efeito em FIIs

### **📌 concepts-carteira**

* Diversificação
* Alocação
* Exposição setorial

Todas são respondidas **via Narrator**.

---


# **3. Lacunas Identificadas (Gaps)**

| Gap                                                     | Observação                               | Solução Planejada                                 |
| ------------------------------------------------------- | ---------------------------------------- | ------------------------------------------------- |
| IPCA conceitual roteando para revenue_schedule          | **aconteceu nos testes**                 | reforçar tokens em concepts-macro como prioridade |
| perguntas sobre “melhores FIIs”                         | risco regulatório                        | criar modo desambiguação                          |
| notícias sem ticker                                     | hoje cai em fiis_noticias mas pode dar 0 | permitir Narrator responder com conceito          |
| perguntas “me recomende”                                | proibido                                 | criar respostas seguras padrão                    |
| perguntas extremamente técnicas sobre taxonomia de FIIs | poucos conceitos hoje                    | expandir concepts-fiis                            |

---


# **4. Matriz Final (perguntas → entidades)**

| Pergunta                       | Categoria          | Entidade                  | Narrator | Estado |
| ------------------------------ | ------------------ | ------------------------- | -------- | ------ |
| “O que é IPCA alto?”           | Conceitual         | concepts-macro            | forte    | OK     |
| “IPCA do mês”                  | Factual            | history_market_indicators | leve     | OK     |
| “% indexado ao IPCA do HGLG11” | Factual com ticker | revenue_schedule          | leve     | OK     |
| “DY do MXRF11”                 | Factual            | fiis_yield_history        | leve     | OK     |
| “CNPJ do KNRI11”               | Factual            | overview                  | leve     | OK     |
| “Notícias negativas do VISC11” | Notícias           | fiis_noticias             | moderado | OK     |
| “Melhor fundo para investir?”  | Ambígua            | fallback                  | seguro   | OK     |
| “Minha renda está crescendo?”  | Privada            | client_dividends          | moderado | OK     |

---


# **5. Como essa matriz será usada**

* Validar Planner
* Validar Narrator (shadow)
* Criar testes de roteamento
* Criar testes de resposta
* Criar dashboards de cobertura
* Ser referência para roadmap dos próximos 12 meses

---

