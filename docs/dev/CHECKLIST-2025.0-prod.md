# ✅ **CHECKLIST ARAQUEM — RUMO À PRODUÇÃO (2025.0-prod)**

### *(versão Sirius — 21 entidades auditadas, RAG/Narrator/Quality alinhados)*

---

## 0. Contexto Conversacional (M12–M13)

> 🟩 Base técnica pronta. Próxima etapa: *refinar e observar em produção controlada*.

**✔️ Feito**

* [✔] `context_manager.py` criado e integrado ao `/ask` (`append_turn` user/assistant).
* [✔] Presenter injeta `history` no meta do Narrator conforme `data/policies/context.yaml`.
* [✔] Policies de contexto definidas (planner, narrator, `last_reference`) com `context.enabled: true` e escopo controlado.
* [✔] `last_reference` implementado com política dedicada, TTL em número de turnos e gate único `last_reference_allows_entity(entity)`.
* [✔] Política M12 de last_reference alinhada ao Guardrails: `/ask` imutável; last_reference só nasce de resposta aceita; prioridade texto → identifiers → contexto.
* [✔] `param_inference.yaml` enriquecido com `params.ticker` (source: `[text, context]`) para as intents de FII.
* [✔] `infer_params(...)` recebendo `identifiers`, `client_id`, `conversation_id`, validando janelas (`windows_allowed`) e usando contexto apenas como fallback.
* [✔] `Orchestrator.route_question(...)` passando `client_id` e `conversation_id` para `infer_params`.
* [✔] `/ask` registrando `last_reference` best-effort após resposta bem-sucedida.
* [✔] `routing_samples.json` com cenários multi-turno (CNPJ → Sharpe → overview; notícias → processos → risco).
* [✔] Sanity checks de contexto verdes:

  * `context_sanity_check.py` (CNPJ → Sharpe → overview, ticker herdado).
  * `context_sanity_check_news_processos_risk.py` (notícias → processos → risco, ticker herdado).

**🟦 Falta (M13 — refinamento)**

* [ ] Testar **LLM OFF** comparando respostas antes/depois de `context.enabled: true` (mesmo SQL / mesmas respostas).
* [ ] Escrever apêndice `M13_CONTEXT_README.md`:

  * [ ] Prioridades de ticker (texto → identifiers → contexto).
  * [ ] Escopo atual das entidades que herdam contexto.
  * [ ] Como evoluir `last_reference.allowed_entities` sem quebrar Guardrails.
* [ ] Monitorar em ambiente controlado:

  * [ ] Métricas `planner_rag_context_*` + logs de contexto.
  * [ ] Padrões reais de “ele / esse fundo / esse FII” para decidir próximas entidades a receber contexto.

---

## 1. Entidades & Realidade dos Dados (D-1 vs Histórico)

> 🟩 21 entidades auditadas e documentadas em `docs/ARAQUEM_STATUS_2025.md`.

**✔️ Feito**

* [✔] Auditoria profunda das 21 entidades (FIIs, macro, cliente privado, compostas).
* [✔] Classificação D-1 / histórica / quase estática com periodicidade, cardinalidade e chaves naturais mapeadas.
* [✔] Riscos de interpretação e aderência a RAG / Narrator / quality / cache avaliados.
* [✔] Relato consolidado em `docs/ARAQUEM_STATUS_2025.md`.
* [✔] `data/ops/entities_consistency_report.yaml` garantindo:

  * [✔] `has_schema`, `has_quality_projection`, `in_quality_policy`.
  * [✔] Participação (ou exclusão explícita) em cache, RAG, Narrator, param_inference, ontologia.
* [✔] Novos projections de quality criados:

  * [✔] `client_fiis_dividends_evolution`.
  * [✔] `client_fiis_performance_vs_benchmark`.
  * [✔] `fii_overview`, `fiis_yield_history`.
  * [✔] Entidades compostas: `dividendos_yield`, `carteira_enriquecida`, `macro_consolidada`.
* [✔] `routing_samples.json` com:

  * [✔] `fii_overview`, `fiis_yield_history`, `client_fiis_dividends_evolution`, `client_fiis_performance_vs_benchmark`.
  * [✔] Casos compostos (`dividendos_yield`, `carteira_enriquecida`, `macro_consolidada`).
  * [✔] Fluxos multi-turno com herança de ticker (HGLG11).
* [✔] Entidades compostas totalmente integradas (entidade + schema + templates + quality + catálogo + ontologia + policies).

**🟦 Falta**

* [ ] Backlog de modelagem fina (novas entidades futuras, ajustes avançados) — seguir `ARAQUEM_STATUS_2025.md` como fonte.

---

## 2. RAG – Conteúdo e Políticas

> Mantido conceitualmente como no doc original; aqui apenas o resumo.

**✔️ Feito (resumo)**

* [✔] Conteúdo principal indexado (FIIs, macro, educacional) com políticas base de RAG.

**🟦 Falta (macro)**

* [ ] Revisar e fechar políticas finais de RAG por entidade/intenção (nível de confiança, fallback, uso em produção).

---

## 3. Planner – Thresholds e Calibração Final  ▶️ *(foco do caminho A + C)*

**✔️ Feito**

* [✔] Ontologia refinida em `data/ontology/entity.yaml` distinguindo dividendos × DY × rankings × compostas.
* [✔] Roteamento de notícias negativas, dólar e IPCA ajustado.
* [✔] Intents novas incluídas:

  * [✔] `fii_overview`, `fiis_yield_history`.
  * [✔] `client_fiis_dividends_evolution`, `client_fiis_performance_vs_benchmark`.
  * [✔] `dividendos_yield`, `carteira_enriquecida`, `macro_consolidada`.
* [✔] `param_inference.yaml` validado:

  * [✔] Intents temporais (`fiis_dividendos`, `fiis_precos`, `fiis_yield_history`, etc.) com `windows_allowed`.
  * [✔] `params.ticker` com `source: [text, context]` e `context_key: last_reference`.
* [✔] `infer_params(...)`:

  * [✔] Recebe `identifiers`, `client_id`, `conversation_id`.
  * [✔] Aplica compute-on-read com agregações/janelas declarativas via YAML.
  * [✔] Adiciona `ticker` em `agg_params` quando inferido.
* [✔] `Orchestrator.route_question(...)`:

  * [✔] Passa `client_id` e `conversation_id` para `infer_params`.
  * [✔] Mantém SELECT determinístico quando `agg_params` falha/não se aplica.
* [✔] `quality_list_misses.py` com `✅ Sem misses` após inclusão de `params.ticker` e contexto.

**🟦 Falta (A — Planner primeiro)**

* [ ] Revisar **thresholds finos por intent/entity** (`top1_min_score`, `min_gap`), incluindo:

  * [ ] `dividendos_yield`.
  * [ ] `carteira_enriquecida`.
  * [ ] `macro_consolidada`.
* [ ] Ajustar `intent_top2_gap` e `entity_top2_gap` com base em `explain` real.
* [ ] Validar `decision_path`/explain em perguntas de fronteira (DY histórico × snapshot × composto).
* [ ] Fixar baseline final do planner após fechamento de entidades + quality.

---

## 4. Narrator – Modelo & Policies

**✔️ Feito**

* [✔] Políticas estruturais de Narrator definidas.
* [✔] Modelo `sirios-narrator:latest` criado e integrado.

**🟦 Falta**

* [ ] Ajustar `narrator.yaml` para produção:

  * [ ] `llm_enabled`.
  * [ ] `shadow`.
  * [ ] `max_llm_rows`.
  * [ ] `style` (executivo/objetivo/curto).
  * [ ] `use_rag_in_prompt`.
* [ ] Validar fallback seguro por entidade (quando NÃO usar LLM).
* [ ] Testar estilo final de resposta (executivo / objetivo / curto) com amostras reais.

---

## 5. RAG + Narrator – Integração Profissional

**🟦 Falta**

* [ ] Definir políticas de uso do RAG no prompt (quando e como injetar contexto RAG).
* [ ] Reduzir tamanho dos snippets (≈ 250–350 caracteres).
* [ ] Validar tempo de inferência com snippets menores.
* [ ] Testar shadow mode real do Narrator (com logs e métricas).
* [ ] Ajustar tamanho final do prompt (≤ ~3800 tokens).

---

## 6. Quality – Baseline Final  ▶️ *(C — curadoria dos misses)*

**✔️ Feito**

* [✔] `data/policies/quality.yaml` revisado com `targets` realistas.
* [✔] Cobertura de datasets: FIIs, Cliente (privado), Macro, Compostos.
* [✔] `accepted_range` ajustado por entidade.
* [✔] `quality_list_misses.py` e `quality_diff_routing.py` rodando **sem** chamar Ollama.
* [✔] Baseline preliminar 2025.0-prod com:

  * [✔] `quality_list_misses.py` → `✅ Sem misses` (na rodada anterior).
  * [✔] `quality_diff_routing.py` → `✅ Sem misses`.
  * [✔] `routing_samples` cobrindo compostos e cenários multi-turno com contexto.

**🟦 Falta**

* [ ] Curadoria final dos **16 misses** identificados.
* [ ] Rodar `quality_list_misses.py` novamente após ajustes.
* [ ] Rodar `quality_diff_routing.py` em modo seguro (sem Ollama).
* [ ] Fixar baseline final “2025.0-prod” no YAML de quality.
* [ ] Confirmar no Grafana:

  * [ ] `top1`.
  * [ ] `top2_gap`.
  * [ ] `routed_rate`.

---

## 7. Infra / Produção – Ambientes e Deploy

**🟦 Falta**

* [ ] Configurar `DATABASE_URL` de produção.
* [ ] Configurar OTEL Collector + Tempo + Prometheus + Grafana.
* [ ] Definir dashboards finais para:

  * [ ] `/ask`.
  * [ ] Planner.
  * [ ] Narrator.
  * [ ] RAG.
* [ ] Ajustar Redis (TTL, namespaces, blue/green).
* [ ] Criar alertas para:

  * [ ] timeouts.
  * [ ] picos de cache-miss.
  * [ ] latência alta de RAG / Narrator.

---

## 8. Segurança & LGPD

**🟦 Falta**

* [ ] Sanitizar PII no Presenter/Formatter (output final).
* [ ] Reduzir exposição de metas sensíveis em `explain`.
* [ ] Ajustar tokens e policies de acesso (quality ops, observabilidade).
* [ ] Garantir que logs/traces **não** exibem payload completo.
* [ ] Revisar roles do Postgres (`sirios_api`, `edge_user`).

---

## 9. Documentação Final

**🟦 Falta**

* [ ] Atualizar `docs/ARAQUEM_STATUS_2025.md` com o estado final.
* [ ] Atualizar diagramas C4 (context, container, component).
* [ ] Documentar:

  * [ ] RAG flows.
  * [ ] Narrator.
  * [ ] Context Manager.
  * [ ] `planner.explain()`.
  * [ ] Policies (RAG / Narrator / Cache / Context).
  * [ ] Rotas `/ask` e `/ops/*`.

---

## 10. Testes de Carga e Estresse

**🟦 Falta**

* [ ] Testar throughput com `sirios-narrator:latest`.
* [ ] Testar embeddings sob carga (batches 8, 16, 32).
* [ ] Validar latência p95 / p99.
* [ ] Simular 200–500 perguntas simultâneas.

---

## 11. Entrega Final — “2025.0-prod”

**🟦 Falta**

* [ ] Criar tag `2025.0-prod`.
* [ ] Congelar embeddings.
* [ ] Congelar ontologia.
* [ ] Congelar thresholds do planner.
* [ ] Ativar CI/CD com blue/green.
* [ ] Rodar smoke test no ambiente final.
* [ ] Publicar versão.

---
