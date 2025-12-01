# ✅ **CHECKLIST ARAQUEM — RUMO À PRODUÇÃO (2025.0-prod)**

### *(versão Sirius — 21 entidades auditadas, RAG limitado, Narrator em shadow, quality “✅ Sem misses”, contexto ligado)*

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
* [✔] `context.last_reference.allowed_entities` alinhado com o uso real (preços, dividendos, yield, snapshot, overview, imóveis, rankings, processos, cadastro, notícias, `dividendos_yield`).

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

## 4. Narrator – Modelo & Policies (shadow mode)

> 🟩 Narrator ativado em **shadow mode** para entidades textuais, sem impacto na resposta final.

**✔️ Feito**

* [✔] Políticas estruturais de Narrator definidas em `data/policies/narrator.yaml`.
* [✔] Modelo `sirios-narrator:latest` criado e integrado (client funcionando).
* [✔] Presenter sempre constrói baseline determinístico e integra Narrator em modo opcional; **answer final** continua 100% determinístico.
* [✔] `llm_enabled: true` e `shadow: true` configurados para as entidades textuais piloto:

  * [✔] `fiis_financials_risk`
  * [✔] `fiis_noticias`
  * [✔] `history_market_indicators`
  * [✔] `history_b3_indexes`
  * [✔] `history_currency_rates`
* [✔] `use_rag_in_prompt: true` onde permitido por `rag.yaml` (risco, macro, notícias).
* [✔] `max_llm_rows` reduzido (3–5) por entidade piloto, evitando prompts gigantes.
* [✔] `prefer_concept_when_no_ticker` ativado onde faz sentido (risco, macro).
* [✔] Estilo do Narrator ajustado para **executivo / objetivo / curto**, em linha com o Brand Book SIRIOS.
* [✔] Fallback seguro garantido pelo Presenter: em shadow mode o output do Narrator é sempre ignorado para o `answer` final (apenas logado/analisado).
* [✔] Métricas do Narrator instrumentadas:

  * [✔] `sirios_narrator_tokens_in_total`
  * [✔] `sirios_narrator_tokens_out_total`
  * [✔] `sirios_narrator_prompt_chars_total`
  * [✔] `sirios_narrator_prompt_rows_total`
* [✔] Guardrails Araquem v2.2.0 respeitados:

  * [✔] `/ask` imutável (sem campos extras).
  * [✔] Zero hardcodes/heurísticas novas; tudo via `narrator.yaml` + `rag.yaml`.
  * [✔] Orchestrator, Planner, Builder e Formatter inalterados.

**🟦 Falta (Módulo Narrator)**

* [ ] Criar uma amostra fixa de perguntas reais para comparar:

  * [ ] Baseline determinístico vs. textos shadow do Narrator (apenas análise offline).
* [ ] Ajustar fino de `max_llm_rows` e estilo por entidade com base nessa amostra.
* [ ] Documentar claramente em `ARAQUEM_STATUS_2025.md`:

  * [ ] Lista de entidades com Narrator em shadow.
  * [ ] Garantia de não-impacto no `answer`.
  * [ ] Estratégia de leitura dos logs/metrics do shadow.

---

## 5. RAG + Narrator – Integração Profissional

> 🟦 Seção atual de foco: **refinar integração RAG → Narrator em shadow**.

**✔️ Feito (setup inicial)**

* [✔] Para as entidades textuais piloto, o Narrator já recebe:

  * [✔] `facts` determinísticos do baseline.
  * [✔] Contexto RAG limitado, via `use_rag_in_prompt: true` e `rag.entities`/`profiles` apropriados.
* [✔] RAG + Narrator ligados **apenas** para:

  * [✔] `fiis_noticias`.
  * [✔] `fiis_financials_risk` (com foco em explicação conceitual).
  * [✔] `history_market_indicators`, `history_b3_indexes`, `history_currency_rates`.
* [✔] `max_llm_rows` já reduzido (3–5) para conter o tamanho do prompt.

**🟦 Falta (refino Seção 5)**

* [ ] Definir políticas mais explícitas de uso do RAG no prompt do Narrator:

  * [ ] Limitar tamanho dos snippets (~250–350 caracteres) focados em explicação, não em número.
  * [ ] Normalizar formato dos trechos (ex.: bullet points curtos).
* [ ] Validar tempo de inferência com snippets menores e logs de shadow (impacto em p95/p99).
* [ ] Testar shadow mode com cenários reais:

  * [ ] Perguntas de risco qualitativo.
  * [ ] Notícias específicas de FII.
  * [ ] Perguntas sobre dólar, IPCA e índices em contexto macro.
* [ ] Ajustar tamanho final do prompt (≤ ~3800 tokens) com base nos experimentos.
* [ ] Registrar uma estratégia de “prompts de validação” para ler se o Narrator está:

  * [ ] Evitando criar números inexistentes.
  * [ ] Explicando conceitos com base no contexto (facts + RAG), sem delírio.

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
  * [ ] Narrator (incluindo shadow mode + métricas).
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

## 12. 🎯 Próxima Etapa Prioritária (atualizada)

> Com baseline determinístico fechado, RAG limitado, contexto ligado e Narrator em shadow nas entidades textuais, a **próxima etapa programada** é:

1. **Seção 5 – RAG + Narrator (refino)**

   * Refinar política de snippets (tamanho, formato, foco conceitual).
   * Medir impacto em latência e tokens.
   * Criar conjunto de perguntas “canônicas” de risco/macro/notícias para avaliar a qualidade do shadow.

2. **Em paralelo leve**

   * Avançar documentação (Seção 9) para RAG + Narrator + Contexto.
   * Preparar observabilidade (Seção 7) específica para Narrator/RAG em shadow (dashboards e alertas básicos).
