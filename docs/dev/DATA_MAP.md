# Mapa de dependências `data/`

## Visão geral
- **Propósito**: centralizar artefatos estáticos que parametrizam o planner/orquestrador (/ask), pipelines de qualidade e o índice de RAG.
- **Subpastas**:
  - `concepts/`: materiais de referência que alimentam o índice de embeddings (conceitos de FIIs).
  - `embeddings/`: configuração do índice (`index.yaml`) e artefatos gerados (`store/`).
  - `entities/`: contratos YAML por entidade (colunas, agregações, cache) usados para construir SQL e inferir parâmetros.
  - `golden/`: casos de roteamento/qualidade (YAML/JSON) e arquivos `.hash` de integridade.
  - `ontology/`: definição da ontologia de intents→entities e hash de integridade.
  - `ops/`: parâmetros operacionais (observabilidade, thresholds, inferência) e amostras de qualidade para scripts/rotas de QA.

---
## data/concepts/catalog.yaml
**Objetivo**: Catálogo estruturado de conceitos FIIs (domínio textual) para enriquecer o índice de embeddings.
**Consumidores**:
  - `scripts/embeddings_build.py::build_index` — (rota? não) — estágio: script
    snippet:
    ```py
    for item in include:
        doc_id = str(item.get("id") or "")
        p = Path(item.get("path") or "")
        ...
        text = _read_text(p)
        if not text.strip():
            print(f"[skip] {doc_id} → empty")
            continue
    ```
**Esquema resumido**: YAML com metadados (`name`, descrições) — serializado como texto no índice.
**Env/Flags relacionadas**: `EMBED_BATCH_SIZE` (processamento em lotes na geração do índice).
**Riscos e overlap**: duplicidade com `data/concepts/fiis.md` se o conteúdo divergir; ambos alimentam o mesmo índice.
**Observações**: Não há leitura direta pelo backend; depende do pipeline de embeddings.

## data/concepts/fiis.md
**Objetivo**: Texto descritivo (Markdown) sobre FIIs, usado como corpus no RAG.
**Consumidores**:
  - `scripts/embeddings_build.py::build_index` — (rota? não) — estágio: script
    snippet:
    ```py
    def _read_text(path: Path) -> str:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            return text
        except Exception:
            ...
    ```
**Esquema resumido**: Markdown livre.
**Env/Flags relacionadas**: `EMBED_BATCH_SIZE` (pipeline de geração).
**Riscos e overlap**: Conteúdo textual pode ficar desatualizado em relação aos YAMLs de entidade.
**Observações**: Apenas fonte de conhecimento para o índice vetorial; não chega ao tempo de execução do planner.

## data/embeddings/index.yaml
**Objetivo**: Configuração declarativa do índice de embeddings (documentos incluídos, chunking, pesos RAG).
**Consumidores**:
  - `scripts/embeddings_build.py::build_index` — (rota? não) — estágio: script
    snippet:
    ```py
    idx = yaml.safe_load(Path(index_path).read_text(encoding="utf-8"))
    ...
    include = idx.get("include", []) or []
    with out_jsonl.open("w", encoding="utf-8") as fw:
        for item in include:
            doc_id = str(item.get("id") or "")
            p = Path(item.get("path") or "")
    ```
**Esquema resumido**: chaves `version`, `collection`, `chunk`, `hint_filters`, `include[id,path,tags]`, parâmetros de peso (`weight`, `min_score`).
**Env/Flags relacionadas**: `EMBED_BATCH_SIZE`; docker compose usa `--index data/embeddings/index.yaml`.
**Riscos e overlap**: Divergência entre `include` e arquivos reais (scripts falham silenciosamente se o path não existir).
**Observações**: Governa quais arquivos entram no `embeddings.jsonl` e, indiretamente, o conteúdo disponível para o RAG.

## data/embeddings/store/embeddings.jsonl
**Objetivo**: Base vetorial (documentos chunkados + embeddings) consumida pelo planner quando o RAG está habilitado.
**Consumidores**:
  - `app/planner/planner.py::Planner.explain` — (rota /ask; /ops/quality/push) — estágio: request
    snippet:
    ```py
    rag_index_path = os.getenv(
        "RAG_INDEX_PATH", "data/embeddings/store/embeddings.jsonl"
    )
    if rag_enabled:
        store = EmbeddingStore(rag_index_path)
        ...
        rag_results = store.search_by_vector(qvec, k=rag_k) or []
    ```
**Esquema resumido**: JSONL por linha com campos `collection`, `doc_id`, `chunk_id`, `text`, `embedding` (lista float), `tags`.
**Env/Flags relacionadas**: `RAG_INDEX_PATH`, `OLLAMA_BASE_URL`, `OLLAMA_EMBED_MODEL`, `PLANNER_THRESHOLDS_PATH` (habilita RAG).
**Riscos e overlap**: Arquivo grande é recarregado em cada request quando RAG ativo (não há cache in-memory) → latência/custo.
**Observações**: Gerado por `scripts/embeddings_build.py`; sem ele, o RAG falha ao iniciar (FileNotFoundError).

## data/embeddings/store/manifest.json
**Objetivo**: Manifesto do índice vetorial (metadados de geração, checksums).
**Consumidores**: sem consumidores encontrados (`rg -n "manifest.json" app scripts tests` só aponta para escrita na build). 
**Esquema resumido**: JSON com `version`, `collection`, `embedding_model`, `docs[id,path,chunks,sha_all]`.
**Env/Flags relacionadas**: n/d.
**Riscos e overlap**: Sem uso operacional; risco de drift caso se confie nele manualmente.
**Observações**: Gerado pelo pipeline; pode ser útil para auditoria manual.

## data/entities/cache_policies.yaml
**Objetivo**: TTL/escopo do cache por entidade para o read-through Redis.
**Consumidores**:
  - `app/cache/rt_cache.py::CachePolicies.__init__` — (rota /ask) — estágio: bootstrap
    snippet:
    ```py
    POLICY_PATH = Path("data/entities/cache_policies.yaml")
    class CachePolicies:
        def __init__(self, path: Path = POLICY_PATH):
            with open(path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
            self._policies = raw.get("policies") or {}
    ```
  - `app/core/context.py` (instancia `CachePolicies()` no carregamento da app) — estágio: bootstrap
**Esquema resumido**: `policies.<entity>.{ttl_seconds,refresh_at,scope}`.
**Env/Flags relacionadas**: `REDIS_URL` (para o cache); `BUILD_ID` usado na chave mas não no YAML.
**Riscos e overlap**: Não há versionamento → mudanças aplicam-se instantaneamente após reload; não valida entidades inexistentes.
**Observações**: `read_through` só respeita TTL quando a entidade está declarada aqui; entidades novas exigem atualização do YAML.

## data/entities/fiis_cadastro.yaml
**Objetivo**: Contrato da entidade `fiis_cadastro` (colunas, identificadores, apresentação).
**Consumidores**:
  - `app/builder/sql_builder.py::build_select_for_entity` — (rotas /ask; /ops/quality/push tipo projection) — estágio: request
    snippet:
    ```py
    ENTITIES_DIR = Path("data/entities")
    def _load_entity_yaml(entity: str) -> dict:
        ypath = ENTITIES_DIR / f"{entity}.yaml"
        with open(ypass := ypath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    ```
  - `app/planner/param_inference.py::_entity_agg_defaults` — (rotas /ask; /ops/quality/push) — estágio: request
    snippet:
    ```py
    y = _load_yaml(Path(entity_yaml_path)) if entity_yaml_path else {}
    agg = (y.get("aggregations") or {}) if isinstance(y, dict) else {}
    defaults = (agg.get("defaults") or {}) if isinstance(agg, dict) else {}
    ```
  - `scripts/embeddings_build.py::build_index` (inclui no corpus RAG) — estágio: script
**Esquema resumido**: `identifiers`, `presentation.result_key/return_columns`, `columns`, `ask`, `order_by_whitelist`.
**Env/Flags relacionadas**: `PLANNER_THRESHOLDS_PATH` (gates que usam `entity`), `RAG_INDEX_PATH` (para hints via embeddings).
**Riscos e overlap**: Duplicidade de defaults com `data/ops/param_inference.yaml`; ausência de `aggregations` impede compute-on-read.
**Observações**: Atualizações impactam SQL gerado, telemetria e RAG; versionar cuidadosamente.

## data/entities/fiis_dividendos.yaml
**Objetivo**: Contrato para histórico de dividendos com suporte a agregações.
**Consumidores**: iguais a `fiis_cadastro` (builder, infer_params, embeddings).
    snippet:
    ```py
    agg_cfg = cfg.get("aggregations") or {}
    agg_enabled = bool(agg_cfg.get("enabled", False))
    default_date_field = cfg.get("default_date_field") or None
    ```
**Esquema resumido**: `aggregations.enabled/defaults/windows_allowed`, `order_by_whitelist`, `presentation` (4 colunas principais).
**Env/Flags relacionadas**: idem entidades (RAG/thresholds).
**Riscos e overlap**: Windows permitidos replicam as mesmas listas do YAML de inferência — risco de divergência.
**Observações**: `infer_params` lê este arquivo em toda requisição para validar janela/limit.

## data/entities/fiis_precos.yaml
**Objetivo**: Contrato da série histórica de preços.
**Consumidores**: builder/infer_params/embeddings (mesmos callsites acima).
**Esquema resumido**: colunas de OHLCV, `aggregations` habilitando list/avg/sum.
**Env/Flags relacionadas**: idem.
**Riscos e overlap**: `default_date_field` é essencial para janelas `months`; falta dele quebra compute-on-read.
**Observações**: `order_by_whitelist` controla SQL ORDER; cuidado ao alterar.

## data/entities/fiis_rankings.yaml
**Objetivo**: Contrato de métricas de ranking por FII.
**Consumidores**: builder/infer_params/embeddings.
**Esquema resumido**: métricas de aparições/movimentos IFIX/IFIL/Sírios.
**Env/Flags relacionadas**: idem.
**Riscos e overlap**: Sem `aggregations` → compute-on-read retorna lista simples; verificar se faz sentido expandir.
**Observações**: A falta de `aggregations` implica que `infer_params` sempre retorna defaults (list simples).

## data/golden/.hash
**Objetivo**: Snapshot hash dos artefatos em `data/golden/` para detectar drift.
**Consumidores**:
  - `scripts/hash_guard.py::main` — (rota? não) — estágio: script
    snippet:
    ```py
    TARGETS = [
        ("data/ontology", "data/ontology/.hash"),
        ("data/golden", "data/golden/.hash"),
    ]
    ...
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    ```
**Esquema resumido**: JSON com `files` (sha256 por arquivo) e `tree` agregado.
**Env/Flags relacionadas**: n/d.
**Riscos e overlap**: Atualizado manualmente; se não for rodado, hashes ficam obsoletos.
**Observações**: Útil para CI/guardrails; não há validação automática no backend.

## data/golden/m65_quality.json
**Objetivo**: Casos "golden" (JSON) de roteamento intent→entity usados como referência manual/RAG.
**Consumidores**: sem consumidores diretos (além do índice de embeddings via `data/embeddings/index.yaml`).
**Esquema resumido**: `samples[{question,expected_intent,expected_entity}]`.
**Env/Flags relacionadas**: n/d.
**Riscos e overlap**: Duplicado com `m65_quality.yaml` e `data/ops/quality/routing_samples.json`; manter sincronizado é custoso.
**Observações**: Considerar consolidar fonte única ou gerar automaticamente.

## data/golden/m65_quality.yaml
**Objetivo**: Mesma lista de casos "golden" em YAML (provavelmente fonte primária humana).
**Consumidores**: idem JSON (sem leitura direta pelo código).
**Esquema resumido**: `samples` com campos equivalentes.
**Env/Flags relacionadas**: n/d.
**Riscos e overlap**: Divergência entre YAML e JSON; múltiplas cópias dos mesmos prompts.
**Observações**: Pipeline de embeddings inclui ambos → conteúdo duplicado no índice.

## data/ontology/.hash
**Objetivo**: Hashes para detectar drift na ontologia.
**Consumidores**: `scripts/hash_guard.py` (mesmo snippet acima).
**Esquema resumido**: JSON com sha por arquivo e hash agregado.
**Env/Flags relacionadas**: n/d.
**Riscos e overlap**: Precisa ser regenerado manualmente ao alterar a ontologia.
**Observações**: Pode ser usado em CI para bloquear deploy com ontologia alterada sem aprovação.

## data/ontology/entity.yaml
**Objetivo**: Ontologia de intents, tokens e entidades — coração do planner.
**Consumidores**:
  - `app/planner/ontology_loader.py::load_ontology` — (rotas /ask; /ops/quality/push; scripts de QA) — estágio: bootstrap (carregado na inicialização do Planner)
    snippet:
    ```py
    def load_ontology(path: str) -> Ontology:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        intents: List[IntentDef] = []
        for it in raw.get("intents", []):
            intents.append(IntentDef(...))
    ```
  - `app/core/context.py` (passa `ONTOLOGY_PATH` ao `Planner`) — estágio: bootstrap
  - `scripts/try_m3.py` (carrega Planner manualmente) — estágio: script
  - `scripts/embeddings_build.py` (inclui o YAML no índice) — estágio: script
**Esquema resumido**: `normalize`, `tokenization`, `weights`, `intents[{tokens,phrases,entities}]`, `anti_tokens`.
**Env/Flags relacionadas**: `ONTOLOGY_PATH` (sobrepõe caminho), `PLANNER_THRESHOLDS_PATH` (gates por intent/entity).
**Riscos e overlap**: Mudanças alteram roteamento sem migrações; exige alinhamento com entidades YAML e dados reais.
**Observações**: Não há cache on-disk; Planner mantém estrutura em memória após bootstrap.

## data/ops/quality/m66_projection.json
**Objetivo**: Regras de verificação do contrato de explain (`m66`) para operações de qualidade.
**Consumidores**: sem consumidores ativos (somente listado em `data/embeddings/index.yaml`).
**Esquema resumido**: `type`, `checks[field,required]`, `sources`, `notes`.
**Env/Flags relacionadas**: n/d.
**Riscos e overlap**: Pode divergir do comportamento real do `/ask?explain`; armazenado mas não executado.
**Observações**: Avaliar integração com pipelines de QA.

## data/ops/quality/param_inference_samples.json
**Objetivo**: Amostras canônicas para testar `infer_params` (agg/window/list/avg/sum).
**Consumidores**:
  - `tests/test_param_inference.py::test_inference_samples` — estágio: test
    snippet:
    ```py
    with open(
        "data/ops/quality/param_inference_samples.json", "r", encoding="utf-8"
    ) as f:
        samples = json.load(f)["samples"]
    for s in samples:
        got = infer_params(q, exp["intent"])
    ```
**Esquema resumido**: `samples[{question, expected.intent/entity/aggregates}]`.
**Env/Flags relacionadas**: n/d.
**Riscos e overlap**: Cron de qualidade (`scripts/quality_push_cron.py`) também envia todos os `*.json`; este arquivo não segue o contrato esperado pelo endpoint `/ops/quality/push` (não possui `type`).
**Observações**: Útil como regressão local; não em produção.

## data/ops/quality/planner_rag_integration.json
**Objetivo**: Cenários esperados de integração Planner+RAG.
**Consumidores**: sem consumidores ativos (apenas incluído no índice de embeddings).
**Esquema resumido**: `type`, `runner`, `defaults.expect`, `samples[{question,expect.entity_prefix}]`.
**Env/Flags relacionadas**: n/d.
**Riscos e overlap**: Não utilizado — risco de ficar obsoleto em relação às configurações de RAG.
**Observações**: Poderia ser reutilizado por scripts de QA de RAG.

## data/ops/quality/projection_fiis_cadastro.json
**Objetivo**: Amostras para validar projeções (`must_have_columns`) da entidade cadastro.
**Consumidores**:
  - `scripts/quality_push_cron.py::main` — (rota /ops/quality/push) — estágio: script (envia payload para a API)
    snippet:
    ```py
    GLOB = os.environ.get("QUALITY_SAMPLES_GLOB", "data/ops/quality/*.json")
    files = sorted(base.glob(GLOB))
    for p in files:
        with open(p, "rb") as f:
            data = json.load(f)
        r = httpx.post(f"{API_URL}/ops/quality/push", ...)
    ```
**Esquema resumido**: JSON `type: "projection"`, campos `entity`, `result_key`, `must_have_columns`, lista de `samples`.
**Env/Flags relacionadas**: `QUALITY_SAMPLES_GLOB`, `API_URL`, `QUALITY_OPS_TOKEN`, `QUALITY_AUTH_BEARER`.
**Riscos e overlap**: Conteúdo muito semelhante aos casos golden; manter ambos sincronizados é oneroso.
**Observações**: Endpoint `/ops/quality/push` valida as colunas utilizando estes dados.

## data/ops/quality/projection_fiis_dividendos.json
**Objetivo**: Casos de QA para projeções de dividendos.
**Consumidores**: `scripts/quality_push_cron.py` (igual acima).
**Esquema resumido**: `type: projection`, `entity: fiis_dividendos`, `must_have_columns` (ticker/payment/dividend/traded_until).
**Env/Flags relacionadas**: idem.
**Riscos e overlap**: Campos replicam `presentation.return_columns`; atualizar YAML da entidade exige refletir aqui.
**Observações**: Útil para detectar regressões no builder ao alterar `return_columns`.

## data/ops/quality/projection_fiis_precos.json
**Objetivo**: Amostras para QA da entidade preços.
**Consumidores**: `scripts/quality_push_cron.py` (igual acima).
**Esquema resumido**: `must_have_columns` com colunas OHLCV.
**Env/Flags relacionadas**: idem.
**Riscos e overlap**: Muitos prompts repetem datas fixas; pode quebrar com dados históricos limitados.
**Observações**: Ajustar datas conforme disponibilidade no banco.

## data/ops/quality/projection_fiis_rankings.json
**Objetivo**: QA de projeções para rankings.
**Consumidores**: `scripts/quality_push_cron.py` (igual acima).
**Esquema resumido**: `must_have_columns` cobrindo métricas IFIX/IFIL/Sírios.
**Env/Flags relacionadas**: idem.
**Riscos e overlap**: Campos repetem `return_columns`; atualização exige tocar nos dois arquivos.
**Observações**: Usado para garantir colunas presentes nos resultados do `/ask`.

## data/ops/quality/rag_search_basics.json
**Objetivo**: Amostras de busca RAG básica (expectativa de `doc_id_prefix`).
**Consumidores**: `scripts/quality_push_cron.py` (envia payload), embora o endpoint `/ops/quality/push` ainda não implemente `type: "rag_search"` → hoje não há processamento.
**Esquema resumido**: `defaults.request/expect`, `samples[{name,request.question,expect.doc_id_prefix}]`.
**Env/Flags relacionadas**: idem cron.
**Riscos e overlap**: Endpoint ignora este tipo → QA não é executado.
**Observações**: Considerar implementação dedicada no backend.

## data/ops/quality/routing_samples.json
**Objetivo**: Dataset de perguntas ↔ intent/entity para QA contínuo do planner.
**Consumidores**:
  - `scripts/quality_push_cron.py` — estágio: script (push para `/ops/quality/push`)
  - `scripts/embeddings_build.py` (inclui no índice RAG) — estágio: script
**Esquema resumido**: `type: "routing"`, `samples[{question, expected_intent, expected_entity}]`.
**Env/Flags relacionadas**: `QUALITY_SAMPLES_GLOB`.
**Riscos e overlap**: Repetição dos mesmos exemplos nos arquivos golden; divergências podem gerar métricas inconsistentes.
**Observações**: Endpoint `/ops/quality/push` gera métricas de acurácia/top2 gap a partir deste arquivo.

## data/ops/observability.yaml
**Objetivo**: Configuração de métricas/tracing para bootstrap de observabilidade.
**Consumidores**:
  - `app/observability/runtime.py::load_config` — (rota? não) — estágio: bootstrap
    snippet:
    ```py
    cfg_path = os.environ.get("OBSERVABILITY_CONFIG", "data/ops/observability.yaml")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
    ```
  - `app/core/context.py` (chama `load_config()` ao inicializar) — estágio: bootstrap
**Esquema resumido**: `services.<component>.metrics/tracing`, `global.exporters`.
**Env/Flags relacionadas**: `OBSERVABILITY_CONFIG`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `PROMETHEUS_URL`.
**Riscos e overlap**: Valores duplicam nomes de métricas definidos em código (`app/observability/metrics.py`); manter sincronizado.
**Observações**: Alterações impactam instantaneamente o bootstrap (sem cache).

## data/ops/param_inference.yaml
**Objetivo**: Regras declarativas para inferir agregações/janelas a partir de texto.
**Consumidores**:
  - `app/planner/param_inference.py::infer_params` — (rotas /ask; /ops/quality/push) — estágio: request
    snippet:
    ```py
    cfg_path = Path(defaults_yaml_path) if defaults_yaml_path else _DEFAULTS_PATH
    cfg = _load_yaml(cfg_path) or {}
    intents = (cfg or {}).get("intents", {})
    icfg = intents.get(intent, {})
    ```
  - `app/api/ask.py` e `app/orchestrator/routing.py` passam caminho explícito ao chamar `infer_params` — estágio: request
  - `tests/test_param_inference.py` (regressão) — estágio: test
**Esquema resumido**: `intents.<nome>.{default_agg, default_window, windows_allowed, agg_keywords, window_keywords}`.
**Env/Flags relacionadas**: `PLANNER_THRESHOLDS_PATH` (gates que podem bloquear agregações de baixa confiança).
**Riscos e overlap**: Config duplicada com `aggregations.defaults` nos YAMLs de entidade; divergências causam inconsistência.
**Observações**: Lido do disco a cada requisição; avaliar cache em memória.

## data/ops/planner_thresholds.yaml
**Objetivo**: Thresholds do planner (score/gap), config do RAG e quality gates globais.
**Consumidores**:
  - `app/orchestrator/routing.py::_load_thresholds` — (rota /ask) — estágio: request
    snippet:
    ```py
    _TH_PATH = os.getenv("PLANNER_THRESHOLDS_PATH", "data/ops/planner_thresholds.yaml")
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return (raw.get("planner") or {}).get("thresholds") or {}
    ```
  - `app/planner/planner.py::_load_thresholds` — (rotas /ask; /ops/quality/push) — estágio: request (determina RAG/k/min_score/peso)
  - `app/api/ops/quality.py::quality_report` — (rota /ops/quality/report) — estágio: request
  - `scripts/gen_quality_dashboard.py::main` — estágio: script
**Esquema resumido**: `quality_gates.thresholds`, `planner.thresholds` (defaults/intents/entities), `planner.rag` (enabled/k/min_score/weight).
**Env/Flags relacionadas**: `PLANNER_THRESHOLDS_PATH`, `RAG_INDEX_PATH`, `OLLAMA_*` (via habilitação de RAG).
**Riscos e overlap**: Lido múltiplas vezes por request → custo IO; divergência entre thresholds aqui e valores hard-coded de fallback.
**Observações**: Desabilitar RAG (`rag.enabled: false`) evita leitura do índice vetorial.

---
## Mapa temporal de uso
| Estágio | Arquivos principais |
| --- | --- |
| **Bootstrap** | `data/entities/cache_policies.yaml`, `data/ontology/entity.yaml`, `data/ops/observability.yaml` |
| **Request (/ask)** | Entidades `fiis_*.yaml`, `data/ops/param_inference.yaml`, `data/ops/planner_thresholds.yaml`, `data/embeddings/store/embeddings.jsonl` (quando RAG ativo) |
| **Request (/ops/quality/***)** | Mesmos de `/ask` para `planner.explain`/builder + thresholds; `/ops/quality/report` lê `planner_thresholds.yaml` |
| **Scripts** | `concepts/*`, `embeddings/index.yaml`, `ops/quality/*.json`, `golden/.hash`, `ontology/.hash`, `gen_quality_dashboard.py` |
| **Testes** | `data/ops/quality/param_inference_samples.json` |

## Overlap & Conflitos
- **Param inference × entidades**: `data/ops/param_inference.yaml` repete defaults/listas já presentes em `aggregations.defaults` das entidades (`fiis_dividendos`, `fiis_precos`). Divergência quebra compute-on-read.
- **Quality datasets duplicados**: `data/golden/m65_quality.{yaml,json}` e `data/ops/quality/routing_samples.json` contêm o mesmo conjunto de perguntas; risco de desalinhamento.
- **QA scripts × endpoint**: `data/ops/quality/param_inference_samples.json` e `rag_search_basics.json` não atendem ao contrato esperado por `/ops/quality/push`, mas são enviados pelo cron (possível erro silencioso).
- **Embeddings duplicados**: Incluir YAML e JSON do golden gera conteúdo repetido no índice vetorial.

## Recomendações de documentação futura
- Documentar claramente qual arquivo é a fonte de verdade para as amostras "golden" (YAML vs JSON vs routing_samples) e automatizar a geração dos demais.
- Registrar o contrato esperado para cada `type` aceito por `/ops/quality/push` e ajustar o cron para filtrar arquivos incompatíveis.
- Considerar uma nota operacional sobre caching de `param_inference.yaml`/entidades para reduzir I/O por requisição.
- Adicionar instruções de atualização dos `.hash` ao guia de release para evitar drift.

## Como reproduzir
```
rg -n "data/(concepts|embeddings|entities|golden|ontology|ops)" app scripts tests
rg -n "cache_policies.yaml" -g'!data'
rg -n "embeddings.jsonl" -g'!*.jsonl'
rg -n "planner_thresholds.yaml" app scripts tests
rg -n "param_inference.yaml" app scripts tests
rg -n "OBSERVABILITY_CONFIG" -g'!venv'
rg -n "QUALITY_SAMPLES_GLOB" scripts
```
