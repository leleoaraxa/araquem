# 📈 Financial Indicators Reference (SIRIOS Indicators)

Este documento consolida todos os **indicadores financeiros** calculados e utilizados pela plataforma **SIRIOS**, com seus conceitos, fórmulas, unidades, interpretações e equivalentes em inglês.
Serve como **fonte de consulta e validação cruzada** dos cálculos historicamente implementados no módulo compute-on-read `fiis_metrics` (atualmente desativado) e demais entidades relacionadas.

> Métricas compute-on-read desativadas temporariamente; projeto opera apenas com 11 D-1.

## 🔗 Rastreamento operacional (legado `fiis_metrics` — desativado)

| Indicador lógico | Métrica (`metric`) | Origem de dados | Observações |
| ---------------- | ------------------ | --------------- | ----------- |
| Beta Índice | `risk.beta_index` | Séries de preços do FII (`fiis_quota_prices`) + benchmark IFIX | Projeção ajusta janela e índice.
| Sharpe Ratio | `risk.sharpe_ratio` | Preços do FII (`fiis_quota_prices`) + taxa livre (`CDI`) | Considera retorno excedente diário.
| Sortino Ratio | `risk.sortino_ratio` | Preços do FII (`fiis_quota_prices`) + `CDI` | Penaliza apenas downside volatility.
| Treynor Ratio | `risk.treynor_ratio` | Preços do FII (`fiis_quota_prices`) + IFIX + `CDI` | Usa beta projetado para ajuste de risco sistemático.
| Alpha de Jensen | `risk.jensen_alpha` | Preços do FII (`fiis_quota_prices`) + IFIX + `CDI` | Calculado sobre a janela parametrizada.
| Volatility Ratio | `risk.volatility_ratio` | Preços do FII (`fiis_quota_prices`) + IFIX | Compara volatilidade do fundo vs. índice.
| Max Drawdown (MDD) | `risk.max_drawdown` | Preços do FII (`fiis_quota_prices`) | Avalia pior perda no período solicitado.
| R² | `risk.r_squared` | Preços do FII (`fiis_quota_prices`) + IFIX | Coeficiente de determinação do ajuste linear.
| Soma de dividendos | `dividends.dividends_sum` | Pagamentos (`fiis_dividends`) | Agrega valores do período/janela.
| Contagem de dividendos | `dividends.dividends_count` | Pagamentos (`fiis_dividends`) | Número de eventos na janela.
| DY médio | `dividends.dy_avg` | Dividendos (`fiis_dividends`) + preços (`fiis_quota_prices`) | Calcula yield médio ponderado.
| Preço médio | `prices.price_avg` | Preços do FII (`fiis_quota_prices`) | Média de fechamento ajustada pelo período.
| Retorno no período | `prices.return_period` | Preços do FII (`fiis_quota_prices`) + `CDI` (para comparação opcional) | Percentual acumulado solicitado.

**Sumário**
- [1. Beta Índice](#-1-beta-índice)
- [2. Sharpe Ratio](#-2-sharpe-ratio)
- [3. Alpha de Jensen](#-3-alpha-de-jensen)
- [4. Volatility Ratio](#-4-volatility-ratio)
- [5. Treynor Ratio](#-5-treynor-ratio)
- [6. Sortino Ratio](#-6-sortino-ratio)
- [7. Max Drawdown (MDD)](#-7-max-drawdown-mdd)
- [8. R² (Coeficiente de Determinação)](#-8-r²-coeficiente-de-determinação)

---

## 🧩 1. Beta Índice

**Nome em inglês:** Beta Coefficient
**Símbolo:** β

### 🧭 Conceito
O **Beta Índice** mede a **sensibilidade de um ativo em relação ao movimento do mercado**.
É um indicador de **risco sistemático**, usado para avaliar se o ativo tende a se mover mais, menos ou na direção oposta ao índice de referência (geralmente o IBOVESPA ou IFIX).

### ⚙️ Fórmula
\[
\beta = \frac{Cov(R_i, R_m)}{Var(R_m)}
\]
onde:
- \(R_i\): retorno do ativo
- \(R_m\): retorno do mercado
- \(Cov(R_i, R_m)\): covariância entre os retornos do ativo e do mercado
- \(Var(R_m)\): variância dos retornos do mercado

Alternativamente:
\[
\beta = \rho_{i,m} \times \frac{\sigma_i}{\sigma_m}
\]
onde:
- \(\rho_{i,m}\): correlação entre ativo e mercado
- \(\sigma_i, \sigma_m\): desvios-padrão dos retornos

### 📊 Interpretação
| Faixa de Beta | Tipo de ativo | Interpretação prática |
|----------------|----------------|------------------------|
| **β < 0** | Anticíclico | Move-se inversamente ao mercado |
| **0 < β < 0,5** | Defensivo | Baixa sensibilidade, risco menor |
| **0,5 ≤ β ≤ 1,5** | Neutro / moderado | Movimento próximo ao mercado |
| **β > 1,5** | Agressivo | Alta volatilidade, risco elevado |

### 🧮 Exemplo de cálculo (Python)
```python
beta = cov(returns_asset, returns_index) / var(returns_index)
```

### 🧠 Aplicação

* Avaliar **risco sistemático** de FIIs.
* Comparar **sensibilidade** de diferentes fundos.
* Usar no **CAPM** para estimar retorno esperado:
\[
E(R_i) = R_f + \beta_i \big(E(R_m) - R_f\big)
\]

### 🧾 Notas técnicas (SIRIOS)

* Usa retornos logarítmicos diários (janela de 252 dias).
* Índice de referência padrão: IFIX.
* Em caso de dados insuficientes → retorna `NULL`.
* Atualização: D-1 via processo compute-on-read legado (desativado).

---

## 📚 Estrutura sugerida para novos indicadores

| Campo              | Descrição                                     |
| ------------------ | --------------------------------------------- |
| **Nome (pt-br)**   | Nome do indicador                             |
| **Nome (en)**      | Equivalente em inglês                         |
| **Símbolo**        | Abreviação técnica (se existir)               |
| **Conceito**       | Descrição teórica e uso                       |
| **Fórmula**        | Expressão matemática                          |
| **Interpretação**  | Faixas e leitura prática                      |
| **Aplicação**      | Como usar no contexto SIRIOS                  |
| **Notas técnicas** | Regras internas, periodicidade, janelas, etc. |

## 💎 2. Sharpe Ratio

**Nome em inglês:** Sharpe Ratio
**Símbolo:** SR

### 🧭 Conceito
O **Sharpe Ratio** mede o **retorno excedente de um ativo em relação ao seu risco total**.
Ele mostra **quanto de retorno adicional o investidor obteve para cada unidade de risco** assumida.
É um dos principais indicadores de **eficiência de risco-retorno**.

Em outras palavras, o Sharpe indica **se o retorno obtido compensa a volatilidade enfrentada**.

---

### ⚙️ Fórmula
\[
SR = \frac{R_p - R_f}{\sigma_p}
\]

onde:
- \( R_p \): retorno médio do portfólio (ou ativo)
- \( R_f \): taxa livre de risco (ex: Selic, CDI)
- \( \sigma_p \): desvio padrão dos retornos (volatilidade total)

---

### 📊 Interpretação
| Faixa de Sharpe | Interpretação prática | Avaliação |
|------------------|------------------------|------------|
| **SR < 0** | Retorno abaixo da taxa livre de risco | Ineficiente |
| **0 ≤ SR < 1** | Retorno moderado em relação ao risco | Abaixo da média |
| **1 ≤ SR < 2** | Bom equilíbrio risco-retorno | Eficiente |
| **SR ≥ 2** | Excelente retorno para o risco | Altamente eficiente |

---

### 🧮 Exemplo de cálculo (Python)
```python
sharpe_ratio = (mean(returns_asset) - risk_free_rate) / std(returns_asset)
```

---

### 🧠 Aplicação

* Comparar o **desempenho ajustado ao risco** entre diferentes FIIs ou carteiras.
* Avaliar a **eficiência do gestor**.
* Utilizar como métrica de seleção em estratégias quantitativas.

---

### 🧾 Notas técnicas (SIRIOS)

* Base: retornos diários logarítmicos (janela de 252 dias).
* Taxa livre de risco padrão: CDI diário.
* Cálculo compute-on-read originalmente implementado no módulo legado `fiis_metrics` (desativado).
* Retorna `NULL` se não houver dados suficientes ou volatilidade zero.

## 🚀 3. Alpha de Jensen

**Nome em inglês:** Jensen's Alpha
**Símbolo:** α

### 🧭 Conceito
O **Alpha de Jensen** mede o **retorno excedente de um ativo ou portfólio em relação ao que seria esperado pelo seu nível de risco (Beta)**.
É um indicador de **desempenho ajustado ao risco sistemático**, derivado do modelo CAPM.

Em outras palavras, mostra **quanto o gestor ou fundo superou (ou ficou abaixo) do retorno esperado pelo mercado**.

---

### ⚙️ Fórmula
\[
\alpha = R_p - [R_f + \beta_p (R_m - R_f)]
\]

onde:
- \( R_p \): retorno médio do portfólio (ou ativo)
- \( R_f \): taxa livre de risco (ex: Selic, CDI)
- \( R_m \): retorno médio do mercado (ex: IFIX, IBOVESPA)
- \( \beta_p \): Beta do ativo em relação ao mercado

---

### 📊 Interpretação
| Faixa de Alpha | Interpretação prática | Avaliação |
|-----------------|------------------------|------------|
| **α > 0** | Superou o retorno esperado pelo risco | Desempenho superior |
| **α = 0** | Igual ao retorno esperado | Desempenho neutro |
| **α < 0** | Abaixo do retorno esperado | Desempenho inferior |

---

### 🧮 Exemplo de cálculo (Python)
```python
alpha = mean(returns_asset) - (risk_free_rate + beta * (mean(returns_market) - risk_free_rate))
```

---

### 🧠 Aplicação

* Avaliar **gestores ativos**: indica se houve geração de valor além do risco assumido.
* Comparar **fundos ou FIIs** com o mesmo perfil de risco.
* Integrar ao CAPM para mensurar desempenho ajustado ao risco sistemático.

---

### 🧾 Notas técnicas (SIRIOS)

* Usa o mesmo período-base do cálculo do Beta (252 dias úteis).
* Índice de referência padrão: IFIX.
* Taxa livre de risco: CDI diário.
* Dependia do Beta calculado no módulo legado `fiis_metrics` (desativado).
* Se `Beta` não disponível, retorna `NULL`.

## 🌪️ 4. Volatility Ratio

**Nome em inglês:** Volatility Ratio
**Símbolo:** VR

### 🧭 Conceito
O **Volatility Ratio** mede a **proporção entre a volatilidade de um ativo e a volatilidade do mercado**.
Ele mostra **o quanto o ativo é mais ou menos volátil que o índice de referência**, funcionando como uma forma simplificada de sensibilidade ao risco total (sem depender do Beta).

Enquanto o **Beta** considera a covariância com o mercado, o **Volatility Ratio** compara apenas as **magnitudes das variações**.

---

### ⚙️ Fórmula
\[
VR = \frac{\sigma_i}{\sigma_m}
\]

onde:
- \( \sigma_i \): desvio padrão dos retornos do ativo
- \( \sigma_m \): desvio padrão dos retornos do mercado

---

### 📊 Interpretação
| Faixa de VR | Interpretação prática | Avaliação |
|--------------|------------------------|------------|
| **VR < 1** | Menos volátil que o mercado | Defensivo |
| **VR = 1** | Volatilidade igual ao mercado | Neutro |
| **VR > 1** | Mais volátil que o mercado | Agressivo |

---

### 🧮 Exemplo de cálculo (Python)
```python
volatility_ratio = std(returns_asset) / std(returns_market)
```

---

### 🧠 Aplicação

* Comparar a **instabilidade relativa** de diferentes fundos.
* Identificar ativos **mais arriscados** em termos de variação de preço.
* Usar como base para **classificação de perfil de risco** dentro da ontologia histórica de métricas (desativada).

---

### 🧾 Notas técnicas (SIRIOS)

* Usa retornos logarítmicos diários (janela de 252 dias).
* Índice de referência padrão: IFIX.
* Atualização D-1 via processo compute-on-read legado (desativado).
* Retorna `NULL` se desvio-padrão do índice for zero.


## ⚖️ 5. Treynor Ratio

**Nome em inglês:** Treynor Ratio
**Símbolo:** TR

### 🧭 Conceito
O **Treynor Ratio** mede o **retorno excedente obtido por unidade de risco sistemático (Beta)**.
É uma métrica de **eficiência de retorno ajustada ao risco de mercado**, semelhante ao Sharpe Ratio, mas considera apenas o **risco não diversificável** (aquele que vem do mercado).

Em resumo: mostra **quanto o investidor ganhou acima da taxa livre de risco, para cada unidade de risco de mercado assumido**.

---

### ⚙️ Fórmula
\[
TR = \frac{R_p - R_f}{\beta_p}
\]

onde:
- \( R_p \): retorno médio do portfólio (ou ativo)
- \( R_f \): taxa livre de risco (ex: CDI, Selic)
- \( \beta_p \): Beta do ativo em relação ao mercado

---

### 📊 Interpretação
| Faixa de TR | Interpretação prática | Avaliação |
|--------------|------------------------|------------|
| **TR < 0** | Retorno abaixo da taxa livre de risco | Ineficiente |
| **0 ≤ TR < 0.5** | Baixa compensação de risco sistemático | Abaixo da média |
| **0.5 ≤ TR < 1.0** | Boa compensação | Eficiente |
| **TR ≥ 1.0** | Alta eficiência de risco-retorno | Excelente desempenho |

*(valores de referência indicativos, podem variar conforme a janela e o tipo de ativo)*

---

### 🧮 Exemplo de cálculo (Python)
```python
treynor_ratio = (mean(returns_asset) - risk_free_rate) / beta_asset
```

---

### 🧠 Aplicação

* Comparar fundos com diferentes exposições ao mercado (diferentes Betas).
* Avaliar **gestores que buscam superar o mercado** com risco sistemático controlado.
* Complementar a análise do Sharpe Ratio (quando o Beta é mais relevante que a volatilidade total).

---

### 🧾 Notas técnicas (SIRIOS)

* Usa retornos logarítmicos diários (janela de 252 dias).
* Beta calculado conforme o módulo legado `fiis_metrics` (desativado).
* Taxa livre de risco padrão: CDI diário.
* Retorna `NULL` se Beta ≤ 0 (não aplicável).
* Atualização D-1 via processo compute-on-read legado (desativado).

## 🧠 6. Sortino Ratio

**Nome em inglês:** Sortino Ratio
**Símbolo:** SoR

### 🧭 Conceito
O **Sortino Ratio** mede o **retorno excedente** de um ativo **por unidade de risco de queda** (*downside risk*), penalizando **apenas retornos abaixo de uma meta** (geralmente a taxa livre de risco).
É mais apropriado do que o Sharpe quando o foco é **evitar perdas**.

### ⚙️ Fórmula
\[
SoR = \frac{R_p - T}{\sigma_{down}}
\]
onde:
- \( R_p \): retorno médio do ativo/portfólio
- \( T \): retorno alvo (padrão: \( R_f \), taxa livre de risco)
- \( \sigma_{down} \): desvio-padrão **apenas** dos retornos \( R_t < T \)

### 📊 Interpretação
| Faixa de Sortino | Leitura |
|------------------|---------|
| **SoR < 0** | Retorno abaixo do alvo; ineficiente |
| **0 ≤ SoR < 1** | Compensação fraca do risco de queda |
| **1 ≤ SoR < 2** | Boa compensação do risco de queda |
| **SoR ≥ 2** | Excelente |

### 🧮 Exemplo de cálculo (Python)
```python
excess = returns_asset - target_rate  # target = risk-free por padrão
downside = excess[excess < 0]
sortino = excess.mean() / downside.std(ddof=1)
```

### 🧾 Notas técnicas (SIRIOS)

* Janela: 252 pregões (D-1).
* `target_rate` padrão = CDI diário (pode ser 0, se configurado).
* Retorna `NULL` se não houver retornos abaixo do alvo suficientes para estimativa.

---

## 📉 7. Max Drawdown (MDD)

**Nome em inglês:** Maximum Drawdown
**Símbolo:** MDD

### 🧭 Conceito
O **Max Drawdown** é a **maior queda percentual** do valor acumulado (ou preço) **do pico ao vale** em um período. Mede a **pior perda** ocorrida.

### ⚙️ Fórmula (definição)
\[
\mathrm{MDD} = \min_t \left( \frac{V_t - \max_{\tau \le t} V_\tau}{\max_{\tau \le t} V_\tau} \right)
\]
onde \( V_t \) é o valor acumulado no tempo \( t \). Resultado é **negativo** (queda). Frequentemente reportado como módulo **positivo** em %.

### 📊 Interpretação
* **0%** → sem perda.
* **-20%** → perdeu 20% do pico ao vale (ou **20%** se reportado em módulo).
* Quanto **mais negativo** (ou maior em módulo), **pior** o risco histórico de perda.

### 🧮 Exemplo de cálculo (Python)
```python
import numpy as np

cum = (1 + returns_asset).cumprod()
rolling_max = np.maximum.accumulate(cum)
dd = (cum - rolling_max) / rolling_max
max_drawdown = dd.min()  # tipicamente negativo
```

### 🧾 Notas técnicas (SIRIOS)

* Janela: 252 pregões (D-1).
* Na view, será exposto como **valor positivo** (módulo) por padrão.
* Retorna `NULL` se a série for muito curta.

---

## 📐 8. R² (Coeficiente de Determinação)

**Nome em inglês:** Coefficient of Determination
**Símbolo:** \( R^2 \)

### 🧭 Conceito
O **R²** mede a **fração da variação** dos retornos do ativo **explicada pelo mercado** (índice de referência) numa regressão linear:
\[
R_i = \alpha + \beta R_m + \varepsilon
\]
Em regressão simples com intercepto, **\( R^2 = \rho_{i,m}^2 \)** (correlação ao quadrado).

### ⚙️ Fórmula (equivalente)
\[
R^2 = \frac{\mathrm{Var}(\hat{R}_i)}{\mathrm{Var}(R_i)} = \rho_{i,m}^2
\]

### 📊 Interpretação
| R²            | Leitura                                         |
| ------------- | ----------------------------------------------- |
| **0.00–0.25** | Pouca explicação pelo mercado (idiossincrático) |
| **0.25–0.50** | Mista                                           |
| **0.50–0.75** | Moderada                                        |
| **0.75–1.00** | Alta explicação pelo mercado                    |

### 🧮 Exemplo de cálculo (Python)
```python
import numpy as np
r2 = np.corrcoef(returns_asset, returns_market)[0,1] ** 2
```

### 🧾 Notas técnicas (SIRIOS)

* Mesma janela do Beta (252 pregões, D-1).
* Índice padrão: IFIX.
* Retorna `NULL` se dados insuficientes ou variância nula.
