# ✅ **CHECKLIST ARAQUEM — RUMO À PRODUÇÃO (2025.0-prod)**

### *(versão Sirius — 21 entidades auditadas, RAG/Narrator/Quality alinhados)*

---

## **0. Contexto Conversacional (M12–M13)**

> 🟩 Base técnica pronta. Próxima etapa: *refinar e observar em produção controlada*.

**✔️ Feito**

* ✔ `context_manager.py` criado
* ✔ Integração mínima no `/ask` (`append_turn` para `user` e `assistant`)
* ✔ Presenter injeta `history` no meta do Narrator (quando permitido em `context.yaml`)
* ✔ Policies definidas em `data/policies/context.yaml` (planner, narrator e `last_reference`)
* ✔ `context.enabled: true` com **escopo controlado** (entidades liberadas para history e last_reference)
* ✔ Implementado `last_reference` no `ContextManager` com:

  * política dedicada (`context.last_reference.{enable_last_ticker, allowed_entities, max_age_turns}`)
  * contador lógico de turns por `(client_id, conversation_id)` para TTL em “número de turnos”
* ✔ `last_reference_allows_entity(entity)` consolidado como único gate de uso do ticker herdado
* ✔ `param_inference.yaml` enriquecido com `params.ticker` (source: `text` + `context`) para:

  * `fiis_precos`
  * `fiis_financials_risk`
  * `fii_overview`
* ✔ `infer_params(...)` atualizado para:

  * receber `identifiers`, `client_id`, `conversation_id` **sem alterar payload do `/ask`**
  * priorizar ticker do texto (`identifiers`/regex) e usar contexto apenas como fallback
* ✔ `Orchestrator.route_question(...)` agora injeta `client_id` e `conversation_id` na chamada de `infer_params` (compute-on-read + contexto)
* ✔ `/ask` registra `last_reference` best-effort após resposta bem-sucedida, sem impactar contrato HTTP
* ✔ `data/policies/context.yaml` atualizado com:

  * `narrator.allowed_entities` para histórico de conversa (fiis_* “públicos”)
  * `last_reference.allowed_entities` restrito a:

    * `fiis_financials_risk`
    * `fii_overview`
    * `fiis_precos`
* ✔ `routing_samples.json` expandido com cenário multi-turno de referência:

  * `“CNPJ do HGLG11?”` → `fiis_cadastro`
  * `“Esse fundo tem Sharpe bom?”` → `fiis_financials_risk`
  * `“E o overview dele?”` → `fii_overview`

**🟦 Falta (M13 refinamento)**

* [ ] Validar, via testes manuais / logs, a **herança de referência** no fluxo real:

  * Pergunta 1: “CNPJ do HGLG11?”
  * Pergunta 2: “Esse fundo tem Sharpe bom?”
  * Pergunta 3: “E o overview dele?”
  * Verificar que:

    * `fiis_financials_risk` e `fii_overview` recebem `ticker=HGLG11` via contexto
    * não há fallback errado quando o usuário troca de FII
* [ ] Testes com LLM OFF (estado atual) garantindo que a ativação do contexto **não altera respostas determinísticas**:

  * mesmas perguntas antes/depois do contexto habilitado → mesmas respostas / mesmo SQL
* [ ] Adicionar um mini doc interno (apêndice do `M13_CONTEXT_README.md`) explicando:

  * prioridades de ticker: texto → identifiers → contexto
  * escopo atual das entidades que herdam contexto
  * como evoluir a lista de `allowed_entities` sem quebrar guardrails

---

## **1. Entidades & Realidade dos Dados (D-1 vs Histórico)**

> 🟩 **21 entidades** auditadas e documentadas no `ARAQUEM_STATUS_2025.md`.

### 🟩 **1.1 O que já foi feito**

*(mantido como você trouxe, apenas com o número “21 entidades” já alinhado)*

* ✔ Auditoria profunda das **21 entidades reais** do Araquem (FIIs, macro, cliente privado e compostas)
* ✔ Classificação de cada uma: D-1, histórica ou quase estática
* ✔ Identificação de:

  * periodicidade real
  * cardinalidade
  * chaves naturais
  * riscos de interpretação
  * aderência a RAG / Narrator / quality / cache
* ✔ Registro consolidado em `docs/ARAQUEM_STATUS_2025.md`
* ✔ Criação e atualização de `data/ops/entities_consistency_report.yaml` garantindo:

  * `has_schema`, `has_quality_projection`, `in_quality_policy`
  * participação (ou exclusão explícita) em cache, RAG, Narrator, param_inference, ontologia
* ✔ Novos projections de quality criados (incluindo privadas/compostas):

  * `client_fiis_dividends_evolution`
  * `client_fiis_performance_vs_benchmark`
  * `fii_overview` / `fiis_yield_history` (evoluções históricas)
  * **novas entidades compostas**: projections específicas para

    * `dividendos_yield`
    * `carteira_enriquecida`
    * `macro_consolidada`
* ✔ `routing_samples.json` expandido com cenários:

  * resumo de FII (`fii_overview`)
  * histórico de DY (`fiis_yield_history`)
  * evolução de dividendos da carteira (`client_fiis_dividends_evolution`)
  * performance da carteira vs benchmark (`client_fiis_performance_vs_benchmark`)
  * **casos compostos**:

    * “histórico de dividendos **e DY** do MXRF11” (`dividendos_yield`)
    * perguntas de carteira enriquecida (peso, DY, risco na carteira) (`carteira_enriquecida`)
    * perguntas macro consolidadas por data/período (`macro_consolidada`)
  * **multi-turno com herança de ticker** (HGLG11: CNPJ → Sharpe → overview)
* ✔ **Adicionadas e integradas**:

  * ✔ **dividendos_yield** (pública, multi-ticker)
  * ✔ **carteira_enriquecida** (privada)
  * ✔ **macro_consolidada** (macro histórica)
  * todas com entidades, schemas, templates, projections de quality, catálogo, ontologia e políticas integradas

### 🟦 **1.2 Backlog de modelagem (não implementado ainda)**

*(mantido)*

---

## **2. RAG – Conteúdo e Políticas**

*(sem mudanças estruturais nessa rodada; só herdou os efeitos indiretos de o planner/quality continuarem verdes depois das alterações.)*

**✔️ Feito**

*(como já estava)*

**🔵 Falta**

*(como já estava)*

---

## **3. Planner – Thresholds e Calibração Final**

**✔️ Feito**

* ✔ Ontologia refinada (`data/ontology/entity.yaml`) para:

  * separar claramente dividendos × DY (snapshot × histórico × ranking × **compostas**)
  * ajustar roteamento de notícias negativas, dólar e IPCA
  * incluir intents novas:

    * `fii_overview`
    * `fiis_yield_history`
    * `client_fiis_dividends_evolution`
    * `client_fiis_performance_vs_benchmark`
    * `dividendos_yield`
    * `carteira_enriquecida`
    * `macro_consolidada`
* ✔ `param_inference.yaml` validado com:

  * intents temporais (`fiis_dividendos`, `fiis_precos`, `fiis_yield_history`, etc.)
  * janelas declaradas (`windows_allowed`) e defaults coerentes
  * blocos `params.ticker` para:

    * `fiis_precos`
    * `fiis_financials_risk`
    * `fii_overview`
    * usando `source: [text, context]` e `context_key: last_reference` (ainda sem semântica própria)
* ✔ `infer_params(...)` agora:

  * recebe `identifiers`, `client_id`, `conversation_id`
  * aplica compute-on-read com agregações/janelas totalmente declarativas (YAML)
  * adiciona `ticker` ao `agg_params` quando inferido
* ✔ `Orchestrator.route_question(...)`:

  * passa `client_id` e `conversation_id` para `infer_params`
  * continua usando apenas o SELECT determinístico quando `agg_params` falha ou não se aplica
* ✔ `quality_list_misses.py` confirmou:

  * roteamento consistente após inclusão de `params.ticker` e last_reference
  * `✅ Sem misses.` com o C3 de contexto ligado

**🔵 Falta**

*(igual, focado em ajustes finos – agora considerando também os intents que usam contexto)*

* [ ] Revisar thresholds finos por intent/entity (top1_min_score, min_gap), cobrindo também `dividendos_yield`, `carteira_enriquecida`, `macro_consolidada`
* [ ] Ajustar `intent_top2_gap` e `entity_top2_gap` com base no explain real
* [ ] Validar explain logs / `decision_path` em perguntas de fronteira (DY histórico x snapshot x composto)
* [ ] Fixar baseline final após fechamento de entidades e quality

---

## **4. Narrator – Versão para Produção**

*(sem mudanças de código nessa rodada; contexto só influencia meta e history, com LLM OFF.)*

**✔️ Feito**

*(como já estava)*

**🔵 Falta**

*(como já estava)*

---

## **5. RAG + Narrator – Integração Profissional**

*(mantido)*

---

## **6. Quality – Baseline Final**

**✔️ Feito**

*(igual ao que você mandou, com um detalhe a mais)*

* ✔ `quality.yaml` revisado com `targets` realistas
* ✔ Cobertura de datasets: FIIs, Cliente (privado), Macro, compostos
* ✔ Regras de faixa (`accepted_range`) ajustadas
* ✔ `quality_list_misses.py` e `quality_diff_routing.py` rodando **sem** chamar Ollama
* ✔ Baseline **2025.0-prod** fixado:

  * `python scripts/quality/quality_list_misses.py` → `✅ Sem misses.`
  * `python scripts/quality/quality_diff_routing.py` → `✅ Sem misses.`
  * routing_samples cobrindo:

    * compostos (`dividendos_yield`, `carteira_enriquecida`, `macro_consolidada`)
    * **e cenários de contexto multi-turno** (HGLG11: CNPJ → Sharpe → overview)

**🔵 Falta**

*(mantido)*

---

## **7. Infra/Produção – Ambientes e Deploy**

*(mantido)*

---

## **8. Segurança & LGPD**

*(mantido; bindings via `context.client_id` continuam sendo a âncora de segurança.)*

---

## **9. Documentação Final**

* [ ] Manter `ARAQUEM_STATUS_2025.md` como fonte viva de estado (incluir resumo do M13/contexto)
* [ ] Atualizar C4, fluxos de RAG, Narrator, **ContextManager/last_reference** e quality
* [ ] Documentar entidades compostas **existentes e futuras**:

  * `dividendos_yield`
  * `carteira_enriquecida`
  * `macro_consolidada`
  * (e quaisquer novos compostos aprovados no Guardrails)

---

## **10. Testes de Carga e Estresse**

*(mantido)*

---

## **11. Entrega Final — “2025.0-prod”**

*(mantido)*

---

## 🎯 Próxima tarefa sugerida (mão na massa agora)

Eu sugiro a **próxima micro-tarefa** ser bem focada em validar o C3 de contexto ponta-a-ponta, sem mexer em infra:

### Tarefa: Validar “Sharpe do fundo anterior” com contexto ligado

**Objetivo:**
Garantir, na prática, que `last_reference` está funcionando como desenhado, sem alterar payload ou quebrar nada do determinístico.

**Passos sugeridos:**

1. Subir stack dev normal (`docker compose up -d api`).

2. Fazer uma sequência real contra o `/ask` (via Postman/curl ou scriptzinho Python), *sempre com o mesmo `conversation_id` e `client_id`*:

   1. `question = "CNPJ do HGLG11?"`
   2. `question = "Esse fundo tem Sharpe bom?"`
   3. `question = "E o overview dele?"`

3. Para cada chamada:

   * Conferir `meta.planner_entity` (`fiis_cadastro`, `fiis_financials_risk`, `fii_overview`).
   * Logar/inspecionar:

     * `meta.aggregates.ticker` (quando existir)
     * qualquer log do `ContextManager` (pode usar um `LOGGER.info` temporário só pra validar).

4. Confirmar que:

   * Perguntas 2 e 3 recebem `ticker=HGLG11` via `_ticker_from_context`, quando o texto não traz o ticker explicitamente.
   * Se você mudar a pergunta 1 para outro fundo (ex.: MXRF11), a herança acompanha corretamente.

5. Se ficar tudo OK:

   * Marcar no checklist 0:

     * “Validar herança de referência (ex.: Sharpe do fundo anterior)” → ✔
   * Atualizar o `M13_CONTEXT_README.md` com um mini exemplo real de fluxo (essas três perguntas).
