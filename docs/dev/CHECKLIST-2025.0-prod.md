# ✅ **CHECKLIST ARAQUEM — RUMO À PRODUÇÃO (2025.0-prod)**

### *(versão Sirius — atualizada com 14 entidades e melhorias estruturais)*

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

## **1. Entidades & Realidade dos Dados (D-1 vs Histórico)** 🆕

> 🟦 14 entidades auditadas hoje — **bloco 100% concluído**.

### 🟩 **1.1 O que já foi feito**

* ✔ Auditoria profunda das **14 entidades reais** do Araquem
* ✔ Classificação de cada uma: D-1, histórica ou quase estática
* ✔ Identificação de:

  * periodicidade real
  * cardinalidade
  * chaves naturais
  * riscos de interpretação
  * aderência a RAG/Narrator/quality/cache
* ✔ Discussão sobre lacunas essenciais (DY histórico, views compostas, macro sem quality)
* ✔ Incorporado ao ARAQUEM_STATUS_2025.md

### 🟦 **1.2 Melhorias adicionadas ao checklist**

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

* [ ] Criar regras de quality para:

  * history_currency_rates
  * history_b3_indexes
  * history_market_indicators

* [ ] Criar janelas padrão em param_inference para:

  * macro
  * índices B3
  * moedas

* [ ] Documentar tudo no ARAQUEM_STATUS_2025.md (em andamento)

---

## **2. RAG – Conteúdo e Políticas**

**✔️ Feito**

* ✔ Collections validadas por entidade
* ✔ Perfis risk/macro/default revisados
* ✔ deny/allow_intents alinhado ao Guardrails
* ✔ RAG isolado aos domínios permitidos

**🔵 Falta**

* [ ] Validar **quantidade real** de chunks por entidade
* [ ] Revisar **qualidade semântica** dos chunks
* [ ] Regerar embeddings (batch 8)
* [ ] Testar fusion/re-rank com perguntas reais
* [ ] Validar top_k ideal por domínio

---

## **3. Planner – Thresholds e Calibração Final**

**🔵 Falta**

* [ ] Revisar thresholds por intent/entity
* [ ] Ajustar intent_top2_gap e entity_top2_gap
* [ ] Validar explain logs
* [ ] Fixar baseline final após “Entidades D-1 vs Histórico”

---

## **4. Narrator – Versão para Produção**

**✔️ Políticas ok; LLM OFF**

**🔵 Falta**

* [ ] Ajustar narrator.yaml para prod
* [ ] Decidir se max_llm_rows continua zero
* [ ] Ajustar estilo final (executivo/objetivo)
* [ ] Validar fallback seguro entidade a entidade

---

## **5. RAG + Narrator – Integração Profissional**

* [ ] Uso de RAG no prompt
* [ ] Limitar snippets (250–350 chars)
* [ ] Testar latência
* [ ] Testar modos shadow

---

## **6. Quality – Baseline Final**

* [ ] Curadoria dos 16 misses
* [ ] Rodar testes sem RAG
* [ ] Fixar baseline 2025.0-prod
* [ ] Validar métricas no Grafana

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

* [ ] Atualizar `ARAQUEM_STATUS_2025.md`
* [ ] Documentar tudo (C4, RAG flows, narrator, context)

---

## **10. Testes de Carga e Estresse**

Checklist mantido

---

## **11. Entrega Final — “2025.0-prod”**

Checklist mantido
