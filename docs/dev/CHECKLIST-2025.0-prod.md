# ✅ **CHECKLIST ARAQUEM — RUMO À PRODUÇÃO (2025.0-prod)**

### *(versão Sirius — 21 entidades auditadas, RAG/Narrator/Quality alinhados)*

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

> 🟩 **21 entidades** auditadas e documentadas no `ARAQUEM_STATUS_2025.md`.

### 🟩 **1.1 O que já foi feito**

* ✔ Auditoria profunda das **21 entidades reais** do Araquem (FIIs, macro, cliente privado e compostas)
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
* ✔ Novos projections de quality criados (incluindo privadas/compostas):

  * `client_fiis_dividends_evolution`
  * `client_fiis_performance_vs_benchmark`
  * `fii_overview` / `fiis_yield_history` (evoluções históricas)
  * **novas entidades compostas**: projections específicas para

    * `dividendos_yield`
    * `carteira_enriquecida`
    * `macro_consolidada`
* ✔ `routing_samples.json` expandido com cenários:

  * resumo de FII (`fii_overview`)
  * histórico de DY (`fiis_yield_history`)
  * evolução de dividendos da carteira (`client_fiis_dividends_evolution`)
  * performance da carteira vs benchmark (`client_fiis_performance_vs_benchmark`)
  * **casos compostos**:

    * “histórico de dividendos **e DY** do MXRF11” (`dividendos_yield`)
    * perguntas de carteira enriquecida (peso, DY, risco na carteira) (`carteira_enriquecida`)
    * perguntas macro consolidadas por data/período (`macro_consolidada`)
* ✔ **Adicionadas e integradas**:

  * ✔ **dividendos_yield** (pública, multi-ticker) com entity/schema/templates, projeção de qualidade, catálogo, ontologia, políticas (quality/cache/rag/narrator/context), `param_inference` histórico e thresholds atualizados
  * ✔ **carteira_enriquecida** (privada) com bindings seguros (`document_number: context.client_id`), templates, projeção de qualidade, catálogo, ontologia, políticas (quality/cache/rag/narrator/context), `param_inference` desabilitado e thresholds alinhados para privadas
  * ✔ **macro_consolidada** (macro histórica) com entity/schema/templates, projeção de qualidade, catálogo, ontologia, políticas (quality/cache/rag/narrator/context), `param_inference` histórico e thresholds ajustados

### 🟦 **1.2 Backlog de modelagem (não implementado ainda)**

* [ ] Extensões de `fii_overview` com histórico consolidado (DY, preço, risco ao longo do tempo) seguindo padrão compute-on-read D-1
* [ ] Mapear perguntas reais que dependem de visões futuras (além das 21 entidades atuais), por exemplo:

  * “FIIs com DY alto e P/VP baixo **em janela específica**”
  * “Qual o risco da minha carteira **ao longo do tempo**?”
  * “Como evoluiu o risco/retorno da minha carteira desde 2020?”

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

  * FIIs puramente SQL (preços, dividendos, snapshots, overview, cronograma, **dividendos_yield**)
  * carteira do cliente e compostos privados (`client_fiis_*`, `carteira_enriquecida`)
  * `macro_consolidada` fica em SQL puro (sem RAG) para garantir consistência numérica

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

  * separar claramente dividendos × DY (snapshot × histórico × ranking × **compostas**)
  * ajustar roteamento de notícias negativas, dólar e IPCA (corrigindo misses antigos)
  * incluir intents novas:

    * `fii_overview`
    * `fiis_yield_history`
    * `client_fiis_dividends_evolution`
    * `client_fiis_performance_vs_benchmark`
    * **`dividendos_yield` (pública, multi-ticker)**
    * **`carteira_enriquecida` (privada)**
    * **`macro_consolidada` (macro histórica)**
* ✔ `quality_list_misses.py` volta ao alvo “✅ Sem misses” após ajustes de tokens/phrases/anti_tokens, incluindo os novos intents.

**🔵 Falta**

* [ ] Revisar thresholds finos por intent/entity (top1_min_score, min_gap), cobrindo também `dividendos_yield`, `carteira_enriquecida`, `macro_consolidada`
* [ ] Ajustar `intent_top2_gap` e `entity_top2_gap` com base no explain real
* [ ] Validar explain logs / `decision_path` em perguntas de fronteira (ex.: DY histórico x snapshot x composto)
* [ ] Fixar baseline final após fechamento de entidades e quality

---

## **4. Narrator – Versão para Produção**

**✔️ Feito**

* ✔ `narrator.yaml` revisado com:

  * `llm_enabled: false`, `shadow: false`, `max_llm_rows: 0`
  * overrides explícitos documentados (mas todos com LLM OFF)
* ✔ Presenter sempre retorna baseline determinístico (templates / md.j2)
* ✔ Inclusão explícita das novas entidades (`dividendos_yield`, `carteira_enriquecida`, `macro_consolidada`) com **Narrator OFF** (sem risco de LLM em domínios numéricos/privados)

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
    * carteira enriquecida (`carteira_enriquecida`)
  * Macro:
    * `history_currency_rates`, `history_b3_indexes`, `history_market_indicators`, `macro_consolidada`
* ✔ Regras de faixa (`accepted_range`) adicionadas/ajustadas para:
  * buckets de receita (`fiis_financials_revenue_schedule`)
  * risco (`fiis_financials_risk`)
  * macro/índices/moedas (variações e taxas > 0, limites razoáveis)
  * carteiras (`client_fiis_*` – retornos entre -1.0 e 1.0, valores >= 0)
* ✔ `quality_list_misses.py` e `quality_diff_routing.py` rodando sem chamar Ollama
* ✔ Baseline **2025.0-prod** fixado:
  * `python scripts/quality/quality_list_misses.py` → `✅ Sem misses.`
  * `python scripts/quality/quality_diff_routing.py` → `✅ Sem misses.`
  * routing_samples cobrindo também `dividendos_yield`, `carteira_enriquecida` e `macro_consolidada`.

**🔵 Falta**

* [ ] Rodar rotina de quality periodicamente e registrar histórico de baseline
* [ ] Documentar no README interno de quality o procedimento de atualização de baseline (quando houver mudança em ontologia/entities/policies)
* [ ] Validar e ajustar dashboards de qualidade no Grafana (top1, routed, gap)
* [ ] Preparar check de qualidade para novos domínios (futuros compostos / yield avançado)

---

## **7. Infra/Produção – Ambientes e Deploy**

Checklist de produção
*(igual ao que você já tinha — mantido, agora assumindo **21 entidades** estabilizadas no status/quality.)*

---

## **8. Segurança & LGPD**

Checklist de segurança
*(igual ao original — mantido; reforço aqui que `client_fiis_*` e `carteira_enriquecida` seguem binding via contexto e não expõem documento nem dados cruzados entre clientes.)*

---

## **9. Documentação Final**

* [ ] Manter `ARAQUEM_STATUS_2025.md` como fonte viva de estado
* [ ] Atualizar C4, fluxos de RAG, Narrator, contexto e quality
* [ ] Documentar entidades compostas **existentes e futuras**:

  * `dividendos_yield`
  * `carteira_enriquecida`
  * `macro_consolidada`
  * (e quaisquer novos compostos aprovados no Guardrails)

---

## **10. Testes de Carga e Estresse**

Checklist mantido

---

## **11. Entrega Final — “2025.0-prod”**

Checklist mantido
