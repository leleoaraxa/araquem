# ✅ **CHECKLIST ARAQUEM — RUMO À PRODUÇÃO (2025.0-prod)**

### *(versão Sirius 24/11 — consolidada e atualizada)*

---

# **0. Contexto Conversacional (M12–M13)**

> 🟩 *Base técnica pronta. Próxima etapa: ativar e calibrar.*

### ✔️ Feito:

* ✔ `context_manager.py` criado
* ✔ Integração mínima no `/ask` (append_turn)
* ✔ Presenter injeta `history` no meta do Narrator
* ✔ Policies definidas em `data/policies/context.yaml`
* ✔ Total compliance com Guardrails v2.1.1
* ✔ Zero impacto quando `enabled: false`

### 🔵 Falta:

* [ ] Ativar context (`enabled: true`) **somente após baseline**
* [ ] Definir quais entidades podem usar contexto
* [ ] Validar herança de referência (ex.: Sharpe do “fundo anterior”)
* [ ] Testar histórico em modo Narrator (sem afetar dados)
* [ ] Criar heurísticas leves para “entity fallback” no Narrator

---

# **1. RAG – Conteúdo e Políticas**

* [✔️] Collections revisadas por entidade
* [✔️] Collections específicas (risk, rankings, macro, mercado)
* [ ] Validar **quantidade real** de chunks por entidade
* [ ] Revisar **qualidade semântica** dos chunks
* [ ] Regerar embeddings (batch 8 – nomic-embed-text)
* [ ] Testar fusion/re-rank com perguntas reais
* [ ] Analisar RAG pelo `rag_debug.sh` após cada ajuste

---

# **2. Planner – Thresholds e Calibração Final**

* [ ] Revisar `planner_thresholds.yaml`
* [ ] Ajustar thresholds por intent/entity
* [ ] Validar explain logs:

  * [ ] intent_top2_gap
  * [ ] entity_top2_gap
* [ ] Validar comportamento com RAG habilitado
* [ ] Fechar baseline de roteamento final

---

# **3. Narrator – Versão para Produção**

* [✔️] Políticas estruturadas
* [✔️] Modelo sirios-narrator criado
* [ ] Ajustar `narrator.yaml` para produção
* [ ] Definir:

  * [ ] `llm_enabled`
  * [ ] `shadow`
  * [ ] `max_llm_rows`
  * [ ] `style`
  * [ ] `use_rag_in_prompt`
* [ ] Validar fallback seguro para cada entidade
* [ ] Testar estilo final (executivo / objetivo / curto)

---

# **4. RAG + Narrator – Integração Profissional**

* [ ] Definir políticas de uso do RAG no prompt
* [ ] Reduzir tamanho dos snippets (máx. 250–350 chars)
* [ ] Validar tempo de inferência com snippets
* [ ] Testar shadow mode real (com logs)
* [ ] Ajustar tamanho final do prompt (≤ 3800 tokens)

---

# **5. Quality – Baseline Final**

* [ ] Curadoria dos 16 misses
* [ ] Rodar `quality_list_misses.py` novamente
* [ ] Rodar `quality_diff_routing.py` em modo seguro (sem Ollama)
* [ ] Fixar baseline “2025.0-prod” no YAML
* [ ] Confirmar métricas `top1`, `top2_gap`, `routed_rate` no Grafana

---

# **6. Infra/Produção – Ambientes e Deploy**

* [ ] Configurar `DATABASE_URL` de produção
* [ ] Configurar OTEL Collector + Tempo + Prometheus + Grafana
* [ ] Definir dashboards finais (/ask, planner, narrator, rag)
* [ ] Ajustar Redis (TTL, namespaces, blue/green)
* [ ] Habilitar alertas de:

  * timeouts
  * cache-miss spikes
  * RAG latency high

---

# **7. Segurança & LGPD**

* [ ] Sanitização de PII no Presenter/Formatter
* [ ] Reduzir exposição de metas sensíveis em explain
* [ ] Ajustar tokens e policies de acesso (quality ops)
* [ ] Verificar que logs/traces não mostram payload completo
* [ ] Revisar roles do Postgres (sirios_api e edge_user)

---

# **8. Documentação Final**

* [ ] Atualizar `ARAQUEM_STATUS_2025.md`
* [ ] Atualizar diagramas C4 (context, container, component)
* [ ] Documentar:

  * [ ] RAG flows
  * [ ] Narrator
  * [ ] Context Manager
  * [ ] planner.explain()
  * [ ] policies (RAG/Narrator/Cache/Context)
* [ ] Documentar rotas `/ask` e `/ops/*`

---

# **9. Testes de Carga e Estresse**

* [ ] Testar throughput com sirios-narrator:latest
* [ ] Testar embeddings sob carga (batch 8, 16, 32)
* [ ] Validar latência p95/p99
* [ ] Simular 200–500 perguntas simultâneas

---

# **10. Entrega Final — “2025.0-prod”**

* [ ] Criar tag
* [ ] Congelar embeddings
* [ ] Congelar ontologia
* [ ] Congelar thresholds
* [ ] Ativar CI/CD com blue/green
* [ ] Smoke test no ambiente final
* [ ] Publicar versão

---

# ✔️ **Checklist atualizado e pronto**

Se quiser, posso:

👉 Priorizar a ordem de execução
👉 Criar um **roadmap de 3 dias** até produção
👉 Gerar um **Kanban CSV/Excel**
👉 Gerar um **patch plan** por módulo (RAG, Narrator, Planner, Context)

Só pedir.
