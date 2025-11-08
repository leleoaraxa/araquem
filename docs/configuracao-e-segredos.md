# Configuração e segredos

> **Como validar**
> - Compare `.env.example`, `docker-compose.yml` e as chamadas `os.getenv` no código para garantir que os valores estejam alinhados e com defaults seguros.【F:.env.example†L1-L43】【F:docker-compose.yml†L2-L185】【F:app/api/ask.py†L28-L170】
> - Revise os YAMLs em `data/ops/` e `data/policies/` para confirmar políticas declarativas carregadas em runtime.【F:data/ops/observability.yaml†L1-L120】【F:data/ops/param_inference.yaml†L1-L80】【F:data/policies/cache.yaml†L8-L71】
> - Verifique quem consome cada variável observando a injeção nos módulos (`planner`, `orchestrator`, `narrator`, scripts de ops).【F:app/planner/planner.py†L187-L345】【F:app/orchestrator/routing.py†L208-L459】【F:app/narrator/narrator.py†L71-L120】【F:scripts/quality/quality_push.py†L21-L22】

## Variáveis de ambiente principais

| Variável | Local (arquivo/env) | Default / exemplo | Consumidores | Observações |
| --- | --- | --- | --- | --- |
| `DATABASE_URL` ⚠️ | `.env`, pipeline CI | `postgresql://edge_user:senha@...` | `PgExecutor`, healthcheck, explain analytics, testes | ⚠️ Sensível; obrigatório para queries e INSERT de explain.【F:.env.example†L1-L3】【F:app/executor/pg.py†L21-L69】【F:app/api/ask.py†L272-L299】 |
| `REDIS_URL` ⚠️ | `.env`, compose | `redis://redis:6379/0` | `RedisCache`, health `/health/redis`, testes | ⚠️ Sensível; fallback local `redis://redis:6379/0`.【F:.env.example†L1-L4】【F:app/cache/rt_cache.py†L44-L216】【F:app/api/health.py†L11-L33】 |
| `ONTOLOGY_PATH` | `.env`, default | `data/ontology/entity.yaml` | `Planner` no `core.context` | Pode apontar para ontologia alternativa; recarregar planner se alterar.【F:.env.example†L32-L33】【F:app/core/context.py†L9-L17】 |
| `OBSERVABILITY_CONFIG` | `.env`, compose | `data/ops/observability.yaml` | `load_config()` no bootstrap | Determina métricas habilitadas e tracing.【F:.env.example†L24-L31】【F:app/observability/runtime.py†L17-L96】 |
| `PROMETHEUS_URL` | `.env`, compose | `http://prometheus:9090` | Métricas runtime e scripts de qualidade | Utilizado por façade e scripts para queries de saúde.【F:.env.example†L24-L31】【F:scripts/quality/quality_push_cron.py†L189-L206】 |
| `GRAFANA_URL` | `.env`, compose | `http://grafana:3000` | Scripts/observabilidade (dashboards) | Referência em pipelines de dashboards.【F:.env.example†L24-L31】【F:Makefile†L1-L110】 |
| `OTEL_EXPORTER_OTLP_ENDPOINT` ⚠️ | `.env`, compose | `http://otel-collector:4317` | `init_tracing` | Deve apontar para collector válido; combina com `service.name`.【F:.env.example†L24-L31】【F:app/observability/runtime.py†L24-L64】 |
| `BUILD_ID` | `.env`, compose | `dev-20251030` | Cache keys, health payload | Parte da chave Redis e metadados de resposta.【F:.env.example†L36-L41】【F:app/cache/rt_cache.py†L169-L173】【F:app/api/health.py†L11-L27】 |
| `CACHE_OPS_TOKEN` ⚠️ | `.env`, compose env | `araquem-secret-bust-2025` | `/ops/cache/bust` auth | ⚠️ Deve ser secreto; sem token válido rota retorna 403.【F:.env.example†L36-L41】【F:app/api/ops/cache.py†L19-L39】 |
| `QUALITY_OPS_TOKEN` ⚠️ | `.env`, compose env | `araquem-secret-bust-2025` | Quality cron, `/ops/quality/*`, `/ops/metrics` | ⚠️ Sensível; header configurável e suporte a Bearer.【F:.env.example†L36-L41】【F:app/api/ops/quality.py†L29-L99】【F:app/api/ops/metrics.py†L15-L38】 |
| `QUALITY_TOKEN_HEADER` | compose (cron) | `X-OPS-TOKEN` | `/ops/quality/push` | Define header case-insensitive para autenticação.【F:docker-compose.yml†L149-L170】【F:app/api/ops/quality.py†L41-L58】 |
| `QUALITY_AUTH_BEARER` | compose (cron) | `false` | `/ops/quality/push` | Habilita fallback Bearer; valores verdadeiros aceitam header Authorization.【F:docker-compose.yml†L149-L170】【F:app/api/ops/quality.py†L49-L60】 |
| `QUALITY_ALLOW_RAG` | scripts | `1/0` | `quality_push_cron.py` | Permite avaliar RAG em rotas quality.【F:scripts/quality/quality_push_cron.py†L189-L213】 |
| `RAG_INDEX_PATH` | `.env`, compose | `data/embeddings/store/embeddings.jsonl` | Planner (RAG hints), `/ops/metrics/rag`, Ask | Compartilhado com cron de refresh e rotas de analytics.【F:.env.example†L21-L23】【F:app/planner/planner.py†L187-L213】【F:app/api/ops/rag.py†L12-L80】 |
| `OLLAMA_URL` / `OLLAMA_BASE_URL` | `.env`, compose env | `http://ollama:11434` | `OllamaClient` e scripts embeddings | Ajusta host para embedder e Narrator.【F:.env.example†L9-L18】【F:app/rag/ollama_client.py†L18-L99】 |
| `OLLAMA_EMBED_MODEL` | compose | `nomic-embed-text` | Planner (embeddings), rag-indexer | Alinha modelo de embedding com store.【F:docker-compose.yml†L76-L90】【F:app/planner/planner.py†L187-L236】 |
| `LLM_MODEL` / `NARRATOR_MODEL` | `.env`, Narrator | `mistral:instruct` | Narrator e `OllamaClient.generate` | Seleção do modelo generativo; fallback textual se indisponível.【F:.env.example†L9-L19】【F:app/narrator/narrator.py†L71-L120】【F:app/rag/ollama_client.py†L100-L135】 |
| `NARRATOR_ENABLED` / `NARRATOR_SHADOW` | `.env` | `false` / `true` | `app/api/ask` | Controla modo shadow ou substituição total da resposta.【F:.env.example†L15-L18】【F:app/api/ask.py†L25-L254】 |
| `LLM_TIMEOUT` / `NARRATOR_TIMEOUT` | `.env` | `60` | `OllamaClient` | Timeout de embed/generate; se ausente usa default do construtor.【F:.env.example†L9-L19】【F:app/rag/ollama_client.py†L22-L59】 |
| `PLANNER_THRESHOLDS_PATH` | env opcional | `data/ops/planner_thresholds.yaml` | Orchestrator gates | Permite alternar thresholds sem redeploy.【F:app/orchestrator/routing.py†L41-L240】【F:data/ops/planner_thresholds.yaml†L1-L32】 |
| `FILECACHE_DISABLE` | env opcional | `0` | `app.utils.filecache` | Quando `1`, força reload de YAML/JSONL a cada acesso (debug).【F:app/utils/filecache.py†L12-L115】 |
| `ARAQUEM_ASK_URL`, `ARAQUEM_NICKNAME`, `ARAQUEM_CLIENT_ID` | scripts core | defaults (`http://localhost:8000/ask`, `Leleo`, `cli-local`) | `scripts/core/ask.py` | Facilita testes CLI do endpoint /ask.【F:scripts/core/ask.py†L33-L156】 |
| `QUALITY_CONVERSATION_ID`, `QUALITY_NICK`, `QUALITY_CLIENT` | scripts quality | defaults `ops-quality`, `ops`, `ops` | `quality_diff_routing.py`, `quality_push_cron.py` | Identificadores usados nos payloads de quality.【F:scripts/quality/quality_diff_routing.py†L12-L16】 |
| `SIRIOS_METRICS_STRICT` | `.env` | `false` | `app.observability.metrics` | Quando `true`, bloqueia labels desconhecidas em métricas.【F:.env.example†L24-L31】【F:app/observability/metrics.py†L18-L134】 |
| `EXECUTOR_MODE` | compose | `read-only` | Dockerfile API | Indicativo operacional (não usado diretamente no código).【F:docker-compose.yml†L11-L18】【F:docker/Dockerfile.api†L38-L44】 |

⚠️ Indica segredos/credenciais que não devem ser versionados com valores reais.

## Arquivos de configuração declarativa

| Arquivo | Conteúdo | Consumidores | Observações |
| --- | --- | --- | --- |
| `data/ops/observability.yaml` | Catálogo de métricas, thresholds e dashboards | `load_config` no bootstrap, scripts Grafana | Define buckets, alertas e bindings Prometheus; manter sincronizado com `grafana/` e `prometheus/`.【F:data/ops/observability.yaml†L1-L120】 |
| `data/ops/param_inference.yaml` | Regras de inferência de agregação/tempo por intent | Planner/Orchestrator (`infer_params`) | Permite ajustar janelas e métricas sem alterar código; fallback vazio gera SELECT básico.【F:data/ops/param_inference.yaml†L1-L64】【F:app/orchestrator/routing.py†L288-L298】 |
| `data/ops/planner_thresholds.yaml` | Limiares de score/gap e configuração RAG | Planner & Orchestrator | Controla gates por intent/entity e modo de fusão RAG (blend/additive).【F:data/ops/planner_thresholds.yaml†L1-L34】【F:app/planner/planner.py†L187-L345】 |
| `data/policies/cache.yaml` | TTL e escopos de cache por entidade | `CachePolicies`, `/ops/cache` | Atenção a typos (`cope` em algumas entradas); escopo inválido cai no default público.【F:data/policies/cache.yaml†L8-L47】【F:app/cache/rt_cache.py†L15-L200】 |
| `data/entities/*/entity.yaml` | Contratos NL→SQL por entidade (colunas, agregações, synonyms) | SQL Builder, Planner, Formatter | É a fonte de verdade dos campos disponíveis e result_key; usado também por templates do Narrator.【F:data/entities/fiis_precos/entity.yaml†L1-L115】【F:app/builder/sql_builder.py†L18-L160】 |
| `grafana/`, `prometheus/`, `tempo/` | Dashboards e regras geradas | Observabilidade stack | Regenerar via `make dashboards` / `make regen-observability` após ajustes no YAML base.【F:Makefile†L58-L90】 |

## Precedência e carregamento

1. Variáveis de ambiente sobrescrevem defaults embutidos no código (por exemplo, `REDIS_URL`, `NARRATOR_ENABLED`).【F:app/cache/rt_cache.py†L44-L173】【F:app/api/ask.py†L25-L171】
2. Quando o valor não está presente no ambiente, o código recorre a defaults hardcoded ou arquivos YAML (ontologia, thresholds, policies).【F:app/core/context.py†L9-L17】【F:app/orchestrator/routing.py†L288-L298】【F:data/policies/cache.yaml†L8-L71】
3. Scripts e crons preferem argumentos CLI, depois variáveis de ambiente, por fim defaults definidos no próprio script (ver `scripts/core/ask.py`).【F:scripts/core/ask.py†L33-L168】

## Lacunas

- LACUNA: credenciais de Postgres e dados sensíveis (views, usuários) não estão descritos; confirmar política de provisionamento com DBAs.
- LACUNA: ausência de documentação sobre rotação dos tokens `CACHE_OPS_TOKEN` e `QUALITY_OPS_TOKEN`; definir processo de secret management.
