# 🧩 **Guia Pragmático de Criação e Evolução de Entidades — Projeto Araquem**

> Manual objetivo para solicitar, gerar e validar **novas entidades** (1×1 ou históricas) no núcleo Araquem — sem heurísticas, sem hardcodes, 100% YAML + Ontologia + SQL real.

---

## 🔹 1️⃣ Conceito

Uma **entidade** é uma *representação lógica YAML* de uma view SQL real.
Ela define o contrato semântico, os metadados, os campos, o roteamento (`ask`) e o cache — servindo de fonte única para o planner, executor e explain (Íris).

---

## 🔹 2️⃣ Checklist mínimo (entidade nova)

Cada nova entidade precisa obrigatoriamente dos **7 arquivos/pontos** abaixo:

| Ordem | Componente                 | Local                                         | Descrição                              |
| :---- | :------------------------- | :-------------------------------------------- | :------------------------------------- |
| 1️⃣   | View SQL real              | `CREATE VIEW <nome>`                          | Base de verdade no banco               |
| 2️⃣   | YAML da entidade           | `data/entities/<nome>.yaml`                   | Estrutura completa da entidade         |
| 3️⃣   | Cache policy               | `data/entities/cache_policies.yaml`           | TTL, refresh e escopo                  |
| 4️⃣   | Ontologia                  | `data/ontology/entity.yaml`                   | Inclusão de intent + tokens + entities |
| 5️⃣   | Golden routing (YAML/JSON) | `data/golden/m65_quality.yaml` e `.json`      | Casos ouro de roteamento (NL→SQL)      |
| 6️⃣   | Quality projection         | `data/ops/quality/projection_<entidade>.json` | Verifica colunas e schema              |
| 7️⃣   | (opcional) Concepts        | `data/concepts/<entidade>_templates.md`       | Frases determinísticas e contextos     |

---

## 🔹 3️⃣ Convenções rápidas

| Item             | Regra                                                                  |
| ---------------- | ---------------------------------------------------------------------- |
| Nome lógico      | `snake_case`, sem `view_`                                              |
| Result key       | `result_key: <entidade>_fii`                                           |
| Identificadores  | `[ticker]` ou `[id]` conforme a view                                   |
| Campo temporal   | `default_date_field: traded_at`, `payment_date`, etc.                  |
| Campos booleanos | prefixo `is_` / `has_`                                                 |
| Nome PT-BR       | `alias:` e `description:` sempre em português claro                    |
| ask.intents      | nome curto do domínio (`cadastro`, `precos`, `dividendos`, `rankings`) |
| Cache            | sempre declarado no arquivo `cache_policies.yaml`                      |
| Sem heurísticas  | tudo lido de YAML, Ontologia e SQL real                                |
| Testes           | **obrigatório ter golden e projection** antes do push                  |

---

## 🔹 4️⃣ Comando de pedido padrão (Sirius Prompt)

Para criar qualquer nova entidade (exemplo abaixo: `fiis_dividendos`):

```
Sirius, criar a entidade fiis_dividendos no padrão Araquem.
Base: CREATE VIEW fiis_dividendos AS ...
Identificador: ticker
Data principal: payment_date
Result key: dividendos_fii
Inclua cache, ontologia, golden e projection como fizemos nos últimos casos.
```

---

## 🔹 5️⃣ Estrutura esperada no repositório

```
data/
├── entities/
│   ├── fiis_precos.yaml
│   ├── fiis_dividendos.yaml
│   ├── fiis_rankings.yaml
│   └── cache_policies.yaml
├── ontology/
│   └── entity.yaml
├── ops/
│   └── quality/
│       ├── projection_fiis_precos.json
│       ├── projection_fiis_dividendos.json
│       └── projection_fiis_rankings.json
├── golden/
│   └── m65_quality.yaml
│   └── m65_quality.json
```

---

## 🔹 6️⃣ Cache Policy Padrão

| Entidade          | TTL        | Refresh  | Escopo |
| ----------------- | ---------- | -------- | ------ |
| `fiis_cadastro`   | 86400 (1d) | 01:15    | pub    |
| `fiis_precos`     | 86400 (1d) | 01:15    | pub    |
| `fiis_dividendos` | 86400 (1d) | 01:15    | pub    |
| `fiis_rankings`   | 86400 (1d) | 01:15    | pub    |

> Todos os TTLs e horários devem ser ajustados apenas por necessidade operacional, nunca via código.

---

## 🔹 7️⃣ Workflow real

| Etapa | Ação                                   | Ferramenta         |
| :---- | :------------------------------------- | :----------------- |
| 1️⃣   | Criar view SQL no banco                | SQL real           |
| 2️⃣   | Gerar `data/entities/<nome>.yaml`      | via Sirius         |
| 3️⃣   | Incluir cache policy                   | manual/YAML        |
| 4️⃣   | Atualizar ontologia (`intent`)         | via patch          |
| 5️⃣   | Adicionar samples no `golden`          | YAML + JSON        |
| 6️⃣   | Criar projection para schema check     | JSON               |
| 7️⃣   | Rodar `python scripts/quality_push.py` | garante 100% verde |

---

## 🔹 8️⃣ Git Flow

```bash
git checkout -b feat(entities):add-fiis-dividendos
git add data/entities/fiis_dividendos.yaml data/ontology/entity.yaml data/golden/m65_quality.yaml data/ops/quality/projection_fiis_dividendos.json
git commit -m "feat(entities): add fiis_dividendos with ontology intent dividendos + golden + projection"
git push origin feat(entities):add-fiis-dividendos
```

---

## 🔹 9️⃣ Critérios de Aceitação

✅ `pytest tests/test_ask_<entidade>.py`
✅ `/ops/quality/push` retorna `{"status":"pass"}`
✅ Nenhum hardcode nas rotas
✅ Ontologia e cache consistentes
✅ Planner.explain() retorna intent correta

---

## 🔹 10️⃣ Exemplo direto de uso

```
CREATE VIEW fiis_rankings AS
SELECT ticker, users_ranking_count, users_rank_movement_count, sirios_ranking_count,
       sirios_rank_movement_count, ifix_ranking_count, ifix_rank_movement_count,
       ifil_ranking_count, ifil_rank_movement_count, created_at, updated_at
FROM view_fiis_info;

Sirius, gerar a entidade fiis_rankings no padrão Araquem, 1×1, identificador ticker,
incluindo cache policy, intent rankings e golden samples.
```

---

**Resumo final:**

> Sempre que surgir uma nova view SQL → pedir a entidade YAML → gerar pacote completo (YAML + cache + ontologia + golden + projection) → validar via `/ops/quality/push`.
> Sem heurísticas, sem atalhos, sempre pelo contrato Araquem.

---
