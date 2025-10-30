# 🧩 Guia de Criação e Evolução de Entidades — Projeto **Araquem**

> Documento de referência para padronizar a criação, revisão e manutenção de **entidades** (views lógicas YAML) no ecossistema Mosaic / Sírios AI.

---

## 🔹 O que é uma Entidade

Uma **entidade** representa uma *unidade de conhecimento estruturado* do domínio (ex.: FIIs, indicadores, clientes, carteiras, etc.).  
Ela é declarada em YAML dentro de `data/views/` e é a **fonte de verdade** para o orquestrador (planner → executor → formatter → Íris).

Cada entidade contém:
- metadados (nome, descrição, escopo);
- campos (colunas, tipos, aliases, descrição);
- instruções de roteamento semântico (`ask`);
- parâmetros de apresentação (`result_key`, `return_columns`);
- políticas de cache (`cache_policies.yaml`);
- e links com a ontologia (`data/ask/ontology.yaml`).

---

## 🔹 Convenções Gerais

| Item | Regra | Exemplo |
|------|--------|---------|
| **Nome lógico** | sempre em *snake_case*, sem `view_` | `fiis_cadastro`, `fiis_dividendos` |
| **Arquivo YAML** | mesmo nome do `entity`, dentro de `data/views/` | `data/views/fiis_cadastro.yaml` |
| **result_key** | deve ser o mesmo nome da entidade, prefixado se necessário | `cadastro_fii`, `dividendos_fii` |
| **identifiers** | chaves primárias conhecidas | `[ticker]` ou `[ticker, fii_cnpj]` |
| **default_date_field** | `updated_at` (ou campo temporal principal) | `default_date_field: updated_at` |
| **private** | `true` para views com dados sensíveis (ex.: posições de cliente) | `private: true` |
| **ask.intents** | nome canônico do domínio | `cadastro`, `dividendos`, `precos`, etc. |
| **cache policy** | definida em `data/views/cache_policies.yaml` | TTL e horário de atualização |
| **colunas booleanas** | prefixo `is_` ou `has_` | `is_exclusive`, `has_risk` |
| **enumeração** | indicar valores válidos (quando aplicável) | `allowed_values: [ATIVA, PASSIVA]` |

---

## 🔹 Workflow Padrão

### 1️⃣ Solicitar uma nova entidade (ou revisão futurista)

Use o comando:

> “Sirius, nova **análise futurista** da entidade `<nome_da_view>`.”

ou, se for gerar do zero:

> “Sirius, quero criar a entidade `<nome>` no padrão Araquem (ontologia + cache + testes + templates).”

---

### 2️⃣ Sirius executa o pacote completo

Para cada entidade, ele gera (ou revisa):

| Arquivo / Componente | Descrição |
|-----------------------|------------|
| `data/views/<entidade>.yaml` | Estrutura base da entidade |
| `data/views/cache_policies.yaml` | TTL e refresh |
| `data/ask/ontology.yaml` (patch) | Inclusão do intent |
| `data/concepts/<entidade>_templates.md` | Frases determinísticas de resposta |
| `tests/test_ask_<entidade>.py` | Testes ouro do roteamento |
| `tests/test_results_key_<entidade>.py` | Validação do result_key |
| `docs/dev/<ENTIDADE>_README.md` | Documentação técnica e origem dos dados |

---

### 3️⃣ Regras de qualidade obrigatórias

1. Nenhum hardcode — todos os metadados vêm dos YAMLs.
2. Nenhuma heurística fora da ontologia.
3. Nomes e aliases devem estar **em português claro** (sem termos técnicos).
4. Cada entidade deve ter **apenas um propósito semântico** (ex.: cadastro ≠ ranking).
5. Toda nova entidade precisa passar nos **testes ouro automáticos** antes de ser incluída no catálogo principal.

---

### 4️⃣ Estrutura de Pastas (Design Contract)

```
data/
  ├── views/
  │   ├── fiis_cadastro.yaml
  │   ├── fiis_rankings.yaml
  │   └── cache_policies.yaml
  ├── ask/
  │   └── ontology.yaml
  ├── concepts/
  │   ├── catalog.yaml
  │   └── fiis_cadastro_templates.md
docs/
  ├── dev/
  │   ├── ENTIDADE_GUIDE.md      ← este documento
  │   └── fiis_cadastro_README.md
  └── runbooks/
      └── cache_incidentes.md
tests/
  ├── test_ask_<entidade>.py
  ├── test_results_key_<entidade>.py
  └── test_cache_views.py
```

---

## 🔹 Níveis de Maturidade (entidades)

| Nível | Estado | Descrição |
|-------|---------|-----------|
| **M0** | Esboço | YAML inicial sem testes nem ontologia |
| **M1** | Básico | Roteia via `/ask`, resultado plano |
| **M2** | Com Ontologia | tokens e intents definidos |
| **M3** | Explicável | `planner.explain()` descreve decisão |
| **M4** | Cacheado | TTL e políticas no Redis |
| **M5** | Observável | métricas e telemetria de acesso |
| **M6+** | Integrado | gera respostas naturais via Íris (phi3) |

---

## 🔹 Git Flow recomendado

```bash
# criar branch nova
git checkout -b feat(views):add-fiis-cadastro

# adicionar arquivos
git add data/views/fiis_cadastro.yaml data/views/cache_policies.yaml

# commit semântico
git commit -m "feat(views): add fiis_cadastro entity with cache and ontology intent"

# push e PR
git push origin feat(views):add-fiis-cadastro
```

---

## 🔹 Dúvidas frequentes

| Pergunta | Resposta |
|-----------|-----------|
| Posso chamar de “view” em vez de “entidade”? | Sim, mas “entidade” é preferido no contexto do Araquem. |
| Posso incluir ranking, preço e cadastro na mesma view? | Não — um propósito por entidade. |
| Como defino se é privada? | `private: true` e inclua o filtro obrigatório (`client_id`, `document_number`). |
| Como altero TTL do cache? | Em `data/views/cache_policies.yaml`. |
| E se eu quiser revalidar tudo? | Rode `pytest -q` ou o warmup de cache. |

---

### 🔸 Exemplo de pedido completo para nova entidade

> Sirius, quero criar uma nova entidade chamada **fiis_dividendos** no padrão Araquem.  
> Ela representa o histórico de dividendos pagos por cada FII.  
> Use `ticker` como identificador, TTL diário, e result_key `dividendos_fii`.  
> Gere também o patch de ontologia e testes ouro.
