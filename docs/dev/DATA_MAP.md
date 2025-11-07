# Data Map (vivo)

Resumo operacional dos contratos de dados Araquem.
Atualizado automaticamente a cada lote de sincronização.

---

### 📊 Tabela de referência

| Arquivo / Grupo                | Objetivo resumido                 | Consumidores principais | Estágio de uso |
| ------------------------------ | --------------------------------- | ----------------------- | -------------- |
| `ontology/entity.yaml`         | Ontologia intents→entities        | Planner / Orchestrator  | Bootstrap      |
| `entities/*.yaml`              | Contratos SQL e agregações        | Builder / Infer Params  | Request `/ask` |
| `ops/param_inference.yaml`     | Inferência semântica (agg/window) | Planner / Builder       | Request `/ask` |
| `ops/planner_thresholds.yaml`  | Thresholds e gates                | Planner / Quality       | Request / QA   |
| `ops/observability.yaml`       | Config métricas/tracing           | Bootstrap               | Startup        |
| `concepts/*`                   | Corpus textual (conceitos)        | Embeddings build        | Pipeline RAG   |
| `embeddings/index.yaml`        | Config de índice vetorial         | Embeddings build        | Pipeline RAG   |
| `embeddings/store/*`           | Base e manifest RAG               | Planner (RAG)           | Request `/ask` |
| `golden/m65_quality.yaml`      | Casos canônicos de roteamento     | QA / RAG index          | QA e Corpus    |
| `ops/quality/*.json`           | Amostras automáticas de QA        | Cron / QA endpoints     | QA pipeline    |
| `entities/cache_policies.yaml` | TTL por entidade                  | Cache layer             | Request `/ask` |

---

### ⚖️ Fontes únicas (decisões de governança)

* **Ontologia:** `data/ontology/entity.yaml` é a única fonte de intents/tokens.
* **Golden set:** `data/golden/m65_quality.yaml` é a única fonte canônica de QA; o `routing_samples.json` é **gerado automaticamente** via `scripts/core/golden_sync.py`.
* **Inferência:** semântica em `param_inference.yaml`, capacidades em `entities/*.yaml`.
* **Embeddings:** `index.yaml` define *o que entra*, `manifest.json` controla invalidação de cache.

---

### ⚙️ Geradores e utilitários

| Script                                    | Função                                                  | Saída                    | Execução                                         |
| ----------------------------------------- | ------------------------------------------------------- | ------------------------ | ------------------------------------------------ |
| `scripts/gen_projection_from_entities.py` | Gera projeções QA (`projection_*.json`)                 | `data/ops/quality/`      | `python scripts/gen_projection_from_entities.py` |
| `scripts/core/golden_sync.py`                  | Sincroniza `m65_quality.yaml` → `routing_samples.json`  | `data/ops/quality/`      | `python scripts/core/golden_sync.py --check`          |
| `scripts/core/validate_data_contracts.py`      | Valida contratos YAML e inferência                      | Console                  | `python scripts/core/validate_data_contracts.py`      |
| `scripts/embeddings/embeddings_build.py`             | Regera índice RAG (`embeddings.jsonl`, `manifest.json`) | `data/embeddings/store/` | `python scripts/embeddings/embeddings_build.py`             |

---

### 🔄 Ordem de leitura no ciclo `/ask`

```
1️⃣ Ontologia → detecta intent/entity
2️⃣ Thresholds → aplica gates mínimos
3️⃣ Param inference → define agg/window
4️⃣ Entidade YAML → valida e constrói SQL
5️⃣ Executor → consulta PostgreSQL
6️⃣ Formatter → normaliza saída
7️⃣ RAG (opcional) → enriquece contexto
8️⃣ Cache / Observabilidade → métricas e TTL
```

---

### 🧾 Notas operacionais

* Todos os arquivos sob `data/` são YAML/JSON versionados e auditáveis.
* Alterações em `ontology/` ou `entities/` impactam o planner imediatamente.
* `manifest.json` funciona como *chave de hot reload* do embeddings.
* Antes do build:

  ```
  python scripts/core/validate_data_contracts.py
  python scripts/core/golden_sync.py --check
  ```
* Durante QA contínuo:

  ```
  python scripts/quality/quality_push_cron.py --dry-run
  ```
