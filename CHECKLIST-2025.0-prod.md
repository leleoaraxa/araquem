# ✅ **CHECKLIST ARAQUEM — RUMO À PRODUÇÃO (2025.0-prod)**

**(Somente o que realmente falta — baseado no status REAL do sistema)**

---

## **1. RAG – Conteúdo e Políticas**

* [X] Revisar collections por entidade em `data/policies/rag.yaml`
* [X] Criar/organizar collections específicas (ex.: fiis_risk, fiis_rankings, macro, mercado)
* [ ] Validar quantidade e qualidade dos chunks
* [ ] Regerar embeddings se necessário (com batch embed)
* [ ] Testar RAG fusion/re-rank em perguntas reais

---

## **2. Planner – Thresholds e Calibração Final**

* [ ] Revisar `planner_thresholds.yaml` (min_score, min_gap)
* [ ] Ajustar threshold por intent/entity com base nos gaps reais
* [ ] Validar threshold com explain logs (aceites vs rejections)
* [ ] Validar comportamento com RAG blend/re-rank habilitado
* [ ] Fechar baseline de roteamento pós-calibração

---

## **3. Narrator – Versão para Produção**

* [ ] Revisar `data/policies/narrator.yaml`
* [ ] Definir níveis de:

  * [ ] llm_enabled
  * [ ] shadow
  * [ ] max_llm_rows
  * [ ] style
  * [ ] use_rag_in_prompt
* [ ] Definir fallback seguro para todos intents
* [ ] Garantir respostas curtas/precisas para todas entidades

---

## **4. RAG + Narrator – Integração**

* [ ] Confirmar quando Narrator deve usar RAG no prompt
* [ ] Validar tamanhos dos snippets e compressão
* [ ] Verificar latências do Ollama (LLM e embeddings)
* [ ] Testar shadow mode com dataset real

---

## **5. Quality – Baseline Final**

* [ ] Corrigir os 16 misses restantes (curadoria final)
* [ ] Rodar nova bateria `quality_list_misses.py`
* [ ] Rodar push com samples completos
* [ ] Validar gaps e top1/top2 no Prometheus
* [ ] Fixar baseline “2025.0-prod”

---

## **6. Infra/Prod – Ambiente Real**

* [ ] Definir e aplicar `DATABASE_URL` de produção
* [ ] Configurar OTEL Collector (prod URL)
* [ ] Configurar Tempo/Grafana/Prometheus prod
* [ ] Habilitar alerts e dashboards reais
* [ ] Confirmar cache Redis (TTL e blue/green)

---

## **7. Segurança & LGPD**

* [ ] Sanitização de PII no presenter/formatter
* [ ] Garantir que explain-events não vazam dados sensíveis
* [ ] Ajustar regras de acesso e tokens (quality & ops)
* [ ] Validar logs/traces para ausência de payloads sensíveis

---

## **8. Documentação Final**

* [ ] Atualizar `ARAQUEM_STATUS_2025.md` com baseline final
* [ ] Gerar diagramas (C4) atualizados
* [ ] Documentar roles e policies (RAG/Narrator/Quality/Cache)
* [ ] Documentar rotas `/ask`, `/ops/*`, explain-mode

---

## **9. Testes de Carga e Estresse**

* [ ] Testar throughput do /ask com llama3.1:latest
* [ ] Testar embedding client (batch) sob carga
* [ ] Testar latência com Prometheus histograms
* [ ] Validar estabilidade em cenários extremos

---

## **10. Entrega Final (2025.0-prod)**

* [ ] Criar tag da versão
* [ ] Ativar CI/CD com blue/green Redis
* [ ] Congelar embeddings + ontology
* [ ] Gerar pacote final para deploy
* [ ] Validar smoke test no ambiente final
