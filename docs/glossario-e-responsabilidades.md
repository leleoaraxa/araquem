# Glossário e responsabilidades

> **Como validar**
> - Recorra aos contratos YAML e ontologia (`data/entities`, `data/ontology`) para confirmar termos de negócio e suas descrições.【F:data/entities/fiis_precos/entity.yaml†L1-L115】【F:data/entities/fiis_dividendos/entity.yaml†L1-L94】【F:data/ontology/entity.yaml†L1-L120】
> - Revise os módulos responsáveis por cada camada (planner, orchestrator, cache, narrador) para assegurar a atribuição correta de responsabilidades técnicas.【F:app/planner/planner.py†L90-L345】【F:app/orchestrator/routing.py†L208-L459】【F:app/cache/rt_cache.py†L15-L216】【F:app/narrator/narrator.py†L71-L120】

## Glossário de domínio

| Termo | Descrição | Fonte |
| --- | --- | --- |
| **FII (Fundo de Investimento Imobiliário)** | Ativo alvo das consultas; identificado por ticker `AAAA11` e descrito em entidades como `fiis_cadastro`, `fiis_precos`, `fiis_dividendos`. | 【F:data/entities/fiis_precos/entity.yaml†L1-L83】【F:data/entities/fiis_dividendos/entity.yaml†L1-L70】 |
| **Dividendos / Proventos** | Distribuições periódicas pagas pelos FIIs; campos `dividend_amt`, `payment_date` e intents específicas no planner. | 【F:data/entities/fiis_dividendos/entity.yaml†L13-L94】【F:data/ontology/entity.yaml†L69-L112】 |
| **Metricas FII** | Indicadores financeiros agregados (DY, cap rate, leverage) provenientes de `fiis_financials_snapshot` e `fiis_metrics`. | 【F:data/entities/fiis_financials_snapshot/entity.yaml†L15-L160】【F:data/entities/fiis_metrics/entity.yaml†L1-L120】 |
| **Planner** | Componente que mapeia pergunta NL para intent/entity usando ontologia, thresholds e hints RAG. | 【F:app/planner/planner.py†L90-L345】 |
| **Orchestrator** | Faixa de execução que aplica gates, infere parâmetros, aciona SQL builder e formata resposta/caches. | 【F:app/orchestrator/routing.py†L208-L459】 |
| **Read-through cache** | Estratégia de cache declarada por entidade que tenta Redis antes de executar SQL, preenchendo TTL conforme políticas YAML. | 【F:app/cache/rt_cache.py†L155-L216】【F:data/policies/cache.yaml†L8-L71】 |
| **Narrator** | Camada opcional que gera resposta textual natural a partir de fatos retornados, utilizando LLM via Ollama. | 【F:app/api/ask.py†L179-L254】【F:app/narrator/narrator.py†L71-L120】 |
| **Explain Analytics** | Payload estruturado que resume decisão do planner e métricas de execução, anexado ao response e opcionalmente persistido. | 【F:app/analytics/explain.py†L1-L160】【F:app/api/ask.py†L255-L299】 |
| **Quality Gate** | Processo automatizado que avalia acurácia do planner e métricas de RAG usando rotas `/ops/quality/push`. | 【F:app/api/ops/quality.py†L29-L200】【F:scripts/quality/quality_push_cron.py†L21-L226】 |

## Responsabilidades técnicas

| Área / Componente | Responsável primário | Escopo | Evidência |
| --- | --- | --- | --- |
| API HTTP (`app/api`) | Squad Core / Integradores | Rotas públicas `/ask`, saúde e endpoints operacionais; aplica middlewares e métricas. | 【F:app/api/__init__.py†L24-L43】【F:app/api/ask.py†L56-L330】 |
| Planejamento (`app/planner`) | Squad Inteligência/Ontologia | Manutenção da ontologia, thresholds e integração RAG; garante roteamento correto. | 【F:app/planner/planner.py†L90-L345】【F:data/ontology/entity.yaml†L1-L120】 |
| Execução SQL (`app/builder`, `app/executor`) | Squad Dados/SQL | Tradução de YAML em SQL seguro e execução em Postgres com métricas e tracing. | 【F:app/builder/sql_builder.py†L18-L160】【F:app/executor/pg.py†L16-L69】 |
| Cache & Políticas (`app/cache`, `data/policies`) | Squad Plataforma | Definir TTL, escopo e lógica de read-through; expor bust seguro via `/ops/cache`. | 【F:app/cache/rt_cache.py†L15-L216】【F:data/policies/cache.yaml†L8-L71】【F:app/api/ops/cache.py†L19-L39】 |
| Narrativa (`app/narrator`) | Squad Experiência | Prompting, fallback e controle de Shadow Mode para respostas naturais. | 【F:app/narrator/narrator.py†L71-L120】【F:app/api/ask.py†L200-L254】 |
| Observabilidade (`app/observability`, scripts) | Squad Observabilidade | Configuração de métricas, tracing, dashboards e coletores Prometheus/Grafana/Tempo. | 【F:app/observability/runtime.py†L17-L96】【F:data/ops/observability.yaml†L1-L120】【F:Makefile†L58-L90】 |
| Qualidade & Crons (`scripts/quality`, `docker-compose` crons) | Squad Ops/Qualidade | Executar quality gate, refresh RAG, integrar com tokens e métricas de monitoramento. | 【F:docker-compose.yml†L149-L185】【F:scripts/quality/quality_push_cron.py†L21-L226】 |

## Lacunas

- LACUNA: Não há documentação de responsáveis por dados sensíveis (ex.: manutenção das views SQL ou compliance de `client_fiis_positions`); coordenar com equipe de dados/governança.
- LACUNA: Ausência de mapa de owners para dashboards Grafana/alertas Prometheus; identificar time mantenedor para incidentes.


<!-- ✅ confirmado: termos de domínio FIIs (ticker, dividendos, cotistas, IFIX, gestão, subsetor, etc.) extraídos corretamente de data/concepts/fiis.md. -->

<!-- ✅ confirmado: mapeamento de responsabilidades por módulo segue estrutura app/, ex.:
     planner (interpretação e roteamento), builder (SQL declarativo), executor (execução),
     formatter (saída tabular), narrator (voz da SIRIOS), observability (métricas e tracing). -->

<!-- ✅ confirmado: terminologia alinhada à ontologia; nomes PT-BR e intents idênticos. -->

<!-- 🕳️ LACUNA: incluir “analytics” como módulo analítico emergente (explain.py, metrics.py, repository.py). -->

<!-- 🕳️ LACUNA: registrar ownership futura de MLOps/RAG (responsável pela manutenção dos embeddings e índices). -->
