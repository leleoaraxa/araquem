# ✅ **CHECKLIST DE VALIDAÇÃO — DOCUMENTAÇÃO ARAQUEM (Fase M10.1)**

> Objetivo: validar se a documentação gerada pelo Codex reflete fielmente o estado real do repositório Araquem
>
> 📍 *Não alterar código, apenas marcar divergências e lacunas.*

---

## 🧭 1. VISÃO GERAL (`docs/README_ARQUITETURA.md`)

<details>
<summary>Verificações</summary>

* [ ] 1.1 O resumo do sistema descreve corretamente o propósito do Araquem
* [ ] 1.2 O mapa de documentos (links) está funcional
* [ ] 1.3 O fluxo “Como rodar local” está alinhado ao `docker-compose.yml`
* [ ] 1.4 A tabela de ambientes/endpoints reflete os serviços reais
* [ ] 1.5 O checklist de observabilidade (logs, métricas, tracing) condiz com `app/observability/`

📝 **Observações:**

<!-- Escreva aqui -->

</details>

---

## 🧩 2. MODELO C4

<details>
<summary>Contexto (`docs/c4-context.md`)</summary>

* [ ] 2.1 Atores externos corretos (usuário, Redis, Ollama, Grafana etc.)
* [ ] 2.2 Interações e protocolos (HTTP, Redis, SQL, etc.) representados corretamente
* [ ] 2.3 Diagrama em Mermaid renderiza corretamente

📝 **Observações:**

<!-- -->

</details>

<details>
<summary>Contêineres (`docs/c4-containers.md`)</summary>

* [ ] 2.4 Todos os serviços do compose (api, redis, prometheus, grafana, tempo, ollama, quality-cron) aparecem no diagrama
* [ ] 2.5 Propósito e tecnologia de cada contêiner estão corretos
* [ ] 2.6 Relações entre serviços (ex.: api ↔ ollama) estão corretas

📝 **Observações:**

<!-- -->

</details>

<details>
<summary>Componentes (`docs/c4-components.md`)</summary>

* [ ] 2.7 Módulos principais (planner, builder, executor, formatter, responder) mapeados corretamente
* [ ] 2.8 Dependências internas (quem chama quem) coerentes

📝 **Observações:**

<!-- -->

</details>

---

## ⚙️ 3. FLUXOS DE SEQUÊNCIA (`docs/fluxos-sequencia.md`)

<details>
<summary>Verificações</summary>

* [ ] 3.1 Fluxo `/ask` cobre todas as camadas (planner → builder → executor → formatter → responder)
* [ ] 3.2 Métricas e cache aparecem no ponto certo (`app/cache/rt_cache.py`)
* [ ] 3.3 Há pelo menos 1 fluxo adicional documentado (ex.: job de qualidade ou ingestão)

📝 **Observações:**

<!-- -->

</details>

---

## 🔐 4. CONFIGURAÇÃO E SEGREDOS (`docs/configuracao-e-segredos.md`)

<details>
<summary>Verificações</summary>

* [ ] 4.1 Todas as variáveis de `.env` listadas
* [ ] 4.2 Cada variável mostra origem (env/arquivo) e consumidores
* [ ] 4.3 Itens sensíveis marcados corretamente ⚠️
* [ ] 4.4 Precedência (env > arquivo > default) descrita corretamente

📝 **Observações:**

<!-- -->

</details>

---

## 📦 5. DEPENDÊNCIAS (`docs/dependencias.md`)

<details>
<summary>Verificações</summary>

* [ ] 5.1 Dependências internas entre módulos corretas
* [ ] 5.2 Dependências externas (libs/serviços) com versão e propósito descritos
* [ ] 5.3 Nenhuma dependência essencial faltando (`psycopg`, `redis`, `fastapi`, etc.)

📝 **Observações:**

<!-- -->

</details>

---

## 🧠 6. DADOS (`docs/dados.md`)

<details>
<summary>Verificações</summary>

* [ ] 6.1 Principais tabelas/entidades listadas (`basics_tickers`, `hist_dividends`, `explain_events`, etc.)
* [ ] 6.2 Campos e chaves relevantes identificados (id, ticker, updated_at...)
* [ ] 6.3 Leitores e escritores de cada entidade estão corretos

📝 **Observações:**

<!-- -->

</details>

---

## 📘 7. GLOSSÁRIO E RESPONSABILIDADES (`docs/glossario-e-responsabilidades.md`)

<details>
<summary>Verificações</summary>

* [ ] 7.1 Termos FIIs (ticker, dividendos, cotistas...) descritos corretamente
* [ ] 7.2 Responsáveis/donos por área ou módulo listados (se aplicável)

📝 **Observações:**

<!-- -->

</details>

---

## ⚠️ 8. RISCOS E DÍVIDAS TÉCNICAS (`docs/risks-e-tech-debt.md`)

<details>
<summary>Verificações</summary>

* [ ] 8.1 Riscos classificados por severidade (Alta, Média, Baixa)
* [ ] 8.2 Cada risco contém causa → impacto → evidência (arquivo:linha) → mitigação
* [ ] 8.3 LACUNAS registradas como riscos “descobrir/confirmar”

📝 **Observações:**

<!-- -->

</details>

---

## 🧩 9. COMPLETUDE GERAL

<details>
<summary>Verificações</summary>

* [ ] 9.1 Todos os arquivos `.md` do pacote gerados
* [ ] 9.2 Diagramas Mermaid renderizam corretamente no GitHub
* [ ] 9.3 Linguagem clara e aderente ao Guardrails Araquem v2.1.1
* [ ] 9.4 Nenhum trecho contém especulação ou refatoração sugerida

📝 **Observações:**

<!-- -->

</details>

---

## 📋 **RESUMO FINAL**

| Categoria     | Itens | Situação |
| ------------- | ----- | -------- |
| ✅ Confirmados |       |          |
| ❌ Divergentes |       |          |
| 🕳️ Lacunas   |       |          |

🗂️ *Salve este resumo como `docs/VALIDACAO_ARQUITETURA_M10.1.md` após concluir todas as marcações.*

