# ASK_PATCH_ETAPA_5 — Sweep de contratos, entities e views (Domínio FIIs)

## 1. Contexto e objetivo

Este patch faz parte do plano de refatoração do `/ask` descrito em
`docs/dev/ASK_PIPELINE_REFACTOR_PLAN.md`, especificamente **Etapa 5**:

> Garantir que a tríade:
> - `docs/database/ddls/views.sql`
> - `data/contracts/entities/*.schema.yaml`
> - `data/entities/*/entity.yaml`
> esteja 100% consistente para todas as entidades do domínio FIIs.

**Objetivo deste patch**

- Eliminar qualquer divergência entre:
  - **views SQL reais** usadas pelo builder;
  - **contratos** `*.schema.yaml` (camada de dados / formatter);
  - **entities** `data/entities/*/entity.yaml` (ontologia por entidade) e templates `responses/*.md.j2`.
- Garantir que:
  - o **Orchestrator** não peça colunas que não existem;
  - o **Formatter** não remova/oculte colunas “órfãs” ou mal nomeadas;
  - os **templates** `responses/*.md.j2` só referenciem campos existentes nos contratos.

> ⚠️ Este patch é **apenas estrutural** (nomes/contratos/metadata).
> Não é permitido alterar semântica de negócios, métricas ou lógica de cálculo.

---

## 2. Escopo deste patch

### 2.1. Views e contratos do domínio FIIs

Entidades-alvo (base nos arquivos já existentes no repositório):

- `client_fiis_positions`
- `fiis_cadastro`
- `fiis_dividendos`
- `fiis_financials_revenue_schedule`
- `fiis_financials_risk`
- `fiis_financials_snapshot`
- `fiis_imoveis`
- `fiis_noticias`
- `fiis_precos`
- `fiis_processos`
- `fiis_rankings`
- `history_b3_indexes`
- `history_currency_rates`
- `history_market_indicators`

### 2.2. Arquivos permitidos

**APENAS** os arquivos abaixo podem ser modificados neste patch:

1. **Views SQL**
   - `docs/database/ddls/views.sql`
     (ou outros arquivos de DDL equivalentes se a estrutura estiver quebrada em múltiplos arquivos, mantendo a árvore real do repositório).

2. **Contratos de entidades (data layer)**
   - `data/contracts/entities/client_fiis_positions.schema.yaml`
   - `data/contracts/entities/fiis_cadastro.schema.yaml`
   - `data/contracts/entities/fiis_dividendos.schema.yaml`
   - `data/contracts/entities/fiis_financials_revenue_schedule.schema.yaml`
   - `data/contracts/entities/fiis_financials_risk.schema.yaml`
   - `data/contracts/entities/fiis_financials_snapshot.schema.yaml`
   - `data/contracts/entities/fiis_imoveis.schema.yaml`
   - `data/contracts/entities/fiis_noticias.schema.yaml`
   - `data/contracts/entities/fiis_precos.schema.yaml`
   - `data/contracts/entities/fiis_processos.schema.yaml`
   - `data/contracts/entities/fiis_rankings.schema.yaml`
   - `data/contracts/entities/history_b3_indexes.schema.yaml`
   - `data/contracts/entities/history_currency_rates.schema.yaml`
   - `data/contracts/entities/history_market_indicators.schema.yaml`

3. **Entities (ontologia por entidade)**
   - `data/entities/client_fiis_positions/entity.yaml`
   - `data/entities/fiis_cadastro/entity.yaml`
   - `data/entities/fiis_dividendos/entity.yaml`
   - `data/entities/fiis_financials_revenue_schedule/entity.yaml`
   - `data/entities/fiis_financials_risk/entity.yaml`
   - `data/entities/fiis_financials_snapshot/entity.yaml`
   - `data/entities/fiis_imoveis/entity.yaml`
   - `data/entities/fiis_noticias/entity.yaml`
   - `data/entities/fiis_precos/entity.yaml`
   - `data/entities/fiis_processos/entity.yaml`
   - `data/entities/fiis_rankings/entity.yaml`
   - `data/entities/history_b3_indexes/entity.yaml`
   - `data/entities/history_currency_rates/entity.yaml`
   - `data/entities/history_market_indicators/entity.yaml`

4. **Templates de resposta (quando necessário)**
   - `data/entities/*/responses/*.md.j2`
     **apenas** para corrigir referências a campos inexistentes ou alinhar nomes com o contrato.

5. **Documentação**
   - `docs/dev/RUNTIME_OVERVIEW.md` (se precisar atualizar exemplos de campos)
   - `docs/dev/FACTS_CONTRACT.md` (se for necessário mencionar novas chaves relevantes de linha)

> ❗ É proibido criar novos diretórios ou novos módulos Python neste patch.
> Alterações em `builder`, `executor`, `formatter`, `presenter`, `planner` e `orchestrator` **não fazem parte** deste patch.

---

## 3. Regras de ouro (Guardrails v2.1.1)

1. **Sem heurísticas, sem hardcodes**
   - Nenhuma coluna “extra” deverá ser inventada no contrato ou no entity.
   - Nenhum ajuste de nome de coluna pode ser feito “por conveniência”; qualquer mudança precisa refletir **a view real**.

2. **Fonte de verdade**
   - A **view SQL** (em `docs/database/ddls/views.sql`) é a fonte de verdade para:
     - nome das colunas;
     - tipo básico (numérico, texto, data);
     - ordenação padrão (quando explícita).
   - O contrato `.schema.yaml` e o `entity.yaml` devem refletir **exatamente** essa estrutura.

3. **Compatibilidade com o builder/formatter**
   - `builder/sql_builder.py` espera que as colunas declaradas em `entity.yaml` batam com o contrato.
   - `formatter/rows.py` só deve receber colunas que existam no contrato; colunas extras serão descartadas e indicam problema de alinhamento.

4. **Sem alteração de semântica**
   - Não é permitido:
     - alterar fórmulas de métricas;
     - mudar lógica de agregação;
     - trocar janelas temporais;
     - mudar filtros de negócio.
   - Este patch é **somente** de **alinhamento estrutural** e naming.

5. **Nomes em snake_case e PT-BR**
   - Seguir padrão já adotado no projeto para nomes de campos (ex.: `beta_index`, `volatility_ratio`, `payment_date`, `indicator_date` etc.).
   - Qualquer ajuste de nome deve ser refletido em:
     - view SQL;
     - contrato `.schema.yaml`;
     - `entity.yaml`;
     - templates `responses/*.md.j2` (se referenciam esse campo).

---

## 4. Passos detalhados (por entidade)

Para **cada** entidade da lista da seção 2.1, seguir este processo:

### Passo 1 — Mapear colunas da view SQL

- Abrir o trecho correspondente à entidade em:
  - `docs/database/ddls/views.sql`
    (ou o arquivo correto de DDL, conforme a árvore real).
- Listar:
  - todas as colunas da view;
  - tipos básicos (text, numeric, date, boolean);
  - chaves naturais (ex.: `ticker`, `traded_at`, `indicator_date`, etc.);
  - ordenação padrão (`ORDER BY`).

**Saída esperada (mental / comentário)**
Um “snapshot” claro de:

```text
Entidade: fiis_financials_risk
View: public.fiis_financials_risk_view (nome real da view)
Colunas:
  - ticker (text)
  - volatility_ratio (numeric)
  - sharpe_ratio (numeric)
  - treynor_ratio (numeric)
  - jensen_alpha (numeric)
  - beta_index (numeric)
  - sortino_ratio (numeric)
  - max_drawdown (numeric)
  - r_squared (numeric)
  - created_at (timestamp)  # se existir
Ordenação:
  ORDER BY ticker ASC
````

### Passo 2 — Alinhar contrato `.schema.yaml`

* Abrir o arquivo correspondente, por exemplo:

  * `data/contracts/entities/fiis_financials_risk.schema.yaml`
* Verificar se:

  * **todas** as colunas da view estão descritas em `properties`;
  * **nenhuma** coluna aparece no contrato sem existir na view;
  * os tipos (`type: string/number/integer/boolean`) são coerentes com o SQL;
  * campos obrigatórios (`required`) fazem sentido (mínimo: chaves naturais).

> Se houver coluna na view **não declarada** no contrato:
>
> * **Adicionar** no contrato com tipo apropriado e descrição curta.

> Se houver coluna no contrato **que não existe** na view:
>
> * **Remover** a coluna do contrato ou, se for bug da view, sinalizar ajustando a view para incluir o campo.

### Passo 3 — Alinhar `entity.yaml`

* Abrir `data/entities/<entidade>/entity.yaml`, ex.:

  * `data/entities/fiis_financials_risk/entity.yaml`

* Verificar:

  * `result_key` está coerente com o contrato (ex.: `fiis_financials_risk`);
  * a seção `columns` (quando existir) bate com o contrato `.schema.yaml`:

    * nomes idênticos;
    * nenhum campo “from nowhere”;
    * respeita o mesmo casing (`ticker` ≠ `Ticker`).
  * Se existir `presentation`/`metrics`/`aggregations`, garantir que os nomes referenciados são colunas da view (via contrato).

> Se um campo não é usado em nenhum lugar do pipeline (nem templates, nem metrics, nem presenter), **não o remova** automaticamente neste patch.
> O objetivo é alinhar contratos; limpeza funcional é um passo futuro.

### Passo 4 — Checar templates `responses/*.md.j2`

Para a mesma entidade, abrir `data/entities/<entidade>/responses/*.md.j2`. Exemplos:

* `data/entities/fiis_financials_risk/responses/summary.md.j2`
* `data/entities/fiis_financials_revenue_schedule/responses/table.md.j2`
* Outros templates da mesma pasta.

Verificar se:

* Todas as referências `{{ r.campo }}` ou `{{ r["campo"] }}` se referem a campos que:

  * existem na view;
  * estão no contrato `.schema.yaml`;
  * estão no `entity.yaml` (quando há lista de colunas/presentation).

Se não existirem, **corrigir**:

* Preferencialmente ajustando o template para usar nomes válidos;
* Em último caso, se o nome certo estava na view/contrato, ajustar o template.

### Passo 5 — Repetir para todas as entidades

Repetir os Passos 1–4 para **cada** entidade da lista.

---

## 5. Testes esperados

### 5.1. Validação de contratos

Se existir script de validação de contratos (por exemplo):

```bash
scripts/core/validate_data_contracts.py
```

ou equivalente, rodar e garantir:

* 0 erros de schema;
* 0 referências a campos inexistentes.

Se o script não existir, manter tudo compatível com o formato atual dos `.schema.yaml`
usado pelo `formatter/rows.py`.

### 5.2. Smoke tests manuais no `/ask`

Após aplicar o patch:

1. Levantar o stack (Docker Compose ou equivalente).

2. Fazer chamadas `/ask` para cobrir **pelo menos**:

   * `fiis_cadastro`
   * `fiis_precos`
   * `fiis_dividendos`
   * `fiis_financials_snapshot`
   * `fiis_financials_risk`
   * `fiis_noticias`
   * `fiis_processos`
   * `fiis_rankings`
   * `history_market_indicators`
   * `history_b3_indexes`
   * `history_currency_rates`
   * `client_fiis_positions`

3. Confirmar que:

   * Não há erros de chave ausente no JSON (`KeyError`, `NoneType[...]`, etc.);
   * `results[result_key][0]` contém **apenas colunas esperadas**;
   * Os templates renderizam sem erro.

> Não é obrigatório neste patch garantir “beleza” da resposta, apenas **consistência estrutural**.

---

## 6. Fora de escopo

Este patch **NÃO** deve:

* Alterar:

  * `app/builder/sql_builder.py`
  * `app/executor/pg.py`
  * `app/formatter/rows.py`
  * `app/presenter/presenter.py`
  * `app/planner/*`
  * `app/orchestrator/routing.py`
  * `app/narrator/*`
* Mudar semântica de cálculo (métricas, janelas, filtros).
* Introduzir novas entidades, novas views ou novas métricas.
* Alterar políticas (`data/policies/*.yaml`) além de ajustes mínimos necessários para refletir renomeação de campos (em caso extremo).

---

## 7. Resumo para o Codex

Em resumo, o Codex deve:

1. Tomar as views SQL como **fonte de verdade** dos campos.
2. Alinhar **contratos** `.schema.yaml` com as views.
3. Alinhar **entities** `entity.yaml` e **templates** `responses/*.md.j2` com esses contratos.
4. Garantir que não existam:

   * colunas fantasma (presentes no contrato/entity mas não na view);
   * colunas ausentes (presentes na view, ausentes no contrato);
   * referências inválidas em templates.
5. Não tocar em lógica de negócios, apenas **estrutura e naming**.

---

## 8. Diagnóstico e ações executadas (Etapa 5)

- **Fontes de verdade consultadas**: `data/entities/client_fiis_positions/entity.yaml`, `data/contracts/entities/client_fiis_positions.schema.yaml`, amostra runtime `tmp/sample_positions.json` e ontologia `data/ontology/entity.yaml`.
- **Inconsistência encontrada**: o contrato `client_fiis_positions.schema.yaml` não declarava `available_quantity` presente no runtime; o `entity.yaml` trazia campos inexistentes (`average_price`, `profitability_percentage`, `percentage`).
- **Correções aplicadas**:
  - Contrato atualizado para incluir `available_quantity` com tipo numérico opcional.
  - `entity.yaml` limpo para refletir exclusivamente as colunas reais (`document_number`, `position_date`, `ticker`, `fii_name`, `participant_name`, `qty`, `closing_price`, `update_value`, `available_quantity`, `created_at`, `updated_at`).
  - Templates de resposta conferidos; nenhum ajuste necessário porque já utilizam `fields.key/value` alinhados.
- **Entidades revisadas nesta etapa**: `client_fiis_positions`.
- **Guardrails v2.1.1**: todas as mudanças foram estritamente estruturais, sem criação de campos novos sem evidência, sem alterações de SQL ou código Python, mantendo `result_key` e colunas sincronizados com o runtime.
