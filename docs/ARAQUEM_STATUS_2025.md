# ✅ **CHECKLIST ARAQUEM — RUMO À PRODUÇÃO (2025.0-prod)**

### *(versão Sirios — status alinhado ao `docs/ARAQUEM_STATUS_2025.md`: pipeline determinístico, ContextManager ativo por policy, buckets neutros por decisão explícita, RAG negado por policy, Narrator com LLM off por policy, quality gate ativo; freeze 2025.0 ainda “não apto” por pendências em contratos/coverage)*

---

## 0. Contexto Conversacional (M12–M13)

> 🟩 Contexto **ativo e auditável**, governado por `data/policies/context.yaml`. Próxima etapa: **validar impacto com LLM OFF** e estabilizar documentação operacional.

**✔️ Feito (confirmado no status atual)**

* [✔] `ContextManager` integrado ao `/ask` com registro de turnos `user/assistant` (best-effort).
* [✔] `/ask` aplica `resolve_last_reference(...)` de forma condicionada por policy (quando habilitado).
* [✔] Presenter injeta `history` **apenas quando** `context.enabled=true` e a entidade é permitida por policy.
* [✔] Política de contexto (`context.yaml`) governa TTL / limites / allowlist — sem heurísticas.

**🟦 Falta (M13 — refinamento / validação)**

* [ ] Rodar comparação controlada **LLM OFF**: respostas antes/depois de `context.enabled: true` (esperado: números idênticos; apenas herança de identificadores quando aplicável).
* [ ] Criar documentação operacional curta: `docs/dev/M13_CONTEXT_README.md` (escopo, TTL, last_reference, limites, casos esperados e anti-casos).
* [ ] Instrumentar/monitorar em ambiente controlado:

  * [ ] métricas de contexto/last_reference (hit rate, no-op rate)
  * [ ] logs de resolução (casos “ele/esse fundo”)

> Nota: **Buckets A/B/C/D estão neutros por decisão explícita** (`data/ontology/bucket_rules.yaml` disabled). Portanto, qualquer menção a “TTL por bucket” deve ser considerada **não aplicável** enquanto buckets estiverem neutros.

---

## 1. Entidades & Realidade dos Dados (D-1 vs Histórico)

> 🟩 A fonte canônica de estado é `docs/ARAQUEM_STATUS_2025.md`. Auditorias e inconsistências devem refletir esse documento (não o contrário).

**✔️ Feito (confirmado)**

* [✔] `docs/ARAQUEM_STATUS_2025.md` consolidado como fonte única do estado atual (pós R1–R5).
* [✔] Catálogo (`data/entities/catalog.yaml`) alinhado em pontos críticos (ex.: remover drift de `rag_policy` em `history_*` e `narrator_policy` indevido em `fiis_financials_revenue_schedule`).
* [✔] Contrato de `dividendos_yield` migrado para padrão tabular (R1 resolvido no nível de schema).

**🟦 Falta (bloqueios para “freeze apto”)**

* [ ] Padronizar cabeçalho de **todos** os contratos em `data/contracts/entities/*.schema.yaml` conforme padrão:

  * `entity == filename`, `name == entity`, `kind: view`, `description` não vazia.
* [ ] Revalidar cobertura cruzada Ontologia ↔ Catálogo ↔ Policies (lint estático / relatório).
* [ ] Fechar backlog de “modelagem fina” somente após o freeze ficar “APTO” (para evitar regressões).

---

## 2. RAG – Conteúdo e Políticas

> 🟨 Estado atual: **RAG negado por policy** no runtime. `meta.rag` é gerado com `enabled=false` e razão explícita.

**✔️ Feito (confirmado)**

* [✔] `data/policies/rag.yaml` mantém RAG efetivamente **desabilitado** para intents atuais (deny ativo; allow vazio).
* [✔] Orchestrator ainda gera `meta.rag` canônico com `{enabled: false, reason: ...}` (auditabilidade preservada).
* [✔] Catálogo não sinaliza RAG como ativo em `history_*` (drift removido).

**🟦 Falta (quando decidirem reativar, via policy e em lote próprio)**

* [ ] Definir plano de reativação **opt-in e restrito** (somente intents textuais), com métricas/latência/recall.
* [ ] Garantir que reativação não afeta números: RAG apenas contextual, nunca substitui SQL.

---

## 3. Planner – Thresholds e Calibração Final

> 🟩 Planner ativo e governado por ontologia + thresholds YAML.

**✔️ Feito (confirmado)**

* [✔] Ontologia central em `data/ontology/entity.yaml`.
* [✔] Thresholds declarativos em `data/ops/planner_thresholds.yaml`.
* [✔] ParamInference compute-on-read governado por YAML (`data/ops/param_inference.yaml`).

**🟦 Falta (produção controlada)**

* [ ] Rodar e registrar um baseline atual de quality (com evidência reproduzível):

  * [ ] comando(s) de suíte + output consolidado
  * [ ] anexar resultado (ex.: “0 misses”) com data/commit — sem placeholders
* [ ] Tratar caso “macro sem ticker” para preferir entidade conceitual quando aplicável (via ontologia/policy, sem heurística).

> Nota: **buckets neutros** ⇒ qualquer “calibração por bucket” não se aplica enquanto `bucket_rules.yaml` estiver disabled.

---

## 4. Narrator – Modelo & Policies (shadow mode)

> 🟨 Estado atual: **LLM desligado por policy** (`llm_enabled=false`, `shadow=false`). O baseline determinístico é a resposta final.

**✔️ Feito (confirmado)**

* [✔] `data/policies/narrator.yaml` com LLM desligado no estado atual.
* [✔] Presenter/Narrator preservam determinismo (não alteram `results`, apenas poderiam escrever meta quando habilitado).

**🟦 Falta (se/quando habilitar shadow, em lote próprio e com guardrails)**

* [ ] Criar `docs/dev/NARRATOR_README.md` (quando entra, o que pode alterar, métricas, exemplos).
* [ ] Preparar “shadow mode” como experimento controlado (dev/staging) antes de qualquer produção:

  * [ ] sampling + redaction + storage + métricas
* [ ] Ajuste dirigido de prompt/policy para casos limites (ex.: Sharpe negativo), **sem tocar em números**.

---

## 5. RAG + Narrator – Integração Profissional

> 🟨 Estado atual: integração existe como estrutura (meta/payload), mas **RAG e LLM estão neutros por policy**.

**✔️ Feito (confirmado)**

* [✔] Pipeline mantém “facts/rows/meta” como fonte determinística.
* [✔] Estrutura para meta de contexto/narrativa existe, mesmo com LLM OFF.

**🟦 Falta**

* [ ] Definir compute-mode “data vs concept” de forma declarativa (ontologia/policy), sem heurística.
* [ ] Garantir limites de payload para qualquer ativação futura (prompt budget).

---

## 6. Observabilidade do Narrator (Shadow Logs)

> 🟨 Estado atual: manter como **plano**; só marcar “feito” quando estiver realmente ativo e evidenciado.

**✔️ Feito**

* [ ] (Somente marcar como feito quando existir evidência no repo e no status canônico.)

**🟦 Falta**

* [ ] Se habilitar shadow: política + redaction + storage + métricas + README + processo de revisão humana.

---

## 7. Quality – Baseline Final

> 🟩 Quality gate ativo; baseline “0 misses” só deve ser declarado com evidência datada/commitada.

**✔️ Feito (confirmado parcialmente)**

* [✔] Quality gate existe e é aplicado (score/gap/routed).

**🟦 Falta (evidência formal do baseline)**

* [ ] Registrar baseline atual (data, commit, comando, output consolidado).
* [ ] Expandir dataset com perguntas reais e casos edge.

---

## 8. Infra / Produção – Ambientes e Deploy

**🟦 Falta**

* [ ] Definir DB prod (roles, schemas, migração).
* [ ] Stack OTEL/Tempo/Prometheus/Grafana coerente com o compose atual.
* [ ] Redis: TTL, chaves, blue-green, alertas.
* [ ] Checklist de smoke test pós-deploy (objetivo e curto).

---

## 9. Segurança & LGPD

**🟦 Falta**

* [ ] Redação de PII em logs/telemetria (sobretudo entidades privadas).
* [ ] Política de acesso ao explain (evitar vazamento de SQL/dados sensíveis).
* [ ] Revisão de privilégios no Postgres (read-only real, least privilege).

---

## 10. Documentação Final

**✔️ Feito (confirmado)**

* [✔] `docs/ARAQUEM_STATUS_2025.md` atualizado com o estado real (pós auditorias).

**🟦 Falta**

* [ ] Diagramas C4 atualizados.
* [ ] READMEs operacionais mínimos: Context, Quality, (futuro) RAG/Narrator.

---

## 11. Testes de Carga e Estresse

**🟦 Falta**

* [ ] p95/p99 por endpoint.
* [ ] simulação de bursts (200–500 perguntas).
* [ ] validar impacto de cache e contexto sob carga.

---

## 12. Entrega Final — “2025.0-prod”

> 🎯 Só declarar “2025.0-prod” quando o **freeze 2025.0** estiver **APTO**.

**🟦 Falta**

* [ ] Concluir padronização de contratos (`entity/name/kind/description`) + lint de coverage.
* [ ] Executar tag final do release (após “APTO”).
* [ ] Congelar ontologia/thresholds/policies na versão 2025.0 (versionamento).
* [ ] CI/CD blue-green + smoke test.

---

## 13. Plano de Trabalho de Amanhã — **Modo Safe (só concluir, sem quebrar nada)**

> Objetivo: **fechar pendências de freeze** e reforçar guardrails/documentação, **sem tocar em pipeline/core**.

**Escopo POSITIVO (pode mexer)**

* [ ] Ajustes **somente** em:

  * [ ] `data/contracts/entities/*.schema.yaml` (padronização de cabeçalho)
  * [ ] `docs/**` (READMEs operacionais e checklist)
  * [ ] policies/prompt **somente** se for documental (sem mudar runtime) — caso contrário, lote separado

**Escopo NEGATIVO (proibido)**

* [ ] ❌ Não alterar `planner`, `builder/sql_builder`, `executor/pg`, `presenter`, `context_manager`, `cache`.
* [ ] ❌ Não alterar contrato do `/ask`.
* [ ] ❌ Não criar novas entidades/views/projections.
* [ ] ❌ Não reativar RAG/LLM (shadow ou não) neste lote.
* [ ] ❌ Não mexer em buckets (continuam neutros até decisão explícita).
