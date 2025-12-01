# ✅ **CHECKLIST ARAQUEM — RUMO À PRODUÇÃO (2025.0-prod)**

### *(versão Sirius — 21 entidades auditadas, RAG limitado, Narrator em shadow, quality “✅ Sem misses”, contexto ligado, Shadow ligado em dev, experimento v0 configurado)*

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
  * `history_market_indicators` / `history_b3_indexes` / `history_currency_rates` (macro/índices/moedas)
* [✔] RAG **negado** para tudo numérico e privado.
* [✔] Collections alinhadas (`concepts-*`).
* [✔] Fallback seguro (`default`).
* [✔] Estado de RAG documentado em `ARAQUEM_STATUS_2025.md`.

**🟦 Falta**

* [ ] Monitorar latência, uso, recall real.
* [ ] Ajustar min_score/pesos com dados reais (usando `data/ops/quality*` + `data/golden`).

---

## 3. Planner – Thresholds e Calibração Final

> 🟩 Planner calibrado com baseline de roteamento **“Sem misses”**.

**✔️ Feito**

* [✔] Ontologia consolidada (`data/ontology/entity.yaml`).
* [✔] Conflitos resolvidos (macro, dy x dividendos, risk x snapshot).
* [✔] `param_inference.yaml` calibrado.
* [✔] Compute-on-read solidificado (D-1, janelas 3/6/12m, etc.).
* [✔] Thresholds finalizados por família (min_score, min_gap, por entidade).
* [✔] `quality_list_misses.py` → **0 misses**.
* [✔] `quality_diff_routing.py` limpo, sem regressões.

**🟦 Falta**

* [ ] Acompanhar `planner.explain()` em produção controlada (mapear dúvidas reais de usuário).
* [ ] Tratar explicitamente o caso “IPCA alto para FIIs?”:

  * [ ] Ajustar para preferir `history_market_indicators` (conceito) em vez de executar `fiis_financials_revenue_schedule` com 0 linhas.

---

## 4. Narrator – Modelo & Policies (shadow mode)

> 🟩 Narrator ativado em shadow, 100% seguro (zero impacto no answer).

**✔️ Feito**

* [✔] `data/policies/narrator.yaml` estruturado com:

  * [✔] `default` determinístico (LLM desligado).
  * [✔] Entidades com LLM+shadow:

    * `fiis_financials_risk`
    * `fiis_noticias`
    * `history_market_indicators`
    * `history_b3_indexes`
    * `history_currency_rates`
* [✔] `sirios-narrator:latest` integrado ao `app/narrator/narrator.py`.
* [✔] Presenter integrando Narrator, mas mantendo baseline determinístico como **fonte da resposta final** (shadow puro).
* [✔] `llm_enabled` / `shadow` por entidade controlados só por YAML.
* [✔] `max_llm_rows` ajustado (3–5) por entidade textual.
* [✔] Estilo executivo curto configurado via policy.
* [✔] Narrator respeita `prefer_concept_when_no_ticker` para entidades macro/risk (design pronto, ligado à policy).
* [✔] Instrumentação-base:

  * [✔] Latência por chamada (`sirios_narrator_latency_ms`).
  * [✔] Contador de render (`sirios_narrator_render_total`, outcome `ok|skip|error`).

**🟦 Falta**

* [ ] Rodar uma bateria de perguntas (usando `data/ops/quality*` + `data/golden`) para comparar textos do Narrator vs baseline.
* [ ] Ajustar estilo/nível de detalhe por entidade (risk vs notícias vs macro).
* [ ] Consolidar um `NARRATOR_README.md` explicando:

  * quando o Narrator entra,
  * o que ele pode ou não alterar,
  * como interpretar métricas.

---

## 5. RAG + Narrator – Integração Profissional

> 🟦 Seção atual de foco (UX + conceito + dados).

**✔️ Feito (setup inicial)**

* [✔] Narrator recebendo facts estruturados (`FactsPayload`) + snippets RAG limitados por entidade.
* [✔] Shadow mode ligado apenas para entidades textuais certas (risco, notícias, macro).
* [✔] Snippet RAG limitado por entidade via `rag_snippet_max_chars` em `narrator.yaml`:

  * [✔] `fiis_financials_risk`: 280 chars
  * [✔] `fiis_noticias`: 320 chars
  * [✔] `history_*`: 260 chars
* [✔] Policy `prefer_concept_when_no_ticker` ativada nas entidades macro, preparando terreno para perguntas conceituais (IPCA, juros, câmbio) sem ticker.
* [✔] Presenter já monta pacote completo para o Narrator:

  * [✔] Pergunta original.
  * [✔] Facts (rows/aggregates/identifiers).
  * [✔] Snippets de RAG.
  * [✔] Histórico de conversa (quando permitido).

**🟦 Falta (refino UX)**

* [ ] Fechar a regra de compute-mode (`data` vs `concept`) na prática:

  * [ ] Garantir que perguntas macro sem ticker caiam em modo conceito.
  * [ ] Garantir que perguntas “percentual da receita indexada ao IPCA do FII X” continuem em `fiis_financials_revenue_schedule` (dados).
* [ ] Validar tempo de inferência real do Narrator (p95/p99) em ambiente controlado.
* [ ] Desenhar exemplos canônicos de UX:

  * [ ] Risco de um FII (explicação simples a partir dos indicadores).
  * [ ] Interpretação de IPCA alto/baixo para FIIs.
  * [ ] Interpretação de notícia negativa/neutra/positiva.
* [ ] Ajustar prompt final para ficar sempre ≤ ~3800 tokens (contando contexto, RAG, facts).
* [ ] Criar prompts de verificação (anti-alucinação) no lado do Narrator (ex: “não inventar números; se não houver dados, dizer explicitamente”).

---

## 6. Observabilidade do Narrator (Shadow Logs)

> 🟩 Camada de auditabilidade do Narrator implementada, sem impacto no `/ask`.

**✔️ Feito**

* [✔] `data/policies/narrator_shadow.yaml` criado com:

  * [✔] `enabled`, `environment_allowlist`, `private_entities`.
  * [✔] Bloco de `sampling`:

    * [✔] `default` (rate=1.0, `only_when_llm_used`, `only_when_answer_nonempty`, `always_on_llm_error`).
    * [✔] Overrides por entidade (`fiis_financials_risk`, `fiis_noticias`, `history_market_indicators`).
  * [✔] Bloco de `redaction` (mask_fields, max_rows_sample, max_chars).
  * [✔] Bloco de `storage` com sink `file` (`logs/narrator_shadow/*.jsonl`, payload limitado por KB).
  * [✔] Bloco de `metrics` (`sirios_narrator_shadow_*`).
* [✔] Novo módulo `app/observability/narrator_shadow.py`:

  * [✔] Estrutura `NarratorShadowEvent`.
  * [✔] Integração com `narrator.yaml` via `_load_narrator_policy` + `_get_effective_policy`.
  * [✔] Lógica de sampling baseada em:

    * `llm_enabled` + `shadow` por entidade,
    * `environment_allowlist`,
    * `rate`,
    * erros de LLM (força coleta).
  * [✔] Redação de PII:

    * Mascara campos (`document_number`, `cpf`, `cnpj`, `email`, `phone`, etc.).
    * Entidades privadas (`client_fiis_*`) recebem redaction agressivo.
  * [✔] Registro de tamanho e descarte se exceder `max_shadow_payload_kb`.
* [✔] Hook no Presenter:

  * [✔] Monta `NarratorShadowEvent` com:

    * request (question, client_id, conversation_id, nickname),
    * routing (intent, entity, planner_score, tokens, thresholds),
    * facts,
    * rag,
    * narrator (strategy, error, latency, effective_policy),
    * presenter (answer_final, answer_baseline, rows_used, style).
  * [✔] Chama `collect_narrator_shadow(...)` em bloco `try/except` (best-effort absoluto).
* [✔] Métrica `sirios_narrator_shadow_total` com `outcome=ok|error`.
* [✔] Testes dedicados em `tests/observability/test_narrator_shadow.py` cobrindo:

  * [✔] Sampling em entidade pública (`fiis_noticias`).
  * [✔] Força de coleta em caso de erro de LLM.
  * [✔] Redação para entidade privada (`client_fiis_positions`).
* [✔] Experimento v0 configurado:

  * [✔] Arquivo de roteiro: `data/ops/quality_experimental/shadow_experiment_v0.yaml`.
  * [✔] Script executor: `scripts/experiments/run_shadow_experiment_v0.py` (chama `/ask` respeitando `conversation_id`/`client_id`).

**🟦 Falta**

* [ ] Rodar o script do experimento v0 em `dev`:

  * [ ] `docker-compose exec api bash` + `python scripts/experiments/run_shadow_experiment_v0.py`.
  * [ ] Verificar geração de `logs/narrator_shadow/narrator_shadow_*.jsonl`.
* [ ] Ajustar sampling efetivo por ambiente:

  * [ ] `dev`: rate alto (ex: 0.5–1.0).
  * [ ] `staging`: rate moderado (ex: 0.2).
  * [ ] `prod`: rate baixo (ex: 0.01–0.05), sempre `always_on_llm_error=true`.
* [ ] Desenhar plano de análise:

  * [ ] Como ler os JSONL (DuckDB / Python / outro).
  * [ ] Quais KPIs de Narrator queremos ver (taxa de erros, entidades que mais usam LLM, média de latência, etc.).
* [ ] Criar um pequeno `NARRATOR_SHADOW_README.md` com:

  * Estrutura do JSON.
  * Campos importantes.
  * Como amostrar casos para revisão manual.

---

## 7. Quality – Baseline Final

> 🟩 Quality com **0 misses** (*baseline determinístico*).

**✔️ Feito**

* [✔] Policies de quality alinhadas ao contrato atual de `/ask`.
* [✔] Datasets cobrindo FIIs, carteira do cliente, macro e compostas.
* [✔] Scripts de quality rodando sem RAG/LLM (`QUALITY_DISABLE_RAG=1`).
* [✔] Baseline **0 misses**, `quality_diff_routing.py` limpo.

**🟦 Falta**

* [ ] Expandir dataset com:

  * [ ] Perguntas reais de usuários (SIRIOS).
  * [ ] Perguntas dos arquivos em `data/ops/quality*` e `data/golden`.
* [ ] Criar dashboards de quality (futuro), ligando:

  * [ ] Acurácia de roteamento.
  * [ ] Diferença “baseline vs Narrator” por entidade.

---

## 8. Infra / Produção – Ambientes e Deploy

**🟦 Falta**

* [ ] Configurar DB prod (roles, schemas, migrations).
* [ ] Configurar OTEL/Tempo/Prometheus/Grafana para o stack atual.
* [ ] Dashboards finais (planner, executor, RAG, Narrator, Shadow).
* [ ] Ajustar Redis (TTL, chaves de cache, métricas).
* [ ] Alertas para:

  * [ ] timeouts,
  * [ ] cache-miss anormal,
  * [ ] latência alta de Narrator/RAG.

---

## 9. Segurança & LGPD

**🟦 Falta**

* [ ] Sanitizar PII no output onde for necessário (principalmente respostas de entidades privadas).
* [ ] Reduzir exposição do `explain` (não vazar SQL bruto/dados sensíveis).
* [ ] Policies de acesso operacional (quem pode rodar o quê).
* [ ] Garantir que logs não gravem payload completo desnecessariamente.
* [ ] Revisar roles do Postgres e privilégios de views materializadas.

---

## 10. Documentação Final

**✔️ Feito**

* [✔] `ARAQUEM_STATUS_2025.md` atualizado com estado real do projeto (pipeline `/ask`, RAG, Narrator, Quality, Context).

**🟦 Falta**

* [ ] Diagramas C4 atualizados (por serviço e pelo fluxo `/ask`).
* [ ] Documentar:

  * [ ] RAG (policies, collections, limites).
  * [ ] Narrator (policies, compute-mode, shadow).
  * [ ] Context Manager (last_reference, histórico).
  * [ ] Explain / analytics.
  * [ ] Policies de qualidade, RAG, cache, observability.

---

## 11. Testes de Carga e Estresse

**🟦 Falta**

* [ ] Testar Narrator sob carga (shadow ligado).
* [ ] Testar ingestão/consulta de embeddings em batches.
* [ ] Validar p95/p99 por endpoint.
* [ ] Simular 200–500 perguntas em janela curta.

---

## 12. Entrega Final — “2025.0-prod”

**🟦 Falta**

* [ ] Tag final do release.
* [ ] Congelar embeddings / ontologia / thresholds na versão 2025.0.
* [ ] CI/CD blue-green (rotina de deploy segura).
* [ ] Smoke test pós-deploy (checklist objetivo).
* [ ] Publicação e handover (interno SIRIOS).
