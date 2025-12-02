# Requisitos DevOps para Stage na AWS — Projeto Araquem

## 1. Visão Geral da Stack
- **api**: FastAPI/Uvicorn com dependência de redis, observabilidade (Prometheus, Grafana, Tempo, Otel) e pipeline de LLM via Ollama.
- **redis**: cache chave-valor usado pela API.
- **ollama**: runtime de modelos LLM com volume persistente para modelos.
- **ollama-init**: job de inicialização que baixa modelos do Ollama e cria o modelo customizado `sirios-narrator`.
- **rag-indexer**: constrói embeddings via scripts de RAG.
- **prometheus**: coleta métricas da API, Otel collector e Tempo.
- **grafana**: dashboards e datasources pré-provisionados (Prometheus, Tempo, JSON API da própria API).
- **tempo**: backend de traces OpenTelemetry (armazenamento local em volume).
- **otel-collector**: coleta e exporta traces para o Tempo e expõe métricas em 8888.
- **quality-cron**: rotina que dispara coleta de qualidade e validações após a API estar saudável.
- **rag-refresh-cron**: rotina agendada que chama endpoints de refresh e métricas de RAG.

## 2. Inventário Técnico por Serviço
- **api**
  - Imagem: build `docker/Dockerfile.api` (base python:3.12-slim).
  - Portas: 8000 exposta.
  - Volumes: bind do repositório em `/app`.
  - Variáveis: `EXECUTOR_MODE`, `PROMETHEUS_URL`, `GRAFANA_URL`, `QUALITY_OPS_TOKEN`, `RAG_INDEX_PATH`, `OLLAMA_BASE_URL`, `OLLAMA_URL`, além de `.env` externo.
  - Networks: `araquem_network`, `zaratustra_default` (externa).
  - Dependências: redis, prometheus, grafana, tempo, ollama, ollama-init, otel-collector.
  - Criticidade: crítica.
- **redis**
  - Imagem: `redis:7`.
  - Portas: 6379 exposta.
  - Volumes: não declarado.
  - Variáveis: nenhuma.
  - Networks: `araquem_network`.
  - Criticidade: apoio essencial de cache.
- **ollama**
  - Imagem: `ollama/ollama:0.3.14`.
  - Portas: 11434 exposta.
  - Volumes: `ollama:/root/.ollama` para modelos.
  - Variáveis: controle de paralelismo, threads, cache e log.
  - Networks: `araquem_network`.
  - Criticidade: crítica para LLM.
- **ollama-init**
  - Imagem: build `docker/Dockerfile.ollama-init`.
  - Portas: não expõe.
  - Volumes: bind do repo.
  - Variáveis: `OLLAMA_HOST`, `OLLAMA_MODELS`, `SIRIOS_MODEFILE`.
  - Networks: `araquem_network`.
  - Criticidade: job de apoio.
- **rag-indexer**
  - Imagem: build `docker/Dockerfile.rag-indexer` (python:3.12-slim).
  - Portas: não expõe.
  - Volumes: bind do repo.
  - Variáveis: `OLLAMA_BASE_URL`, `TZ`, `OLLAMA_EMBED_MODEL`, `EMBED_BATCH_SIZE`.
  - Networks: `araquem_network`.
  - Criticidade: apoio (processo batch).
- **prometheus**
  - Imagem: `prom/prometheus:latest`.
  - Portas: 9090 exposta.
  - Volumes: config em bind e dados em `prometheus-data`.
  - Variáveis: não.
  - Networks: `araquem_network`.
  - Criticidade: observabilidade (apoio).
- **grafana**
  - Imagem: `grafana/grafana:11.2.0`.
  - Portas: 3000 exposta.
  - Volumes: `grafana` e binds de provisioning/dashboards.
  - Variáveis: autenticação anônima habilitada, plugin JSON API.
  - Networks: `araquem_network`.
  - Criticidade: observabilidade (apoio).
- **tempo**
  - Imagem: build `docker/Dockerfile.tempo` (grafana/tempo:latest).
  - Portas: 3200 exposta; recebe OTLP em 4317/4318 via config.
  - Volumes: `tempo-data` + bind de config.
  - Variáveis: não.
  - Networks: `araquem_network`.
  - Criticidade: observabilidade (apoio).
- **otel-collector**
  - Imagem: build `docker/Dockerfile.otel-collector` (otel/opentelemetry-collector:latest).
  - Portas: expõe OTLP 4317/4318 e métricas 8888 via config.
  - Volumes: bind do config.
  - Variáveis: não.
  - Networks: `araquem_network`.
  - Criticidade: observabilidade (apoio).
- **quality-cron**
  - Imagem: build `docker/Dockerfile.quality-cron`.
  - Portas: não.
  - Volumes: repo montado read-only.
  - Variáveis: `QUALITY_OPS_TOKEN`, `QUALITY_SAMPLES_GLOB`, `QUALITY_PUSH_SLEEP`, `QUALITY_AUTH_BEARER`, `QUALITY_TOKEN_HEADER`, `QUALITY_REPORT_WAIT_MAX`, `QUALITY_REPORT_WAIT_SLEEP`, `QUALITY_API_URL`, `QUALITY_CRON_INTERVAL`.
  - Network: compartilha `service:api`.
  - Criticidade: apoio (qualidade/observabilidade).
- **rag-refresh-cron**
  - Imagem: build `docker/Dockerfile.rag-refresh-cron` (curl base).
  - Portas: não.
  - Volumes: nenhum.
  - Variáveis: `QUALITY_OPS_TOKEN`, `TZ`.
  - Network: compartilha `service:api`.
  - Criticidade: apoio (rotina RAG).

## 3. Requisitos de Infraestrutura na AWS (Stage)
### 3.1 Compute
- **Opção A – EC2 + docker-compose**: alinhamento direto com o compose; esforço baixo; exige gestão manual de updates, reinícios e auto-recovery.
- **Opção B – ECS/Fargate**: mais gerenciado e escalável; exige conversão do compose (ecs-cli/Compose-X) e setup de service discovery, mas simplifica deploy rolling e logs centralizados.
- **Opção C – EKS ou ECS on EC2**: maior flexibilidade e customização; esforço alto e pode ser excesso para stage, mas facilita observabilidade nativa e sidecars.

### 3.2 Banco de Dados e Armazenamento
- Postgres não está definido no compose; assumir uso externo (RDS) ou service compartilhado. Necessita VPC privada e SG restrito.
- Volumes persistentes requeridos: `ollama` (modelos), `prometheus-data` (métricas), `grafana` (dashboards/provisionamento dinâmico), `tempo-data` (traces). Logs podem ir para CloudWatch.
- Volumes efêmeros: binds de código podem ser substituídos por imagem; serviços de cron podem ser stateless.

### 3.3 Redes e Segurança
- VPC com subnets públicas (para ALB/API se exposta) e privadas (redis, observabilidade, Ollama, RDS).
- SGs sugeridos: HTTP/HTTPS para API; portas internas para redis 6379, OTLP 4317/4318, Prometheus 9090, Grafana 3000 (acesso restrito), Tempo 3200 (interno), Ollama 11434 (interno).
- Serviços externos: API (via ALB). Internos somente: redis, ollama, ollama-init, rag-indexer, quality/rag crons, otel-collector, tempo, prometheus. Grafana pode ser interno ou exposto via VPN/SSO.

### 3.4 Observabilidade
- Subir Prometheus, Grafana, Tempo e Otel Collector em stage. Garantir persistência para métricas/traces (EBS/EFS) e config mounts.
- Datasources: Prometheus em `http://prometheus:9090`, Tempo em `http://tempo:3200`, JSON API para `http://api:8000`.
- Exposição: Grafana apenas para time interno; Prometheus/Tempo restritos a VPC.

## 4. Gestão de Config/Secrets
- Sensíveis: `QUALITY_OPS_TOKEN`, possíveis variáveis do `.env` (ex.: credenciais de Postgres, chaves API externas), tokens de observabilidade se houver.
- Armazenamento sugerido: Secrets Manager para tokens/credenciais; Parameter Store para URLs/config não sigilosa.
- Parametrizar por ambiente: endpoints de banco/redis/Ollama, tokens de qualidade, flags de debug/EXECUTOR_MODE, caminhos de índices RAG.

## 5. CI/CD e Fluxo de Deploy
- Pipeline: build das imagens Docker (api, cron jobs, otel, tempo se custom, rag-indexer) → push para ECR → deploy em ECS/Fargate ou EC2 + compose.
- Versionar imagens com tags git/semver; crons referenciam API saudável, então garantir ordem de subida (API antes de quality-cron e rag-refresh-cron; Tempo antes de Otel Collector; Ollama antes de ollama-init e rag-indexer).
- Migrações de banco não visíveis; confirmar processo se houver.

## 6. Dimensionamento Inicial (Stage)
- EC2/ECS tasks aproximadas: API (1 vCPU/2GB), Redis (cache pequeno: 1 vCPU/1GB ou ElastiCache t4g.micro), Ollama (CPU-bound; sugerir 4-8 vCPU/8-16GB), Prometheus (1 vCPU/2-4GB), Grafana (1 vCPU/2GB), Tempo (1 vCPU/2GB + storage), Otel Collector (0.5 vCPU/0.5-1GB), crons (0.25 vCPU/0.5GB cada), rag-indexer (1 vCPU/2GB em job pontual).

## 7. Riscos, Dúvidas e Pendências
- Postgres não definido no compose; confirmar endpoint, credenciais e migrações.
- Volume de modelos Ollama pode ser grande; validar storage e tempo de download em stage.
- Tráfego esperado e SLAs não informados → sizing é apenas estimativa.
- Dependência de rede externa para baixar modelos e pacotes; considerar mirror/cache em ambientes restritos.
- Necessário revisar políticas de segurança para exposição de Grafana/Prometheus/Tempo.
