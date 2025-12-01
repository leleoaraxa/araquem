Perfeito, então vamos executar os 3 passos combinados, ainda 100% em modo “design”, sem tocar em código.

---

## 1️⃣ Documento: `docs/dev/NARRATOR_SHADOW_CONTRACT.md`

Sugestão de conteúdo completo:

```markdown
# NARRATOR SHADOW — CONTRATO DE OBSERVABILIDADE

> **Versão:** 2025-12-01
> **Escopo:** definir o contrato lógico (dados, condições, responsabilidades) para o **shadow logging** do Narrator no Araquem, sem alterar o contrato do `/ask`.

---

## 1. Objetivo

O **Narrator Shadow** é um mecanismo de observabilidade que registra, em background, tudo o que aconteceu numa chamada do `/ask` envolvendo o Narrator (LLM ou não), **sem impactar**:

- o payload do endpoint `/ask` (imutável);
- a resposta entregue ao cliente final;
- a performance em produção (via sampling controlado).

Ele serve para:

- depurar decisões do Planner/Router (qual entidade foi escolhida e por quê);
- entender como o Narrator está usando (ou não) RAG + dados;
- coletar exemplos reais para ajustes de prompt, thresholds e policies;
- avaliar o impacto de ligar o LLM “valendo” para determinadas entidades.

---

## 2. Posição no pipeline `/ask`

Linha de produção simplificada:

```mermaid
flowchart TD

A[/POST /ask/] --> B[Orchestrator / Routing]
B --> C[Planner]
C --> D[Builder + Executor (SQL)]
D --> E[Formatter (rows -> resposta bruta)]
E --> F[Presenter (facts + baseline)]
F --> G[Narrator (LLM ou determinístico)]
G --> H[Presenter (merge final)]
H --> I[Shadow Collector (Narrator Shadow)]
I --> J[Resposta para o cliente]
```

Pontos importantes:

1. O **Shadow Collector** é chamado **somente** no Presenter, depois que:

   * o Planner já decidiu `intent/entity`;
   * o banco já foi consultado (quando aplicável);
   * o Narrator já rodou (LLM ou modo determinístico);
   * a resposta final já foi construída para o cliente.

2. O Shadow **não altera**:

   * o conteúdo de `answer`;
   * o meta retornado ao cliente;
   * o contrato JSON do `/ask`.

Ele apenas **lê** os metadados internos e os escreve em um sink (arquivo JSONL, por exemplo), obedecendo às policies.

---

## 3. Quando o Shadow é disparado

A decisão de registrar um evento de shadow é feita com base em:

1. **Policy do Narrator (`data/ops/narrator.yaml`)**

   * Só entra em shadow se, para a entidade em questão:

     ```yaml
     narrator:
       entities:
         fiis_financials_risk:
           llm_enabled: true
           shadow: true
           ...
     ```

   * Se `llm_enabled: false` ou `shadow: false`, o evento é **ignorado** pelo Shadow Collector.

2. **Policy global de shadow (`data/ops/narrator_shadow.yaml`)**

   Exemplo de chaves relevantes:

   ```yaml
   narrator_shadow:
     enabled: true
     environment_allowlist: [dev, staging]
     sink:
       kind: file
       path_pattern: "data/observability/narrator_shadow_%Y%m%d.jsonl"
     sampling:
       default:
         rate: 0.1
         only_when_llm_used: true
         only_when_answer_nonempty: true
         always_on_llm_error: true
       entities:
         fiis_financials_risk:
           rate: 0.5
         fiis_noticias:
           rate: 0.3
     redaction:
       enabled: true
       private_entities:
         - client_fiis_positions
         - client_fiis_dividends_evolution
         - client_fiis_performance_vs_benchmark
       mask_patterns:
         cpfs: true
         emails: true
         document_numbers: true
   ```

   O Shadow Collector só grava se:

   * `narrator_shadow.enabled == true`;
   * `environment` atual ∈ `environment_allowlist`;
   * as regras de `sampling` forem satisfeitas (ver abaixo).

3. **Regras de sampling**

   Para cada evento, o collector:

   * resolve a config de sampling:

     * se existir `sampling.entities[entity]`, usa essa;
     * caso contrário, usa `sampling.default`.

   * aplica as condições:

     * `only_when_llm_used`
       Se `true`, só loga se o Narrator efetivamente tentou usar LLM
       (ex.: `narrator.strategy` ∈ {`llm_shadow`, `llm_primary`, `llm_failed`}).

     * `only_when_answer_nonempty`
       Se `true`, descarta casos em que `presenter.answer_final` está vazio.

     * `always_on_llm_error`
       Se `true`, **grava sempre** quando `narrator.error != null`,
       independentemente de `rate`.

   * aplica o `rate`:

     * sorteio uniforme `[0,1)`;
     * se `< rate` → grava; caso contrário, descarta.

4. **Privacidade / entidades privadas**

   * Para entidades em `narrator_shadow.redaction.private_entities`, o collector:

     * aplica **redaction mais agressiva** (máscara de CPFs, emails, documentos, etc.);
     * nunca grava identificadores diretos (ex.: `document_number` completo).

   * Em caso de conflito entre sampling e privacidade, a regra é:

     * **melhor errar por menos dados** (pode reduzir rate ou bloquear completamente shadow para certas entidades privadas no futuro).

---

## 4. Contrato do registro de shadow (`NarratorShadowRecord`)

Cada evento de shadow é gravado como **uma linha JSON** (JSONL), com a seguinte estrutura lógica:

```jsonc
{
  "timestamp": "2025-12-01T10:15:23.456Z",
  "environment": "dev",
  "request": { ... },
  "routing": { ... },
  "facts": { ... },
  "rag": { ... },
  "narrator": { ... },
  "presenter": { ... },
  "shadow": { ... }
}
```

### 4.1. Campo `timestamp`

* ISO 8601 com milissegundos, em UTC.
* Ex.: `"2025-12-01T10:15:23.456Z"`.

### 4.2. Campo `environment`

* String curta identificando o ambiente lógico:

  * `"dev"`, `"staging"`, `"prod"`, etc.
* Deve coincidir com o valor usado em `observability.yaml`.

---

## 5. Bloco `request`

Origem: payload do `/ask`, sem modificações de contrato.

```jsonc
"request": {
  "question": "como interpretar uma notícia negativa sobre um FII?",
  "conversation_id": "abc123",
  "nickname": null,
  "client_id": null
}
```

Regras:

* **Nunca** adicionar campos ao contrato original.
* É permitido logar `null` para `nickname`/`client_id`.
* Dados sensíveis devem ser redigidos se `redaction.enabled == true`.

---

## 6. Bloco `routing`

Origem: meta do Planner / Orchestrator.

Exemplo:

```jsonc
"routing": {
  "intent": "fiis_noticias",
  "entity": "fiis_noticias",
  "planner_score": 1.5039417027464652,
  "tokens": ["como","interpretar","uma","noticia","negativa","sobre","um","fii"],
  "thresholds": {
    "min_score": 0.8,
    "min_gap": 0.1,
    "gap": 1.9714417027464652,
    "accepted": true,
    "source": "final"
  }
}
```

Campos recomendados:

* `intent`, `entity`: escolhidos pelo Planner;
* `planner_score`: score final após fusão base+RAG;
* `tokens`: lista de tokens normalizados;
* `thresholds`: snapshot da decisão (`min_score`, `min_gap`, `gap`, `accepted`, `source`).

---

## 7. Bloco `facts`

Origem: Formatter + Executor (resumo dos dados retornados).

Exemplo para `fiis_noticias`:

```jsonc
"facts": {
  "entity": "fiis_noticias",
  "rows_total": 3,
  "rows_sample": [
    {
      "ticker": "HGLG11",
      "source": "Infomoney",
      "title": "FII X tem vacância recorde",
      "published_at": "2025-11-20T10:00:00",
      "tags": ["vacância", "resultado", "risco"]
    }
  ],
  "aggregates": {
    "agg": null,
    "window": null,
    "limit": null,
    "order": null
  }
}
```

Regras:

* `rows_total`: número total de linhas retornadas pelo banco.
* `rows_sample`: até `N` linhas (controlado por policy), com redaction aplicada.
* Para entidades privadas, evitar colunas sensíveis (ex.: `document_number`).
* `aggregates`: snapshot do contrato de agregação (quando aplicável).

---

## 8. Bloco `rag`

Origem: meta do RAG utilizado pelo Narrator.

Exemplo:

```jsonc
"rag": {
  "enabled": true,
  "collections": ["fiis_noticias","concepts-fiis","concepts-risk"],
  "chunks_sample": [
    {
      "source_id": "entity-fiis-noticias",
      "path": "data/entities/fiis_noticias/entity.yaml",
      "score": 0.6762780183097683,
      "snippet": "Notícias e matérias relevantes sobre FIIs (fonte externa consolidada D-1)..."
    },
    {
      "source_id": "concepts-macro",
      "path": "data/concepts/concepts-macro.yaml",
      "score": 0.6598566954792594,
      "snippet": "como os FIIs se comportaram nesse cenário de juros altos?..."
    }
  ]
}
```

Regras:

* `enabled`: se RAG estava habilitado na chamada do Narrator.
* `collections`: lista de coleções consultadas.
* `chunks_sample`: amostra das passagens usadas, com:

  * `source_id`, `path`: identificação/caminho do arquivo;
  * `score`: score de relevância;
  * `snippet`: trecho texto limitado por `rag_snippet_max_chars`.

---

## 9. Bloco `narrator`

Origem: meta do módulo Narrator.

Exemplo:

```jsonc
"narrator": {
  "enabled": true,
  "shadow": true,
  "model": "sirios-narrator:latest",
  "strategy": "llm_shadow",
  "latency_ms": 300083.56,
  "error": "llm_error: TimeoutError('timed out')",
  "effective_policy": {
    "llm_enabled": true,
    "shadow": true,
    "max_llm_rows": 5,
    "use_rag_in_prompt": true,
    "use_conversation_context": true
  }
}
```

Campos:

* `enabled`: se o Narrator estava ativo para essa entidade.
* `shadow`: se estava em modo shadow para essa chamada.
* `model`: identificador do modelo (ex.: `sirios-narrator:latest`).
* `strategy`: estratégia usada (`llm_shadow`, `llm_primary`, `deterministic_only`, `llm_failed`, etc.).
* `latency_ms`: tempo total gasto no Narrator.
* `error`: string de erro (se houver).
* `effective_policy`: snapshot da policy aplicada (já mesclada: default + entidade).

---

## 10. Bloco `presenter`

Origem: Presenter, imediatamente antes de devolver a resposta ao cliente.

Exemplo:

```jsonc
"presenter": {
  "answer_final": "Não sei responder com segurança agora. Exemplos de perguntas válidas: 'cnpj do MCCI11', 'preço do MXRF11 hoje'.",
  "answer_baseline": null,
  "rows_used": 0,
  "style": "executivo"
}
```

Regras:

* `answer_final`: resposta efetivamente enviada ao cliente (texto, truncado por `max_chars`).
* `answer_baseline`: resposta determinística antes do LLM (quando existir).
* `rows_used`: quantas linhas de dados entraram na narrativa.
* `style`: estilo aplicado (ex.: `"executivo"`).

---

## 11. Bloco `shadow`

Origem: lógica do próprio Shadow Collector.

Exemplo:

```jsonc
"shadow": {
  "sampled": true,
  "reason": "rate_hit",
  "policy_version": 1,
  "sampling_config": {
    "entity": "fiis_noticias",
    "rate": 0.3,
    "only_when_llm_used": true,
    "only_when_answer_nonempty": true,
    "always_on_llm_error": true
  },
  "redaction_applied": {
    "masked_fields": ["document_number"],
    "truncated_fields": ["answer_final", "snippet"]
  }
}
```

Campos:

* `sampled`: se o evento foi realmente gravado (sempre `true` para registros que existem).
* `reason`: motivo principal (`rate_hit`, `llm_error_forced`, `manual_debug`, etc.).
* `policy_version`: numero da versão da policy (`terms[*].version`).
* `sampling_config`: configuração efetiva usada nesta chamada.
* `redaction_applied`: resumo da sanitização feita (campos mascarados, truncados, etc.).

---

## 12. Sink e rotação de arquivos

Pela policy (`narrator_shadow.sink`):

* `kind: file`
* `path_pattern: "data/observability/narrator_shadow_%Y%m%d.jsonl"`

Regras:

* Um arquivo por dia, com nome baseado em data.
* Cada linha do arquivo é um `NarratorShadowRecord` completo (JSON).
* Em ambientes futuros, o `sink.kind` pode ser expandido para:

  * `stdout` (APM externo),
  * ou outra solução (S3, etc.), mantendo o mesmo contrato do record.

---

## 13. Restrições e guardrails

1. **Contrato `/ask` imutável**

   * O Shadow Collector **não** pode alterar o payload do `/ask`.
   * Todo o contexto usado deve vir de estruturas internas já existentes
     (meta do Planner, do Narrator, do Formatter, etc.).

2. **Sem heurísticas hardcoded**

   * Todo comportamento de sampling, redaction e sink deve vir de:

     * `data/ops/narrator_shadow.yaml`,
     * `data/ops/narrator.yaml`,
     * `data/ops/observability.yaml` (quando aplicável).
   * Código deve apenas ler essas configs e executar.

3. **Impacto controlado**

   * Shadow deve ser capaz de ser **desligado** por config:

     * `narrator_shadow.enabled: false`
     * ambiente fora de `environment_allowlist`
   * Sampling deve garantir custo previsível de disco/CPU.

4. **Privacidade**

   * Dados sensíveis devem ser mascarados **antes de gravar**.
   * Eventos com dados de cliente podem ser:

     * redigidos,
     * ou até bloqueados por completo, se necessário.

---
