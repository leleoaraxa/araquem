# 🧠 Araquem — Fase M2 (Ontologia Inteligente · Planner-first)

> **Objetivo:** Implementar o núcleo de planejamento semântico (`planner.explain`) totalmente YAML-driven, sem heurísticas, garantindo rastreabilidade e auditabilidade sobre intenções e entidades.

---

## 📘 Sumário

- [1. Estrutura e Escopo](#1-estrutura-e-escopo)
- [2. Entidades e Ontologia](#2-entidades-e-ontologia)
- [3. Planner YAML-driven](#3-planner-yaml-driven)
- [4. Endpoints e Contratos](#4-endpoints-e-contratos)
- [5. Testes e Smoke](#5-testes-e-smoke)
- [6. Próximos Passos (M3 Preview)](#6-próximos-passos-m3-preview)

---

## 1. Estrutura e Escopo

**Fase:** M2 — Ontologia Inteligente
**Meta:** Decodificar perguntas em intenções e entidades com base em `data/ontology/entity.yaml`, sem SQL ainda.
**Stack:** FastAPI · Pydantic · YAML · Planner local · Redis/Grafana/Tempo já provisionados (infra M1).
**Escopo ativo:** domínio público `fiis_cadastro`.

**Diretórios relevantes:**
```

data/
├─ entities/
│   ├─ fiis_cadastro.yaml
│   └─ cache_policies.yaml
└─ ontology/
└─ entity.yaml
app/
└─ planner/
├─ ontology_loader.py
└─ planner.py
tests/
├─ test_planner_explain.py
├─ test_ontology_tokens.py
scripts/
└─ test_smoke.sh

```

---

## 2. Entidades e Ontologia

### 🔹 Entidade: `fiis_cadastro.yaml`

- Reflete fielmente a view `fiis_cadastro` no banco (colunas `ticker`, `fii_cnpj`, `display_name`, `b3_name`, `classification`, `sector`, etc.).
- Inclui colunas documentadas e aliases amigáveis.
- Configurada como pública (`private: false`) com TTL diário (`00:15`).

### 🔹 Cache Policy (`cache_policies.yaml`)

```yaml
policies:
  fiis_cadastro:
    ttl_seconds: 86400
    refresh_at: "00:15"
    scope: pub
```

### 🔹 Ontologia (`entity.yaml`)

* Normalização: `lower` + `strip_accents`
* Tokens relevantes: `cadastro`, `cnpj`, `administrador`, `site`, `custodiante`
* Anti-tokens: `preco`, `cotacao`, `dividendo`, `noticia`
* Ponderação: token = 1.0, frase = 2.0
* Entidade associada: `fiis_cadastro`

> ⚖️ Anti-tokens penalizam intenções incorretas, garantindo que perguntas como “preço do HGLG11” não sejam mapeadas para “cadastro”.

---

## 3. Planner YAML-driven

**Local:** `app/planner/`
**Arquivos:**

* `ontology_loader.py`: parser seguro do YAML → objetos `IntentDef` e `Ontology`.
* `planner.py`: normalização, tokenização, scoring e `explain()`.

### 🔍 Funcionamento

1. **Normalize:** converte para minúsculas, remove acentos.
2. **Tokenize:** divide por `\b`.
3. **Score:** soma pesos por tokens e frases incluídas; aplica penalidades por anti-tokens.
4. **Escolhe:** intenção com maior pontuação → primeira entidade vinculada.
5. **Retorna:** JSON explicativo com detalhes e scores.

---

## 4. Endpoints e Contratos

### `/debug/planner`

> Inspeciona a decisão do planner (sem SQL).

**Exemplo:**

```
GET /debug/planner?q=CNPJ%20do%20VINO11
```

**Resposta:**

```json
{
  "normalized": "cnpj do vino11",
  "tokens": ["cnpj", "do", "vino11"],
  "chosen": {
    "intent": "cadastro",
    "entity": "fiis_cadastro",
    "score": 1.0
  }
}
```

---

### `/ask` (modo Planner-first)

> Ainda não executa SQL; apenas valida payload e injeta metadados do planner.

**Payload:**

```json
{
  "question": "Qual o CNPJ do HGLG11?",
  "conversation_id": "conv-001",
  "nickname": "leleo",
  "client_id": "00000000000"
}
```

**Resposta esperada:**

```json
{
  "status": {"reason": "unroutable", "message": "Planner not configured yet"},
  "results": {},
  "meta": {
    "planner": {
      "chosen": {
        "intent": "cadastro",
        "entity": "fiis_cadastro",
        "score": 1.0
      }
    }
  }
}
```

---

## 5. Testes e Smoke

### 🧪 Unit tests

* `test_planner_explain.py`: garante retorno e estrutura do `/debug/planner`.
* `test_ontology_tokens.py`: valida score positivo para “CNPJ do VINO11” e penalização em “Preço do HGLG11 hoje”.

### 🚀 Smoke Test Script

`scripts/test_smoke.sh` executa:

1. `/healthz`
2. `/debug/planner`
3. `/ask`
4. `pytest -q`

**Rodar:**

```bash
docker compose exec api bash scripts/test_smoke.sh
```

**Saída esperada:**

```
✅ Smoke test passed — Infra + Planner OK
```

---

## 6. Próximos Passos (M3 Preview)

**Fase M3 — Orquestração (Routing → SQL → Formatter)**

> “Do YAML ao dado real.”

🔜 Objetivos:

* Conectar planner ao `orchestrator` e `builder`.
* Injetar filtros e montar SQL dinâmico.
* Implementar `formatter` para normalizar tipos (datas, decimais, bools).
* Produzir respostas reais via Postgres.

**DoD de M3:**

* `/ask` retorna dados reais da view `fiis_cadastro`.
* `meta.planner_intent/entity/score` propagados corretamente.
* Painel Grafana exibe latência e linhas retornadas.

---

📅 **Status Atual:**
✅ Infra (M1)
✅ Ontologia e Planner (M2)
⏳ Routing e SQL (M3, próximo passo)

---

**Íris é o cérebro. Sirius é o guardião.**
*Araquem aprende com consciência — e nunca por acaso.*
