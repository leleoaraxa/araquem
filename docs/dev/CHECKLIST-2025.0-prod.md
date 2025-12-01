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

  * [✔] `context_sanity_check.py` (CNPJ → Sharpe → overview).
  * [✔] `context_sanity_check_news_processos_risk.py` (notícias → processos → risco).
* [✔] `context.last_reference.allowed_entities` alinhado com o uso real.

**🟦 Falta (M13 — refinamento)**

* [ ] Testar **LLM OFF** comparando respostas antes/depois de `context.enabled: true`.
* [ ] Criar `M13_CONTEXT_README.md` (prioridades de ticker, escopo, evolução segura).
* [ ] Monitorar em ambiente controlado:

  * [ ] `planner_rag_context_*`
  * [ ] Logs de padrão real de “esse fundo / ele”.

---

## 1. Entidades & Realidade dos Dados (D-1 vs Histórico)

> 🟩 21 entidades auditadas e documentadas em `docs/dev/ARAQUEM_STATUS_2025.md`.

**✔️ Feito**

* [✔] Auditoria profunda das 21 entidades.
* [✔] Classificação D-1 / histórica / quase-estática.
* [✔] Impactos sobre RAG, Narrator, Quality e cache mapeados.
* [✔] Documentado em `ARAQUEM_STATUS_2025.md`.
* [✔] `entities_consistency_report.yaml` garantindo integridade (schema, policies, quality).
* [✔] Novos projections:

  * [✔] `client_fiis_dividends_evolution`
  * [✔] `client_fiis_performance_vs_benchmark`
  * [✔] `fii_overview`
  * [✔] `fiis_yield_history`
  * [✔] Compostas: `dividendos_yield`, `carteira_enriquecida`, `macro_consolidada`
* [✔] `routing_samples.json` atualizado com compostas e multi-turno.

**🟦 Falta**

* [ ] Backlog de modelagem fina — seguir `ARAQUEM_STATUS_2025.md`.

---

## 2. RAG – Conteúdo e Políticas

> 🟩 RAG limitado, seguro e alinhado às políticas v2.

**✔️ Feito**

* [✔] `rag.yaml` revisto (versão 2): perfis `default`, `macro`, `risk`.
* [✔] RAG permitido apenas para intents textuais:

  * `fiis_noticias`
  * `fiis_financials_risk`
  * macro / índices / moedas
* [✔] RAG **negado** para tudo numérico e privado.
* [✔] Collections alinhadas (`concepts-*`).
* [✔] Fallback seguro (`default`).
* [✔] Estado de RAG documentado em `ARAQUEM_STATUS_2025.md`.

**🟦 Falta**

* [ ] Monitorar latência, uso, recall real.
* [ ] Ajustar min_score/pesos com dados reais.

---

## 3. Planner – Thresholds e Calibração Final

> 🟩 Planner calibrado com baseline de roteamento **“Sem misses”**.

**✔️ Feito**

* [✔] Ontologia consolidada (`entity.yaml`).
* [✔] Conflitos resolvidos (macro, dy x dividendos, risk x snapshot).
* [✔] `param_inference.yaml` calibrado.
* [✔] Compute-on-read solidificado.
* [✔] Thresholds finalizados por família.
* [✔] `quality_list_misses.py` → **0 misses**.
* [✔] `quality_diff_routing.py` limpo.

**🟦 Falta**

* [ ] Acompanhar `planner.explain()` em produção controlada.

---

## 4. Narrator – Modelo & Policies (shadow mode)

> 🟩 Narrator ativado em shadow, 100% seguro (zero impacto no answer).

**✔️ Feito**

* [✔] `narrator.yaml` estruturado.
* [✔] `sirios-narrator:latest` integrado.
* [✔] Presenter integrando Narrator mas mantendo baseline determinístico final.
* [✔] Shadow mode habilitado para 5 entidades textuais.
* [✔] `use_rag_in_prompt: true` onde permitido.
* [✔] `max_llm_rows` ajustado (3–5).
* [✔] Estilo executivo curto.
* [✔] Instrumentação completa:

  * tokens_in/out
  * prompt_chars
  * prompt_rows
  * latency
* [✔] Respeito total ao Guardrails v2.2.0.

**🟦 Falta**

* [ ] Criar amostra fixa de perguntas para comparação baseline vs shadow.
* [ ] Ajustar estilo e `max_llm_rows`.
* [ ] Documentar tudo em `ARAQUEM_STATUS_2025.md`.

---

## 5. RAG + Narrator – Integração Profissional

> 🟦 Seção atual de foco.

**✔️ Feito (setup inicial)**

* [✔] Narrator recebendo facts + snippets RAG limitados.
* [✔] Shadow mode ligado só para entidades certas.
* [✔] Prompts menores garantindo segurança.

**🟦 Falta (refino)**

* [ ] Limitar snippet RAG (~250–350 chars).
* [ ] Normalizar formatação (bullets curtos).
* [ ] Validar tempo de inferência real.
* [ ] Testar cenários reais.
* [ ] Ajustar prompt final ≤ 3800 tokens.
* [ ] Criar prompts de verificação (anti-alucinação).

---

## 6. Quality – Baseline Final

> 🟩 Quality com **0 misses**.

**✔️ Feito**

* [✔] Policies realistas.
* [✔] Datasets FIIs + Cliente + Macro + Compostos.
* [✔] Scripts rodando sem RAG/Ollama.
* [✔] Baseline **0 misses**, diff limpo.

**🟦 Falta**

* [ ] Expandir dataset com casos reais.
* [ ] Criar dashboards de quality (later).

---

## 7. Infra / Produção – Ambientes e Deploy

**🟦 Falta**

* [ ] Configurar DB prod.
* [ ] Configurar OTEL/Tempo/Prometheus/Grafana.
* [ ] Dashboards finais.
* [ ] Ajustar Redis.
* [ ] Alertas para timeouts, cache-miss, latência Narrator/RAG.

---

## 8. Segurança & LGPD

**🟦 Falta**

* [ ] Sanitizar PII no output.
* [ ] Reduzir exposição do `explain`.
* [ ] Policies de acesso (ops).
* [ ] Logs sem payload completo.
* [ ] Revisar roles do Postgres.

---

## 9. Documentação Final

**✔️ Feito**

* [✔] `ARAQUEM_STATUS_2025.md` atualizado com todo estado real.

**🟦 Falta**

* [ ] Diagramas C4.
* [ ] Documentar RAG / Narrator / Context Manager / explain / policies / rotas.

---

## 10. Testes de Carga e Estresse

**🟦 Falta**

* [ ] Testar Narrator under load.
* [ ] Testar embeddings batches.
* [ ] Validar p95/p99.
* [ ] Simular 200–500 perguntas.

---

## 11. Entrega Final — “2025.0-prod”

**🟦 Falta**

* [ ] Tag.
* [ ] Congelar embeddings / ontologia / thresholds.
* [ ] CI/CD blue-green.
* [ ] Smoke test.
* [ ] Publicação.
