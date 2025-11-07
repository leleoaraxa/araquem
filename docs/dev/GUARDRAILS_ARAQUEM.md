# Plataforma de Inteligência Imobiliária Sirios — Guardrails v2.1.1

**Codinome do projeto:** Araquem
**Meta:** Tornar-se a melhor IA do mercado para FIIs no Brasil, com precisão factual, rastreabilidade e evolução contínua — **sem heurísticas, sem hardcodes**.

---

## 0. Princípios Imutáveis

1. **Fonte de verdade única:** Ontologia + YAML de entidades + SQL real.
2. **Sem heurísticas / sem hardcodes:** nenhuma decisão fora dos contratos em `data/*`.
3. **Payloads imutáveis:** `/ask` e `/ws` exigem sempre `{question, conversation_id, nickname, client_id}`.
4. **Separação de poderes:** Ontologia decide *o que*, SQL decide *os fatos*, Íris (phi3) decide *como falar*.
5. **Observabilidade obrigatória:** tudo é mensurável (métricas, logs estruturados, tracing).
6. **Qualidade antes de velocidade:** nada vai para *main* sem testes verdes e painéis sem alertas.
7. **Aprendizado consciente:** autoaprendizado só com proposta + aprovação humana + versionamento.

---

## 1. Infraestrutura de Desenvolvimento (Dev-Only)

* **Stack:** FastAPI (API), Postgres (dados), Redis (cache), Ollama (phi3), Prometheus/Tempo (observabilidade), OTel (traces), Docker Compose (dev).
* **Pastas canônicas (atualizadas):**

```
araquem/
├─ app/
│  ├─ analytics/        # explain/metrics/repository (telemetria analítica)
│  ├─ api/
│  │  ├─ ops/           # endpoints operacionais: analytics, cache, metrics, quality, rag
│  │  ├─ ask.py         # endpoint NL->SQL
│  │  ├─ debug.py       # utilidades de depuração
│  │  └─ health.py      # health endpoints
│  ├─ builder/          # SQL builder
│  ├─ cache/            # read-through cache (Redis)
│  ├─ common/           # utilidades HTTP e comuns
│  ├─ core/             # contexto e hot reload
│  ├─ executor/         # execução no Postgres
│  ├─ formatter/        # normalização de linhas/resultados
│  ├─ observability/    # instrumentation, metrics e runtime obs
│  ├─ orchestrator/     # roteamento pipeline
│  ├─ planner/          # ontologia + param_inference
│  ├─ rag/              # hints, index_reader, ollama_client
│  ├─ utils/            # filecache e afins
│  └─ main.py           # FastAPI app + /metrics exporter
├─ data/
│  ├─ concepts/         # conteúdo e templates do responder
│  ├─ embeddings/
│  │  ├─ index.yaml
│  │  └─ store/         # embeddings.jsonl + manifest.json (fonte de verdade do refresh)
│  ├─ entities/         # contratos de entidades (YAML) + cache_policies.yaml
│  ├─ golden/           # datasets de qualidade canônicos (.json/.yaml + .hash)
│  ├─ ontology/         # ontologia do planner (+ .hash)
│  └─ ops/              # configs operacionais (observability, thresholds, quality/*)
├─ docker/              # Dockerfiles e crons (quality-cron.sh, rag-refresh-cron.sh)
├─ docs/                # dev, ops, ADRs, guardrails
├─ grafana/             # dashboards + provisioning (não alterado neste patch)
├─ k8s/                 # manifests opcionais (quality/cronjob.yaml)
├─ otel-collector/      # config OTel
├─ prometheus/          # prometheus.yml
├─ tempo/               # config Tempo
├─ scripts/             # embeddings_build, quality_* e utilitários
├─ tests/               # suíte canônica (inclui RAG e observabilidade)
└─ docker-compose.yml   # compose.dev
```

* **Compose.dev:** API 8000, Grafana 3000, Prometheus 9090, Tempo 3200, Ollama 11434, Redis 6379.
* **Segredos:** `.env` só para DEV. Produção fora do escopo deste documento.

---

## 2. Estrutura de Dados & Entidades (entities lógicas)

- **Entidade = unidade semântica** (ex.: `fiis_cadastro`, `fiis_dividendos`, `fiis_precos`, `fiis_noticias`, `fiis_rankings`, etc.).
- **Arquivo:** `data/entities/<entidade>/entity.yaml`.
- **Contrato mínimo:**
  - `id`, `result_key`, `sql_view`, `description`, `private`, `identifiers`, `default_date_field`,
    `columns[] {name, alias, description}`, `presentation {kind, fields {key, value}, empty_message}`,
    `ask {intents, keywords, synonyms, weights}`, `order_by_whitelist` (se aplicável).
- **Cache policy:** `data/entities/cache_policies.yaml` com `ttl_seconds`, `refresh_at` e `scope (pub|prv)`.
- **Naming:** snake_case PT-BR; booleanos com `is_`/`has_`; enums com `allowed_values`.

### 2.1 Padrão temporal D-1 (compute-on-read)

* **Regra:** dados D-1 → **compute-on-read**.
* **Uma única entidade de métricas** por domínio; **SQL parametrizado** (3/6/12/24m e “últimas N”).
* **Opcional:** materialized view mensal (sem alterar contrato).
* **Formatter:** agregados **só** em `meta.aggregates`; `results.*` estável.

---

## 3. Ontologia Inteligente (Planner)

- **Arquivo:** `data/ontology/entity.yaml`.
- **Conteúdo:** `normalize`, `tokenization`, `weights`, `intents[] {name, tokens {include, exclude}, phrases {include, exclude}, entities[]}`.
- **Regras:**
  - Nada de “dedução criativa”: tokens/phrases decidem.
  - **Anti-tokens** para evitar vazamentos entre domínios (ex.: `cadastro` ≠ `preços` ≠ `dividendos` ≠ `notícias`).
  - `planner.explain()` habilitado (telemetria de decisão).
  - `param_inference.py` como parte do Planner

* **RAG re-rank leve (M7.4):** apenas **sinal auxiliar**; não sobrepõe ontologia.

---

## 4. Orquestração (Routing → SQL → Formatter)

- **Roteador:** lê entidade do planner, aplica **gate privado** conforme YAML (`private: true` + `ask.filters.required`), injeta filtros (ex.: `document_number ← client_id`), gera SQL via `builder` e executa no `executor`.
- **Contrato de resultado:**
```
{
  "status": { "reason": "ok|forbidden|unroutable|error", "message": "..." },
  "results": { "<result_key>": [...] },
  "meta": {
    "result_key": "<result_key>",
    "planner_intent": "...",
    "planner_entity": "...",
    "planner_score": N,
    "rows_total": N,
    "elapsed_ms": N,
    "aggregates": { ... }   // quando houver (compute-on-read)
  }
}
```
- **Formatter:** não formata “criativamente”; apenas normaliza tipos/decimais/datas.


---

## 5. Cache & Flags (M4/M5)

- **Read-through** no `/ask` por chave canônica `{namespace}:{build_id}:{scope}:{domain}:{hash}`.
- **TTL por entidade** definido em `cache_policies.yaml`.
- **Endpoints operacionais:** `/health/redis`, `/ops/cache/bust` (tokenizado).
- **Modos:** `ok | degraded | disabled` expostos em health.
- **Warmup:** `scripts/cache_warmup.py` (com `--dry-run`, `--only-ask`).


---

## 6. Observabilidade & SLOs

* **Exportador:** `app/observability/metrics.py` publica séries no `/metrics` (Prometheus).
* **Métricas mínimas:** API (latência/status), Cache (hit/miss), e **RAG Index (M7.5)**:

  * `rag_index_size_total{store}` — bytes do JSONL.
  * `rag_index_docs_total{store}` — linhas válidas.
  * `rag_index_last_refresh_timestamp` — epoch do último refresh (fonte: `data/embeddings/store/manifest.json`).
  * `rag_index_density_score` — docs por MB.
* **Endpoints ops:** `app/api/ops/*` para registrar/reconciliar métricas e utilidades (quality/cache/rag).
* **Tracing (OTel → Tempo):** spans do `/ask`, atributos do planner (sem PII), SQL timing, cache decisor.
* **SLOs Dev:** `/ask` p95 ≤ 500ms (sem responder), ≤ 1500ms (com responder). Erro ≤ 1%.
* **Alertas (mínimo):** latência acima do SLO, erro > limiar, Redis degradado, **RAG sem refresh** no período alvo.

---

## 7. Segurança, Acesso & LGPD

- **Payloads imutáveis** (vide Princípios).
- **Gate privado** por YAML: `private: true` + `filters.required` (ex.: `document_number`).
- **Logs:** `request_id` sempre; mascarar `client_id` / PII; sem payload bruto em erro.
- **Retenção:** política mínima de logs em DEV (configurável).
- **Rate limit básico** no gateway; **CORS** restrito.
- **Taxonomia de erros:** `reason` + `message` + `code` (quando aplicável).

---

## 8. Íris (Responder) — phi3 determinístico

- **Papel:** transformar dados em respostas naturais **sem inventar**.
- **Local:** `app/responder/`.
- **Templates por entidade** (ex.: `data/concepts/fiis_cadastro_templates.md`), com *slots* mapeados às colunas declaradas.
- **Exemplos (cadastro):**
  - `O CNPJ do {ticker} é {fii_cnpj}.`
  - `O administrador do {ticker} é {admin_name} (CNPJ {admin_cnpj}).`
  - `O site oficial do {ticker} é {website_url}.`
- **Fallbacks:** campo ausente → resposta declarativa (“não disponível no momento”).
- **Formatação:** moedas/percentuais/datas tratadas no formatter (não no LLM).


---

## 9. Ciclo de Aprendizado Contínuo (Autoaprendizado)

**Objetivo:** evoluir com uso real, mantendo controle humano e versionamento.
1. **Telemetria de perguntas:** log anônimo de `{intent_detected, entity_used, confidence_score, duration_ms}`.
2. **Analisador de drift (semanal):** detecta frases novas/mal mapeadas.
3. **Curadoria assistida:** gera *propostas* de YAML (novos `synonyms/anti_tokens/examples`), nunca aplica sem review.
4. **Ciclo Íris:** coleta dúvidas recorrentes e propõe ajustes no tom/objetividade dos templates.
5. **Reindexação inteligente:** mudou YAML → reindex só daquele domínio (Nomic).
6. **Treino supervisionado opcional:** exporta logs rotulados para fine-tuning.
7. **Painel de evolução:** cobertura por intent, precisão/recall aproximada, backlog de propostas.

> Princípio: *“O Araquem aprende sozinho, mas só muda com consciência.”*

---

## 10. Qualidade, CI e DX

* **Goldens:** `data/golden/*` são parte do **gate de qualidade** (versionados + `.hash`).
* **Suíte:** `tests/*` inclui cenários de RAG (`rag_integration_*`, `rag_manifest_cache`, `rag_index_metrics`) e observabilidade (`obs_counter_value`).
  *(restante inalterado)*
- **Tests first:** toda feature vem com testes (`pytest -q`) e painel verificado.
- **CI (sugestão):** GitHub Actions — `docker compose up -d` + `pytest -q` + upload cobertura + lint (ruff/black/mypy opcional).
- **Pre-commit:** `ruff`, `black`, `pip-audit`.
- **PR Template + CODEOWNERS:** checklist com payloads, hardcodes, testes, dashboards, docs, métricas/tracing.
- **SBOM/Deps:** dependências pinadas; auditoria periódica.

---

## 11. Setup Inicial (passo-a-passo)

1. **Estrutura inicial:**
```
mkdir -p araquem/{app,data/{entities,ontology,concepts,embeddings},docs/dev,grafana/{dashboards,provisioning},prometheus,tempo,scripts,tests}
```
2. **Variáveis `.env` (dev):**
```
DATABASE_URL=postgresql://edge_user:senha@sirios_db:5432/edge_db
REDIS_URL=redis://redis:6379/0
OLLAMA_URL=http://ollama:11434
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
BUILD_ID=dev-20251030
LOG_LEVEL=INFO
ONTOLOGY_PATH=data/ontology/entity.yaml
CACHE_OPS_TOKEN=araquem-secret-bust-2025
QUALITY_OPS_TOKEN=araquem-secret-bust-2025
OTEL_SERVICE_NAME=api
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OBSERVABILITY_CONFIG=data/ops/observability.yaml
SIRIOS_METRICS_STRICT=false
```
3. **Bootstrap git:**
```
git init
git branch -M main
git add .
git commit -m "chore: bootstrap Araquem (Guardrails v2.1.1)"
git remote add origin <SEU_REMOTE>
git push -u origin main
```
4. **Subir stack (dev):** `docker compose up -d`
5. **Verificar saúde:** `/healthz`, `/metrics`, Grafana, Redis health.

---

## 12. Escopo inicial de entidades (FIIs) — sugestão

- `fiis_cadastro` (1×1 cadastral) — TTL diário 00:00.
- `fiis_dividendos` (histórico, valores pagos) — TTL diário; ordenação por data.
- `fiis_precos` (histórico/último) — TTL curto; suporte a “hoje/ontem”.
- `fiis_noticias` (RAG indexado) — TTL curto + embeddings (Nomic).
- `fiis_rankings` (IFIX/IFIL/usuários/Sirios) — TTL hora.
- **Privados:** `client_fiis_positions` (carteira do cliente) — `private: true` + gate `document_number`.


---

## 13. Governança de Mudanças

* **RAG Lifecycle:** qualquer mudança em `data/embeddings/*` → rebuild com `scripts/embeddings_build.py` + atualização `store/manifest.json` + registro das `rag_index_*` (via `docker/rag-refresh-cron.sh` ou `/ops/metrics/rag/register`).
  *(restante inalterado)*
- Toda alteração em `data/*` gera **diff** + **tests** + **verificação de painel**.
- `build_id` em settings para segregar cache por release.
- `rollback` simples: tag anterior + invalidação de cache.

---

### Epílogo
**Íris é o cérebro. Sirius é o guardião.**
O Araquem é o sistema — audita, mede, aprende e melhora, mas só muda com consciência.

— v2.1.1
