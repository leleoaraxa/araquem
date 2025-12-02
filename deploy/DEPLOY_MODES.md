# DEPLOY_MODES — Araquem

> Como subir o Araquem em **dev**, **stage** e **prod** sem quebrar nada, mantendo qualidade e performance.

---

## 1. Visão Geral

O Araquem trabalha com **3 modos de deploy**:

- **DEV** → ambiente local do dev (explorar, quebrar, ajustar).
- **STAGE** → espelho da produção, com quality completo (gate de entrada).
- **PROD** → ambiente que atende usuário final (leve, previsível).

A regra-mãe é:

> **Qualquer mudança passa por DEV → STAGE (quality OK) → PROD.
> PROD não roda bateria completa de quality.**

---

## 2. Arquivos de Compose por ambiente

### 2.1. DEV

- Arquivo sugerido: **`docker-compose.yaml`** (o atual).
- Objetivo:
  - ambiente completo pra desenvolvimento local,
  - com todos os serviços, inclusive `quality-cron`.

Serviços principais:

- `api`
- `redis`
- `ollama`
- `ollama-init`
- `rag-indexer`
- `prometheus`
- `grafana`
- `tempo`
- `otel-collector`
- `quality-cron`
- `rag-refresh-cron`

Exemplo de uso:

```bash
docker compose up -d
# ou
docker-compose up -d
