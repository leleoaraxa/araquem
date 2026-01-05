# 🟦 **GUIA OPERACIONAL — SUBIR O STAGE DO ARAQUEM NA AWS**

## 🎯 Objetivo

Montar **um ambiente Stage replicando a stack do compose**:

* API (FastAPI/Uvicorn)
* Redis
* Ollama + sirios-narrator
* RAG indexer / RAG refresh cron
* Quality cron
* Observabilidade completa (Prometheus, Grafana, Tempo, OTEL Collector)

Sem mudar nada no core do Araquem.
Infra **mínima, segura e funcional**.

---

# 🟩 **1. Decisão Inicial**

O relatório mapeou 3 opções de compute.
A recomendação realista para **Stage**, considerando simplicidade + fidelidade ao compose, é:

## ⭐ **Opção A — EC2 + docker-compose**

> Melhor para Stage (rápido, fiel ao dev, sem conversão para ECS).

**Por quê?**

* Compose já funciona.
* Olhamos shadow, RAG, Narrator, Tempo, Grafana tudo junto sem precisar distribuir tasks.
* Não existe SLA de Stage que exija auto-scaling.
* Custos menores.
* Mais fácil de depurar.

**Onde usar ECS/Fargate?**
Somente quando você quiser Prod com autoscaling e alta resiliência.

---

# 🟩 **2. Arquitetura Final do Stage (Sirius → DevOps)**

## 📌 Layout resumido

```
VPC (10.0.0.0/16)
 ├── Subnet Pública (ALB)
 └── Subnet Privada (EC2 Stage)
        ├── API:8000
        ├── Redis:6379
        ├── Ollama:11434
        ├── Prometheus:9090
        ├── Grafana:3000
        ├── Tempo:3200
        ├── OTEL Collector:4317/4318
        ├── quality-cron
        └── rag-refresh-cron
```

### 📌 Serviços EXTERNOS (expostos)

* **API** → via **ALB (porta 80/443)**

### 📌 Serviços INTERNOS (somente rede privada)

* redis
* ollama
* prometheus
* grafana*
* tempo
* otel-collector
* rag-indexer
* crons

(*Grafana pode ser exposto somente para VPN da SIRIOS ou via SSO.*)

---

# 🟩 **3. Passo-a-Passo Operacional do Stage**

Agora começa o procedimento para o DevOps executar.

---

# **PASSO 1 — Criar a VPC do Stage**

### Estrutura mínima:

* 1 VPC / 2 Subnets:

  * **public-subnet-stage**
  * **private-subnet-stage**
* Rota:

  * públicas → Internet Gateway
  * privadas → NAT Gateway

### Security Groups

#### SG-ALB

* 80/443 → público
* Saída para SG-EC2-Stage

#### SG-EC2-Stage

* Permite:

  * HTTP/8000 **apenas do ALB**
  * Redis 6379 interno
  * Ollama 11434 interno
  * OTLP 4317/4318 interno
  * Prometheus 9090 interno
  * Grafana 3000 interno
  * Tempo 3200 interno
* Bloquear tudo externo exceto updates do apt/docker.

---

# **PASSO 2 — Criar a instância EC2 Stage**

## Tipo recomendado:

* **c6a.2xlarge** (8 vCPU / 16GB RAM)
  → suficiente para Ollama, API, observabilidade.

## Configurar:

* SO: Ubuntu 22.04 LTS
* Armazenamento:

  * **60GB EBS** geral
  * **+50GB EBS extra** para volume do Ollama (modelos)
  * **+20GB** para Tempo/Prometheus (pode ser 1 volume EBS)

## Após iniciar, conectar e instalar:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose git unzip
sudo usermod -aG docker ubuntu
```

---

# **PASSO 3 — Provisionar Postgres (RDS)**

Porque o compose não define Postgres, o Stage **deve usar RDS**.

Requisitos:

* Engine: Postgres 15
* Classe inicial: db.t3.medium
* Armazenamento: 20GB GP3
* Acesso: **somente SG-EC2-Stage**
* Parâmetros:

  * timezone: America/Sao_Paulo
  * max_connections: ajustar conforme carga futura

Registrar:

* HOST
* PORT
* DB_NAME
* USER
* PASSWORD

Guardar no **Secrets Manager**.

---

# **PASSO 4 — Preparar Secrets/Configs**

Todos os segredos devem estar em **AWS Secrets Manager**.

Criar:

### /stage/araquem/api

* POSTGRES_HOST
* POSTGRES_USER
* POSTGRES_PASSWORD
* QUALITY_OPS_TOKEN
* RAG paths
* URLs de observabilidade
* OLLAMA_URL
* OLLAMA_BASE_URL

### /stage/araquem/cron

* QUALITY_OPS_TOKEN
* QUALITY_API_URL

### /stage/araquem/rag

* OLLAMA_EMBED_MODEL
* EMBED_BATCH_SIZE

E assim por diante.

---

# **PASSO 5 — Preparar a instância para rodar a stack**

Na EC2:

```bash
git clone https://gitlab.com/sirios/araquem
cd araquem
```

Criar o `.env.stage` usando valores vindos do Secrets Manager.

Exemplo:

```
EXECUTOR_MODE=stage
POSTGRES_HOST=...
OLLAMA_BASE_URL=http://ollama:11434
QUALITY_OPS_TOKEN=...
```

**IMPORTANTE**

* Não expor esses valores em commits.
* `.env.stage` fica apenas na EC2.

---

# **PASSO 6 — Criar diretórios persistentes na EC2**

Volumes no compose:

* ollama
* prometheus-data
* grafana
* tempo-data

Criar:

```bash
sudo mkdir -p /data/ollama
sudo mkdir -p /data/prometheus
sudo mkdir -p /data/grafana
sudo mkdir -p /data/tempo

sudo chown -R ubuntu:ubuntu /data
```

Editar `docker-compose.stage.yml` (não alterar o original) mapeando:

```yaml
volumes:
  ollama:
    driver: local
    driver_opts:
      type: none
      device: /data/ollama
      o: bind
```

Mesma coisa para Prometheus/Grafana/Tempo.

---

# **PASSO 7 — Subir a stack do Araquem**

Na EC2:

```bash
docker-compose -f docker-compose.yaml --env-file .env.stage up -d
```

Verificar:

```bash
docker ps
curl http://localhost:8000/healthz
```

Esperar ~1–2 minutos para:

* ollama iniciar
* ollama-init baixar modelos
* rag-indexer criar embeddings se necessário
* quality-cron aguardar API saudável

---

# **PASSO 8 — Criar Load Balancer para expor a API**

### ALB

* Listener 80/443
* Target → EC2 Stage porta **8000**
* Health check: `/healthz`
* Timeout: 5s
* Healthy threshold: 2

Definir URL final:

`https://stage-api.sirios.com` (por exemplo)

---

# **PASSO 9 — Observabilidade**

### Prometheus

* Interno (porta 9090)
* Consultas via Grafana

### Grafana

* Pode expor **somente via SSO**:

  * AWS SSO
  * Cognito
  * VPN interna

### Tempo

* Fica apenas interno
* Api → Otel Collector → Tempo

### OTEL Collector

* Já coleta automáticamente via compose

Verificar dashboards:

http://EC2_PRIVATE_IP:3000

---

# **PASSO 10 — Testes finais**

### Verificar:

1. API respondendo com sucesso (`/healthz`)
2. Roteamento do Planner normal
3. Narrator em shadow
4. RAG funcionando
5. Tempo coletando traces
6. Prometheus recebendo métricas
7. Dashboards Grafana completos
8. quality-cron rodando de tempos em tempos
9. RAG-refresh-cron funcionando

Comandos úteis:

```bash
docker logs api
docker logs ollama
docker logs ollama-init
docker logs quality-cron
docker logs rag-refresh-cron
docker logs otel-collector
docker logs prometheus
```

---

# 🟪 **11. Checklist Final para DevOps**

### ☑ Infra

* VPC 2 subnets
* SGs prontos
* RDS criado e configurado
* EC2 Stage provisionada

### ☑ Configs

* Secrets criados no Secrets Manager
* `.env.stage` configurado
* Volumes persistentes preparados

### ☑ Deploy

* clone repo
* compose up
* ALB configurado
* testes realizados

### ☑ Observabilidade

* Prometheus up
* Grafana up
* Tempo + OTEL funcionando
* Dashboards visíveis

---
