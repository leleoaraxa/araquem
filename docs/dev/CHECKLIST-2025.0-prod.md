# ✅ **CHECKLIST ARAQUEM — RUMO À PRODUÇÃO (2025.0-prod)**

### *(versão Sirius — 21 entidades auditadas, RAG/Narrator/Quality alinhados, baseline de roteamento “✅ Sem misses”)*

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

  * [✔] `context_sanity_check.py` (CNPJ → Sharpe → overview, ticker herdado).
  * [✔] `context_sanity_check_news_processos_risk.py` (notícias → processos → risco, ticker herdado).
* [✔] `context.last_reference.allowed_entities` alinhado com o uso real (preços, dividendos, yield, snapshot, overview, imóveis, rankings, processos, cadastro, notícias, dividendos_yield).

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

> 🟩 21 entidades auditadas e documentadas em `docs/dev/ARAQUEM_STATUS_2025.md`.

**✔️ Feito**

* [✔] Auditoria profunda das 21 entidades (FIIs, macro, cliente privado, compostas).
* [✔] Classificação D-1 / histórica / quase estática com periodicidade, cardinalidade e chaves naturais mapeadas.
* [✔] Riscos de interpretação e aderência a RAG / Narrator / quality / cache avaliados.
* [✔] Relato consolidado em `docs/dev/ARAQUEM_STATUS_2025.md` (versão atualizada com notas sobre perguntas conceituais sem ticker, DY, compostas e macro).
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

* [ ] Backlog de modelagem fina (novas entidades futuras, ajustes avançados) — seguir `docs/dev/ARAQUEM_STATUS_2025.md` como fonte.

---

## 2. RAG – Conteúdo e Políticas

> 🟩 RAG limitado, seguro e alinhado às políticas v2.

**✔️ Feito**

* [✔] `data/policies/rag.yaml` revisado para **versão 2**, com:

  * [✔] Perfis `default`, `macro`, `risk` (k, `min_score`, pesos `bm25`/`semantic`, `tie_break`, `max_context_chars`).
  * [✔] `routing.deny_intents` e `routing.allow_intents` alinhados ao catálogo e ao Guardrails.
* [✔] RAG **permitido apenas** para intents textuais/explicativas:

  * [✔] `fiis_noticias`.
  * [✔] `fiis_financials_risk` (apenas explicação conceitual, nunca números).
  * [✔] `history_market_indicators`, `history_b3_indexes`, `history_currency_rates`.
* [✔] RAG **negado** para:

  * [✔] Todas as entidades puramente numéricas (históricas e snapshots).
  * [✔] Entidades privadas de cliente.
  * [✔] Overview consolidado (`fii_overview`).
  * [✔] Entidades compostas numéricas (`dividendos_yield`, `carteira_enriquecida`, `macro_consolidada`).
* [✔] `rag.entities` alinhado com o catálogo, usando collections:

  * [✔] `fiis_noticias` → `fiis_noticias`, `concepts-fiis`, `concepts-risk`.
  * [✔] `fiis_financials_risk` → `concepts-risk`, `concepts-fiis`.
  * [✔] macro/índices/moedas → `concepts-macro`.
* [✔] `rag.default` configurado para fallback seguro (`concepts-fiis`, `min_score: 0.25`).
* [✔] ARAQUEM_STATUS atualizado explicando claramente o escopo do RAG (onde entra e onde é explicitamente negado).

**🟦 Falta**

* [ ] Monitorar em ambiente real:

  * [ ] Latência e uso de RAG por intent.
  * [ ] Relevância dos snippets (`rag_eval_*` em `data/ops/quality_experimental`).
* [ ] Reabrir ajuste fino de `profiles.*.min_score`/pesos apenas com base em métricas reais.

---

## 3. Planner – Thresholds e Calibração Final

> 🟩 Planner calibrado com baseline de roteamento **“✅ Sem misses”**.

**✔️ Feito**

* [✔] Ontologia refinida em `data/ontology/entity.yaml` distinguindo dividendos × DY × rankings × compostas.
* [✔] Roteamento de notícias negativas, dólar e IPCA ajustado (evitando colisão com preços).
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
* [✔] Thresholds afinados em `data/ops/planner_thresholds.yaml` por família:

  * [✔] Históricas numéricas (`fiis_precos`, `fiis_dividendos`, `fiis_yield_history`) com `min_score ≈ 0.9`, `min_gap ≈ 0.15`.
  * [✔] Snapshot de risco (`fiis_financials_risk`) com `min_score ≈ 0.85`, `min_gap = 0.2`.
  * [✔] Snapshots numéricos de contexto (`fiis_imoveis`, `fiis_processos`) com `min_score ≈ 0.85`.
  * [✔] Compostas (`dividendos_yield`, `carteira_enriquecida`, `macro_consolidada`) mais rígidas (`min_score: 0.9`, `min_gap: 0.2`).
  * [✔] Intents e entities com blocos separados, mantendo contrato `apply_on: fused`.
* [✔] Conflitos resolvidos:

  * [✔] `macro_consolidada` vs `history_market_indicators`.
  * [✔] `dividendos_yield` vs `fiis_dividendos`.
* [✔] `quality_list_misses.py`:

  * [✔] Agora retorna **“✅ Sem misses.”** com o dataset atual.
* [✔] `quality_diff_routing.py`:

  * [✔] Confirmado sem divergências relevantes no roteamento.

**🟦 Falta**

* [ ] Usar `planner.explain()` em produção controlada para observar fronteiras reais (onde o usuário força ambiguidades) e, se necessário, reabrir micro-ajustes de thresholds.

---

## 4. Narrator – Modelo & Policies

> 🎯 Próxima grande frente funcional (após baseline determinístico consolidado).

**✔️ Feito**

* [✔] Políticas estruturais de Narrator definidas em `data/policies/narrator.yaml`.
* [✔] Modelo `sirios-narrator:latest` criado e integrado (client funcionando).
* [✔] Presenter sempre constrói baseline determinístico e integra Narrator em modo opcional.
* [✔] Estado atual documentado: LLM globalmente OFF, inclusive para risco/macro/notícias.

**🟦 Falta (Módulo Narrator)**

* [ ] Definir plano de ativação:

  * [ ] Habilitar `shadow` em subconjunto de entidades textuais (ex.: risco, macro, notícias).
  * [ ] Manter `answer` sempre igual ao baseline neste primeiro ciclo.
* [ ] Ajustar `narrator.yaml` para modo shadow:

  * [ ] `llm_enabled: true` apenas para entidades piloto.
  * [ ] `shadow: true` para essas entidades.
  * [ ] `max_llm_rows` adequado por entidade (ex.: risco vs notícias).
  * [ ] `style` (executivo/objetivo/curto) consistente com brand book SIRIOS.
  * [ ] `use_rag_in_prompt` somente onde permitido por `rag.yaml`.
* [ ] Validar fallback seguro por entidade (quando **NÃO** usar LLM).
* [ ] Testar estilo final de resposta com amostras reais, sempre comparando baseline vs shadow.

---

## 5. RAG + Narrator – Integração Profissional

**🟦 Falta**

* [ ] Definir políticas de uso do RAG no prompt do Narrator (quando e como injetar contexto RAG).
* [ ] Reduzir tamanho dos snippets (≈ 250–350 caracteres) focados em explicação, não em número.
* [ ] Validar tempo de inferência com snippets menores e logs de shadow.
* [ ] Testar shadow mode real do Narrator com RAG ligado apenas em:

  * [ ] `fiis_noticias`.
  * [ ] `fiis_financials_risk` (parte conceitual).
  * [ ] Macro/índices/moedas.
* [ ] Ajustar tamanho final do prompt (≤ ~3800 tokens) com base nos experimentos.

---

## 6. Quality – Baseline Final

> 🟩 Baseline de roteamento consolidado, sem misses no dataset atual.

**✔️ Feito**

* [✔] `data/policies/quality.yaml` revisado com `targets` realistas.
* [✔] Cobertura de datasets: FIIs, Cliente (privado), Macro, Compostos.
* [✔] `accepted_range` ajustado por entidade.
* [✔] `quality_list_misses.py` e `quality_diff_routing.py` rodando em modo **sem Ollama** (via flag/env).
* [✔] Baseline atual:

  * [✔] `python scripts/quality/quality_list_misses.py` → **“✅ Sem misses.”**
  * [✔] `quality_diff_routing.py` sem divergências relevantes.
  * [✔] `routing_samples` cobrindo compostos e cenários multi-turno com contexto.
* [✔] Estado consolidado descrito em `docs/dev/ARAQUEM_STATUS_2025.md`.

**🟦 Falta**

* [ ] Expandir o dataset de qualidade de forma incremental (novos cenários reais dos usuários).
* [ ] Conectar dashboards do Grafana para quality:

  * [ ] `top1`, `top2_gap`, `routed_rate`.
  * [ ] Métricas de erros e de misses corrigidos ao longo do tempo.

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

**✔️ Feito**

* [✔] `docs/dev/ARAQUEM_STATUS_2025.md` atualizado com:

  * [✔] Calibração real de thresholds por família.
  * [✔] Escopo real do RAG (allow/deny por intent).
  * [✔] Estado das entidades compostas (`dividendos_yield`, `carteira_enriquecida`, `macro_consolidada`).
  * [✔] Notas sobre perguntas conceituais “sem ticker” retornarem zero rows no baseline (aguardando Narrator).
  * [✔] Estado consolidado de quality (**0 misses**).

**🟦 Falta**

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

* [ ] Testar throughput com `sirios-narrator:latest` em modo shadow.
* [ ] Testar embeddings sob carga (batches 8, 16, 32).
* [ ] Validar latência p95 / p99 para:

  * [ ] `/ask` puro SQL.
  * [ ] `/ask` com RAG.
  * [ ] `/ask` com Narrator em shadow.
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

## 12. 🎯 Próxima Etapa Prioritária

> Com baseline determinístico fechado (RAG limitado, quality “✅ Sem misses”, contexto ligado), a **próxima etapa programada** é:

1. **Seção 4 – Narrator (shadow mode)**

   * Ativar `sirios-narrator:latest` em shadow para entidades textuais (risco, macro, notícias), sem mudar a resposta final.
   * Instrumentar bem métricas de uso, latência e tamanho de prompt.

2. **Seção 5 – RAG + Narrator**

   * Testar a integração RAG→Narrator em shadow, com snippets curtos e foco em explicação conceitual.

3. **Paralelo leve**

   * Avançar itens de documentação (Seção 9) e observabilidade (Seção 7) para apoiar esses testes em ambiente controlado.
