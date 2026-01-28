# ASK_CONCEPTS_INSTITUTIONAL_SUPPORT_AUDIT

## 1) ASK PIPELINE MAP

### Entry point + quota + planner
- **/ask entrypoint** → `app/api/ask.py::ask` (FastAPI). Fluxo inicial:
  1) Carrega quota (`load_ask_quota_policy`) e aplica `enforce_ask_quota`.
  2) Executa `planner.explain(question)`.
  3) Se não houver entidade (`entity=None`) retorna `unroutable`; se o `orchestrator` retornar `gated`, responde com motivo de gate.
- **Planner** → `app/planner/planner.py::Planner.explain`.
  - Normalização + tokenização: `_normalize`, `_tokenize`.
  - Bucketize (pré e pós-escolha): `_resolve_bucket_from_plan` com `data/ontology/entity.yaml`.
  - Intent scoring base (tokens/phrases + anti_tokens).
  - Fusão RAG (opcional) + thresholds (gates) via `data/ops/planner_thresholds.yaml`.
  - Resultado com `chosen.intent`, `chosen.entity`, `chosen.score` + `explain`.
- **Ontologia** → `app/planner/ontology_loader.py::load_ontology` carrega `data/ontology/entity.yaml`.

### Orchestrator (plan + gate + entity select + SQL)
- **prepare_plan** → `app/orchestrator/routing.py::Orchestrator.prepare_plan`.
  - Reusa `planner.explain`.
  - Extrai identificadores (tickers), inferência paramétrica (`infer_params` → `data/ops/param_inference.yaml`).
  - Decide `compute_mode` (SQL vs conceptual), calcula `plan_hash` para cache.
- **gate de thresholds** → `app/orchestrator/routing.py::Orchestrator.route_question`.
  - Aplica thresholds (prioridade entity > intent > defaults) com base no snapshot do planner.
  - Se gate bloqueia, retorna status `gated` antes de SQL.
- **Entity select + SQL** → `app/orchestrator/routing.py` chama `build_select_for_entity` e executa via `PgExecutor`.

### Presenter/Narrator + resposta
- **Presenter** → `app/presenter/presenter.py::present` (chamado no /ask após `orchestrator.route_question`).
- **RAG context** → `app/rag/context_builder.py::build_context` (usa `data/policies/rag.yaml` + índice de embeddings).
- **Narrator** → `app/narrator/narrator.py` para formatação/explicações finais.

### Configs/YAML carregados + cache
- **Ontologia**: `data/ontology/entity.yaml` → `Planner`/`ontology_loader`.
- **Thresholds**: `data/ops/planner_thresholds.yaml` → `_load_thresholds` (cache em `_THRESHOLDS_CACHE`).
- **RAG policy**: `data/policies/rag.yaml` → `_load_rag_policy` (cache em `_RAG_POLICY_CACHE`).
- **Embeddings**: `data/embeddings/store/embeddings.jsonl` (via `cached_embedding_store`).
- **Cache YAML**: `app/utils/filecache.py::load_yaml_cached` (cache por mtime).
- **Entity ontology cache**: `_load_entity_ontology` usa `lru_cache(maxsize=1)`.

## 2) INTENTS LOADED AT RUNTIME

### Fonte canônica
- **Fonte única**: `data/ontology/entity.yaml` carregado por `app/planner/ontology_loader.py::load_ontology`.

### Intents carregados (nome + bucket + weight + sources)
> **Sources** = `data/ontology/entity.yaml` (intents + entities). Bucket é lido de `intents[].bucket` e/ou mapeado para buckets de `buckets:` no mesmo arquivo.

| Intent | Bucket | Weight | Entities (sources) |
|---|---|---|---|
| ticker_query | A | 10 | fiis_quota_prices, fiis_dividends, fiis_overview, fiis_financials_risk, fiis_financials_snapshot, fiis_financials_revenue_schedule, fiis_rankings, fiis_yield_history, fiis_legal_proceedings, fiis_real_estate, fiis_dividends_yields, fiis_registrations |
| client_fiis_positions |  |  | client_fiis_positions |
| client_fiis_dividends_evolution |  |  | client_fiis_dividends_evolution |
| client_fiis_performance_vs_benchmark |  | 7 | client_fiis_performance_vs_benchmark |
| client_fiis_performance_vs_benchmark_summary |  |  | client_fiis_performance_vs_benchmark_summary |
| fiis_registrations |  |  | fiis_registrations |
| fiis_overview |  | 3 | fiis_overview |
| fiis_quota_prices |  | 4 | fiis_quota_prices |
| fiis_dividends |  | 2.5 | fiis_dividends |
| fiis_yield_history |  | 3 | fiis_yield_history |
| fiis_financials_snapshot |  | 5 | fiis_financials_snapshot |
| fiis_financials_revenue_schedule |  | 2 | fiis_financials_revenue_schedule |
| fiis_financials_risk |  | 7 | fiis_financials_risk |
| fiis_real_estate |  |  | fiis_real_estate |
| fiis_news |  |  | fiis_news |
| fiis_legal_proceedings |  | 4 | fiis_legal_proceedings |
| fiis_rankings |  | 6 | fiis_rankings |
| history_b3_indexes |  | 6 | history_b3_indexes |
| history_currency_rates |  | 5 | history_currency_rates |
| history_market_indicators |  | 2 | history_market_indicators |
| fiis_dividends_yields |  | 6 | fiis_dividends_yields |
| client_fiis_enriched_portfolio |  | 3 | client_fiis_enriched_portfolio |
| consolidated_macroeconomic |  | 5 | consolidated_macroeconomic |

### Conclusões
- **NÃO há intents institucionais/support/concept_lookup** na ontologia carregada. A lista acima é a única carregada em runtime.
- **Buckets**: apenas `ticker_query` possui bucket explícito na ontologia (A). Os demais não definem bucket; bucket é resolvido pela lista de entidades em `buckets:`.

## 3) CONCEPTS DATA AUDIT

### Arquivos lidos
- `data/concepts/catalog.yaml` + todos os `data/concepts/concepts-*.yaml`.

### Schema e consistência
- O schema canônico (validado pelo script `scripts/diagnostics/validate_concepts_schema.py`) espera:
  - **Top-level**: `version`, `domain`, `owner`, `sections`.
  - **Section**: `id`, `title`, `items`.
  - **Item**: `name`, `description`, `aliases`, `related_entities`, `related_intents`, `typical_questions`, `typical_uses`, `interpretation`, `definition`, `usage`, `cautions`, `notes`, `subitems`, `id`.
- Não existe chave obrigatória única para `items` (o campo `id` é opcional), logo o **lookup determinístico não está especificado** por schema.

### Duplicidades
- **Section IDs**: sem duplicidades globais.
- **Item IDs**: sem duplicidades globais (onde existem).
- **Item names duplicados** (entre arquivos diferentes):
  - "Índices da B3"
  - "Moedas"
  - "Alfa de Jensen"
  - "Beta e R²"
  - "Pedir explicação de colunas"
  (conferir fontes nos YAMLs listados no comando de auditoria abaixo).

### Ponte com embeddings / entidades
- `data/embeddings/index.yaml` inclui TODOS os YAMLs de conceitos nas coleções (`concepts-*`).
- `data/policies/rag.yaml` habilita RAG por **entidade**, não por conceito. Não há entity/intents institucionais ou support amarradas a essas coleções.
- Não há código no pipeline de roteamento consumindo `data/concepts/*` diretamente (apenas scripts de diagnóstico e o índice de embeddings).

### Evidências usadas nesta auditoria (comandos)
```bash
rg -n "data/concepts|concepts-" app scripts tests
python - <<'PY'
from pathlib import Path
import yaml
from collections import defaultdict

root = Path('data/concepts')
concept_files = sorted(root.glob('concepts-*.yaml'))
section_ids = defaultdict(list)
item_ids = defaultdict(list)
item_names = defaultdict(list)
for path in concept_files:
    data = yaml.safe_load(path.read_text())
    for section in data.get('sections', []) or []:
        sid = section.get('id')
        if sid:
            section_ids[sid].append(str(path))
        for item in section.get('items', []) or []:
            iid = item.get('id')
            if iid:
                item_ids[iid].append(str(path))
            name = item.get('name')
            if name:
                item_names[name].append(str(path))

print('section_id_duplicates', {k:v for k,v in section_ids.items() if len(v)>1})
print('item_id_duplicates', {k:v for k,v in item_ids.items() if len(v)>1})
print('item_name_duplicates', {k:v for k,v in item_names.items() if len(v)>1})
PY
```

## 4) REPRO: "o que a sirios faz" (evidence)

### Comando local (Planner)
```bash
python - <<'PY'
from app.planner.planner import Planner
p = Planner('data/ontology/entity.yaml')
q = 'o que a sirios faz'
plan = p.explain(q)
print('chosen', plan['chosen'])
print('intent_scores', {k:v for k,v in plan['intent_scores'].items() if v != 0.0})
print('all_scores_zero', all(v == 0.0 for v in plan['intent_scores'].values()))
print('tokens', plan['tokens'])
print('normalized', plan['normalized'])
print('thresholds_applied', plan.get('explain', {}).get('scoring', {}).get('thresholds_applied'))
PY
```

### Saída observada
- `tokens`: `['o', 'que', 'a', 'sirios', 'faz']`
- **Todos os intent_scores = 0.0**
- `chosen.intent`: `ticker_query` (score 0.0, `accepted=False`)
- `thresholds_applied.reason`: `low_score`

## 5) ROOT CAUSE — why all scores are 0.0

1) **A ontologia carregada não contém intents institucionais/support/concept_lookup**.
   - A lista runtime é exclusivamente de FIIs, macro e carteira (23 intents). Não existe intent “institutional_about”, “support_howto” etc.
2) **A pergunta “o que a sirios faz” não bate tokens/phrases incluídas nos intents atuais.**
   - As únicas ocorrências de “sirios” na ontologia são em frases do intent `fiis_rankings` ("ranking sirios", etc.). Isso não cobre o enunciado institucional.
3) **Como não há intent com score > 0**, o planner escolhe o fallback (`ticker_query`) com score 0.0 e **thresholds bloqueiam** com `low_score`.
4) **`data/concepts/*` não é consumido pelo roteamento** do /ask. Esses YAMLs entram apenas no índice de embeddings, mas o RAG é acionado por `entity`, e **não há entidade/intents conceituais** configuradas para institucional/support.

## 6) DECISION: patch safe? (YES/NO)

**NO.**

### Motivo
- Não há wiring atual para intents institucionais/concepts/support.
- Qualquer patch exigiria:
  - Definir intents/entidades novas na ontologia (YAML),
  - Conectar entidade a respostas (SQL vs conceptual),
  - E provar em suites que não regressa o roteamento atual.

Sem essas garantias (testes + suites de roteamento), não é possível provar ausência de regressão.

## 7) If YES: Patch summary + Evidence

N/A (decisão = NO).

## 8) If NO: Next steps to reach certainty (no guesswork)

1) **Introduzir intents institucionais/support em `data/ontology/entity.yaml`** (somente via YAML, sem heurísticas). Exemplos:
   - `institutional_about`, `institutional_privacy`, `institutional_terms`, `support_howto`, `concept_lookup`.
   - Cada intent precisa apontar para uma entidade (`entities`) dedicada a conteúdo conceitual.
2) **Criar entidade textual (conceptual)** que não dependa de SQL:
   - Nova entidade `concepts_institutional` (exemplo) com `ask.requires_identifiers` vazio e `options.supports_multi_ticker=false`.
   - Configurar para `skip_sql` quando não houver identificadores, para que o narrator use contexto RAG.
3) **Atualizar política RAG** (`data/policies/rag.yaml`) para habilitar as novas entidades em coleções `concepts-*`.
4) **Adicionar testes/suites**:
   - Suite routing: "o que a sirios faz" -> `institutional_about` (ou equivalente).
   - Suite routing: "qual a posição no ranking sirios do hglg11" permanece em `fiis_rankings`.
5) **Rodar gates** (obrigatório p/ patch): `pytest` + `scripts/diagnostics/run_ask_suite.py` nas suites relevantes.

