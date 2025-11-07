# Data map — quick reference

| Arquivo | Objetivo | Principais consumidores | Momento de uso | Riscos / overlap |
| --- | --- | --- | --- | --- |
| data/concepts/catalog.yaml | Catálogo YAML para RAG | `scripts/embeddings/embeddings_build.py::build_index` | Pipeline de embeddings | Conteúdo duplicado com `fiis.md` |
| data/concepts/fiis.md | Texto conceitual FIIs | `scripts/embeddings/embeddings_build.py::build_index` | Pipeline de embeddings | Pode divergir das entidades |
| data/embeddings/index.yaml | Config do índice vetorial | `scripts/embeddings/embeddings_build.py::build_index` | Pipeline de embeddings | Paths quebrados derrubam geração |
| data/embeddings/store/embeddings.jsonl | Base vetorial consumida pelo planner | `Planner.explain` (RAG) | Request `/ask`, `/ops/quality/push` (quando RAG ativo) | Recarregado a cada request; depende de thresholds |
| data/embeddings/store/manifest.json | Manifesto do índice | — | — | Sem uso atual |
| data/entities/cache_policies.yaml | TTL de cache por entidade | `CachePolicies` via `app/core/context` | Bootstrap + `/ask` | Entidades novas exigem update manual |
| data/entities/<entidade>/entity.yaml | Contratos de entidades (SQL + aggregations) | `build_select_for_entity`, `_entity_agg_defaults`, `scripts/embeddings/embeddings_build.py` | Request `/ask` e QA projection | Defaults duplicados com `param_inference.yaml` |
| data/golden/.hash | Hash guard rails | `scripts/observability/hash_guard.py` | Script | Obsoleto se não regenerar |
| data/golden/m65_quality.{yaml,json} | Casos golden de roteamento | `scripts/embeddings/embeddings_build.py` | Pipeline de embeddings | Mesmas perguntas também em `routing_samples.json` |
| data/ontology/.hash | Hash da ontologia | `scripts/observability/hash_guard.py` | Script | Precisa atualização manual |
| data/ontology/entity.yaml | Ontologia intents→entities | `load_ontology`, `scripts/core/try_m3.py`, `scripts/embeddings/embeddings_build.py` | Bootstrap + todas as rotas que usam planner | Alterações impactam roteamento imediatamente |
| data/ops/quality_experimental/m66_projection.json | QA contract check explain | `scripts/quality/quality_push_cron.py` | Script (push `/ops/quality/push`) | Endpoint ainda não suporta o tipo |
| data/ops/quality_experimental/param_inference_samples.json | Regressão de inferência | `tests/test_param_inference.py` | Testes | Cron envia arquivo incompatível |
| data/ops/quality_experimental/planner_rag_integration.json | QA Planner+RAG | `scripts/quality/quality_push_cron.py`, `scripts/embeddings/embeddings_build.py` | Script | Backend não trata o tipo |
| data/ops/quality/projection_*.json | QA projeções por entidade | `scripts/quality/quality_push_cron.py` | Script (push `/ops/quality/push`) | Repete `columns` das entidades |
| data/ops/quality_experimental/rag_search_basics.json | QA busca vetorial | `scripts/quality/quality_push_cron.py` | Script | Endpoint sem implementação |
| data/ops/quality/routing_samples.json | QA roteamento contínuo | `scripts/quality/quality_push_cron.py`, `scripts/embeddings/embeddings_build.py` | Script + corpus RAG | Conteúdo duplicado com golden |
| data/ops/observability.yaml | Config de métricas/tracing | `load_config` (bootstrap) | Bootstrap | Deve refletir métricas reais definidas em código |
| data/ops/param_inference.yaml | Regras declarativas de agregação | `infer_params` | Request `/ask`, `/ops/quality/push` | Divergência com YAMLs de entidade |
| data/ops/planner_thresholds.yaml | Thresholds e config RAG | `_load_thresholds` (planner/orchestrator), `/ops/quality/report`, `scripts/quality/gen_quality_dashboard.py` | Request & scripts | Lido a cada request; fonte única para RAG e quality gates |

