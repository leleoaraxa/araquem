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
* ✔ **M12 – Política de Last Reference (Ticker)** definida conceitualmente e alinhada ao Guardrails:

  * /ask permanece imutável
  * last_reference só nasce de resposta aceita
  * prioridade: texto → identifiers → contexto
* ✔ `param_inference.yaml` enriquecido com `params.ticker` (source: `text` + `context`) para intents de FII:

  * `fiis_dividendos`
  * `fiis_precos`
  * `fiis_yield_history`
  * `fiis_financials_revenue_schedule`
  * `fiis_financials_risk`
  * `dividendos_yield`
  * `fiis_processos`
  * `fiis_cadastro`
  * `fiis_noticias`
  * `fiis_imoveis`
  * `fii_overview`
* ✔ `infer_params(...)` atualizado para:

  * receber `identifiers`, `client_id`, `conversation_id` **sem alterar payload do `/ask`**
  * priorizar ticker do texto (`identifiers`) e usar contexto apenas como fallback
  * validar janelas contra `windows_allowed` (intent + entidade)
* ✔ `Orchestrator.route_question(...)` agora injeta `client_id` e `conversation_id` na chamada de `infer_params` (compute-on-read + contexto)
* ✔ `/ask` registra `last_reference` best-effort após resposta bem-sucedida, sem impactar contrato HTTP
* ✔ `data/policies/context.yaml` atualizado com:

  * `narrator.allowed_entities` para histórico de conversa (fiis_* “públicos”)
  * `last_reference.allowed_entities` cobrindo as intents que de fato precisam de ticker herdado:

    * `fiis_dividendos`, `fiis_precos`, `fiis_yield_history`
    * `fiis_financials_revenue_schedule`, `fiis_financials_risk`
    * `dividendos_yield`, `fiis_processos`
    * `fiis_cadastro`, `fiis_noticias`, `fiis_imoveis`, `fii_overview`
* ✔ `routing_samples.json` expandido com cenários multi-turno de referência:

  * `“CNPJ do HGLG11?”` → `fiis_cadastro`
  * `“Esse fundo tem Sharpe bom?”` → `fiis_financials_risk`
  * `“E o overview dele?”` → `fii_overview`
  * `“Quais são as últimas notícias do HGLG11?”` → `fiis_noticias`
  * `“Qunatos processos tem ele?”` → `fiis_processos`
  * `“E o risco dele?”` → `fiis_financials_risk`
* ✔ **Sanity checks de contexto implementados e verdes**:

  * `python scripts/dev/context_sanity_check.py`

    * CNPJ → Sharpe → overview (`fiis_cadastro` → `fiis_financials_risk` → `fii_overview`)
    * `meta.aggregates.ticker` herdando `HGLG11` corretamente
  * `python scripts/dev/context_sanity_check_news_processos_risk.py`

    * notícias → processos → risco (`fiis_noticias` → `fiis_processos` → `fiis_financials_risk`)
    * `meta.aggregates.ticker` preenchido com `HGLG11` nas perguntas 2 e 3
  * resumo final: **HERANÇA DE TICKER OK** (C3 de contexto fechado para esses fluxos)

**🟦 Falta (M13 refinamento)**

* [ ] Testes comparativos com LLM OFF garantindo que a ativação do contexto **não altera respostas determinísticas**:

  * mesmo conjunto de perguntas antes/depois de `context.enabled: true` → mesmo SQL / mesmas respostas
* [ ] Adicionar um mini doc interno (apêndice do `M13_CONTEXT_README.md`) explicando:

  * prioridades de ticker: texto → identifiers → contexto
  * escopo atual das entidades que herdam contexto
  * como evoluir a lista de `last_reference.allowed_entities` sem quebrar guardrails
* [ ] Monitorar em ambiente controlado:

  * métricas `planner_rag_context_*` (já implementadas) + logs de context
  * padrões de uso real de “ele / esse fundo / esse FII” para decidir próximas entidades a receber contexto

---

## **1. Entidades & Realidade dos Dados (D-1 vs Histórico)**

> 🟩 **21 entidades** auditadas e documentadas no `ARAQUEM_STATUS_2025.md`.

### 🟩 **1.1 O que já foi feito**

*(mantido, apenas ajustado o texto pra “21 entidades”)*

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
  * **multi-turno com herança de ticker** (HGLG11: CNPJ → Sharpe → overview, notícias → processos → risco)
* ✔ **Adicionadas e integradas**:

  * ✔ **dividendos_yield** (pública, multi-ticker)
  * ✔ **carteira_enriquecida** (privada)
  * ✔ **macro_consolidada** (macro histórica)
  * todas com entidades, schemas, templates, projections de quality, catálogo, ontologia e políticas integradas

### 🟦 **1.2 Backlog de modelagem (não implementado ainda)**

*(mantido)*

---

## **2. RAG – Conteúdo e Políticas**

*(mantido como estava — nenhuma mudança estrutural nessa rodada.)*

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
  * blocos `params.ticker` para intents de FII com contexto:

    * `fiis_dividendos`, `fiis_precos`, `fiis_yield_history`
    * `fiis_financials_revenue_schedule`, `fiis_financials_risk`
    * `dividendos_yield`, `fiis_processos`
    * `fiis_cadastro`, `fiis_noticias`, `fiis_imoveis`, `fii_overview`
    * usando `source: [text, context]` e `context_key: last_reference`
* ✔ `infer_params(...)` agora:

  * recebe `identifiers`, `client_id`, `conversation_id`
  * aplica compute-on-read com agregações/janelas totalmente declarativas (YAML)
  * adiciona `ticker` ao `agg_params` quando inferido (texto ou contexto)
* ✔ `Orchestrator.route_question(...)`:

  * passa `client_id` e `conversation_id` para `infer_params`
  * continua usando apenas o SELECT determinístico quando `agg_params` falha ou não se aplica
* ✔ `quality_list_misses.py` confirmou:

  * roteamento consistente após inclusão de `params.ticker` e last_reference
  * `✅ Sem misses.` com o C3 de contexto ligado

**🔵 Falta**

* [ ] Revisar thresholds finos por intent/entity (top1_min_score, min_gap), cobrindo também `dividendos_yield`, `carteira_enriquecida`, `macro_consolidada`
* [ ] Ajustar `intent_top2_gap` e `entity_top2_gap` com base no explain real
* [ ] Validar explain logs / `decision_path` em perguntas de fronteira (DY histórico x snapshot x composto)
* [ ] Fixar baseline final após fechamento de entidades e quality

---

* [✔️] Políticas estruturadas
* [✔️] Modelo sirios-narrator criado
* [ ] Ajustar narrator.yaml para produção
* [ ] Definir:
  * [ ] llm_enabled
  * [ ] shadow
  * [ ] max_llm_rows
  * [ ] style
  * [ ] use_rag_in_prompt
  * [ ] Validar fallback seguro para cada entidade
  * [ ] Testar estilo final (executivo / objetivo / curto)

  ---

  ## **5. RAG + Narrator – Integração Profissional**

  * [ ] Definir políticas de uso do RAG no prompt
  * [ ] Reduzir tamanho dos snippets (máx. 250–350 chars)
  * [ ] Validar tempo de inferência com snippets
  * [ ] Testar shadow mode real (com logs)
  * [ ] Ajustar tamanho final do prompt (≤ 3800 tokens)

  ---

## **6. Quality – Baseline Final**

**✔️ Feito**

* ✔ `quality.yaml` revisado com `targets` realistas
* ✔ Cobertura de datasets: FIIs, Cliente (privado), Macro, compostos
* ✔ Regras de faixa (`accepted_range`) ajustadas
* ✔ `quality_list_misses.py` e `quality_diff_routing.py` rodando **sem** chamar Ollama
* ✔ Baseline **2025.0-prod** fixado:

  * `python scripts/quality/quality_list_misses.py` → `✅ Sem misses.`
  * `python scripts/quality/quality_diff_routing.py` → `✅ Sem misses.`
  * routing_samples cobrindo:

    * compostos (`dividendos_yield`, `carteira_enriquecida`, `macro_consolidada`)
    * **cenários de contexto multi-turno** (HGLG11: CNPJ → Sharpe → overview; notícias → processos → risco)

**🔵 Falta**

  * [ ] Curadoria dos 16 misses
  * [ ] Rodar quality_list_misses.py novamente
  * [ ] Rodar quality_diff_routing.py em modo seguro (sem Ollama)
  * [ ] Fixar baseline “2025.0-prod” no YAML
  * [ ] Confirmar métricas top1, top2_gap, routed_rate no Grafana


## **7. Infra/Produção – Ambientes e Deploy**

* [ ] Configurar DATABASE_URL de produção
* [ ] Configurar OTEL Collector + Tempo + Prometheus + Grafana
* [ ] Definir dashboards finais (/ask, planner, narrator, rag)
* [ ] Ajustar Redis (TTL, namespaces, blue/green)
* [ ] Habilitar alertas de: * timeouts * cache-miss spikes * RAG latency high --- ##

**8. Segurança & LGPD**

* [ ] Sanitização de PII no Presenter/Formatter
* [ ] Reduzir exposição de metas sensíveis em explain
* [ ] Ajustar tokens e policies de acesso (quality ops)
* [ ] Verificar que logs/traces não mostram payload completo
* [ ] Revisar roles do Postgres (sirios_api e edge_user)

---

## **9. Documentação Final**

* [ ] Atualizar ARAQUEM_STATUS_2025.md
* [ ] Atualizar diagramas C4 (context, container, component)
* [ ] Documentar:
* [ ] RAG flows
* [ ] Narrator
* [ ] Context Manager
* [ ] planner.explain()
* [ ] policies (RAG/Narrator/Cache/Context)
* [ ] Documentar rotas /ask e /ops/*

---

## **10. Testes de Carga e Estresse**

* [ ] Testar throughput com sirios-narrator:latest
* [ ] Testar embeddings sob carga (batch 8, 16, 32)
* [ ] Validar latência p95/p99
* [ ] Simular 200–500 perguntas simultâneas

---

## **11. Entrega Final — “2025.0-prod”**

* [ ] Criar tag
* [ ] Congelar embeddings
* [ ] Congelar ontologia
* [ ] Congelar thresholds
* [ ] Ativar CI/CD com blue/green
* [ ] Smoke test no ambiente final
* [ ] Publicar versão
