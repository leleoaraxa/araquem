# Araquem — Mapa de Dependências Internas

## Tabela de dependências principais
| Módulo | Importa de | É importado por | Tipo de acoplamento | Risco |
| --- | --- | --- | --- | --- |
| `app/api/ask` | `app.core.context` (cache, planner, orchestrator), `app.cache.rt_cache`, `app.formatter.rows`, `app.planner.param_inference`, `app.responder`, `app.narrator` | FastAPI app (`app/api/__init__.py`) | Forte; endpoint orquestra múltiplas camadas e conhece detalhes de Narrator/cache | 🔶 Altos fan-ins tornam difícil isolar apresentação |
| `app/api/ops/*` | `app.analytics`, `app.core.context` | FastAPI app | Médio; expõe operações administrativas | ⚠️ Depende de instâncias globais |
| `app/core/context` | `app.cache`, `app.executor`, `app.planner`, `app.orchestrator` | `app/api/*`, `app/main.py`, testes | Forte; ponto único de inicialização | 🔶 Falha aqui derruba a API inteira |
| `app/orchestrator/routing` | `app.cache.rt_cache`, `app.planner.planner`, `app.builder.sql_builder`, `app.executor.pg`, `app.formatter.rows`, `app.analytics.explain`, `app.planner.param_inference`, `app.utils.filecache` | `app.core.context`, `app/api/ask` | Forte; coordenação central | 🔶 Mudanças propagam para todos os módulos |
| `app/planner/planner` | `app.planner.ontology_loader`, `app.rag.hints`, `app.rag.ollama_client`, `app.utils.filecache`, `app.observability.instrumentation` | `app.core.context`, `app/orchestrator`, `app/api/debug` | Médio/forte; integra sinais externos (RAG) | 🔶 Habilitar RAG adiciona dependências de rede/LLM |
| `app/builder/sql_builder` | `app.utils.filecache` | `app/orchestrator` | Forte com YAML declarativo | 🔶 Erros no YAML quebram SQL em runtime |
| `app/executor/pg` | `psycopg`, `app.observability.runtime`, `app.observability.instrumentation` | `app/core.context`, `app/orchestrator` | Médio; depende de ambiente (DATABASE_URL) | 🔶 Falhas de DB propagam exceptions |
| `app/formatter/rows` | `jinja2`, `app.utils.filecache`, `decimal` helpers | `app/orchestrator`, `app/api/ask` | Médio; assume formato específico de YAML | 🔶 Templates inválidos causam vazios silenciosos |
| `app/responder` | `functools.lru_cache`, `pathlib` | `app/api/ask` | Médio; usa templates legados | ⚠️ Templates fora do padrão geram respostas vazias |
| `app/narrator/narrator` | `app.narrator.prompts`, `app.utils.filecache`, `app.rag.ollama_client` | `app/api/ask` | Opcional; depende de cliente Ollama | ⚠️ Quando habilitado exige infraestrutura LLM |
| `app/cache/rt_cache` | `redis`, `yaml`, `json`, `app.observability.instrumentation` | `app/core.context`, `app/api/ask`, `app/orchestrator` | Forte com Redis | 🔶 Queda do cache impacta latência das métricas |
| `app/rag/index_reader` | `app.core.hotreload` | `app.utils.filecache`, `app.planner.planner` | Médio; cache compartilhado | ⚠️ Necessita manifest atualizado |
| `app/analytics/explain` | `app.observability.instrumentation` | `app/api/ask`, `app/orchestrator` | Baixo; puro em memória | ⚠️ Depende de contrato flexível |
| `app/observability/*` | `prometheus_client`, `opentelemetry` | Quase todos os módulos | Transversal | 🔶 Falha de bootstrap impede métricas/tracing |
| `app/utils/filecache` | `yaml`, `json`, `threading`, `app.rag.index_reader` | `app/planner`, `app/builder`, `app/formatter`, `app/narrator`, `app/utils` | Forte; cache global | 🔶 Erros de caminho retornam `{}` silenciosamente |

Legenda de risco: ⚠️ baixa, 🔶 média, 🔥 alta.

## Observações adicionais
- **Ciclos diretos:** nenhum ciclo Python direto detectado; o grafo mantém sentido principal `api → core → orchestrator → (planner/builder/executor/formatter/cache)`.
- **Dependências implícitas:** YAMLs em `data/entities` e `data/ops` são contratos que vários módulos consomem; inconsistências quebram pipeline sem erro de import.
- **Módulos em local inadequado:**
  - Lógica de Narrator (feature flag, facts) está acoplada ao endpoint `app/api/ask`. Parte deveria migrar para camada dedicada (provavelmente futura `app/narrator`/`app.responder`).
  - Inferência de parâmetros (`app/planner/param_inference`) é utilizada tanto no orchestrator quanto no endpoint; poderia residir em camada core para evitar duplicação de chamadas.
- **Isolamento desejado:**
  - `app/observability` mistura configuração de métricas específicas com utilitários genéricos; extrair contratos canônicos poderia reduzir acoplamento.
  - `app/cache/rt_cache` executa limpeza de chaves legadas dentro de `read_through`, acoplando políticas históricas ao fluxo atual.

## Pontos de atenção
1. **`app/api/ask`** concentra responsabilidades de roteamento, cache e apresentação → dificulta evolução independente do Narrator.
2. **`app/orchestrator`** depende simultaneamente de planner, builder, executor e formatter → qualquer mudança quebra o contrato cruzado.
3. **`app/utils/filecache`** fornece caches globais; invalidação incorreta pode servir dados defasados (não há TTL in-memory).
4. **`app/rag`** injeta dependência de cliente Ollama e arquivos de embeddings — precisa de guardrails robustos para habilitação condicional.

## Recomendação inicial de modularização
- Extrair camada de apresentação (`Narrator`/`Responder`) para um módulo dedicado que receba apenas `facts` e `meta`, desacoplando o endpoint da escolha de canal.
- Mover política de construção de cache/identificadores do endpoint para o orchestrator (ou serviço de cache) para reduzir duplicação.
- Formalizar interfaces em `app/core` para que instâncias concretas (`Planner`, `PgExecutor`) possam ser substituídas em testes ou shadow mode.
