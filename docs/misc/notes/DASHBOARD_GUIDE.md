# 📊 Manual Operacional — Dashboards de Observabilidade Araquem (v2.1.1)

**Projeto:** Plataforma de Inteligência Imobiliária SIRIOS — *Araquem*
**Versão:** M7.6 (Consolidação Grafana)
**Autor:** Sirius (AI Observability Framework)
**Data:** *(auto-gerado na atualização do painel)*

---

## 🎯 1. Objetivo Geral

Os dashboards do Araquem foram redesenhados para oferecer **poucos painéis**, porém **completos e acionáveis** — eliminando redundâncias e maximizando o valor visual da telemetria.

Cada dashboard responde a uma **pergunta fundamental** do sistema:

| Dashboard                       | Pergunta-chave                                                               |
| ------------------------------- | ---------------------------------------------------------------------------- |
| **00_SIRIOS_OVERVIEW**          | O sistema está saudável e entregando resultados dentro dos SLOs?             |
| **10_API_SLO_PIPELINE**         | Onde o tempo é gasto no pipeline `/ask` e quais gargalos impactam o SLO?     |
| **20_PLANNER_RAG_INTELLIGENCE** | O Planner e o RAG estão inteligentes, coerentes e atualizados?               |
| **30_OPS_RELIABILITY**          | A infraestrutura e os processos automáticos estão consistentes e confiáveis? |

Esses quatro painéis cobrem todo o ciclo de inteligência do Araquem: **do input da pergunta até a qualidade da resposta**.

---

## 🧭 2. Estrutura e Navegação

Os dashboards são provisionados automaticamente (via `grafana/provisioning/`) e agrupados na pasta **“Sirios Dashboards”** do Grafana.

### Variáveis globais

Todos compartilham variáveis (no topo da tela):

* `job` — normalmente `araquem-api`
* `entity` — domínio em análise (`fiis_cadastro`, `fiis_precos`, etc.)
* `intent` — intenção do usuário (`cadastro`, `preços`, `dividendos`, etc.)
* `store` — índice RAG (`embeddings.jsonl`)
* `interval` — janela temporal (ex.: `1h`, `6h`, `24h`, `7d`)

### Cores e convenções

* **Verde:** dentro do SLO.
* **Amarelo:** em tendência de risco (80–95% do limite).
* **Vermelho:** fora do limite (≥ limiar YAML).
* **Cinza:** métrica não disponível.

---

## 🧩 3. Dashboard 00 — SIRIOS_OVERVIEW

**Função:** visão executiva — saúde global do sistema.

### O que observar

* **KPIs de topo** (linha de cards):

  * **Throughput:** perguntas/minuto (proxy de uso).
  * **Erro (%):** relação entre erros e requisições.
  * **Latência p95:** tempo máximo aceitável (SLO: ≤ 1500 ms).
  * **Cache Hit Ratio:** eficiência de cache (> 60% ideal).
  * **RAG Density:** documentos por MB no índice (indicador de qualidade de embeddings).
  * **Último Refresh RAG:** tempo desde o último rebuild (ideal ≤ 24 h).

* **Tendências:**

  * Tráfego por status HTTP → estabilidade e padrão de uso.
  * Latência p50/p95/p99 → detectar variação diurna.

* **Alertas embutidos:**

  * Latência > 1500 ms → pipeline sobrecarregado.
  * Erros > 1% → possível falha lógica ou infra.
  * RAG sem refresh > 24 h → risco de respostas desatualizadas.
  * Cache hit < 60% → possível invalidação ou carga fria.

### Como ler

* **Verde constante** → operação saudável.
* **Amarelo frequente** → planejar re-otimização.
* **Vermelho persistente** → abrir incidente observabilidade nível 1.

### Acompanhamento

* Checar diariamente durante o horário de pico (≈ 10h–15h).
* Registrar variações > 20% no canal “#sirios-ops”.

---

## ⚙️ 4. Dashboard 10 — API_SLO_PIPELINE

**Função:** engenharia — entender o desempenho interno do pipeline `/ask`.

### Seções principais

1. **SLO de Latência**

   * Distribuição p50/p95/p99 (histogram_quantile).
   * Comparar períodos de carga vs períodos ociosos.
2. **Taxa de Erros**

   * Por status ou código específico.
3. **Pipeline Stages**

   * Divisões lógicas: *Planner → SQL → Formatter → Responder*.
   * Quando há tracing ativo, clicar em “Tempo Trace” → redireciona ao Tempo com o span `/ask`.
4. **Heatmap Entidade × Intent**

   * Mostra variação de latência por domínio.
5. **Tabela de Resultados**

   * Média de `rows_total` (retornos por query).

### O que olhar

* p95 > 1500 ms → gargalo.
* Erros concentrados em uma entidade → provável SQL ou cache.
* Gap grande p50→p95 → inconsistência de cache.

### Frequência recomendada

* Durante deploys ou após novos intents/entidades.
* Mensalmente, para comparar tendência histórica.

---

## 🧠 5. Dashboard 20 — PLANNER_RAG_INTELLIGENCE

**Função:** inteligência semântica e qualidade do índice de conhecimento.

### Planner

* **Top intents** por volume → identificar concentração de uso.
* **Planner score médio** → avaliar confiança das classificações.
* **Unroutables / Misses** → devem ser < 1 %.

### RAG Index

* **Docs & Size:** verifica crescimento do JSONL.
* **Density Score:** docs / MB — alvo > 10 docs/MB.
* **Last Refresh:** tempo desde último rebuild — ideal < 24 h.
* **Correlação p95 × Density:** densidades baixas costumam aumentar latência.

### Crons

* **rag-refresh-cron:** frequência e sucesso das execuções.
* Último log > 24 h → alerta preventivo.

### Leitura estratégica

* Queda de density → indice “rarefeito” (embeddings velhos).
* Crescimento muito rápido → duplicação de chunks.
* Misses planner ↑ → ajustar ontologia/tokens.

---

## 🧰 6. Dashboard 30 — OPS_RELIABILITY

**Função:** confiabilidade operacional e processos automatizados.

### Seções

1. **Cache**

   * Hits × Misses (por entidade).
   * Hit ratio global (ideal ≥ 60 %).
   * Picos de miss → reindexações ou flushes.
2. **Quality Gate**

   * Métricas `quality_top1_accuracy` e `quality_routed_rate`.
   * Valores de referência: 95% / 90%.
3. **Infraestrutura**

   * Job `araquem-api` → `up == 1`.
   * Redis / DB → latência e conexões (se expostas).
4. **Crons**

   * `quality-cron` e `rag-refresh-cron` → última execução OK.
   * Erros ou falhas → logs de `docker logs`.

### O que olhar

* Queda repentina no hit ratio ou routed rate → sintomas de drift.
* Qualquer cron > 24 h sem execução → agir.

---

## 🔍 7. Como acompanhar na rotina

| Frequência              | Ação                                                         |
| ----------------------- | ------------------------------------------------------------ |
| **Diariamente (manhã)** | Verificar *Overview*: latência, erros, refresh RAG.          |
| **Após deploy**         | Revisar *API_SLO_PIPELINE* e *OPS_RELIABILITY*.              |
| **Semanalmente**        | Analisar *Planner_RAG_INTELLIGENCE* para drift semântico.    |
| **Mensalmente**         | Exportar métricas agregadas p/ relatórios de confiabilidade. |

---

## 🧮 8. Alertas e thresholds

Os limites são definidos em `data/ops/observability.yaml`.
Grafana usa esses valores diretamente — **sem hardcode**.

| Métrica                            | Limiar    | Ação                      |
| ---------------------------------- | --------- | ------------------------- |
| `api_latency_p95`                  | > 1500 ms | revisar SQL e cache       |
| `api_error_rate`                   | > 1%      | inspecionar logs `/ask`   |
| `cache_hit_ratio`                  | < 60%     | invalidar cache e aquecer |
| `rag_index_last_refresh_timestamp` | > 24 h    | forçar rebuild            |
| `rag_index_density_score`          | < 10      | reindexar embeddings      |
| `quality_top1_accuracy`            | < 95%     | revisar testes de QA      |
| `quality_routed_rate`              | < 90%     | revisar ontologia         |

---

## 🔒 9. Governança dos Dashboards

* Todos os dashboards são **gerados automaticamente** via `scripts/observability/gen_dashboards.py`.
* O versionamento é controlado em `grafana/dashboards/_README.md` e no Git.
* Alterações manuais **não devem ser feitas diretamente** no JSON.
* A atualização segue o ciclo:

  1. Editar `data/ops/observability.yaml`
  2. Rodar `python scripts/observability/gen_dashboards.py`
  3. Revisar no Grafana
  4. Commitar a nova versão (`feat(obs): regenerate dashboards`)

---

## 🧠 10. Filosofia de Observabilidade SIRIOS

> **“Medir é a forma de aprender.”**

O Araquem não mede para vigiar, mede para **melhorar com consciência**.
Cada métrica exposta e cada dashboard têm um propósito claro:

* **Executivo:** medir entrega e estabilidade.
* **Engenharia:** medir gargalos e causas.
* **IA/Ontologia:** medir coerência e aprendizado.
* **Operações:** medir confiabilidade e rotina.

A junção desses quatro níveis forma o ciclo contínuo de melhoria que sustenta a IA SIRIOS.

---

### 📘 Dica final

No canto superior direito de cada dashboard há um **ícone de “?”** com o link para este documento (`docs/dev/DASHBOARD_GUIDE.md`).
Manteremos ambos versionados juntos: sempre que o dashboard mudar, o guia também muda.

---
