# 🧩 Guia de Criação e Evolução de Entidades — Projeto **Araquem**

> Documento de referência para padronizar a criação, revisão e manutenção de **entidades** (entities lógicas YAML) no ecossistema Mosaic / Sírios AI.

---

## 🔹 O que é uma Entidade

Uma **entidade** representa uma *unidade de conhecimento estruturado* do domínio (ex.: FIIs, indicadores, clientes, carteiras, etc.).
Ela é declarada em YAML dentro de `data/entities/` e é a **fonte de verdade** para o orquestrador (planner → executor → formatter → Íris).

Cada entidade contém:
- metadados (nome, descrição, escopo);
- campos (colunas, tipos, aliases, descrição);
- instruções de roteamento semântico (`ask`);
- parâmetros de apresentação (`result_key`, `return_columns`);
- políticas de cache (`cache_policies.yaml`);
- e links com a ontologia (`data/ontology/entity.yaml`).

---

## 🔹 Convenções Gerais

| Item | Regra | Exemplo |
|------|------|---------|
| **Nome lógico** | snake_case, sem `view_` | `fiis_cadastro`, `fiis_precos` |
| **Arquivo YAML** | mesmo nome do `entity` em `data/entities/` | `data/entities/fiis_precos.yaml` |
| **result_key** | igual ao nome da entidade (ou prefixado claro) | `cadastro_fii`, `precos_fii` |
| **identifiers** | chaves primárias conhecidas | `[ticker]` |
| **default_date_field** | campo temporal principal | `traded_at` (preços) |
| **private** | `true` p/ dados sensíveis | `private: false` p/ públicos |
| **ask.intents** | nome canônico do domínio | `cadastro`, `precos`, etc. |
| **cache policy** | em `data/entities/cache_policies.yaml` | TTL e refresh |
| **colunas booleanas** | prefixo `is_`/`has_` | `is_exclusive` |
| **enumeração** | listar valores | `allowed_values: [ATIVA, PASSIVA]` |

---

## 🔹 Workflow Padrão

### 1️⃣ Solicitar uma nova entidade (ou revisão futurista)
- “Sirius, nova **análise futurista** da entidade `<nome_da_view>`.”
- “Sirius, quero criar a entidade `<nome>` no padrão Araquem (ontologia + cache + testes + templates).”

### 2️⃣ Pacote gerado/revisado por entidade

| Arquivo / Componente | Descrição |
|---|---|
| `data/entities/<entidade>.yaml` | Estrutura base da entidade |
| `data/entities/cache_policies.yaml` | TTL e refresh |
| `data/ontology/entity.yaml` (patch) | Inclusão/ajuste de intent e entidades |
| `data/concepts/<entidade>_templates.md` | Frases determinísticas |
| `tests/test_ask_<entidade>.py` | Testes ouro de roteamento |
| `tests/test_results_key_<entidade>.py` | Valida `result_key` |
| `docs/dev/<ENTIDADE>_README.md` | Documentação técnica |

---

## 🔹 Regras de qualidade obrigatórias

1. **Sem hardcodes/heurísticas** — tudo vem de YAML/Ontologia/SQL real.
2. **Propósito único por entidade** (ex.: `fiis_cadastro` ≠ `fiis_precos`).
3. **Nomes/aliases em PT-BR claro**.
4. **Testes ouro obrigatórios** antes de subir ao catálogo.

---

## 🔹 Estrutura de Pastas (Design Contract)

```
data/
├── entities/
│   ├── fiis_cadastro.yaml
│   ├── fiis_precos.yaml
│   └── cache_policies.yaml
├── ontology/
│   └── entity.yaml
├── concepts/
│   ├── catalog.yaml
│   ├── fiis_cadastro_templates.md
│   └── fiis_precos_templates.md
docs/
├── dev/
│   ├── ENTIDADE_GUIDE.md
│   ├── fiis_cadastro_README.md
│   └── fiis_precos_README.md
└── runbooks/
└── cache_incidentes.md
tests/
├── test_ask_<entidade>.py
├── test_results_key_<entidade>.py
└── test_cache_entities.py

```

---

## 🔹 Níveis de Maturidade (entities)

| Nível | Estado | Descrição |
|---|---|---|
| **M0** | Esboço | YAML inicial |
| **M1** | Básico | Roteia via `/ask` |
| **M2** | Com Ontologia | intents/tokens definidos |
| **M3** | Explicável | `planner.explain()` |
| **M4** | Cacheado | TTL/Redis |
| **M5** | Observável | métricas/telemetria |
| **M6+** | Integrado | Respostas naturais (Íris) |

---

## 🔹 Git Flow recomendado

```bash
git checkout -b feat(entities):add-fiis-precos
git add data/entities/fiis_precos.yaml data/ontology/entity.yaml data/golden/m65_quality.yaml
git commit -m "feat(entities): add fiis_precos and ontology intent precos + golden samples"
git push origin feat(entities):add-fiis-precos
```

---

### 🔸 Exemplo de pedido completo para nova entidade

> “Sirius, criar **fiis_precos** no padrão Araquem, baseada na `CREATE VIEW fiis_precos AS ...`.
> Identificador `ticker`, `default_date_field: traded_at`, `result_key: precos_fii`, e testes ouro de roteamento.”

```

---
