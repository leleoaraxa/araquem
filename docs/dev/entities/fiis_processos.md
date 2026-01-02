# Entidade: `fiis_processos`

## 1. Objetivo

A entidade `fiis_processos` consolida **informações de processos judiciais** associados a cada FII (por ticker).
Ela responde perguntas como:

- Se um fundo tem ou não processos.
- Quantos processos existem e em que fase/instância estão.
- Qual o **risco** (probabilidade de perda) e o **valor** das ações.
- Um **resumo dos fatos** e possíveis impactos financeiros.

Camada de dados:

- **View SQL**: `fiis_processos`
- **Grão**: 1 linha por processo judicial por FII (`ticker` + `process_id` / `process_number`).
- **Atualização**: foto D-1 (conforme política geral da base judicial).

---

## 2. Quando usar esta entidade (roteamento ideal)

O Planner deve priorizar `fiis_processos` quando a pergunta envolver, de forma clara, **processos, ações judiciais ou litígios** ligados a um FII específico ou a um conjunto de FIIs.

Padrões de intenção típicos:

- Perguntas sobre **existência de processos**:
  - “O ALMI11 tem processos judiciais?”
  - “Existem ações contra o ALMI11?”

- Perguntas sobre **quantidade de ações/processos**:
  - “Quantos processos o ALMI11 possui?”
  - “Quais FIIs têm mais processos judiciais?”

- Perguntas sobre **status / andamento**:
  - “Qual o status dos processos do ALMI11?”
  - “Como está o andamento das ações judiciais do ALMI11?”

- Perguntas sobre **valor e risco**:
  - “Qual o valor total das causas envolvendo o ALMI11?”
  - “Qual o risco de perda dos processos do ALMI11?”
  - “Quanto o ALMI11 pode perder se perder todas as ações judiciais?”

- Perguntas sobre **detalhes e fatos principais**:
  - “Quais são os principais fatos dos processos do ALMI11?”
  - “Resumo das ações judiciais do ALMI11.”

Essas perguntas são exatamente as que aparecem (e variam) nos `sample_questions` do schema e na ontologia da intenção `fiis_processos`.

---

## 3. Quando **não** usar (anti-conflitos)

O Planner **não** deve usar `fiis_processos` quando:

1. A pergunta é sobre **desempenho, preço, dividendos ou yield**:
   - “Quanto está o ALMI11 hoje?” → `fiis_precos`
   - “Quanto o ALMI11 pagou de dividendos esse mês?” → `fiis_dividends`
   - “Qual o DY do ALMI11 em 2024?” → `fiis_yield_history` ou `fiis_dividends_yields` (conforme o caso).

2. A pergunta é sobre **riscos quantitativos de mercado** (Sharpe, volatilidade, drawdown etc.):
   - “Qual o Sharpe do ALMI11?” → `fiis_financials_risk`
   - “Qual o risco do ALMI11 comparado ao IFIX?” → `fiis_financials_risk` / `fiis_rankings`.

3. A pergunta é sobre **fundamentos, cadastro ou snapshot financeiro**:
   - “Qual o CNPJ do ALMI11?” → `fiis_registrations` ou `fiis_overview`
   - “Qual o patrimônio líquido do ALMI11?” → `fiis_financials_snapshot`.

4. A pergunta é sobre **notícias, fatos relevantes, comunicados**:
   - “Teve alguma notícia recente sobre o ALMI11?” → `fiis_noticias`.

5. A pergunta é sobre **imóveis/portfólio físico**:
   - “Quais imóveis o ALMI11 possui?” → `fiis_imoveis`.

Regra prática:
Se o foco é **litígio judicial** (ação, processo, causa, risco de perda em tribunal) → `fiis_processos`.
Se o foco é **qualquer outra dimensão do fundo** (preço, yield, vacância, patrimônio, notícia, etc.) → outra entidade específica.

---

## 4. Colunas e semântica dos campos

Fonte: `data/contracts/fiis_processos.schema.yaml`.

| Coluna                   | Tipo / Exemplo                                   | Semântica prática                                                                                          |
|--------------------------|--------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| `ticker`                 | `ALMI11`                                        | Código do FII ao qual o processo está associado.                                                           |
| `process_id`             | `123`                                           | ID interno único na base judicial / de mapeamento (chave técnica).                                        |
| `process_number`         | `"0001234-56.2023.8.26.0100"`                    | Número oficial do processo no padrão do tribunal.                                                          |
| `instance`               | `"1ª instância"`, `"2ª instância"`              | Instância do processo (primeira, segunda, tribunal superior etc.).                                        |
| `court`                  | `"TJSP"`, `"TRF3"`                              | Tribunal responsável (ex.: TJ estadual, TRF, STJ, etc.).                                                  |
| `forum`                  | `"São Paulo - Foro Central"`                    | Foro / comarca onde o processo tramita.                                                                   |
| `process_class`          | `"Ação de Cobrança"`, `"Ação Civil Pública"`    | Classe processual / tipo legal da ação.                                                                   |
| `action_type`            | `"Indenizatória"`, `"Revisional"`               | Tipo de ação (natureza jurídica, mais “amigável” ao usuário que a classe do tribunal).                    |
| `filed_by`               | `"Condomínio X"`, `"Delegacia do Consumidor"`   | Parte autora (quem moveu a ação).                                                                         |
| `filed_against`          | `"Fundo ALMI11"`, `"Administrador do fundo"`    | Parte ré (quem está sendo processado).                                                                    |
| `process_status`         | `"Em andamento"`, `"Suspenso"`, `"Encerrado"`   | Situação atual do processo.                                                                               |
| `process_risk`           | `"Alto"`, `"Médio"`, `"Baixo"`                  | Classificação qualitativa do risco (visão consolidada de risco jurídico).                                 |
| `process_value`          | `1500000.00`                                    | Valor da causa (R$) associado ao processo.                                                                |
| `loss_probability`       | `0.75`                                          | Probabilidade estimada de perda (0–1).                                                                    |
| `loss_amount_estimate`   | `500000.00`                                     | Perda estimada em caso de derrota (R$).                                                                   |
| `loss_impact_analysis`   | `"Impacto moderado na geração de caixa"`        | Texto curto explicando impacto potencial para o fundo / cotistas.                                        |
| `main_facts`             | `"Discussão sobre inadimplência de locatário"`  | Resumo dos principais fatos alegados nas ações.                                                           |
| `last_update_date`       | `2025-11-01`                                    | Data da última atualização daquele registro / consolidação.                                              |
| `initiation_date`        | `2023-07-15`                                    | Data de início/distribuição do processo.                                                                 |
| `process_parts`          | `"ALMI11, Administrador X, Locatário Y"`        | Lista estruturada/normalizada das partes principais envolvidas.                                          |
| `created_at`             | `2025-10-01 12:34:56`                           | Carimbo de criação na base (auditoria técnica).                                                           |
| `updated_at`             | `2025-11-01 09:00:00`                           | Carimbo de última atualização na base (auditoria técnica).                                               |

Recomendações para o Narrator / Presenter:

- Usar **linguagem simples**, explicando termos jurídicos quando possível.
- Evitar alarmismo: contextualizar valores (ex.: “valor relativamente pequeno comparado ao patrimônio do fundo”).
- Deixar claro se os números são **estimativas** (ex.: `loss_probability`, `loss_amount_estimate`).

---

## 5. Exemplos de perguntas-alvo (Planner / Routing)

Sugestões de perguntas que **devem** cair em `fiis_processos`:

1. “O ALMI11 tem processos judiciais em aberto?”
2. “Quais processos existem contra o ALMI11?”
3. “Quantos processos o ALMI11 possui hoje?”
4. “Qual o status das ações judiciais do ALMI11?”
5. “Qual o valor total das causas dos processos do ALMI11?”
6. “Quais são os principais fatos dos processos do ALMI11?”
7. “Qual o risco de perda dos processos do ALMI11?”
8. “Quanto o ALMI11 pode perder se perder todas as ações judiciais?”
9. “Existe algum processo relevante contra o ALMI11 que possa afetar o fundo?”
10. “Resumo das ações judiciais envolvendo o ALMI11.”

Esses exemplos devem ser coerentes com:

- `intents.fiis_processos.tokens` e `intents.fiis_processos.phrases` na ontologia.
- `sample_questions` do schema `fiis_processos.schema.yaml`.

---

## 6. Notas para o Planner / Builder

- Entidade está no **bucket A** (grupo FIIs) e compartilha o mesmo `ticker` com as demais entidades de FIIs.
- As palavras-chave de ativação são, principalmente:
  `processo`, `processos`, `judicial`, `judiciais`, `acao`, `acoes`, `andamento`, `status`, `perda`, `condenacao`, `indenizacao`, `valor da causa` etc.
- A ontologia já exclui termos de risco quantitativo, preço, dividendos, ranking e notícias para evitar colisões com:
  - `fiis_financials_risk`
  - `fiis_precos`
  - `fiis_dividends` / `fiis_yield_history`
  - `fiis_noticias`
- Em caso de dúvida entre **risco jurídico** x **risco quantitativo de mercado**:
  - Presença de “processo / ação judicial / causa / tribunal / comarca” → tende a `fiis_processos`.
  - Presença de “Sharpe / volatilidade / beta / drawdown / mdd” → `fiis_financials_risk`.

---

## 7. Notas para o Narrator

- Sempre reforçar que se trata de **informações de processos judiciais**, que podem:
  - mudar de status,
  - ter decisões parciais,
  - ou acordos em andamento.
- Evitar inferir desfechos. Focar em:
  - Status,
  - risco estimado,
  - valores de causa,
  - fatos principais,
  - análise de impacto já pré-calculada em `loss_impact_analysis` quando disponível.
- Em perguntas amplas (“fiis com mais processos”), o Narrator pode:
  - ordenar por quantidade de processos ou por `process_value` / `loss_amount_estimate`,
  - deixar claro o critério usado.

