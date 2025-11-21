# ASK_PATCH_ETAPA_3 — Presenter & Facts alinhados à Ontologia

> **Milestone:** M12 / Etapa 3
> **Status:** Especificação de patch (nenhum código alterado ainda)
> **Escopo:** `Presenter` + contrato de `Facts` + alinhamento com ontologia/entities/templates

---

## 1. Objetivo da Etapa 3

Garantir que a camada **Presenter** e o contrato de **Facts**:

1. Sejam **100% alinhados** à ontologia e às entities:
   - `data/ontology/entity.yaml`
   - `data/entities/*/entity.yaml`
   - `data/contracts/entities/*.schema.yaml`
2. Entreguem um **FactsPayload canônico, estável e previsível** para:
   - Narrator (`Narrator.render`)
   - Explain / logs / observabilidade
   - Futuras camadas de front-end que consumam apenas `facts` + `results` + `meta`
3. Não introduzam heurísticas nem hardcodes:
   - Nenhuma regra “escondida” sobre entidades específicas dentro do código
   - Nenhuma inferência mágica que não esteja amparada em YAML / ontologia / contratos

> **Resumo:** Depois deste patch, o Presenter vira uma camada **fina e confiável**, que apenas orquestra:
> `plan + results + meta → facts + baseline + narrator_meta + answer`,
> sem “surpresas” nem acoplamentos implícitos.

---

## 2. Escopo do patch (arquivos permitidos)

O Codex **só poderá tocar** nos seguintes arquivos:

### Código de produção

- `app/presenter/presenter.py`
  (foco principal: `build_facts`, uso de `facts` dentro de `present`, contrato `FactsPayload` se definido aqui)

### YAML / ontologia / entities (apenas se necessário e de forma mínima)

- `data/ontology/entity.yaml`
  (apenas se for preciso corrigir chaves de alto nível usadas pelo Presenter / Facts)
- `data/entities/*/entity.yaml`
  (apenas correções de:
  - `result_key`
  - chaves esperadas pelo Presenter/Facts
  - flags ligadas a apresentação, se existirem)
- `data/entities/*/responses/*.md.j2`
  (apenas se o patch identificar referências a campos inexistentes/errados, e precisar alinhar com o contrato de Facts / rows)

### Documentação

- `docs/dev/RUNTIME_OVERVIEW.md`
  - atualizar seção que descreve **Facts** / Presenter, caso o patch ajuste o contrato
- Opcional (se for útil):
  - `docs/dev/FACTS_CONTRACT.md` (novo)
    - mini-doc descrevendo o contrato canônico de `facts` (ver seção 5)

> **Proibido nesta etapa:**
> - Alterar qualquer outro módulo (`orchestrator`, `planner`, `rag`, `narrator`, `formatter`, etc.)
> - Criar novas funções públicas fora do Presenter
> - Modificar payload do `/ask` (estrutura de `status`, `results`, `meta`, `answer`)

---

## 3. Estado atual (diagnóstico resumido)

Com base nos lotes analisados e no `RUNTIME_OVERVIEW.md`:

1. `presenter.present` já:
   - recebe `plan`, `orchestrator_results`, `meta`, `identifiers`, `aggregates`, `narrator`, flags do narrador;
   - chama `build_facts(...)`;
   - gera um `legacy_answer` determinístico via `render_answer(...)` + `render_rows_template(...)`;
   - aciona o Narrator, monta `narrator_meta` e decide `answer` final.

2. `Facts` hoje:
   - é usado em vários pontos (`facts.entity`, `facts.intent`, `facts.identifiers`, `facts.aggregates`, `facts.dict()` no Narrator);
   - porém o **contrato não está formalmente congelado**:
     - algumas chaves são esperadas implicitamente pelo Narrator;
     - o RUNTIME_OVERVIEW não descreve o contrato de `facts` de forma completa.

3. Integração com ontologia / entities:
   - `build_facts` usa de forma correta `plan['chosen']`, `result_key`, `rows`, `identifiers`, `aggregates`;
   - mas ainda existe espaço para:
     - amarrar explicitamente `facts.entity` / `facts.intent` à ontologia;
     - garantir que campos como `ticker`/`fund` (quando existirem) sejam sempre preenchidos de forma consistente (ou claramente `None` quando não forem aplicáveis).

---

## 4. Invariantes (regras que NÃO podem ser quebradas)

O patch **não pode**:

1. Mudar a assinatura pública de:
   - `present(question, plan, orchestrator_results, meta, identifiers, aggregates, narrator, narrator_flags, narrator_meta, explain=False)`
   - `build_facts(...)` (parâmetros de entrada)
2. Alterar a estrutura externa da resposta do `/ask`:
   - `status`, `results`, `meta`, `answer`
3. Alterar o contrato de `meta` já documentado, exceto:
   - para atualizar doc e comentários, se necessário, ligando melhor `facts` a `meta`
4. Criar heurísticas que “adivinhem” comportamento por entidade:
   - ex.: `if entity == "fiis_financials_risk": ...` dentro do Presenter → **proibido**
   - qualquer comportamento especial por entidade deve estar em `entity.yaml` / ontologia
5. Introduzir dependência do Presenter em:
   - `rag.yaml`
   - `narrator.yaml`
   - `planner_thresholds.yaml`
   além daquelas já existentes (apenas via `meta` / `facts`).

---

## 5. Contrato alvo para `Facts` (forma conceitual)

O objetivo do patch é consolidar um `FactsPayload` **canônico** com, no mínimo, as seguintes características:

1. **Identidade da rota**
   - `facts.intent`: intent canônico (`fiis_cadastro`, `fiis_financials_risk`, etc.)
   - `facts.entity`: entity canônica (mesmo nome lógico usado em `data/entities/*/entity.yaml`)
   - `facts.result_key`: igual ao `meta['result_key']` / `entity.yaml.result_key`

2. **Dados de saída**
   - `facts.rows`: lista de linhas já formatadas (após formatter), correspondendo exatamente ao `results[result_key]`
   - `facts.primary`: quando existir conceito de “linha principal” (ex.: 1 fundo numa lista), deve refletir de forma clara (ou ser `None` se não for aplicável)

3. **Contexto de pergunta e identificadores**
   - `facts.question`: a pergunta original (string)
   - `facts.identifiers`: dicionário com identificadores extraídos:
     - ex.: `ticker`, `tickers`, eventualmente outros identificadores inferidos (`periodo`, etc.), desde que já definidos em código/YAML
   - `facts.requested_metrics`: lista de métricas inferidas via ontologia/`ask.metrics_synonyms`

4. **Contexto de agregação**
   - `facts.aggregates`: espelho dos dados já inferidos pelo Orchestrator:
     - janela (`window` / `window_months`)
     - agregação (`agg`)
     - ordenação (`order`)
     - outros campos computados por `infer_params` e usados pelo builder

5. **Contexto de confiabilidade**
   - `facts.score`: score do planner (`planner_score`) para a rota escolhida
   - idealmente alinhado com `meta['planner_score']` para rastreabilidade

> **Importante:**
> O patch **não precisa** adicionar novos campos se eles já existem com outro nome.
> Em vez disso, o objetivo é:
> - padronizar nomes / acessos internos no Presenter,
> - documentar claramente o contrato existente,
> - garantir consistência entre `facts`, `meta` e `results`.

Se o Codex precisar ajustar o modelo `FactsPayload` (por exemplo, se for um `BaseModel` Pydantic no Presenter), as mudanças devem ser **apenas estruturais**, para consolidar esses pontos — nunca alterando comportamentos de negócio.

---

## 6. Escopo detalhado de mudanças permitidas

### 6.1. `app/presenter/presenter.py`

**Permitido:**

- Refatorar internamente `build_facts` para:
  - ler de forma mais explícita `plan['chosen']`, `result_key`, `rows`, `identifiers`, `aggregates`, `meta`
  - alinhar campos de `facts` a:
    - ontologia (`entity.yaml` / `data/ontology/entity.yaml`)
    - contrato de `meta`
- Ajustar o modelo `FactsPayload` (caso exista) para:
  - garantir que todos os campos usados em `present` e pelo Narrator estejam declarados
  - tornar opcionais (`Optional[...]`) campos que nem sempre existem
  - adicionar docstrings / comentários explicando o propósito de cada campo
- Melhorar a clareza do código:
  - renomear variáveis internas para algo autoexplicativo (sem mudar contratos externos)
  - adicionar comentários referenciando Guardrails Araquem v2.1.1
- Garantir que:
  - `facts.entity` e `facts.intent` sempre existam (mesmo que `None` em casos extremos)
  - `facts.rows` **sempre** reflita o conteúdo de `results[result_key]`
  - `facts.result_key` esteja alinhado ao `meta['result_key']` (quando disponível)

**Proibido:**

- Alterar a assinatura pública de `present` ou dos métodos utilitários chamados externamente
- Inserir `if/else` específicos para uma entidade ou intent
- Mudar comportamento de fallback de Narrator (já tratado na Etapa 2 / 4)

---

### 6.2. `data/ontology/entity.yaml`

**Somente se necessário** e de forma mínima:

- Ajustar nomes de intents/entities se houver divergência comprovada entre:
  - Planner
  - Orchestrator
  - Presenter
  - `data/entities/*/entity.yaml`
- Incluir comentários que ajudem a documentar:
  - qual campo da ontologia é usado pelo Presenter para construir `facts`

> Qualquer alteração aqui deve ser **cirurgicamente justificada** no diff (comentário no PR).

---

### 6.3. `data/entities/*/entity.yaml` + `responses/*.md.j2`

**Somente se o patch encontrar inconsistência**, por exemplo:

- Template acessando `{{ row.foo }}`, mas:
  - `foo` não existe na view / contrato `.schema.yaml`
  - ou não está em `columns`/`return_columns` do `entity.yaml`
- `result_key` incoerente com o que o Presenter espera para aquela entidade

Nesses casos, o patch pode:

- corrigir o campo / nome no template
- ajustar o `result_key` para refletir a nomenclatura usada end-to-end

> **Não é objetivo desta etapa** fazer um sweep geral de todos templates — isso é papel da Etapa 5.
> Aqui, só pode corrigir o que for estritamente necessário para o Presenter/Facts funcionar de forma consistente.

---

## 7. Antes/Depois esperado (conceitual)

### Antes

- `Facts` usado pelo Presenter e Narrator, mas:
  - contrato não documentado oficialmente
  - alguns campos implícitos
  - possível assimetria entre `facts`, `meta` e `results`

### Depois

- `FactsPayload` com contrato explícito (em código + doc):
  - identidade (`intent`, `entity`, `result_key`)
  - dados (`rows`, `primary`)
  - contexto (`question`, `identifiers`, `aggregates`, `requested_metrics`)
  - confiabilidade (`score`)
- Presenter:
  - mais legível
  - sem acoplamentos implícitos a entidades específicas
  - totalmente orientado por:
    - `plan`
    - `meta`
    - ontologia/entities/templates

---

## 8. Testes obrigatórios

O Codex deve garantir, no mínimo:

1. **Testes existentes continuam verdes**
   - `pytest` completo
   - Especial atenção a:
     - testes de Narrator
     - testes de RAG
     - testes de Orchestrator

2. **Adicionar novos testes (se ainda não existirem)**
   - Criar `tests/presenter/test_presenter_facts.py` ou equivalente com, pelo menos:
     - 1 cenário para entidade tabular (ex.: `fiis_cadastro` ou `fiis_precos`)
     - 1 cenário para entidade de risco (`fiis_financials_risk`)
   - Esses testes devem verificar:
     - `facts.intent` e `facts.entity` consistentes com o `plan`
     - `facts.rows` == `results[result_key]`
     - `facts.requested_metrics` consistente com `meta['requested_metrics']`
     - `facts.score` consistente com `meta['planner_score']` (quando presente)

> Caso já existam testes cobrindo parte disso, o Codex deve **apenas estender/adaptar** em vez de recriar tudo.

---

## 9. Como usar este arquivo com o Codex

Quando for enviar o patch desta etapa para o Codex:

1. Inclua **apenas**:
   - este arquivo: `docs/dev/ASK_PATCH_ETAPA_3.md`
   - os arquivos de código/YAML dentro do escopo (listados na seção 2)
2. Reforce no prompt:
   - que este é um patch **cirúrgico**
   - que o Codex **não pode** criar novos módulos nem alterar payload do `/ask`
   - que o contrato de `facts` deve ficar explícito, mas compatível com o runtime atual
3. Exija:
   - diff unificado (`git diff`) com contexto suficiente
   - resumo técnico no cabeçalho do PR
   - confirmação de que `pytest` foi rodado (mesmo que “not run (not requested)” seja mantido, seu ideal é rodar localmente)

---

## 10. Checklist de aceite da Etapa 3

A etapa será considerada concluída quando:

- [ ] `app/presenter/presenter.py` estiver:
  - [ ] mais legível
  - [ ] sem acoplamentos heurísticos por entidade
  - [ ] com contrato de `Facts` explícito
- [ ] `facts` estiver:
  - [ ] coerente com ontologia/entities
  - [ ] alinhado a `results`/`meta`
  - [ ] pronto para uso por Narrator e futuras camadas de front-end
- [ ] Documentação:
  - [ ] `RUNTIME_OVERVIEW.md` mencionar claramente o contrato de `facts`
  - [ ] (Opcional) `FACTS_CONTRACT.md` criado/atualizado
- [ ] `pytest` completo sem regressões
