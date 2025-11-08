# README de Arquitetura

> **Como validar**
> - Revise o bootstrap da aplicação em `app/api/__init__.py` e `app/main.py` para confirmar a ordem de inicialização e middlewares.【F:app/api/__init__.py†L1-L44】【F:app/main.py†L1-L4】
> - Verifique os serviços declarados em `docker-compose.yml` para garantir que a topologia descrita reflete a stack real.【F:docker-compose.yml†L1-L197】
> - Confirme o uso das políticas e contratos de dados consultando os YAMLs de entidades e políticas em `data/entities/` e `data/policies/cache.yaml`.【F:data/entities/fiis_precos/entity.yaml†L1-L115】【F:data/policies/cache.yaml†L8-L71】

## Visão geral

Araquem é uma API FastAPI que orquestra perguntas em linguagem natural sobre Fundos Imobiliários, roteando-as via um Planner baseado em ontologia para consultas SQL declaradas em YAML e executadas em Postgres.【F:app/api/ask.py†L56-L178】【F:app/orchestrator/routing.py†L185-L459】O serviço aplica políticas de cache em Redis para métricas agregadas, deduzindo parâmetros temporais a partir de regras declarativas antes de construir SQL específico por entidade.【F:app/cache/rt_cache.py†L15-L216】【F:app/planner/param_inference.py†L1-L120】Um módulo Narrator opcional chama um LLM via Ollama para gerar respostas naturais, mantendo fallback determinístico quando indisponível.【F:app/api/ask.py†L179-L254】【F:app/narrator/narrator.py†L1-L120】A observabilidade inclui métricas HTTP, planner, cache, SQL e RAG exportadas para Prometheus, além de tracing configurável via OTLP.【F:app/common/http.py†L58-L69】【F:app/observability/metrics.py†L24-L157】【F:app/observability/runtime.py†L24-L64】Operações de qualidade e RAG têm rotas próprias com autenticação por token para validar roteamentos, índice vetorial e avaliações de recuperação.【F:app/api/ops/quality.py†L29-L200】【F:app/api/ops/metrics.py†L15-L38】【F:app/api/ops/rag.py†L1-L120】A stack containerizada inclui Redis, Ollama, Prometheus, Grafana, Tempo, coletores OTEL e crons para quality e refresh de embeddings, permitindo uma operação completa local.【F:docker-compose.yml†L2-L186】

## Mapa dos artefatos

- [C4 – Contexto](./c4-context.md)
- [C4 – Contêineres](./c4-containers.md)
- [C4 – Componentes](./c4-components.md)
- [Fluxos de sequência](./fluxos-sequencia.md)
- [Configuração e segredos](./configuracao-e-segredos.md)
- [Dependências](./dependencias.md)
- [Dados](./dados.md)
- [Glossário e responsabilidades](./glossario-e-responsabilidades.md)
- [Riscos e dívidas técnicas](./risks-e-tech-debt.md)

## Como rodar local

| Ação | Comando | Fonte |
| --- | --- | --- |
| Subir a stack completa (API, Redis, observabilidade, LLM, crons) | `docker compose up -d` | 【F:docker-compose.yml†L1-L197】 |
| Executar checklist rápido de saúde e métricas (precisa da stack ativa) | `make quick-health` | 【F:Makefile†L33-L61】 |
| Rodar suíte de testes rápida utilizada na automação de observabilidade | `make obs-check` | 【F:Makefile†L78-L109】 |

## Ambientes & endpoints

| Ambiente | Endpoint/Porta | Observações | Fonte |
| --- | --- | --- | --- |
| Local (docker) | `http://localhost:8000` | FastAPI com /ask, /metrics e /healthz expostos pela imagem `docker/Dockerfile.api` | 【F:docker-compose.yml†L2-L37】【F:docker/Dockerfile.api†L4-L54】【F:app/api/health.py†L11-L40】 |
| Local Observabilidade | `http://localhost:9090`, `http://localhost:3000`, `http://localhost:3200` | Prometheus, Grafana e Tempo provisionados via docker compose | 【F:docker-compose.yml†L92-L136】 |
| ⚠️ LACUNA | LACUNA | Não há definição de ambientes de staging/produção no repositório; confirmar com a equipe. | LACUNA |

## Checklist de observabilidade

- [x] Métricas HTTP e de domínio expostas em `/metrics` com catálogo validado pela façade de métricas.【F:app/common/http.py†L58-L69】【F:app/observability/metrics.py†L24-L157】【F:app/api/health.py†L33-L40】
- [x] Tracing OTLP configurável via `app.observability.runtime.init_tracing`, usando `OBSERVABILITY_CONFIG` e OTEL exporter.【F:app/observability/runtime.py†L24-L64】【F:app/api/__init__.py†L24-L43】
- [x] Logs estruturados parciais (planner) com `_LOG.info` para decisões de roteamento.【F:app/planner/planner.py†L311-L340】
- [ ] ⚠️ LACUNA: Não há dashboards/documentação de alertas versionados além dos geradores; validar se os artefatos renderizados estão atualizados.
