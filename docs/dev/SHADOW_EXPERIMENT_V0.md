# 📄 **SHADOW EXPERIMENT V0 — Roteiro de Perguntas para Teste do Narrator (Shadow Mode)**

*Versão 1.0 — Sirius & Leleo*

> **Objetivo**
> Gerar eventos reais de Shadow para analisar o comportamento do Narrator (estilo, estabilidade, latência, coerência, uso de RAG, modo conceitual, etc.) antes de integrar o LLM à UX.

> **Escopo**
> Apenas entidades em **shadow mode**:
>
> * `fiis_financials_risk`
> * `fiis_noticias`
> * `history_market_indicators`
> * `history_b3_indexes`
> * `history_currency_rates`

> **Nota importante**
> Perguntas **macro sem ticker** → devem ir para **modo conceito**.
> Perguntas **macro com ticker** → podem ir para entidades D-1 (`fiis_financials_revenue_schedule`) normalmente.

---

# 1) 🔥 Perguntas sobre **RISCO** (fiis_financials_risk — conceitual + dados)

## 1.1 Perguntas **conceituais puras** (sem ticker)

Essas devem ativar `prefer_concept_when_no_ticker: true`.

1. “O que significa Sharpe negativo em FIIs?”
2. “Como interpretar um Drawdown muito grande?”
3. “Beta alto é ruim para FIIs?”
4. “Diferença entre Sharpe, Sortino e Treynor?”
5. “Como saber se o risco de um FII está aumentando?”
6. “O que é volatilidade e por que importa para FIIs?”
7. “R² alto indica que um FII segue o IFIX?”
8. “Qual métrica de risco é mais importante para FIIs híbridos?”
9. “Como interpretar o Alfa de Jensen em FIIs?”

## 1.2 Perguntas **semiconceituais** (conceito + comportamento do fundo)

Essas passarão pelo risk (dados) + Narrator explicando.

10. “O que significa se um FII X tem Sharpe muito alto?”
11. “Como interpretar a volatilidade do HGLG11?”
12. “Beta elevado do MXRF11 indica o quê?”
13. “Sortino baixo no KNRI11 significa que o fundo cai muito?”
14. “Um FII com MDD profundo é sempre ruim?”
15. “O que esperar de um FII quando o risco sobe repentinamente?”

---

# 2) 📈 Perguntas **MACRO** (IPCA, juros, índices, moedas)

## 2.1 Perguntas **macro sem ticker** (devem ir para modo conceito)

Essas testam exatamente a política:
“prefer_concept_when_no_ticker: true” + RAG `concepts-macro.yaml`.

**IPCA / Inflação**

1. “O que significa IPCA alto para FIIs?”
2. “IPCA baixo favorece quais tipos de FIIs?”
3. “Como FIIs de tijolo reagem à inflação alta?”
4. “Por que inflação corrói dividendos reais?”

**Juros / CDI / SELIC**
5. “Como juros altos afetam FIIs de papel?”
6. “O que significa SELIC cair para os FIIs?”
7. “CDI alto melhora ou piora o cenário dos FIIs?”

**Câmbio / Moedas**
8. “O que significa dólar forte nos FIIs?”
9. “Como euro e dólar impactam FIIs com receitas dolarizadas?”
10. “O que acontece com FIIs de logística quando o dólar dispara?”

**Índices / Mercado**
11. “Como interpretar um IFIX caindo por vários meses?”
12. “O que significa quando o CDI supera o IFIX?”

---

## 2.2 Perguntas **macro com ticker** (devem ir para dados, NÃO conceito)

Essas devem cair em `fiis_financials_revenue_schedule`.

1. “Qual percentual da receita do HGLG11 é indexado ao IPCA?”
2. “O XPML11 tem receitas atreladas ao IGP-M?”
3. “Algum contrato do KNRI11 é indexado ao IPCA?”
4. “Mostre o calendário de reajustes do VISC11.”
5. “O VRTA11 ganha com IPCA alto?”

---

# 3) 📰 Perguntas sobre **NOTÍCIAS** (fiis_noticias — 3.218 itens)

## 3.1 Perguntas diretas sobre notícia

1. “Quais notícias mais recentes do HGLG11?”
2. “Principais fatos relevantes do MXRF11 nesta semana?”
3. “Houve alguma notícia negativa recente sobre KNRI11?”
4. “O que saiu de importante sobre o XPLG11 este mês?”
5. “Quais foram os comunicados relevantes sobre o CPTS11?”

## 3.2 Perguntas **qualitativas** (Narrator explicando o que as notícias significam)

6. “Essa notícia ruim sobre o fundo é motivo para preocupação?”
7. “Como interpretar um fato relevante negativo?”
8. “Notícias negativas costumam afetar o preço do fundo imediatamente?”
9. “Como saber se uma notícia já está precificada?”
10. “Como comparar duas notícias diferentes para o mesmo fundo?”

## 3.3 Perguntas **misturadas com contexto**

11. “Quais foram as últimas notícias do MXRF11?”
    → seguida por:
12. “Isso aumenta o risco do fundo?”
13. “Esse fundo ainda está saudável apesar das notícias?”

---

# 4) 🔄 Perguntas **MULTI-TURNO** (Context Manager + Narrator Shadow)

Fluxos completos para gerar shadow contextual real.

## 4.1 Fluxo 1 — Cadastro → Risco → Overview

1. “Qual o CNPJ do HGLG11?”
2. “Esse fundo tem Sharpe bom?”
3. “Me dê um overview dele.”

## 4.2 Fluxo 2 — Notícias → Processos → Risco

4. “Quais notícias recentes do MXRF11?”
5. “Esse fundo tem processos judiciais?”
6. “Isso aumenta o risco dele?”

## 4.3 Fluxo 3 — Preço → Dividendos → Yield → Risco

7. “Qual o preço atual do KNRI11?”
8. “Quanto ele pagou de dividendos nos últimos meses?”
9. “O yield está estável?”
10. “Esse fundo é arriscado?”

## 4.4 Fluxo 4 — Macro + Ticker

11. “O que significa IPCA alto para FIIs?” (modo conceito)
12. “E o IPCA impacta o HGLG11?” (modo dados)
13. “Esse impacto é positivo ou negativo no curto prazo?” (Narrator explica)

---

# 5) 🌍 Perguntas sobre **Market Indicators / B3 Indexes / Currency Rates**

Essas devem cair nesses três domínios:

* `history_market_indicators`
* `history_b3_indexes`
* `history_currency_rates`

## 5.1 Indicadores de mercado

1. “Qual a diferença entre IPCA, IGP-M e CDI?”
2. “Como interpretar a queda recente do CDI?”
3. “O que significa o IPCA vir acima do esperado?”

## 5.2 Índices B3

4. “O que explica o IFIX cair 1% hoje?”
5. “Por que o IFIL tem comportamento diferente do IFIX?”
6. “Como o Ibovespa influencia os FIIs?”

## 5.3 Câmbio

7. “Por que o dólar oscilou tanto este mês?”
8. “O que faz o real se valorizar?”
9. “Como câmbio volátil afeta fundos logísticos?”

---

# 6) 🧪 Perguntas de **cantos da rede** (erro, ambiguidade, responsividade do Shadow)

## 6.1 Perguntas deliberadamente vagas

1. “Esse fundo é bom?”
2. “Ele está saudável?”
3. “É arriscado?”
4. “Está valendo a pena investir?”
   *(Sem ticker → modo conceito)*

## 6.2 Perguntas com ambiguidade

5. “Fala mais dele.”
6. “E esse risco aí?”
7. “Como está o mercado hoje?”
8. “Isso é bom ou ruim para os FIIs?”

## 6.3 Perguntas usando palavras-gatilho erradas (teste de roteamento)

9. “Quanto o IPCA do HGLG11 subiu?”
   → correto: o IPCA não “sobe” por FII, mas os contratos dele podem ser IPCA.
   Narrator deve explicar.

10. “O CDI do MXRF11 está alto?”
    → Narrator deve corrigir com educação.

---

# 7) 🧩 Perguntas extras inspiradas pelo `routing_samples.json`, `quality_list_misses` e `golden`

(sem repetir nada do dataset; apenas variações naturais)

1. “O IFIX tem subido mais que o CDI este ano?”
2. “Quais FIIs foram mais afetados pela inflação alta?”
3. “Como interpretar um IPCA de 0,80% no mês?”
4. “Selic em queda ajuda mais FIIs de tijolo ou de papel?”
5. “Quais fatores mais impactam o risco de um FII de papel?”
6. “Quais notícias costumam alterar o preço do fundo rapidamente?”
7. “Como saber se uma notícia é irrelevante para o fundo?”

---

# 🎯 Conclusão

Com esse roteiro:

* cobrimos **todas as entidades em shadow**;
* testamos **conceito vs dados**;
* exercitamos o **Context Manager**;
* exploramos **RAG conceitual** com limites;
* tocamos em **ambiguidade**, **vaguidade**, **correções educativas** e **snippets curtos**;
* geramos material perfeito para o Shadow Collector.

Assim que você rodar esse experimento e gerar o primeiro `narrator_shadow_*.jsonl`, eu preparo:

* um **checklist de avaliação**,
* um **roteiro de leitura**,
* e um **modelo de relatório v0** para analisarmos juntos.
