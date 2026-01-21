# Mapa de carregamento de Concepts/Contracts (Institutional) no Araquem

## 1) Resumo executivo (5–10 linhas)
1. O `/ask` chama o `Planner` para roteamento e depois delega a construção da resposta ao `Presenter`, que decide baseline (templates/formatter) e, se habilitado, chama o `Narrator`. (ver `app/api/ask.py` e `app/presenter/presenter.py`).
2. O `Planner` carrega ontologia via `load_ontology` a partir de `data/ontology/entity.yaml` (por default), além de regras de bucket em `data/ontology/bucket_rules.yaml`. (ver `app/core/context.py` e `app/planner/planner.py`).
3. Não há loader no runtime para `data/concepts/catalog.yaml` ou `data/concepts/concepts-*.yaml`; o único uso direto de `data/concepts` em runtime é o fallback de templates legados (`data/concepts/<entity>_templates.md`). (ver `app/templates_answer/__init__.py`).
4. Os conceitos aparecem no pipeline de RAG apenas via índice/embeddings: `data/embeddings/index.yaml` lista `data/concepts/catalog.yaml` e `concepts-*.yaml` como fontes para indexação. (ver `data/embeddings/index.yaml`).
5. Os contratos institucionais (`data/contracts/responses/*.yaml`) existem e descrevem o contrato 1–2–3, mas não há referência a eles no código de resposta atual; o ponto de montagem da resposta está no `Presenter` e no `Narrator`. (ver `data/contracts/responses/*` e `app/presenter/presenter.py`).
6. Para o contrato 1–2–3, o ponto mais natural de acoplamento é o `Presenter`, que já decide baseline/template e orquestra o `Narrator`. (ver `app/presenter/presenter.py`).

---

## 2) Entrega 1 — Inventário de loaders e pontos de entrada

> **Critério:** loaders/parsers de YAML + caminhos usados (concepts, ontology, policies, response contracts/templates/narrator prompts).

| Domínio | Arquivo loader | Função/classe | O que carrega | Paths esperados | Chamado por |
| --- | --- | --- | --- | --- | --- |
| **YAML cache (genérico)** | `app/utils/filecache.py` | `load_yaml_cached(path: str)` | YAML arbitrário com cache por mtime | Qualquer path de YAML passado pelos chamadores | Usado por Planner/Orchestrator/Narrator/RAG/etc. (ver evidências abaixo) |
| **Ontologia** | `app/planner/ontology_loader.py` | `load_ontology(path: str)` | Ontologia (intents, tokens, weights etc.) | `data/ontology/entity.yaml` (default via `ONTO_PATH`) | `Planner` (em `app/planner/planner.py`), instanciado em `app/core/context.py` |
| **Bucket rules (Planner)** | `app/planner/planner.py` | `_load_bucket_rules(path: str)` | Regras declarativas de buckets | `data/ontology/bucket_rules.yaml` | `resolve_bucket()` no fluxo do `Planner` |
| **Ticker index (Planner)** | `app/planner/ticker_index.py` | `TickerIndex.__init__` | Catálogo de tickers e regras de matching | `data/ontology/ticker_index.yaml` (default) | `resolve_ticker_from_text` no `Planner` |
| **Entity YAML (Orchestrator)** | `app/orchestrator/routing.py` | `_load_entity_config(entity)` | YAML de entidade (ask/presentation/etc.) | `data/entities/<entity>/<entity>.yaml` | `Orchestrator` (ex.: extração de métricas solicitadas) |
| **Entity YAML (SQL builder)** | `app/builder/sql_builder.py` | `_load_entity_yaml(entity)` | YAML de entidade (SQL / columns) | `data/entities/<entity>/<entity>.yaml` | `build_select_for_entity` no Orchestrator |
| **Param inference** | `app/planner/param_inference.py` | `_load_yaml(path)` | `param_inference.yaml` (compute-on-read) | `data/ops/param_inference.yaml` (default) | `infer_params` (Orchestrator) |
| **RAG policy** | `app/rag/context_builder.py` | `load_rag_policy()` | Política de RAG | `data/policies/rag.yaml` | `Presenter` (RAG context) e `get_rag_policy()` |
| **Narrator policy** | `app/narrator/narrator.py` | `_load_narrator_policy()` | Política do Narrator | `data/policies/narrator.yaml` | `Narrator.__init__` (instanciado em `/ask`) |
| **Narrator shadow policy** | `app/narrator/narrator.py` | `_load_narrator_shadow_policy()` | Política de shadow | `data/policies/narrator_shadow.yaml` | `Narrator.__init__` |
| **Context policy** | `app/context/context_manager.py` | `_load_policy()` | Política de contexto conversacional | `data/policies/context.yaml` | `ContextManager` (instanciado em `app/core/context.py`) |
| **Templates (legacy)** | `app/templates_answer/__init__.py` | `_load_templates(entity)` | Templates em Markdown (não YAML) | `data/entities/<entity>/template.md`, `data/entities/<entity>/templates.md`, `data/concepts/<entity>_templates.md` | `Presenter.render_answer()` |
| **Templates Jinja (responses)** | `app/formatter/rows.py` | `render_rows_template()` | Templates Jinja para respostas | `data/entities/<entity>/responses/<kind>.md.j2` | `Presenter.render_rows_template()` |
| **Narrator prompts** | `app/narrator/prompts.py` | `SYSTEM_PROMPT`, `PROMPT_TEMPLATES`, `FEW_SHOTS` | Prompts em código (não YAML) | N/A (strings inline) | `Narrator` |

### Evidências (excertos curtos)
- Loader YAML genérico: `load_yaml_cached` com `yaml.safe_load`. (app/utils/filecache.py)
```
34 def load_yaml_cached(path: str) -> Dict[str, Any]:
35     """Carrega YAML com cache por mtime. Retorna {} em falha."""
36     if _DISABLE:
37         try:
38             return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
```
- Ontologia carregada pelo `Planner`, com `ONTO_PATH` default `data/ontology/entity.yaml`. (app/core/context.py + app/planner/planner.py)
```
13 ONTO_PATH = os.getenv("ONTOLOGY_PATH", "data/ontology/entity.yaml")
22 planner = Planner(ONTO_PATH)
```
```
477 class Planner:
478     def __init__(self, ontology_path: str):
479         self.ontology_path = ontology_path
480         self.onto = load_ontology(ontology_path)
```
- Bucket rules do Planner (YAML): `data/ontology/bucket_rules.yaml`. (app/planner/planner.py)
```
24 @lru_cache(maxsize=1)
25 def _load_bucket_rules(path: str = "data/ontology/bucket_rules.yaml") -> Dict[str, Any]:
33     try:
34         return load_yaml_cached(path) or {}
```
- RAG policy (YAML): `data/policies/rag.yaml`. (app/rag/context_builder.py)
```
15 _RAG_POLICY_PATH = os.getenv("RAG_POLICY_PATH", "data/policies/rag.yaml")
19 def load_rag_policy() -> Dict[str, Any]:
33     try:
34         data = load_yaml_cached(str(policy_path)) or {}
```
- Narrator policy (YAML): `data/policies/narrator.yaml`. (app/narrator/narrator.py)
```
553 def _load_narrator_policy(path: str = str(_NARRATOR_POLICY_PATH)) -> Dict[str, Any]:
560     policy_path = Path(path)
565     try:
566         data = load_yaml_cached(str(policy_path))
```
- Legacy templates em `data/concepts/<entity>_templates.md`. (app/templates_answer/__init__.py)
```
18     candidates = [
19         _ENTITY_TEMPLATE_ROOT / entity / "template.md",
20         _ENTITY_TEMPLATE_ROOT / entity / "templates.md",
21         _LEGACY_TEMPLATE_ROOT / f"{entity}_templates.md",
```
- Templates Jinja em `data/entities/<entity>/responses/<kind>.md.j2`. (app/formatter/rows.py)
```
637 template_path = _ENTITY_ROOT / entity / "responses" / f"{kind}.md.j2"
666 template = _JINJA_ENV.from_string(
667     template_path_resolved.read_text(encoding="utf-8")
```

---

## 3) Entrega 2 — Trilha “Concepts” (source of truth)

### 2.1 Existe código que lê `data/concepts/catalog.yaml`?
**Não encontrado no runtime.**
- O único uso direto de `data/concepts` no runtime é o fallback de templates legados (`data/concepts/<entity>_templates.md`). (ver `app/templates_answer/__init__.py`).
- O catálogo e os conceitos aparecem listados em `data/embeddings/index.yaml` como **fontes para indexação** (RAG), mas não há loader no `/ask` que leia esses YAMLs diretamente. (ver `data/embeddings/index.yaml`).

### 2.2 Funções relacionadas e como os conceitos entram (via RAG)
**Funções relevantes (com assinatura + trecho):**
- `load_rag_policy() -> Dict[str, Any]` (carrega política de RAG). (app/rag/context_builder.py)
```
19 def load_rag_policy() -> Dict[str, Any]:
28     policy_path = Path(_RAG_POLICY_PATH)
33     try:
34         data = load_yaml_cached(str(policy_path)) or {}
```
- `build_context(...) -> Dict[str, Any]` (gera contexto RAG com chunks). (app/rag/context_builder.py)
```
199 def build_context(
200     question: str,
201     intent: str,
202     entity: str,
```
- `EmbeddingStore` lê o índice de embeddings (JSONL) e retorna listas de dicts. (app/rag/index_reader.py)
```
31 class EmbeddingStore:
62     rows: List[Dict[str, Any]] = []
63     with self.path.open("r", encoding="utf-8") as f:
64         for line in f:
65             rows.append(json.loads(line))
```

### 2.3 Representação em runtime
- **Conteúdo de conceitos**: não há carregamento direto de YAML de `data/concepts/*.yaml` no runtime; quando usado no `/ask`, entra indiretamente via **chunks RAG** (listas de dicts vindas do índice JSONL). (ver `app/rag/index_reader.py`).

### 2.4 Call chain até `/ask` (com evidência)
1. `/ask` chama `planner.explain()` para roteamento. (app/api/ask.py)
```
153 t_plan0 = time.perf_counter()
154 plan = planner.explain(payload.question)
```
2. `/ask` chama `present(...)`, que monta baseline + chama Narrator/RAG. (app/api/ask.py)
```
584 presenter_result = present(
585     question=payload.question,
586     plan=plan,
```
3. `present(...)` monta contexto RAG (`build_context`) e calcula baseline (templates) antes do Narrator. (app/presenter/presenter.py)
```
369 rag_policy = load_rag_policy()
370 narrator_rag_context = build_context(
371     question=question,
372     intent=intent,
```
```
429 technical_answer = render_answer(
437 rendered_template = render_rows_template(
```

---

## 4) Entrega 3 — Trilha “Institutional Contracts”

### 3.1 Existe módulo que lê `data/contracts/responses/*.yaml`?
**Não encontrado no runtime.**
- Os arquivos de contrato existem e descrevem o contrato 1–2–3 (`institutional_response_contract.yaml`) e o map de intents (`institutional_intent_map.yaml`). (ver `data/contracts/responses/*`).
- Não há referência no pipeline do `/ask` ao carregamento desses YAMLs; o fluxo de resposta está centralizado no `Presenter` + `Narrator`. (ver `app/presenter/presenter.py` e `app/api/ask.py`).

### 3.2 Evidências dos contratos (conteúdo)
- `institutional_response_contract.yaml`: define camadas 1–2–3 e aponta `concepts-institutional.yaml` como fonte. (data/contracts/responses/institutional_response_contract.yaml)
```
14 scope:
15   applies_when:
16     - "planner.domain == 'institutional'"
60 layer_3_concept:
63   source_of_truth:
64     concepts_file: "data/concepts/concepts-institutional.yaml"
```
- `institutional_intent_map.yaml`: referência ao contrato principal e mapeamento de intents. (data/contracts/responses/institutional_intent_map.yaml)
```
9 defaults:
10   response_contract: "data/contracts/responses/institutional_response_contract.yaml"
32 intent_map:
34   - intent_id: "institutional_what_is_sirios"
```

### 3.3 Momento de aplicação (antes/depois do SQL / Narrator)
**Não encontrado.**
- O fluxo atual de resposta passa pelo `Presenter` (baseline + templates + Narrator). (app/presenter/presenter.py)

---

## 5) Entrega 4 — Onde montar “camadas 1–2–3” hoje

**Ponto de acoplamento natural:** o **Presenter** é o local mais apropriado para aplicar o contrato 1–2–3, pois ele já centraliza a construção da resposta: monta baseline via templates (`render_answer` e `render_rows_template`) e aciona o Narrator quando habilitado, antes de retornar o `answer` final ao `/ask`. Isso o coloca exatamente entre o roteamento (Planner/Orchestrator) e a entrega final (Presenter/Narrator), sem exigir mudanças no SQL. (ver `app/presenter/presenter.py` e `app/api/ask.py`).

Evidências objetivas:
- Presenter decide baseline e chama Narrator. (app/presenter/presenter.py)
```
429 technical_answer = render_answer(
437 rendered_template = render_rows_template(
479 if narrator is not None and bool(effective_narrator_policy.get("llm_enabled")):
518     out = narrator.render(question, facts_wire, meta_for_narrator)
```
- `/ask` delega saída final ao Presenter. (app/api/ask.py)
```
581 # Camada de apresentação (Presenter)
584 presenter_result = present(
```
- Templates Jinja vivem em `data/entities/*/responses`. (app/formatter/rows.py)
```
637 template_path = _ENTITY_ROOT / entity / "responses" / f"{kind}.md.j2"
```

---

## 6) Entrega 5 — Checklist de confirmação (para o Leleo)

### Comandos de busca (rg)
- `rg "data/concepts/catalog.yaml" -n`
- `rg "contracts/responses" -n`
- `rg "concepts-" -n`
- `rg "institutional_" -n`
- `rg "narrator.yaml" -n app data`
- `rg "rag.yaml" -n app data`

### Comando para `/ask` em modo debug (explain)
> O endpoint aceita `explain` como query param. (ver `app/api/ask.py`)

Exemplo (ajuste host/porta conforme o ambiente local):
```
curl -X POST "http://localhost:8000/ask?explain=true" \
  -H "Content-Type: application/json" \
  -d '{"question":"O que é a SIRIOS?","conversation_id":"debug","nickname":"dev","client_id":"dev"}'
```

Sugestão de verificação: inspecionar `meta.narrator` e `meta.explain` na resposta para validar se o fluxo executou o Presenter/Narrator.

---

## 7) Gaps encontrados

1. **Não há loader runtime** para `data/concepts/catalog.yaml` e `data/concepts/concepts-*.yaml`; apenas o fallback de templates legados em `data/concepts/<entity>_templates.md`. (ver `app/templates_answer/__init__.py`).
2. **Contratos institucionais não são aplicados** no fluxo atual do `/ask` — os YAMLs existem, mas o pipeline utiliza somente `Presenter` + `Narrator`. (ver `data/contracts/responses/*` e `app/presenter/presenter.py`).
3. A presença de `data/concepts/*.yaml` no índice de embeddings indica uso **pré-runtime** (indexação), mas não há leitura direta desses YAMLs no `/ask`. (ver `data/embeddings/index.yaml`).

---

## 8) Próximo passo recomendado (sem implementar)

**Definir o contrato institucional como decisão explícita no `Presenter`** (por exemplo, criar um carregador dedicado de `data/contracts/responses/institutional_response_contract.yaml` + `institutional_intent_map.yaml` e aplicar as camadas 1–2–3 antes do `Narrator`), já que o `Presenter` é o ponto central da montagem da resposta final. (ver `app/presenter/presenter.py`).

