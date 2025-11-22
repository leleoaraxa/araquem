# 🟦 Araquem — Estado Atual e Rumo à Produção (Versão Sirius)

## 1. Visão Geral

Este documento consolida o estado atual do projeto **Araquem** e define o caminho claro para chegar à **versão de produção 2025.0-prod**, conforme o Guardrails Araquem v2.1.1.

---

## 2. Onde Estamos (ONCÔTÔ)

### 2.1 Entidades FIIs (13/14 concluídas)

* Contratos e entities revisados.
* Presentation, aggregations, tolerances, identifiers: padronizados.
* Faltante: `client_fiis_positions` (enriquecimento final em execução).

### 2.2 Ontologia

* Ontologia FIIs completa.
* Identifiers, keywords, synonyms, metrics_synonyms configurados.
* Roteamento principal consolidado.
* Falta: `planner.explain()` e `/ask?explain=true`.

### 2.3 RAG / Narrator

* RAG funcional com context builder revisado.
* Narrator com política nova instalada.
* Falta: Narrator V2 (shadow, estilo, max_rows, safeguards) + presenter.

### 2.4 Quality & Observabilidade

* Prometheus, Grafana, Tempo, OTEL Collector ativos.
* Routing samples 120/120 (green baseline).
* Falta: suíte nova de testes FIIs + thresholds V3 + top2_gap fix.

### 2.5 `/ask` Pipeline

* Orchestrator → Planner → Builder → Executor → Formatter → Narrator funcionando.
* Falta: Presenter e explain-mode.

### 2.6 SQL / Executor

* Views padronizadas e estáveis.
* Falta: Entidade de Métricas D-1 (compute-on-read) + SQL parametrizado.

---

## 3. Para Onde Vamos (PRONCOVÔ)

### 🔵 M6 – Ontologia Inteligente

* Implementar `planner.explain()`.
* Implementar `/ask?explain=true`.

### 🟧 M7 – RAG + Quality V3

* RAG hints por entidade.
* Thresholds v3.
* Nova suíte de amostras.
* Ajuste do top2_gap.

### 🟨 M8 – Entidade de Métricas (compute-on-read)

* Criar entidade única parametrizável (3, 6, 12, 24 meses / últimas N ocorrências).
* Builder com SQL parametrizado.
* Formatter com meta.aggregates.

### 🟫 M9 – LGPD & Segurança

* Sanitização dura de PII.
* Regras para rotas privadas.

### 🟦 M10 – Narrator V2

* Shadow mode.
* Regras de compressão e estilo.
* Guard contra hallucinations.

### 🟪 M11 – Presenter V1

* Templates: list, summary, table.
* Orquestração visual.

### 🟫 M12 – Documentação & Auditoria

* Documentação técnica final.
* Auditoria de contracts/entities.

### 🟩 M13 – Blue/Green & Deploy Prod

* Redis blue/green.
* CI/CD.
* Teste de carga.
* Versão 2025.0-prod.

---

## 4. Resumo Executivo

* 70% do Araquem está concluído.
* As entidades foram praticamente finalizadas.
* O pipeline `/ask` está estável.
* O restante é **acabamento de produto** e consolidação de qualidade.

---

## 5. Proposta de Próximas Entregas Imediatas

1. Finalizar enriquecimento `client_fiis_positions`.
2. Executar Etapa 5 (harmonização contracts/entities completos).
3. Implementar Explain Mode (M6.3/6.4).
4. Nova suíte de quality samples.
5. Iniciar M8 (Entidade de Métricas D-1).

---

## 6. Conclusão

O Araquem está maduro, sólido e a fundação técnica está pronta. Agora seguimos para acabamento, explicabilidade, apresentação e qualidade — rumo a uma versão de produção robusta e confiável.

**Sirius sempre pronto.**
