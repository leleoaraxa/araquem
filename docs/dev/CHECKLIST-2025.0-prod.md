# ✅ **CHECKLIST ARAQUEM — RUMO À PRODUÇÃO (2025.0-prod)**

### *(versão Sirius — 18 entidades auditadas, RAG/Narrator/Quality alinhados)*

---

## **0. Contexto Conversacional (M12–M13)**

> 🟩 Base técnica pronta. Próxima etapa: ativar e calibrar *somente após baseline final*.

**✔️ Feito**

* ✔ `context_manager.py` criado
* ✔ Integração mínima no `/ask` (append_turn)
* ✔ Presenter injeta `history` no meta do Narrator
* ✔ Policies definidas em `data/policies/context.yaml`
* ✔ Total compliance com Guardrails v2.1.1
* ✔ Zero impacto quando `enabled: false`

**🔵 Falta**

* [ ] Ativar context (`enabled: true`) **após baseline**
* [ ] Definir entidades que podem usar contexto
* [ ] Validar herança de referência (ex.: Sharpe do “fundo anterior”)
* [ ] Testes com LLM OFF garantindo que nada muda
* [ ] Criar fallback leve para fluxos multi-turno no Narrator

---

## **1. Entidades & Realidade dos Dados (D-1 vs Histórico)**

> 🟩 18 entidades auditadas e documentadas no `ARAQUEM_STATUS_2025.md`.

### 🟩 **1.1 O que já foi feito**

* ✔ Auditoria profunda das **18 entidades reais** do Araquem (FIIs, macro e cliente privado)
* ✔ Classificação de cada uma: D-1, histórica ou quase estática
* ✔ Identificação de:
  * periodicidade real
  * cardinalidade
  * chaves naturais
  * riscos de interpretação
  * aderência a RAG / Narrator / quality / cache
* ✔ Registro consolidado em `docs/ARAQUEM_STATUS_2025.md`
* ✔ Criação e atualização de `data/ops/entities_consistency_report.yaml` garantindo:
  * `has_schema`, `has_quality_projection`, `in_quality_policy`
  * participação (ou exclusão explícita) em cache, RAG, Narrator, param_inference, ontologia
* ✔ Novos projections de quality criados:
  * `projection_client_fiis_dividends_evolution.json`
  * `projection_client_fiis_performance_vs_benchmark.json`
  * `projection_fii_overview_evolution.json`
  * `projection_fiis_yield_history_evolution.json`
* ✔ `routing_samples.json` expandido com cenários:
  * resumo de FII (`fii_overview`)
  * histórico de DY (`fiis_yield_history`)
  * evolução de dividendos da carteira (`client_fiis_dividends_evolution`)
  * performance da carteira vs benchmark (`client_fiis_performance_vs_benchmark`)

### 🟦 **1.2 Backlog de modelagem (não implementado ainda)**

* [ ] Criar views **compostas** (compute-on-read) sobre as entidades atuais:

  * [ ] `dividendos_yield`
        (junção de `fiis_dividendos` + `fiis_yield_history` para análises mais ricas)
  * [ ] `carteira_enriquecida`
        (client positions + snapshot + risk + cadastro, respeitando LGPD)
  * [ ] `macro_consolidada`
        (moedas + índices + macro em uma visão executiva)
  * [ ] Extensões de `fii_overview` com histórico (DY, preço, risco ao longo do tempo)

* [ ] Mapear perguntas reais que dependem dessas views:

  * “FIIs com DY alto e P/VP baixo”
  * “Qual o risco da minha carteira?”
  * “Quanto rendeu meu HGLG11 nos últimos 12 meses?”

---

## **2. RAG – Conteúdo e Políticas**

**✔️ Feito**

* ✔ Collections validadas por entidade
* ✔ Perfis `default` / `risk` / `macro` revisados
* ✔ `deny_intents` / `allow_intents` alinhados ao Guardrails
* ✔ RAG isolado aos domínios permitidos:
  * `fiis_noticias`
  * conceitos de risco (`fiis_financials_risk`)
  * macro / índices / moedas (`history_market_indicators`, `history_b3_indexes`, `history_currency_rates`)
* ✔ Comentários explicando por que domínios numéricos/privados ficam **fora de RAG**:
  * FIIs puramente SQL (preços, dividendos, snapshots, overview, cronograma)
  * carteira do cliente (`client_fiis_*`)

**🔵 Falta**

* [ ] Validar **quantidade real** de chunks por entidade (macro, risco, notícias)
* [ ] Revisar **qualidade semântica** dos chunks (noise, duplicidade, textos desatualizados)
* [ ] Regerar embeddings (batch 8) com política final de collections
* [ ] Testar fusion/re-rank com perguntas reais de risco e macro
* [ ] Validar `top_k` ideal por domínio (notícias, risco, macro)

---

## **3. Planner – Thresholds e Calibração Final**

**✔️ Feito**

* ✔ Ontologia refinada (`data/ontology/entity.yaml`) para:
  * separar claramente dividendos × DY (snapshot × histórico × ranking)
  * ajustar roteamento de notícias negativas, dólar e IPCA (corrigindo misses antigos)
  * incluir intents novas:
    * `fii_overview`
    * `fiis_yield_history`
    * `client_fiis_dividends_evolution`
    * `client_fiis_performance_vs_benchmark`
* ✔ `quality_list_misses.py` volta ao alvo “✅ Sem misses” após ajustes de tokens/phrases/anti_tokens.

**🔵 Falta**

* [ ] Revisar thresholds finos por intent/entity (top1_min_score, min_gap)
* [ ] Ajustar `intent_top2_gap` e `entity_top2_gap` com base no explain real
* [ ] Validar explain logs / `decision_path` em perguntas de fronteira
* [ ] Fixar baseline final após fechamento de entidades e quality

---

## **4. Narrator – Versão para Produção**

**✔️ Feito**

* ✔ `narrator.yaml` revisado com:
  * `llm_enabled: false`, `shadow: false`, `max_llm_rows: 0`
  * overrides explícitos documentados (mas todos com LLM OFF)
* ✔ Presenter sempre retorna baseline determinístico (templates / md.j2)

**🔵 Falta**

* [ ] Desenhar política de produção (quais entidades poderão usar LLM no futuro)
* [ ] Decidir se `max_llm_rows` continua zero em prod ou se ativa modo shadow controlado
* [ ] Ajustar estilo final (executivo/objetivo) para quando LLM for ligado
* [ ] Validar fallback seguro entidade a entidade (LLM falha ⇒ baseline)

---

## **5. RAG + Narrator – Integração Profissional**

**🔵 Falta**

* [ ] Testar uso de RAG no prompt do Narrator (somente conceitos)
* [ ] Limitar snippets (250–350 chars) em prompts de risco/macro/notícias
* [ ] Testar latência ponta-a-ponta com RAG + Narrator (shadow)
* [ ] Testar modos shadow em cenários reais sem impactar resposta do cliente

---

## **6. Quality – Baseline Final**

**✔️ Feito**

* ✔ `quality.yaml` revisado com `targets` realistas (min_top1_accuracy 0.93, min_routed_rate 0.98)
* ✔ Cobertura de datasets incluindo:
  * FIIs:
    * preços (`fiis_precos`)
    * dividendos (`fiis_dividendos`)
    * histórico de DY (`fiis_yield_history`)
    * cadastro (`fiis_cadastro`)
    * imóveis (`fiis_imoveis`)
    * processos (`fiis_processos`)
    * rankings (`fiis_rankings`)
    * snapshot financeiro (`fiis_financials_snapshot`)
    * cronograma de receitas (`fiis_financials_revenue_schedule`)
    * risco (`fiis_financials_risk`)
    * overview consolidado (`fii_overview`)
    * notícias (`fiis_noticias`)
  * Cliente (privado):
    * posições de carteira (`client_fiis_positions`)
    * evolução de dividendos da carteira (`client_fiis_dividends_evolution`)
    * performance vs benchmark (`client_fiis_performance_vs_benchmark`)
  * Macro:
    * `history_currency_rates`, `history_b3_indexes`, `history_market_indicators`
* ✔ Regras de faixa (`accepted_range`) adicionadas/ajustadas para:
  * buckets de receita (`fiis_financials_revenue_schedule`)
  * risco (`fiis_financials_risk`)
  * macro/índices/moedas (variações e taxas > 0, limites razoáveis)
  * carteiras (`client_fiis_*` – retornos entre -1.0 e 1.0, valores >= 0)
* ✔ `quality_list_misses.py` e `quality_diff_routing.py` rodando sem chamar Ollama
* ✔ Última intenção de baseline: **0 misses de roteamento** no conjunto de testes atual

**🔵 Falta**

* [ ] Rodar rotina de quality periodicamente e registrar histórico de baseline
* [ ] Fixar baseline 2025.0-prod em README interno de quality
* [ ] Validar e ajustar dashboards de qualidade no Grafana (top1, routed, gap)
* [ ] Preparar check de qualidade para novos domínios (futuros compostos / yield avançado)

---

## **7. Infra/Produção – Ambientes e Deploy**

Checklist de produção
*(igual ao que você já tinha — mantido, apenas referenciando agora 18 entidades).*

---

## **8. Segurança & LGPD**

Checklist de segurança
*(igual ao original — mantido; reforço aqui que `client_fiis_*` seguem binding via contexto e não expõem documento nem dados cruzados entre clientes).*

---

## **9. Documentação Final**

* [ ] Manter `ARAQUEM_STATUS_2025.md` como fonte viva de estado
* [ ] Atualizar C4, fluxos de RAG, Narrator, contexto e quality
* [ ] Documentar entidades compostas planejadas (sem quebrar contratos atuais)

---

## **10. Testes de Carga e Estresse**

Checklist mantido

---

## **11. Entrega Final — “2025.0-prod”**

Checklist mantido
