# ✅ **CHECKLIST ARAQUEM — RUMO À PRODUÇÃO (2025.0-prod)**

### *(versão Sirius — 14 entidades auditadas, RAG/Narrator/Quality alinhados)*

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

> 🟩 14 entidades auditadas e documentadas no ARAQUEM_STATUS_2025.md.

### 🟩 **1.1 O que já foi feito**

* ✔ Auditoria profunda das **14 entidades reais** do Araquem
* ✔ Classificação de cada uma: D-1, histórica ou quase estática
* ✔ Identificação de:
  * periodicidade real
  * cardinalidade
  * chaves naturais
  * riscos de interpretação
  * aderência a RAG / Narrator / quality / cache
* ✔ Registro consolidado em `docs/ARAQUEM_STATUS_2025.md`
* ✔ Criação de `data/ops/entities_consistency_report.yaml` garantindo:
  * `has_schema`, `has_quality_projection`, `in_quality_policy`
  * participação (ou exclusão explícita) em cache, RAG, Narrator, param_inference, ontologia

### 🟦 **1.2 Backlog de modelagem (não implementado ainda)**

* [ ] Criar entidade **fiis_yield_history** (DY histórico real)

* [ ] Criar views compostas (compute-on-read):

  * [ ] **fii_overview** (cadastro + snapshot + risk + rankings)
  * [ ] **dividendos_yield** (dividendos + snapshot DY)
  * [ ] **carteira_enriquecida** (posições + snapshot + risk + cadastro)
  * [ ] **macro_consolidada** (moedas + índices + macro)

* [ ] Mapear perguntas reais que dependem dessas views:

  * “Resumo do HGLG11”
  * “Evolução do DY”
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
* ✔ Comentários explicando por que FIIs numéricos e `client_fiis_positions` ficam **fora de RAG**

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
  * separar claramente dividendos × DY (snapshot × ranking)
  * ajustar roteamento de notícias negativas, dólar e IPCA (corrigir 5 misses de routing)
* ✔ `quality_list_misses.py` agora retorna **“✅ Sem misses”** no conjunto atual

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
  * overrides explícitos para risco, cronograma de receita e notícias
  * comentários por entidade explicando por que o Narrator está desligado
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
  * FIIs: preços, dividendos, imóveis, processos, rankings, snapshot, cronograma, risco, notícias, cadastro, carteira
  * Macro: `history_currency_rates`, `history_b3_indexes`, `history_market_indicators`
* ✔ Regras de faixa (`accepted_range`) adicionadas para:
  * buckets de receita (`fiis_financials_revenue_schedule`)
  * macro/índices/moedas (variações e taxas > 0, limites razoáveis)
* ✔ `quality_list_misses.py` e `quality_diff_routing.py` rodando sem chamar Ollama
* ✔ Última execução: **0 misses de roteamento** no conjunto de testes atual

**🔵 Falta**

* [ ] Rodar rotina de quality periodicamente e registrar histórico de baseline
* [ ] Fixar baseline 2025.0-prod em README interno de quality
* [ ] Validar e ajustar dashboards de qualidade no Grafana (top1, routed, gap)
* [ ] Preparar check de qualidade para novos domínios (futuros compostos / yield histórico)

---

## **7. Infra/Produção – Ambientes e Deploy**

Checklist de produção
(igual ao que você já tem — mantido)

---

## **8. Segurança & LGPD**

Checklist de segurança
(igual ao original — mantido)

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
