# ✅ **CHECKLIST OPERACIONAL — M11 Observability Enhancements**

> **Período estimado:** 2025-11-11 → 2025-11-15
> **Objetivo:** elevar a observabilidade do Araquem ao nível de contrato (SLO-grade).
> **Escopo:** auditoria de schema, dashboards versionados, catálogo de métricas, Explain Loop e CI observability-gate.

---

## 🧭 1. AUDITORIA DE SCHEMA — `explain_events`

<details>
<summary>Verificações</summary>

* [ ] 1.1 Confirmar schema real em `docs/database/views/tables.sql`
* [ ] 1.2 Validar colunas descritas no doc contra `app/analytics/explain.py`
* [ ] 1.3 Criar ou atualizar teste `tests/explain/test_explain_schema_sync.py`
* [ ] 1.4 Adicionar rotina em `scripts/observability/obs_audit.py`
* [ ] 1.5 Registrar resultado na métrica `observability_contracts_pass`

📝 **Observações:**

<!-- -->

</details>

---

## 📊 2. DASHBOARDS & ALERTAS VERSIONADOS

<details>
<summary>Verificações</summary>

* [ ] 2.1 Verificar dashboards existentes em `grafana/dashboards/`
* [ ] 2.2 Garantir hashes ou version tags em todos os `.json` e `.j2`
* [ ] 2.3 Atualizar *20_planner_rag_intelligence* com dados de `explain_events`
* [ ] 2.4 Atualizar *30_ops_reliability* (cache hit, latência, erro)
* [ ] 2.5 Validar alerting rules em `prometheus/alerting_rules.yml`
* [ ] 2.6 Confirmar renderização local no Grafana (`:3000`)

📝 **Observações:**

<!-- -->

</details>

---

## ⚙️ 3. PIPELINE DE MÉTRICAS UNIFICADO

<details>
<summary>Verificações</summary>

* [ ] 3.1 Consolidar métricas de planner, cache, executor, narrator, rag e analytics em `app/observability/metrics.py`
* [ ] 3.2 Atualizar documentação em `docs/dev/observability/overview.md`
* [ ] 3.3 Criar tabela de referência “Catálogo de Métricas” (nome, tipo, unidade, origem)
* [ ] 3.4 Validar exposição completa via `/metrics`
* [ ] 3.5 Conferir ingestão no Prometheus (`:9090/targets`)

📝 **Observações:**

<!-- -->

</details>

---

## 🧠 4. EXPLAIN OBSERVABILITY LOOP

<details>
<summary>Verificações</summary>

* [ ] 4.1 Confirmar coleta de `explain_events` pelo `app/analytics/metrics.py`
* [ ] 4.2 Garantir grafana panels mostrando: latência, planner decisions, cache policy, SQL hash
* [ ] 4.3 Validar relação 1:1 entre eventos e traces OTEL (Tempo)
* [ ] 4.4 Documentar o loop em `docs/dev/observability/overview.md` (nova subseção “Explain Loop”)
* [ ] 4.5 Criar métrica derivada: `planner_explain_latency_ms`

📝 **Observações:**

<!-- -->

</details>

---

## 🔒 5. CI OBSERVABILITY-GATE

<details>
<summary>Verificações</summary>

* [ ] 5.1 Estender `scripts/quality/quality_gate_check.sh` para incluir auditoria de observabilidade
* [ ] 5.2 Integrar `scripts/observability/hash_guard.py` no pipeline
* [ ] 5.3 Validar passagem automática de contratos (`observability_contracts_pass: 1`)
* [ ] 5.4 Adicionar testes `tests/observability/test_obs_counter_value.py` e `test_alerting_rules.py`
* [ ] 5.5 Atualizar relatório `/ops/quality/report` com nova métrica

📝 **Observações:**

<!-- -->

</details>

---

## 📘 6. DOCUMENTAÇÃO E EVIDÊNCIAS

<details>
<summary>Verificações</summary>

* [ ] 6.1 Atualizar `docs/dev/observability/overview.md` com todas as alterações
* [ ] 6.2 Incluir referência cruzada em `docs/VALIDACAO_ARQUITETURA.md` (seção 8-9)
* [ ] 6.3 Exportar dashboards finais (`.json`) e subir hashes em `grafana/provisioning/dashboards.yml`
* [ ] 6.4 Registrar logs de teste e métricas em `docs/misc/notes/QUALITY_FIX_REPORT.md`
* [ ] 6.5 Gerar resumo final `VALIDACAO_OBSERVABILITY_M11.md`

📝 **Observações:**

<!-- -->

</details>

---

## ✅ **Definition of Done (DoD M11)**

* [ ] Auditoria de schema explain_events aprovada e testada
* [ ] Dashboards e alertas versionados com hash
* [ ] Métricas unificadas e documentadas
* [ ] Explain Loop operacional e visível no Grafana
* [ ] CI observability-gate passando
* [ ] Commit final:

  ```
  docs: finalize M11 observability enhancements (schema sync + dashboards v2)
  ```

---

## 🧭 **Mindset**

> “M10 mostrou o que o sistema é.
> M11 mostra o que o sistema sente.”
> — *Observabilidade como contrato.*

