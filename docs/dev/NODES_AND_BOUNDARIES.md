# Araquem — Domínios e Fronteiras

## Classificação por camada

### Core (regras centrais)
- `app/planner/planner.py`, `app/planner/ontology_loader.py`: determinam roteamento de intents → entidades.
- `app/builder/sql_builder.py`: transforma contrato declarativo em SQL real.
- `app/orchestrator/routing.py`: encadeia planner, builder, executor e formatter.
- `app/planner/param_inference.py`: infere agregações a partir de ontologia + YAML.

### Domínio (modelos, narrativas, apresentação)
- `app/formatter/rows.py`: aplica regras de apresentação baseadas em entidades.
- `app/responder/__init__.py`: templates legados para resposta textual.
- `app/narrator/*`: nova camada narrativa (LLM, prompts, fallback textual).

### API / Gateway de entrada
- `app/api/ask.py`, `app/api/__init__.py`: expõem FastAPI, gerenciam payloads e responses.
- `app/api/ops/*`: operações de monitoramento, cache bust, analytics.
- `app/api/debug.py`, `app/api/health.py`: health-check, métricas e debug.

### Infraestrutura / Dados
- `app/executor/pg.py`: acesso Postgres com métricas.
- `app/cache/rt_cache.py`: acesso Redis + políticas YAML.
- `app/utils/filecache.py`: cache de arquivos YAML/JSONL.
- `app/core/context.py`: bootstrap central de dependências.
- `data/entities/*`, `data/ops/*`: contratos declarativos.

### Observabilidade
- `app/observability/runtime.py`, `instrumentation.py`, `metrics.py`.
- `app/analytics/explain.py`: gera payloads de explainability, integrando com tracing.

### RAG / Inteligência
- `app/rag/index_reader.py`, `app/rag/hints.py`, `app/rag/ollama_client.py`: fornecem hints para o planner.

### Gateway de dados externo
- `app/analytics/repository.py`: consulta `explain_events` para dashboards operacionais.

## Limites bem definidos
- **Builder ↔ YAML de entidade:** SQL é derivado exclusivamente de contratos declarativos, evitando hardcode.
- **Executor ↔ Observabilidade:** `PgExecutor` usa façade de instrumentation para métricas/tracing, mantendo dependência única.
- **Narrator opcional:** `_NARR` inicializado com `try/except` garante fallback seguro, mantendo compatibilidade.

## Limites violados ou frágeis
1. **API ↔ Domínio:** `app/api/ask.py` contém lógica de formatação (`render_rows_template`) e narrativa (`facts` do Narrator). Ideal seria delegar a uma camada de apresentação dedicada.
2. **Core ↔ Infraestrutura:** `app/core/context` instancia implementações concretas (`RedisCache`, `PgExecutor`), dificultando substituições em testes/shadow mode.
3. **Planner ↔ Observabilidade:** `planner.py` importa diretamente `emit_counter/histogram` e `OllamaClient`, misturando domínio com efeitos colaterais e dependências externas.
4. **Cache ↔ Domínio:** `read_through` contém regras específicas de métricas (`legacy_cleanup_scan`) que deveriam estar em políticas declarativas ou serviço separado.

## Pontos que precisam encapsulamento antes de M10
- **Narrativa:** extrair pipeline Narrator/Responder para módulo independente que receba `facts` do orchestrator (não do endpoint) e produza `answer` + `meta`.
- **Configuração de políticas:** unificar leitura de YAML (`CachePolicies`, `Planner thresholds`, `Param inference`) em um registro central com versionamento/validação.
- **RAG client:** encapsular chamada Ollama/embedding em adaptador com contrato explícito e fallback claro (no momento depende de import opcional).
- **Explain analytics write path:** inserção em `explain_events` está duplicada (endpoint e orchestrator) e acoplada ao ambiente DB; criar gateway dedicado.

## Onde plugar o Narrator (visão preliminar)
- A melhor fronteira para inserir Narrator/Responder é após o formatter, recebendo `results` já normalizados do orchestrator. Esse ponto será detalhado em `NARRATOR_INTEGRATION_POINTS.md`.

## Notas de domínio específicas
- **Ontologia YAML** é o contrato central para roteamento; qualquer mudança deve acompanhar thresholds e entity.yaml.
- **Presentation templates** (`responses/*.md.j2` e `templates.md`) pertencem à camada Narrator/Responder, não ao endpoint.
- **Facts de métricas** dependem de `agg_params`; esses parâmetros devem ser tratados como parte do contrato Core → Domínio, evitando duplicações no endpoint.
