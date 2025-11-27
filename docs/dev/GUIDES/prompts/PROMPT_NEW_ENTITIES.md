# PROMPT_NEW_ENTITIES.md

Você é um assistente técnico trabalhando NO CÓDIGO, com acesso completo ao repositório Araquem.

SEMPRE SIGA ESTAS REGRAS GERAIS:

1. NÃO invente estrutura de pastas nova. Reaproveite SEMPRE:
   - `data/entities/*`
   - `data/contracts/entities/*`
   - `data/ontology/entity.yaml`
   - `data/policies/*.yaml`
   - `data/ops/entities_consistency_report.yaml`
   - `docs/database/samples/*`
2. NÃO mude o payload do `/ask`. O Guardrails Araquem v2.1.1 define que:
   - o payload é imutável: `{question, conversation_id, nickname, client_id}`
   - não existem novos parâmetros mágicos.
3. NÃO coloque hardcodes nem heurísticas em código Python.
   - Tudo que for comportamento deve estar em **YAML + SQL + ontologia**.
4. Use como referência de padrão:
   - outras entidades já implementadas de FIIs (ex.: `fiis_dividendos`, `fiis_financials_risk`, `fiis_financials_revenue_schedule`, `fiis_precos`, `fiis_cadastro`, etc.)
   - `ARAQUEM_STATUS_2025.md` e Guardrails Araquem em `docs/`.
5. Saída SEMPRE em forma de:
   - **PATCHES (diffs)** ou
   - **CONTEÚDO COMPLETO DE ARQUIVOS**
   nunca apenas descrições genéricas.

---

## CONTEXTO ESPECÍFICO DESTE PEDIDO

Queremos PLUGAR uma nova entidade chamada **fiis_yield_history**, seguindo o padrão de “entidade de métricas histórica (M8 — compute-on-read)”.

IMPORTANTE:

- A view **já existe no banco** com a seguinte assinatura lógica:
  - schema: `public`
  - nome: `fiis_yield_history`
  - colunas:
    - `ticker`        (string/text)
    - `ref_month`     (date) – sempre primeiro dia do mês (`date_trunc('month', ...)::date`)
    - `dividends_sum` (numeric) – soma dos dividendos pagos no mês
    - `price_ref`     (numeric, nullable) – último preço de fechamento disponível no mês
    - `dy_monthly`    (numeric, nullable) – `dividends_sum / price_ref`, se `price_ref > 0`
- NÃO CRIE SQL novo do zero. Se o projeto tiver um lugar padrão para scripts SQL de views, apenas siga o padrão existente. Caso não tenha, **NÃO invente pasta nova**.

Existe um arquivo de amostra de dados:

- `docs/database/samples/fiis_yield_history.csv`

Use esse arquivo para entender a distribuição real dos dados (incluindo outliers de DY) e calibrar faixas de qualidade.

Objetivo:
Implementar COMPLETAMENTE a entidade **fiis_yield_history** em todos os pontos necessários (`entity`, `schema`, `template`, `table`, `hints`, ontologia, quality, entities_consistency_report, etc.), **sem quebrar NADA existente**.

---

## 1) ENTENDER O PADRÃO DAS ENTIDADES EXISTENTES

1.1. Abra e estude as pastas das entidades já existentes, especialmente:

- `data/entities/fiis_dividendos/*`
- `data/entities/fiis_financials_risk/*`
- `data/entities/fiis_financials_revenue_schedule/*`
- `data/entities/fiis_precos/*`
- `data/entities/fiis_cadastro/*`

1.2. Observe:

- Estrutura de `entity.yaml` (campos obrigatórios, seções como: `entity`, `kind`, `version`, `source`, `grain`, `columns`, `defaults`, etc.)
- **Padrão REAL de nome e localização de templates**:
  - template principal da entidade:
    - `data/entities/<entity>/template.md`  ← SEM `.j2`
  - tabela:
    - `data/entities/<entity>/responses/table.md.j2`
- Padrão de `hints`:
  - `data/entities/<entity>/hints.md`
- Como a entidade é referenciada em:
  - `data/contracts/entities/*.schema.yaml`
  - `data/ontology/entity.yaml`
  - `data/policies/quality.yaml`
  - `data/policies/rag.yaml` (se aplicável)
  - `data/policies/narrator.yaml` (se aplicável)
  - `data/ops/entities_consistency_report.yaml`

**NÃO invente estrutura diferente.** Replique o padrão.

> ⚠️ **Nunca crie** `responses/template.md.j2` ou `template.md.j2`.
> O template principal é sempre `template.md` na raiz da entidade.

---

## 2) CRIAR A ENTIDADE `fiis_yield_history` (`entity.yaml`)

2.1. Crie o arquivo:

- `data/entities/fiis_yield_history/entity.yaml`

2.2. Baseando-se nas entidades de métricas já existentes (como `fiis_financials_risk` e `fiis_financials_revenue_schedule`), defina:

- `entity: fiis_yield_history`
- `kind: metrics` (ajuste para o valor correto se o projeto já tiver um padrão específico para entidades históricas de métricas)
- `version: 1`
- `source`:
  - `schema: public`
  - `object: fiis_yield_history`   # view que já existe no banco
- `grain`:
  - `ticker`
  - `ref_month`
- `columns` (tipos no padrão do projeto):
  - `ticker`:
    - `type: string`
    - `nullable: false`
    - `desc: "código do FII (AAAA11)"`
  - `ref_month`:
    - `type: date`
    - `nullable: false`
    - `desc: "mês de referência (primeiro dia do mês)"`
  - `dividends_sum`:
    - `type: numeric`
    - `nullable: false`
    - `desc: "soma dos dividendos pagos no mês (R$ por cota)"`
  - `price_ref`:
    - `type: numeric`
    - `nullable: true`
    - `desc: "preço de referência da cota no mês (última cotação disponível no mês)"`
  - `dy_monthly`:
    - `type: numeric`
    - `nullable: true`
    - `desc: "dividend yield mensal (dividends_sum / price_ref)"`

- `defaults`:
  - `order_by` (siga o padrão real do projeto, algo como):
    - `ref_month: desc`
    - `ticker: asc`

Use exatamente o mesmo estilo de indentação, comentários e campos usados nas demais entidades de FIIs.

> 🔎 Se for usar `aggregations`/janelas:
> - COPIE o formato de uma entidade EXISTENTE que já tenha esse bloco.
> - Se não houver nenhuma referência confiável, **não invente formato novo**. Melhor não declarar `aggregations` do que colocar YAML que ninguém consome.

---

## 3) CRIAR O SCHEMA DA ENTIDADE (`fiis_yield_history.schema.yaml`)

3.1. Crie o arquivo:

- `data/contracts/entities/fiis_yield_history.schema.yaml`

3.2. Siga o padrão das outras entidades de métricas. O schema deve descrever:

- `ticker`: string
- `ref_month`: date (use o mesmo formato que o projeto já utiliza — por exemplo: `type: string` + `format: date`, se for o caso)
- `dividends_sum`: number
- `price_ref`: number (nullable: true, se o padrão permitir)
- `dy_monthly`: number (nullable: true)

3.3. Marque as propriedades obrigatórias:

- `ticker`
- `ref_month`
- `dividends_sum`

---

## 4) CRIAR OS TEMPLATES DE RESPOSTA

4.1. Crie o diretório (se ainda não existir):

- `data/entities/fiis_yield_history/responses/`

4.2. Crie **exatamente** estes arquivos:

### a) `data/entities/fiis_yield_history/responses/table.md.j2`

- Padrão: tabela em Markdown com as colunas:
  - Ticker
  - Mês ref.
  - Dividendos (R$)
  - Preço ref. (R$)
  - DY mensal
- Use os mesmos filtros já existentes no projeto para:
  - datas (ex.: `date_br`, se for o caso)
  - números monetários (ex.: `currency_br`)
  - percentuais (ex.: o filtro real usado em outras entidades — por exemplo `percentage_br` ou equivalente. NÃO invente nome novo; copie de outra tabela.)
- Exemplo de lógica (ADAPTE PARA O PADRÃO REAL DO PROJETO):
  - Se não houver linhas, mostrar uma mensagem amigável.
  - Se `price_ref` ou `dy_monthly` forem nulos, exibir `"-"` no lugar.

### b) `data/entities/fiis_yield_history/template.md`

- Este é o **template principal da entidade** (sem `.j2`).
- Deve conter um resumo executivo objetivo, no mesmo estilo das outras entidades (PT-BR), e:
  - identificar se a resposta é para 1 ticker ou vários (usando a lista de tickers dos `rows`)
  - explicar brevemente o que é o histórico de DY mensal
  - incluir a tabela renderizada via:
    - `{% include "responses/table.md.j2" %}`
  - tratar o caso de “nenhum dado encontrado” com uma mensagem amigável

> ⚠️ **Nunca crie:** `data/entities/fiis_yield_history/responses/template.md.j2`.
> O template principal é SEMPRE `template.md` na raiz da entidade.

---

## 5) CRIAR HINTS PARA O PLANNER (`hints.md`)

5.1. Crie:

- `data/entities/fiis_yield_history/hints.md`

5.2. Adicione perguntas reais que façam o Planner considerar essa entidade, por exemplo (PT-BR, respeitando o estilo existente):

- "Qual foi o DY mensal do {{ticker}} em {{mês/ano}}?"
- "Como tem sido a evolução do DY do {{ticker}} nos últimos 12 meses?"
- "Quais FIIs tiveram maior DY médio nos últimos 6 meses?"
- "Mostre o histórico de dividendos e DY do {{ticker}}."
- "Liste os FIIs com DY consistente ao longo dos últimos 24 meses."

Use o formato e convenções de hints já existentes (veja `hints` de `fiis_financials_risk` e `fiis_financials_revenue_schedule`).

---

## 6) ATUALIZAR A ONTOLOGIA (`data/ontology/entity.yaml`)

6.1. Abra:

- `data/ontology/entity.yaml`

6.2. Adicione a nova entidade **fiis_yield_history**:

- associando ao domínio adequado (provavelmente o mesmo de `fiis_dividendos` / `fiis_financials_revenue_schedule`)
- definindo:
  - intents relevantes (ex.: yield histórico, DY mensal, evolução de DY)
  - vínculos com a entidade `fiis_dividendos` (se houver algum campo de referência/relacionamento no padrão da ontologia atual)

6.3. NÃO deforme a ontologia existente. Apenas inclua o novo bloco seguindo o estilo atual.

---

## 7) ATUALIZAR QUALITY (`data/policies/quality.yaml`)

7.1. Abra:

- `data/policies/quality.yaml`

7.2. Inclua **fiis_yield_history** nas seções relevantes (datasets/entities, ou equivalente), seguindo exatamente o padrão das outras entidades de métricas.

7.3. Use o arquivo de amostra `docs/database/samples/fiis_yield_history.csv` para:

- ver a distribuição de `dy_monthly`
- detectar outliers (ex.: valores muito altos por eventos não recorrentes)

7.4. Defina faixas de qualidade (`accepted_range`) razoáveis, por exemplo (AJUSTE BASEADO NOS DADOS REAIS DO CSV):

- `dividends_sum`:
  - mínimo `>= 0`
- `price_ref`:
  - mínimo `> 0`
- `dy_monthly`:
  - mínimo `>= 0`
  - máximo em torno de uma faixa plausível (por exemplo, algo como `0.00–0.10` para DY normal mensal),
    mas permitindo outliers se o projeto já tiver alguma política de tolerância.

Ajuste essas faixas a partir dos percentis dos dados reais da amostra, seguindo o mesmo critério que foi usado, por exemplo, em `fiis_financials_revenue_schedule` e nas entidades macro.

---

## 8) ATUALIZAR ENTITIES_CONSISTENCY_REPORT (`data/ops/entities_consistency_report.yaml`)

8.1. Abra:

- `data/ops/entities_consistency_report.yaml`

8.2. Adicione a entrada de **fiis_yield_history**, marcando:

- `has_schema: true`
- `has_quality_projection:` conforme padrão (se houver projection para essa entidade)
- `in_quality_policy: true`
- `in_cache_policy:` (copiar lógica das outras entidades de FIIs)
- `in_rag_policy: true` **somente se** houver regra explícita em `rag.yaml` (ex.: em `deny_intents`)
- `in_narrator_policy: false` (para entidades numéricas, tipicamente Narrator fica desligado)
- `has_ontology_intent: true`
- `has_param_inference:` conforme o padrão das demais entidades de métricas

Notas recomendadas (exemplo):

- "entidade historical mensal de dividend yield; consultas via SQL (RAG negado)"
- "espera janelas temporais padrão via param_inference"

IMPORTANTE:

- Como `fiis_yield_history` é uma entidade **puramente numérica/histórica**, NÃO habilite RAG para ela.
  Se precisar, adicione a intent correspondente em `routing.deny_intents` de `rag.yaml`, tal como já é feito com `fiis_dividendos` e `fiis_precos`.

---

## 9) POLÍTICAS DE RAG E NARRATOR (SE NECESSÁRIO)

9.1. Veja:

- `data/policies/rag.yaml`
- `data/policies/narrator.yaml`

9.2. Regras para **entidades numéricas como `fiis_yield_history`**:

- **RAG**
  - Não adicionar em `allow_intents`.
  - Se necessário, adicionar a intent/entidade de `fiis_yield_history` em `routing.deny_intents`, seguindo o mesmo padrão de `fiis_dividendos`, `fiis_precos`, etc.
- **Narrator**
  - Não habilitar LLM para essa entidade (mantê-la fora do Narrator ou marcada como `llm_enabled: false` se houver configuração centralizada).

**Nunca** misture lógica numérica determinística com RAG/Narrator sem um motivo arquitetural muito bem documentado no Guardrails.

---

## 10) VALIDAÇÃO

10.1. Garanta que:

- O arquivo `entity.yaml` é válido e consistente com o padrão das outras entidades de FIIs.
- O schema YAML compila (estrutura idêntica às demais).
- Todos os caminhos de arquivos estão corretos.
- Não há duplicação de chaves em YAML.
- O template principal é **`template.md`** na raiz da entidade, e **NÃO** existe `responses/template.md.j2`.

10.2. Liste ao final TUDO o que foi criado/modificado, por exemplo:

- `[NEW] data/entities/fiis_yield_history/entity.yaml`
- `[NEW] data/entities/fiis_yield_history/template.md`
- `[NEW] data/entities/fiis_yield_history/hints.md`
- `[NEW] data/entities/fiis_yield_history/responses/table.md.j2`
- `[NEW] data/contracts/entities/fiis_yield_history.schema.yaml`
- `[MOD] data/ontology/entity.yaml`
- `[MOD] data/policies/quality.yaml`
- `[MOD] data/ops/entities_consistency_report.yaml`
- `[MOD?] data/policies/rag.yaml` (apenas para negar a intent de fiis_yield_history, se necessário)
- `[NO CHANGE] data/policies/narrator.yaml` (salvo se o padrão atual exigir explicitação, mas sem habilitar LLM)

---

## RESUMO DO QUE VOCÊ DEVE ENTREGAR

- Diffs ou conteúdo completo de:

  - `data/entities/fiis_yield_history/entity.yaml`
  - `data/entities/fiis_yield_history/template.md`
  - `data/entities/fiis_yield_history/responses/table.md.j2`
  - `data/entities/fiis_yield_history/hints.md`
  - `data/contracts/entities/fiis_yield_history.schema.yaml`
  - `data/ontology/entity.yaml` (apenas os trechos alterados)
  - `data/policies/quality.yaml` (apenas os trechos alterados)
  - `data/ops/entities_consistency_report.yaml` (apenas os trechos alterados)
  - `data/policies/rag.yaml`, SE (e somente se) for necessário negar a intent de `fiis_yield_history`.

NÃO responda com explicações genéricas.
Responda com os ARQUIVOS E PATCHES prontos para eu aplicar no repositório.
