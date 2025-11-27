# PROMPT_NEW_ENTITY (GENÉRICO) — MODELO OFICIAL ARAQUEM M8.x

Você é um assistente técnico trabalhando **NO CÓDIGO**, com acesso completo ao repositório Araquem.

Este prompt deve ser usado SEMPRE que uma nova entidade for criada, independentemente do tipo
(snapshot D-1, histórica, compute-on-read, composta, macro, índices, risco, cadastro, mercado, etc.).

-------------------------------------------------------------------------------
REGRAS GERAIS (OBRIGATÓRIAS)
-------------------------------------------------------------------------------

1. **NÃO invente estrutura de pastas nova.**
   Use SEMPRE:
   - `data/entities/<entity>/`
   - `data/contracts/entities/<entity>.schema.yaml`
   - `data/entities/catalog.yaml`
   - `data/ontology/entity.yaml`
   - `data/policies/*.yaml`
   - `data/ops/entities_consistency_report.yaml`
   - `docs/database/samples/*` (se houver amostra)

2. **NÃO altere o payload do `/ask`.**
   Guardrails Araquem v2.1.1 determina:
   - `{question, conversation_id, nickname, client_id}` é imutável.
   - Nenhum parâmetro novo pode ser criado.

3. **NÃO coloque heurísticas ou hardcodes.**
   Todo comportamento deve vir de:
   - YAML
   - SQL
   - Ontologia
   Nada de lógica nova escondida em Python.

4. **SIGA OS PADRÕES EXISTENTES**
   Baseie-se sempre em entidades reais:
   - `fiis_cadastro`
   - `fiis_financials_snapshot`
   - `fiis_financials_risk`
   - `fiis_financials_revenue_schedule`
   - `fiis_precos`
   - `fiis_rankings`
   - e qualquer outra entidade relevante

   Se algo não existir no padrão, **não invente**: copie a decisão mais próxima.

5. **SAÍDA SEMPRE EM FORMA DE ARQUIVOS**
   A resposta final do Codex deve conter:
   - PATCHES (diffs) **ou**
   - conteúdo completo de cada arquivo novo/editado.

   **Nunca** descreva apenas “o que deveria ser feito”.

-------------------------------------------------------------------------------
CONTEXTO DA NOVA ENTIDADE
-------------------------------------------------------------------------------

A entidade será chamada:

**`<entity_name>`**

E deve ser criada a partir de:

- uma VIEW existente **OU**
- um SELECT compute-on-read **OU**
- um modelo D-1 **OU**
- um dataset histórico **OU**
- uma fonte macro / índice / moedas **OU**
- outra fonte combinada

O arquivo de amostra (se existir) estará em:

`docs/database/samples/<entity_name>.csv`

Use o header e os tipos reais para derivar *todas* as colunas do `entity.yaml` e do schema.

-------------------------------------------------------------------------------
1) ANALISAR ENTIDADES EXISTENTES
-------------------------------------------------------------------------------

1. Leia as seguintes entidades como referência de estilo e padrões:
   - `data/entities/fiis_*`
   - `data/entities/history_*`
   - `data/entities/client_*`
   - qualquer entidade do mesmo domínio

2. Observe cuidadosamente:
   - Estrutura de `entity.yaml`
   - Campos obrigatórios (`entity`, `kind`, `version`, `source`, `grain`, `columns`, `defaults`)
   - Padrão REAL de templates:
     - Template principal: **`data/entities/<entity>/template.md`** (documentação)
     - Tabela Jinja: **`data/entities/<entity>/responses/table.md.j2`**
   - Padrão de hints: `data/entities/<entity>/hints.md`
   - Como contratos, ontologia, quality, catalog e consistency são referenciados.

**IMPORTANTE:**
`template.md` **NUNCA** deve ser `.j2` e **NUNCA** deve conter Jinja.
Ele é uma **documentação descritiva**, igual às outras entidades.

-------------------------------------------------------------------------------
2) CRIAR entity.yaml
-------------------------------------------------------------------------------

Criar o arquivo:

`data/entities/<entity_name>/entity.yaml`

O YAML deve conter:

- `entity: <entity_name>`
- `kind:`
  Use o padrão do projeto:
  - `snapshot` para entidades D-1
  - `metrics` para entidades históricas temporais
  - `composite` ou `snapshot` para views compostas
  - `macro`, `indexes`, `currency`, etc. conforme padrão existente

- `version: 1`

- `source:`
  - `schema: public`
  - `object: <entity_name>` (se view já existir)
  - OU USAR padrão compute-on-read conforme outras entidades M8.x.

- `grain:`
  - lista das colunas que definem a granularidade
  - exemplos:
    - histórico: `[ticker, ref_month]`
    - D-1: `[ticker]`
    - macro diária: `[ref_date]`

- `columns:`
  Preencher **uma entrada por coluna real**, derivada do CSV ou da view:

  ```yaml
  - name: <column_name>
    type: <string|numeric|boolean|date|datetime>
    nullable: <true|false>
    desc: "<descrição em PT-BR clara>"
```

* `defaults:`
  Usar padrão existente:

  ```yaml
  order_by:
    <col>: asc|desc
  ```

**NÃO invente seções novas.**
Apenas copie padrões reais.

---

3. CRIAR SCHEMA

---

Criar:

`data/contracts/entities/<entity_name>.schema.yaml`

Deve refletir **exactamente** as colunas do `entity.yaml`:

* tipos (`string`, `number`, `integer`, `boolean`, `string+format: date`, etc.)
* `nullable`
* `required`:

  * chaves naturais
  * demais campos essenciais

Siga o padrão das entidades existentes.

---

4. CRIAR TEMPLATES

---

4.1. Criar diretório:

`data/entities/<entity_name>/responses/`

4.2. Criar:

### a) `responses/table.md.j2`

* Tabela padrão com cabeçalhos Markdown
* Deve conter **somente Jinja**
* Seguir filtros EXISTENTES no projeto:

  * `date_br`
  * `currency_br`
  * `percentage_br`
  * `int_br`
  * `float_br`
  * etc.
* Tratar nulos com `"-"`
* Exibir mensagem amigável para `rows` vazios.

### b) `template.md`  (SEM `.j2`)

* Documento descritivo, estilo das outras entidades:

  * "## Descrição"
  * "## Exemplos de perguntas"
  * "## Respostas usando templates"

NÃO COLOCAR JINJA AQUI.

---

5. CRIAR HINTS

---

Criar:

`data/entities/<entity_name>/hints.md`

Adicionar perguntas reais para o Planner entender quando essa entidade deve ser acionada.

Use o estilo das outras entidades.

---

6. ONTOLOGIA

---

Modificar:

`data/ontology/entity.yaml`

Adicionar entrada para `<entity_name>`:

* blocos `intents`
* termos relevantes
* tokens
* entidades associadas
* domínios corretos

NÃO quebrar a ontologia atual.
Apenas incluir bloco novo usando o mesmo estilo.

---

7. QUALITY

---

Modificar:

`data/policies/quality.yaml`

Adicionar `<entity_name>` com:

* `not_null` (campos obrigatórios)
* `accepted_range` para:

  * percentuais
  * valores monetários
  * indicadores
  * rankings
  * datas
  * etc.

Usar arquivo CSV real para determinar limites plausíveis.

---

8. ENTITIES CONSISTENCY REPORT

---

Modificar:

`data/ops/entities_consistency_report.yaml`

Criar entrada:

* `has_schema: true`
* `has_hints: true`
* `in_quality_policy: true`
* `in_cache_policy:` copiar padrão de entidades equivalentes
* `in_rag_policy:` apenas se houver deny-intents em `rag.yaml`
* `in_narrator_policy:` normalmente `false` para entidades numéricas
* `has_ontology_intent: true`

---

9. CATALOG

---

Modificar:

`data/entities/catalog.yaml`

Adicionar `<entity_name>` com:

* `title:` descritivo em PT-BR
* `kind:` alinhado com o `kind` da entidade (snapshot, historical, metrics, composite, macro, etc.)
* `paths:` apontando para:

  * `entity_yaml`
  * `schema`
  * `quality_projection` (ou `null`/ausente, se ainda não existir)
* `coverage:` alinhado com:

  * cache_policy
  * rag_policy (true se houver alguma regra em `rag.yaml`, mesmo que seja deny)
  * narrator_policy
  * param_inference
* `identifiers.natural_keys:` com as chaves naturais
* `notes:` (pode ser vazio ou incluir anotações úteis)

Copiar o padrão de uma entidade equivalente já existente.

---

10. RAG E NARRATOR

---

10.1. `data/policies/rag.yaml`

* NÃO habilitar RAG para entidades numéricas/determinísticas.
* Se necessário, adicionar sua intent em `routing.deny_intents`.

10.2. `data/policies/narrator.yaml`

* Deixar `<entity_name>` com `llm_enabled: false`
* Ou simplesmente não incluir (seguir padrão real).

---

11. VALIDAÇÃO

---

Verificar:

* YAMLs bem formados
* caminhos corretos
* sem Jinja em `template.md`
* nenhum arquivo fora do padrão
* schema consistente com entity
* entidade registrada no `catalog.yaml`
* tudo referenciado em `entities_consistency_report.yaml`
* quality com limites plausíveis

---

## SAÍDA ESPERADA DO CODEX

Retorne **EXCLUSIVAMENTE**:

* PATCHES completos **OU**
* conteúdo completo para:

  * `data/entities/<entity_name>/entity.yaml`
  * `data/entities/<entity_name>/template.md`
  * `data/entities/<entity_name>/responses/table.md.j2`
  * `data/entities/<entity_name>/hints.md`
  * `data/contracts/entities/<entity_name>.schema.yaml`
  * trechos alterados de:

    * `data/entities/catalog.yaml`
    * `data/ontology/entity.yaml`
    * `data/policies/quality.yaml`
    * `data/ops/entities_consistency_report.yaml`
    * `data/policies/rag.yaml` (se negar intent)
    * `data/policies/narrator.yaml` (se necessário declarar disabled)

Nenhuma explicação.
Nenhum texto solto.
Apenas arquivos prontos para commit.
