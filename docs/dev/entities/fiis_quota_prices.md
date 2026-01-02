# Entidade: `fiis_quota_prices`

## 1. Objetivo da entidade

Fornecer preços e cotações históricas de Fundos Imobiliários (FIIs) no padrão `AAAA11`, incluindo:

- preço de fechamento;
- máxima e mínima do dia;
- variação diária (em % e em R$), quando aplicável.

Foco primário: **perguntas de preço/cotação em janelas curtas (hoje, ontem, data específica)**.

---

## 2. Perguntas típicas (CANON)

Perguntas que **devem** ser roteadas para `fiis_quota_prices`:

1. "Quanto está o HGLG11 hoje?"
2. "Qual a cotação atual do KNRI11?"
3. "Me mostra o preço do VINO11 agora"
4. "Qual foi o último preço negociado de XPLG11?"
5. "Quanto fechou o HGLG11 ontem?"
6. "Preço de fechamento de ontem do KNRI11"
7. "Qual foi a cotação de ontem do VISC11?"
8. "Qual foi a máxima do HGLG11 em 27/10/2025?"
9. "Preço mínimo do VINO11 em 10/09/2023"
10. "O HGLG11 subiu ou caiu hoje?"
11. "Quanto o KNRI11 variou hoje em porcentagem?"
12. "Como está VINO agora?" (sem `11`, mas contexto de FII)

Essas perguntas devem ter:

- `score_top1` alto (idealmente > 0.9);
- `gap` confortável em relação a rivais (`history_b3_indexes`, `fiis_news` etc.), idealmente > 0.15.

---

## 3. Perguntas que NÃO são desta entidade (contraexemplos)

Exemplos de perguntas que **não** devem cair em `fiis_quota_prices`:

- Índices / macro:
  - "Quanto está o IFIX hoje?" → `history_b3_indexes`
  - "Qual foi o fechamento do IBOV ontem?" → `history_b3_indexes`
  - "Variação do CDI este mês" → `history_market_indicators`
  - "Como está o dólar hoje?" → `history_currency_rates`

- Notícias:
  - "Quais as últimas notícias do HGLG11?" → `fiis_news`
  - "Teve fato relevante do KNRI11 hoje?" → `fiis_news`
  - "Resumo das notícias recentes sobre VINO11" → `fiis_news`

- Fundamentos / risco:
  - "Qual o risco do HGLG11 hoje?" → `fiis_financials_risk`
  - "Como está a vacância do VINO11?" → `fiis_financials_risk` ou outra entidade de fundamentos.

---

## 4. Tokens principais (positivos)

Tokens e padrões que **reforçam** a intenção `fiis_quota_prices`:

- Termos de preço/cotação:
  - `cotacao`, `preco`, `preço`, `fechamento`, `ultimo preco`, `ultima cotacao`, `ultimo valor`.
- Termos temporais de curto prazo:
  - `hoje`, `agora`, `ontem`, `no fechamento de ontem`, `no dia DD/MM/AAAA`.
- Termos de variação:
  - `subiu`, `caiu`, `variou`, `alta`, `baixa`, `oscilou`, `oscilacao`, `variacao em %`, `variacao em reais`.
- Padrões de ticker:
  - `AAAA11` (ex.: `HGLG11`, `KNRI11`, `VINO11`, `XPLG11`);
  - `AAAA` quando o bucket de FIIs indicar que é um FII (ex.: `VINO` → `VINO11`).

Regras de design:

- Se aparecer `AAAA11` + qualquer termo de preço/cotação/variação de curto prazo → forte push para `fiis_quota_prices`.
- Se aparecer `AAAA` sem 11, mas classificado como FII via bucket → tratar semanticamente como `AAAA11`.

---

## 5. Anti-tokens e filtros

Palavras que **devem reduzir** o peso de `fiis_quota_prices` quando combinadas com ticker:

- Notícias/texto:
  - `noticia`, `noticias`, `fato relevante`, `relatorio`, `comunicado`, `release`, `avisos ao mercado`.
- Fundamentos/risco:
  - `risco`, `rating`, `vacancia`, `alavancagem`, `gestor`, `administrador`, `setor`, `segmento`.
- Análises descritivas:
  - `comentario`, `analise`, `analise grafica`, `opinia`.

Uso prático:

- Pergunta com `noticias` + `HGLG11` → deve puxar `fiis_news`, e `fiis_quota_prices` recebe penalização.
- Pergunta com `risco` + ticker → `fiis_financials_risk` tem prioridade.

---

## 6. Entidades rivais e regras de separação

- `history_b3_indexes`
  - Foco: IFIX, IBOV, CDI, SELIC, IFIL e outros índices.
  - Tokens positivos: `ifix`, `ibov`, `ibovespa`, `cdi`, `selic`, `ifil`, `indice`.
  - Anti-tokens: foco em não responder perguntas de FIIs padrão `AAAA11`.

- `fiis_news`
  - Foco: notícias, fatos relevantes, comunicados de FIIs.
  - Tokens positivos: `noticia`, `noticias`, `fato relevante`, `release`, `comunicado`.
  - Deve perder peso quando a pergunta é explicitamente de cotação/preço.

- `fiis_financials_risk`
  - Foco: risco, rating, fundamentos de risco dos FIIs.
  - Tokens positivos: `risco`, `rating`, `vacancia`, `alavancagem`, `lajeado`, etc.

---

## 7. Critérios de qualidade para `fiis_quota_prices`

Objetivos mensuráveis:

- Nas amostras canônicas de preço (hoje/ontem/data específica):
  - `top1_accuracy` ≥ 95%;
  - `score_top1` médio ≥ 0.9;
  - `gap_top1_top2` médio ≥ 0.15 contra rivais diretos.
- Nenhuma pergunta de índices (`IFIX`, `IBOV`, `CDI`, `dólar`) deve cair em `fiis_quota_prices` nos testes de regressão.

Quando os critérios **não forem atendidos**:

1. Revisar tokens/anti-tokens da entidade e das rivais.
2. Ajustar/expandir `routing_samples` com exemplos específicos que falharam.
3. Atualizar este documento com novos padrões de pergunta identificados.

---

## 8. Checklist operacional de curadoria (para qualquer pessoa da equipe)

1. Rodar o script de qualidade focado em intents relacionadas a preço de FIIs.
2. Listar todos os misses envolvendo `fiis_quota_prices`.
3. Para cada miss, classificar:
   - `ontologia_fraca` (faltam tokens/anti-tokens);
   - `colisao_com_index` (`history_b3_indexes`, `history_market_indicators`, `history_currency_rates`);
   - `colisao_com_news` (`fiis_news`);
   - `gabarito_duvidoso`.
4. Propor ajustes:
   - adicionar/remover tokens/anti-tokens;
   - criar ou revisar samples em `routing_samples`;
   - corrigir gabarito se estiver errado.
5. Re-rodar a bateria de testes.
6. Atualizar este doc com:
   - novos exemplos canônicos;
   - novos contraexemplos relevantes;
   - observações de colisão (quem briga com quem e por quê).

