## 1. M12 – Política de Last Reference (Ticker)

### 1.1. Objetivo

Definir **como o Araquem herda o último ticker mencionado** em uma conversa para responder perguntas de follow-up do tipo:

* “CNPJ do HGLG11?”
* “Esse fundo tem Sharpe bom?”
* “E o overview dele?”

…sem precisar repetir o ticker, **sem mexer no payload do `/ask`** e obedecendo 100% ao Guardrails (ontologia/YAML como contrato).

---

### 1.2. Arquivos envolvidos

* **Política de contexto (fonte de verdade de last_reference)**
  `data/policies/context.yaml`

  * Bloco `context.enabled`: liga/desliga contexto global.
  * Bloco `context.last_reference`:

    * `enable_last_ticker: bool`
    * `allowed_entities: [string]`
    * `max_age_turns: int`

* **Motor de contexto**
  `app/context/context_manager.py`

  * Mantém:

    * histórico de turns (`ConversationTurn`)
    * `last_reference` com:

      * `ticker`
      * `entity`
      * `intent`
      * `updated_at`
      * `turn_index`
    * API canônica para herança:

      * `resolve_last_reference(...)` aplica `context.yaml` para decidir se o ticker anterior pode ser herdado e devolve `identifiers` enriquecidos com meta (`reason`, `last_reference_used`).【F:app/context/context_manager.py†L353-L441】
  * Aplica políticas:

    * `context.enabled`
    * `last_reference.enable_last_ticker`
    * `last_reference.allowed_entities`
    * `last_reference.max_age_turns`

* **Inferência de parâmetros**
  `app/planner/param_inference.py` +
  `data/ops/param_inference.yaml`

  * Decide:

    * `agg`, `window`, `limit`, `order`
    * **`ticker`**, a partir de:

      * texto (`source: text`)
      * contexto (`source: context`)

---

### 1.3. Contrato de alto nível

1. **/ask continua imutável**
   Payload fixo:

   ```json
   { "question", "conversation_id", "nickname", "client_id" }
   ```

   Nenhum campo novo é adicionado para contexto ou ticker herdado.

2. **Last reference é sempre derivado de respostas aceitas**

   * A cada resposta onde o Planner **aceita** a decisão (`chosen.accepted = true`)
   * E há um ticker claro (via parâmetros / meta / formatter)
   * O Orchestrator/Presenter chama:

     ```python
     context_manager.update_last_reference(
         client_id,
         conversation_id,
         ticker=resolved_ticker,
         entity=entity_name,
         intent=intent_name,
     )
     ```

3. **Herança é resolvida exclusivamente pelo ContextManager**

   * `/ask` chama `context_manager.resolve_last_reference(...)` logo após extrair `identifiers`.
   * A função aplica o `context.yaml` (enable/allowed_entities/max_age_turns) e devolve `identifiers_resolved` + meta (`reason`, `last_reference_used`).【F:app/api/ask.py†L178-L201】【F:app/context/context_manager.py†L353-L441】
   * Nenhuma heurística de herança fica no endpoint; o contrato externo do `/ask` permanece igual.

4. **Herança de ticker só acontece se 3 camadas concordarem**

   * **Context policy** permitir:

     * `context.enabled = true`
     * `last_reference.enable_last_ticker = true`
     * `entity` ∈ `last_reference.allowed_entities` (se a lista não estiver vazia)
   * **ContextManager** considerar o registro ainda válido:

     * `current_turn - last_ref.turn_index <= max_age_turns`
   * **param_inference.yaml** declarar:

     ```yaml
     params:
       ticker:
         source:
           - text
           - context
         context_key: last_reference
     ```

     (o código ignora o `context_key` semanticamente, mas ele documenta o contrato).

4. **Planner/Builder nunca “chutam” ticker via regex solta**

   * Extração **canônica** de identificadores é responsabilidade do Orchestrator.
   * `param_inference` só lê:

     * `identifiers.ticker` / `identifiers.tickers`
     * `context_manager.get_last_reference(...)`
   * Se houver ambiguidade (0 ou >1 tickers), o código retorna `None`.

---

### 1.4. Fluxo canônico – Exemplo 1 (notícias → processos → risco)

**Pergunta 1**

> “Quais são as últimas notícias do HGLG11?”

1. Orchestrator extrai `ticker = "HGLG11"`.
2. Planner roteia para `fiis_noticias`.
3. Param inference (se configurado para ticker) vê:

   * `source: text` → encontra `HGLG11`
   * `source: context` → ignorado (já resolveu pelo texto)
4. Query roda; resposta sai com HGLG11.
5. Orchestrator/Presenter chamam:

   ```python
   context_manager.update_last_reference(
       client_id, conversation_id,
       ticker="HGLG11",
       entity="fiis_noticias",
       intent="fiis_noticias",
   )
   ```

**Pergunta 2**

> “Quantos processos tem ele?”

1. /ask chega **sem ticker no texto**.
2. Planner roteia para `fiis_processos`.
3. `infer_params(..., intent="fiis_processos", entity="fiis_processos", ...)`:

   * `source: text` → nenhum ticker.
   * `source: context` → chama:

     ```python
     _ticker_from_context("fiis_processos", client_id, conversation_id)
     ```
   * `context_manager` verifica:

     * contexto habilitado
     * last_reference habilitado
     * `fiis_processos` permitido em `last_reference.allowed_entities`
     * idade ≤ `max_age_turns`
   * Se tudo OK → devolve `"HGLG11"`.
4. Builder recebe `params = {"agg": "list", ..., "ticker": "HGLG11"}` e monta a SQL filtrando o ticker.

**Pergunta 3**

> “E o risco dele?”

Mesma lógica da pergunta 2, mas agora com:

* `intent/entity = fiis_financials_risk`
* `params.ticker` herdando `"HGLG11"`

---

### 1.5. Fluxo canônico – Exemplo 2 (cadastro → risco → overview)

**Pergunta 1**

> “CNPJ do HGLG11?”

* Intent/entity: `fiis_cadastro`
* Ticker via texto.
* Resposta sai com ticker.
* `update_last_reference(..., ticker="HGLG11", entity="fiis_cadastro")`.

**Pergunta 2**

> “Esse fundo tem Sharpe bom?”

* Intent/entity: `fiis_financials_risk`
* `params.ticker` herdado do contexto (`HGLG11`).

**Pergunta 3**

> “E o overview dele?”

* Intent/entity: `fii_overview`
* `params.ticker` herdado do contexto (`HGLG11`).

Os teus scripts de sanity check (`context_sanity_check.py` e `context_sanity_check_news_processos_risk.py`) são justamente a **prova de contrato** do M12.

---

### 1.6. Escopo da política de Last Reference

**Entidades típicas que devem herdar ticker via contexto**:

* `fiis_cadastro`
* `fiis_noticias`
* `fiis_processos`
* `fiis_financials_risk`
* `fiis_financials_revenue_schedule`
* `fii_overview`
* `fiis_dividendos`
* `fiis_precos`
* `fiis_yield_history`
* `fiis_dividends_yields`
* `fiis_imoveis` (quando a intenção é “imóveis desse fundo”)

**Entidades que NÃO devem usar last_reference** (regra geral):

* Macros e índices globais:

  * `history_b3_indexes`
  * `history_currency_rates`
  * `history_market_indicators`
  * `macro_consolidada`
* Entidades amarradas ao cliente (`document_number`):

  * `client_fiis_*`
  * `client_fiis_enriched_portfolio`

Essas ficam fora de `last_reference.allowed_entities` e/ou nem têm `params.ticker` declarado.

---
