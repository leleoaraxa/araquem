# Operações Araquem — Runbook

## 1. Visão geral da stack
Araquem é a plataforma NL→SQL focada em Fundos Imobiliários com o objetivo de entregar respostas factuais, rastreáveis e evolutivas sem heurísticas. O produto é guiado pelos Guardrails v2.1.1, que reforçam fonte de verdade única, separação de poderes entre ontologia, SQL e resposta final, além de observabilidade e qualidade obrigatórias.【F:docs/dev/GUARDRAILS_ARAQUEM.md†L1-L75】

A stack operacional em Docker Compose orquestra:
- **API (FastAPI + Uvicorn)** — núcleo cognitivo que recebe perguntas, roteia via planner e expõe endpoints operacionais e métricas.【F:docker-compose.yml†L1-L37】【F:docker/Dockerfile.api†L1-L47】
- **Redis** — cache read-through para o planner/executor, exposto em `6379`.【F:docker-compose.yml†L35-L41】
- **Postgres** — dependência externa (não sob compose) usada pelo executor SQL; a API instala cliente para conectar-se.【F:docker/Dockerfile.api†L14-L29】
- **Ollama** — provê embedding model `nomic-embed-text` para RAG e índices.【F:docker-compose.yml†L43-L66】【F:docker/Dockerfile.ollama-init†L1-L4】
- **Prometheus** — telemetria central coletando `/metrics` da API, Tempo e Otel Collector.【F:docker-compose.yml†L82-L103】【F:prometheus/prometheus.yml†L1-L17】
- **Grafana** — visualização com dashboards provisionados via scripts.【F:docker-compose.yml†L105-L125】【F:scripts/gen_dashboards.py†L1-L104】
- **Tempo + OTel Collector** — pipeline de tracing OTLP→Tempo com métricas expostas para Prometheus.【F:docker-compose.yml†L127-L158】【F:tempo/tempo.yaml†L1-L33】【F:otel-collector/config.yaml†L1-L33】
- **Crons (quality e RAG)** — automações que enviam amostras de qualidade, validam gates, atualizam índice e registram métricas.【F:docker-compose.yml†L160-L196】【F:docker/quality-cron.sh†L1-L27】【F:docker/rag-refresh-cron.sh†L1-L20】

## 2. Tabela dos containers
| Container | Porta(s) expostas | Objetivo | Depende de | Healthcheck | Métricas principais |
| --- | --- | --- | --- | --- | --- |
| `api` | 8000/tcp | Servir `/ask`, `/ops/*`, `/metrics` | Redis, Prometheus, Grafana, Tempo, Ollama, OTel | `curl -fsS http://localhost:8000/healthz` | `/metrics` (API, cache, RAG, quality)【F:docker-compose.yml†L1-L37】 |
| `redis` | 6379/tcp | Cache read-through do planner/executor | — | N/A (usar `redis-cli PING`) | Exposto via API (`cache_*`)【F:docker-compose.yml†L35-L41】 |
| `ollama` | 11434/tcp | Servir embeddings `nomic-embed-text` | — | `ollama ps` | Logs via `ollama ps`; consumo indireto pela API/RAG【F:docker-compose.yml†L43-L66】 |
| `ollama-init` | — | Baixar modelo `nomic-embed-text` antes de indexar | Ollama saudável | Herdado via depends_on | — (ver logs)【F:docker-compose.yml†L68-L80】 |
| `rag-indexer` | — | Construir `data/embeddings/store` a partir do `index.yaml` | Ollama, ollama-init | N/A (job pontual) | Emite `manifest` com `chunks` |【F:docker-compose.yml†L82-L101】【F:docker/Dockerfile.rag-indexer†L1-L20】 |
| `prometheus` | 9090/tcp | Scrape `/metrics`, aplicar rules | — | N/A (consultar `/-/ready`) | Recording/alerting rules `job:*`【F:docker-compose.yml†L82-L103】【F:prometheus/recording_rules.yml†L1-L28】 |
| `grafana` | 3000/tcp | Dashboards e alerting UI | Prometheus (datasource) | N/A (ver `/api/health`) | Dashboards `00_*`/`30_*` |【F:docker-compose.yml†L105-L125】【F:grafana/dashboards/_README.md†L1-L40】 |
| `tempo` | 3200/tcp | Armazenar traces OTLP | — | N/A (`/ready`) | `/metrics` expostas para Prometheus |【F:docker-compose.yml†L127-L146】【F:tempo/tempo.yaml†L1-L33】 |
| `otel-collector` | 4317/4318 (interno), 8888 (metrics) | Receber OTLP da API, exportar p/ Tempo | Tempo | N/A (ver logs) | `/metrics` em 8888 scrapeado por Prometheus【F:docker-compose.yml†L148-L158】【F:otel-collector/config.yaml†L1-L33】 |
| `quality-cron` | — (network_mode=api) | Publicar amostras, validar gates hora em hora | API saudável | Loop `quality-cron.sh` com waits | Usa `/ops/quality/report` e outputs JSON【F:docker-compose.yml†L160-L182】【F:docker/quality-cron.sh†L1-L27】 |
| `rag-refresh-cron` | — (network_mode=api) | Executar refresh diário de RAG e registrar métricas | API saudável | Loop em shell | `/ops/rag/refresh`, `/ops/metrics/rag/register`【F:docker-compose.yml†L184-L196】【F:docker/rag-refresh-cron.sh†L1-L20】 |

> **Nota:** Postgres não está definido no compose; configure DSN via variáveis no `.env` e verifique conectividade com `psql` antes do boot da API.【F:docker/Dockerfile.api†L14-L29】

## 3. Scripts & Crons
### Ciclo de qualidade
- `scripts/quality_push_cron.py` — Varre `data/ops/quality/*.json`, valida esquema (routing/projection/RAG), envia para `/ops/quality/push`. Aceita `--dry-run` e respeita `QUALITY_SAMPLES_GLOB`. Rodar manualmente para testar novos datasets.【F:scripts/quality_push_cron.py†L1-L181】
- `docker/quality-cron.sh` — Entry point do container homônimo; instala PyYAML, espera API saudável, roda `quality_push_cron.py`, aguarda métricas Prometheus (`top1_accuracy`, `routed_rate`) e executa `scripts/quality_gate_check.sh` a cada hora.【F:docker/quality-cron.sh†L1-L27】
- `scripts/quality_gate_check.sh` — Chama `validate_data_contracts.py` e consulta `/ops/quality/report`, falhando se o status não for `pass`. Útil para rodar localmente antes de merges.【F:scripts/quality_gate_check.sh†L1-L16】
- `scripts/validate_data_contracts.py` — Garante que `data/golden/m65_quality.yaml` e `.json` estão em sincronia. Rodar após edições do golden set.【F:scripts/validate_data_contracts.py†L1-L67】

### RAG e embeddings
- `scripts/embeddings_build.py` — Lê `data/embeddings/index.yaml`, chunkiza arquivos, chama Ollama para gerar embeddings e escreve `store/embeddings.jsonl` + `manifest.json`. Rodar após atualizar ontologia, entidades ou conceitos usados pelo RAG.【F:scripts/embeddings_build.py†L1-L93】【F:data/embeddings/index.yaml†L1-L52】
- `docker/rag-refresh-cron.sh` — Agenda refresh diário (02:10) chamando `/ops/rag/refresh` e reexecuta 5 minutos depois para consolidar caches. Também registra métricas RAG e força push de qualidade antes do refresh.【F:docker/rag-refresh-cron.sh†L1-L20】
- `docker/rag-eval-cron.sh` — Script utilitário para rodar `scripts/rag_retrieval_eval.py` dentro do cluster e registrar métricas agregadas (Recall@K, MRR, NDCG). Pode ser disparado ad-hoc pós-refresh.【F:docker/rag-eval-cron.sh†L1-L8】【F:scripts/rag_retrieval_eval.py†L1-L87】
- `scripts/rag_retrieval_eval.py` — Calcula métricas em `data/ops/quality/rag_eval_set.json`, consulta índice, registra resultado via `/ops/metrics/rag/eval/register` e persiste última execução em `data/ops/quality/rag_eval_last.json`. Use `--eval`, `--k` e `--index` para personalizar.【F:scripts/rag_retrieval_eval.py†L1-L87】

### Observabilidade
- `scripts/gen_dashboards.py` — Renderiza dashboards Grafana usando templates Jinja e `data/ops/observability.yaml`. Gere novamente após editar bindings, thresholds ou templates.【F:scripts/gen_dashboards.py†L1-L104】【F:data/ops/observability.yaml†L1-L90】
- `scripts/gen_alerts.py` — Constrói `prometheus/recording_rules.yml` e `alerting_rules.yml` a partir da mesma fonte YAML. Execute antes de subir Prometheus ou após mudar thresholds.【F:scripts/gen_alerts.py†L1-L78】【F:prometheus/recording_rules.yml†L1-L28】
- `scripts/obs_audit.py` — Auditoria que valida a existência e frescor de dashboards/regras, ausência de placeholders e cobertura de bindings/thresholds. Ideal para CI e para checar drift de observabilidade.【F:scripts/obs_audit.py†L1-L93】
- `scripts/gen_quality_dashboard.py` — Gera painel específico de quality gates com thresholds de `planner_thresholds.yaml`. Útil para inspeção rápida dos indicadores críticos.【F:scripts/gen_quality_dashboard.py†L1-L98】

### Golden & governança
- `scripts/golden_sync.py` — Normaliza YAML de amostras (`--in`) para JSON estável (`--out`), garantindo ordenação e campos obrigatórios. Use ao atualizar datasets routing/golden.【F:scripts/golden_sync.py†L1-L87】
- `scripts/hash_guard.py` — Calcula hashes de `data/ontology` e `data/golden`, mantendo `.hash` atualizado para detectar drift. Rodar após mudanças planejadas nos contratos.【F:scripts/hash_guard.py†L1-L33】

### Utilitários adicionais
- `scripts/gen_quality_dashboard.py` (ver acima) e `scripts/warmup.ps1` (aquecer cache em ambientes Windows).
- `scripts/quality_push.py` — CLI simples para enviar payloads JSON/YAML específicos para `/ops/quality/push` com cabeçalho de token. Útil para reprocessar amostras isoladas.【F:scripts/quality_push.py†L1-L47】
- `scripts/quality_push_cron.py` também é usado fora do cron para inspeção (`--dry-run`).

## 4. Papel das pastas
- `app/` — Implementação da API e de seus módulos (planner, orchestrator, executor, formatter, observability). Consulte `main.py` para FastAPI e `/ops/*` para endpoints operacionais.【F:docs/dev/GUARDRAILS_ARAQUEM.md†L15-L54】
- `data/` — Contratos e fontes de verdade: ontologia, entidades, embeddings, thresholds e datasets de qualidade. O índice RAG é dirigido por `embeddings/index.yaml`.【F:data/embeddings/index.yaml†L1-L52】【F:docs/dev/GUARDRAILS_ARAQUEM.md†L31-L55】
- `scripts/` — Automatizações reproduzíveis para qualidade, observabilidade e RAG (detalhadas acima).【F:scripts/gen_dashboards.py†L1-L104】
- `docs/` — Guardrails, relatórios técnicos e agora runbooks/cheatsheet de operações.【F:docs/dev/GUARDRAILS_ARAQUEM.md†L1-L75】【F:docs/dev/QUALITY_FIX_REPORT.md†L1-L78】
- `prometheus/`, `grafana/`, `tempo/`, `otel-collector/` — Configurações de monitoramento, dashboards provisionados e tracing pipeline.【F:prometheus/prometheus.yml†L1-L17】【F:grafana/dashboards/_README.md†L1-L40】【F:tempo/tempo.yaml†L1-L33】【F:otel-collector/config.yaml†L1-L33】
- `tests/` — Gates de qualidade/observabilidade; mantenha-os verdes antes de merges (ver relatórios de falha histórica).【F:docs/dev/QUALITY_FIX_REPORT.md†L52-L71】

## 5. Ordem de boot recomendada
1. **Redis → Postgres → Prometheus → Tempo → OTel Collector** — garante cache, banco e pipeline de telemetria prontos para serem consumidos. Use `docker compose up redis postgres prometheus tempo otel-collector` e verifique `docker compose ps` + endpoints (`tempo:3200/status`, `otel-collector:8888/metrics`).【F:docker-compose.yml†L35-L158】【F:otel-collector/config.yaml†L1-L33】
2. **Ollama** — sobe o servidor de modelos; confirme com `docker compose logs ollama` e `docker exec araquem-ollama ollama ps`. O container `ollama-init` só termina após o pull do modelo.【F:docker-compose.yml†L43-L80】【F:docker/Dockerfile.ollama-init†L1-L4】
3. **API** — iniciar `docker compose up api` após telemetria e Ollama estarem prontos. Cheque `curl -f http://localhost:8000/healthz` e `/metrics` para garantir readiness.【F:docker-compose.yml†L1-L37】
4. **Crons (quality, rag-refresh, rag-indexer)** — subir após API saudável; ambos compartilham o namespace da API e dependem de `/ops/*`. Monitore logs para confirmar ciclos completos.【F:docker-compose.yml†L160-L196】

## 6. Fluxos principais
### Quality Gate Loop
```mermaid
digraph
  subgraph cron[Quality Cron]
    qp[quality-cron.sh]
    qp --> qpc[scripts/quality_push_cron.py]
  end
  qpc --> api_ops[API /ops/quality/push]
  api_ops --> prom[Prometheus scrape /metrics]
  prom --> graf[Grafana dashboards]
  api_ops --> rep[API /ops/quality/report]
  rep --> qcheck[scripts/quality_gate_check.sh]
  qcheck --> status[Status PASS/FAIL]
```

### RAG Refresh Loop
```mermaid
digraph
  cron[RAG Refresh Cron] --> refresh[API /ops/rag/refresh]
  refresh --> indexer[RAG Indexer (embeddings_build.py)]
  indexer --> store[data/embeddings/store]
  store --> metrics[API /ops/metrics/rag/register]
  metrics --> prom[Prometheus]
  prom --> graf[Grafana RAG panels]
  cron --> quality_push[API /ops/quality/push]
```

### Observabilidade Loop
```mermaid
digraph
  app[API + Modules] --> metrics[/metrics exporter]
  metrics --> prom[Prometheus scrape]
  app --> traces[OTel SDK]
  traces --> otel[OTel Collector]
  otel --> tempo[Tempo Storage]
  prom --> graf[Grafana Dashboards]
  prom --> alerts[Alerting Rules]
  tempo --> graf
```

## 7. Operações diárias
- **Verificar saúde:** `docker compose ps`, depois `curl -s localhost:8000/healthz`, `curl -s localhost:8000/metrics | head`, `curl -s http://localhost:9090/-/ready`, `curl -s http://localhost:3200/status`. Prometheus deve listar `araquem-api`, `otel-collector` e `tempo` como `UP` conforme `prometheus.yml`.【F:prometheus/prometheus.yml†L1-L17】
- **Rodar quality manualmente:** `docker compose run --rm quality-cron /usr/local/bin/quality-cron.sh` ou local `python scripts/quality_push_cron.py && scripts/quality_gate_check.sh`. Use `QUALITY_SAMPLES_GLOB` para escopar datasets.【F:docker/quality-cron.sh†L1-L27】【F:scripts/quality_push_cron.py†L1-L181】
- **Reindexar embeddings:** `docker compose run --rm rag-indexer` (usa CMD do Dockerfile) ou `python scripts/embeddings_build.py --index data/embeddings/index.yaml --out data/embeddings/store`. Confirmar `manifest.json` atualizado e métricas RAG via `/ops/metrics/rag/register`.【F:docker/Dockerfile.rag-indexer†L1-L20】【F:scripts/embeddings_build.py†L1-L93】
- **Regenerar dashboards/alerts:** `python scripts/gen_dashboards.py --config data/ops/observability.yaml --out grafana/dashboards` e `python scripts/gen_alerts.py --config data/ops/observability.yaml`. Rodar `scripts/obs_audit.py` para validar saída.【F:scripts/gen_dashboards.py†L47-L98】【F:scripts/gen_alerts.py†L50-L75】【F:scripts/obs_audit.py†L37-L76】
- **Validar dados D-1:** Executar `python scripts/validate_data_contracts.py` e (se banco disponível) rodar queries canônicas via `/ops/cache/bust` + `/ask` para verificar latências e dados recentes conforme contratos em `data/entities`.【F:scripts/validate_data_contracts.py†L1-L67】【F:docs/dev/GUARDRAILS_ARAQUEM.md†L57-L75】

## 8. Troubleshooting rápido
| Sintoma | Causa provável | Diagnóstico | Ação |
| --- | --- | --- | --- |
| `quality gate: fail` | Métricas `top1_accuracy` ou `top2_gap_p50` abaixo do threshold | `curl -s localhost:8000/ops/quality/report | jq` | Ajustar datasets, rerodar `quality_push_cron.py`, revisar planner thresholds.【F:docker/quality-cron.sh†L15-L27】【F:data/ops/observability.yaml†L21-L45】 |
| `no data in Grafana` | Prometheus indisponível ou datasource incorreto | `curl -s http://localhost:9090/-/ready`; verificar `datasources` provisionados | Reiniciar Prometheus, regenerar dashboards/alerts, conferir `prometheus.yml`.【F:prometheus/prometheus.yml†L1-L17】【F:docker-compose.yml†L105-L125】 |
| `rag metrics 0.0` | Índice desatualizado ou refresh falhou | `curl -s -X POST localhost:8000/ops/metrics/rag/register -d '{"store":"data/embeddings/store/embeddings.jsonl"}'` | Rodar `rag-indexer`, garantir Ollama online, revisar logs do cron.【F:docker/rag-refresh-cron.sh†L1-L20】【F:scripts/embeddings_build.py†L1-L93】 |
| `ollama-init` preso | Pull do modelo pendente | `docker compose logs ollama ollama-init` | Garantir internet ou pré-carregar modelo; reiniciar container.【F:docker/Dockerfile.ollama-init†L1-L4】 |
| `obs_audit` falha | Dashboards/alerts desatualizados vs `observability.yaml` | `python scripts/obs_audit.py` | Regenerar com `gen_dashboards.py`/`gen_alerts.py`.【F:scripts/obs_audit.py†L37-L84】 |

## 9. Automatizações seguras (futuras)
- **CI para observabilidade:** adicionar job pós-merge que roda `scripts/gen_dashboards.py` e `scripts/gen_alerts.py` seguido de `scripts/obs_audit.py`, garantindo que os artefatos estejam sempre alinhados com `observability.yaml` sem tocar em código.【F:scripts/gen_dashboards.py†L47-L98】【F:scripts/gen_alerts.py†L50-L75】【F:scripts/obs_audit.py†L37-L84】
- **Quality gate nightly:** agendar execução de `quality-cron.sh` em runner controlado para validar datasets após merges (já compatível com `quality_push_cron.py --dry-run`).【F:docker/quality-cron.sh†L1-L27】
- **RAG eval scheduled:** usar `docker/rag-eval-cron.sh` como base para pipeline que registra métricas em Prometheus após cada refresh, alimentando painéis automáticos.【F:docker/rag-eval-cron.sh†L1-L8】【F:scripts/rag_retrieval_eval.py†L1-L87】

## 10. Referências cruzadas
- Guardrails e estrutura canônica: `docs/dev/GUARDRAILS_ARAQUEM.md`。【F:docs/dev/GUARDRAILS_ARAQUEM.md†L1-L75】
- Relatório de qualidade histórico e comandos de observabilidade: `docs/dev/QUALITY_FIX_REPORT.md`。【F:docs/dev/QUALITY_FIX_REPORT.md†L1-L78】
- Fonte de bindings/thresholds de observabilidade: `data/ops/observability.yaml`。【F:data/ops/observability.yaml†L1-L90】
- Configurações Prometheus/Grafana: `prometheus/*.yml`, `grafana/dashboards/`。【F:prometheus/prometheus.yml†L1-L17】【F:prometheus/recording_rules.yml†L1-L28】【F:grafana/dashboards/_README.md†L1-L40】
