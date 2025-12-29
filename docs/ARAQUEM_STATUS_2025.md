# ARAQUEM_STATUS_2025

> **Fonte única do estado atual do Araquem (pós-auditorias R1–R5).** Este documento é a referência canônica do que está ativo, opcional ou desabilitado no pipeline `/ask`, sem promessas futuras.

## 1. Fontes de verdade

* **Ontologia e contratos**: `data/ontology/entity.yaml` + `data/entities/**` (compute), `data/contracts/entities/*.schema.yaml` (schemas), SQL real em `docs/database/**` (intocável).
* **Policies YAML**: `data/policies/context.yaml`, `data/policies/narrator.yaml`, `data/policies/rag.yaml`, `data/policies/cache.yaml`, `data/ops/planner_thresholds.yaml`, `data/ops/param_inference.yaml`.
* **Runtime**: `/ask` em `app/api/ask.py`; orquestração em `app/orchestrator/routing.py`; Planner em `app/planner/*.py`; Builder/Executor/Formatter em `app/builder/sql_builder.py`, `app/executor/pg.py`, `app/formatter/rows.py`; Presenter/Narrator em `app/presenter/presenter.py`, `app/narrator/narrator.py`; ContextManager em `app/context/context_manager.py`.
* **Observabilidade**: OTEL + Prometheus em `app/observability/runtime.py` e métricas emitidas pelas camadas principais (`planner`, `cache`, `executor`, `rag`, `narrator`, `context`).

## 2. Pipeline `/ask` (compute-on-read, sem heurísticas)

1. **Planner** normaliza/tokeniza a pergunta e aplica thresholds declarativos (`data/ops/planner_thresholds.yaml`).【F:app/planner/planner.py†L65-L358】
2. **Registro do turno do usuário**: `/ask` sempre grava o turno `user` no ContextManager com intent/entity/bucket detectados.【F:app/api/ask.py†L94-L142】
3. **Herança condicionada (ContextManager)**: após extrair identificadores, `/ask` chama `resolve_last_reference(...)` para aplicar `context.yaml` (enable/TTL/buckets/allowed_entities) e só então segue com os identifiers resolvidos.【F:app/api/ask.py†L278-L308】【F:app/context/context_manager.py†L202-L315】
4. **Inferência e compute-on-read**: `infer_params(...)` aplica regras declarativas (`param_inference.yaml`) para agg/janela/limit/ordem; nada é inferido por heurística fora do YAML.【F:app/planner/param_inference.py†L488-L566】
5. **Orchestrator** revalida gate, monta SQL determinístico (Builder/Executor), tenta cache de métricas apenas quando a policy permite, e sempre gera o `meta.rag` canônico (aplicando a policy de RAG; se negado, retorna `{enabled: False, reason: ...}`).【F:app/orchestrator/routing.py†L702-L806】【F:app/rag/context_builder.py†L70-L152】
6. **Presenter** constrói baseline determinístico (`render_answer` + templates) e injeta `history` no `meta_for_narrator` somente quando `context.enabled` e a entidade é permitida pela policy de contexto.【F:app/presenter/presenter.py†L369-L407】
7. **Narrator** executa com `llm_enabled=False`/`shadow=False` (policy), portanto retorna o baseline; `use_conversation_context` e `use_rag_in_prompt` seguem `false` por padrão, mantendo o fluxo determinístico.【F:app/narrator/narrator.py†L85-L169】【F:data/policies/narrator.yaml†L1-L126】
8. **Registro do turno do assistant**: após responder (inclusive caminhos `unroutable/gated`), `/ask` grava o turno `assistant` e atualiza `last_reference` conforme policy; se o contexto estiver desabilitado, a operação é no-op.【F:app/api/ask.py†L708-L777】【F:app/context/context_manager.py†L215-L315】

## 3. Estado por componente (ativo x opcional x desligado por policy)

| Componente | Estado atual | Governança / observações |
| ---------- | ------------ | ------------------------ |
| **Planner** | **Ativo.** Ontologia YAML + thresholds reais; decisão única por pergunta; explain/gate expostos em `meta`. | `data/ops/planner_thresholds.yaml` (min_score/min_gap), `planner.rag` respeitado mas rerank desligado por policy. |
| **Builder/Executor/Formatter** | **Ativos.** SQL determinístico com contracts YAML; `formatter` só formata campos declarados. | `app/builder/sql_builder.py`, `app/executor/pg.py`, `app/formatter/rows.py`. |
| **Cache RT** | **Opcional.** Read-through apenas para entidades não privadas quando `cache.yaml` define TTL; fallback compute-on-read quando não há cache. | `app/cache/rt_cache.py` aplica policies; sanitize de campos sensíveis no hash. |
| **ContextManager** | **Ativo.** Registra user/assistant, aplica TTL/bucket TTL, resolve `last_reference` e fornece `history` ao Narrator quando permitido. In-memory, determinístico e auditável; se `context.enabled=false`, todas as operações viram no-op. | `app/context/context_manager.py` + `data/policies/context.yaml`; nenhuma heurística fora do YAML. |
| **RAG** | **Desligado por policy.** `rag.yaml` tem `allow_intents=[]` + `deny_intents` cobrindo intents atuais; `rerank.enabled=false`. O orchestrator ainda gera `meta.rag` com `enabled=False`/`reason` e nunca chama embeddings. | `app/rag/context_builder.py`, `data/policies/rag.yaml`. |
| **Narrator** | **Desligado para LLM.** `llm_enabled=false`, `shadow=false`, `use_conversation_context=false` por default; apenas baseline determinístico é retornado. | `data/policies/narrator.yaml`; Presenter ainda registra meta para auditoria. |
| **Contextualização histórica** | **Ativa, mas condicionada por policy.** `history` só é entregue ao Narrator quando `context.narrator.enabled=true` e a entidade está em `allowed_entities`; não há heurísticas de ordenação além do TTL/max_turns. | `app/presenter/presenter.py`, `data/policies/context.yaml`. |
| **Quality Gate** | **Ativo.** Gating por score/gap do Planner; caminhos `gated`/`unroutable` retornam resposta segura e ainda registram contexto. | `app/planner/planner.py`, `app/orchestrator/routing.py`, `app/api/ask.py`. |

## 4. Garantias e ausências

* **Sem heurísticas implícitas:** todas as decisões vêm de YAML/policies/ontologia; erros em loaders de policy resultam em status explícito ou falha rápida (sem fallback silencioso).【F:app/planner/planner.py†L20-L58】【F:app/rag/context_builder.py†L18-L68】
* **Compute-on-read como padrão:** parâmetros, janelas e agregações são inferidos a cada requisição via `param_inference.yaml`; não há pré-processamento ou cache obrigatório de respostas.【F:app/planner/param_inference.py†L488-L566】
* **Contexto determinístico:** histórico e `last_reference` são governados por `context.yaml`; se a policy estiver desligada, o restante do pipeline segue sem impacto operacional (fail-open controlado).【F:app/context/context_manager.py†L202-L315】
* **RAG e Narrator** permanecem opt-in por policy; no estado atual ambos estão neutros (RAG negado, LLM off), mantendo o `/ask` totalmente determinístico.
