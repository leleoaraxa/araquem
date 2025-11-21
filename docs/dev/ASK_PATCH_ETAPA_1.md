# 📄 ASK_PATCH_ETAPA_1.md

**Etapa 1 — Atualização e Consolidação da Documentação Oficial do Pipeline /ask**
**Status:** Document-only
**Guardrails Araquem v2.1.1: compliant**
**Código não deve ser modificado.**

---

## 1. Objetivo da etapa

Atualizar e consolidar a documentação do `/ask`:

* Garantir que **todo o fluxo pergunta → resposta** está descrito formalmente.
* Atualizar e corrigir o arquivo `docs/dev/RUNTIME_OVERVIEW.md`.
* Criar/atualizar o arquivo `docs/dev/ASK_PIPELINE_REFACTOR_PLAN.md` (já existente).
* Documentar *sem alterar nenhum arquivo Python*.

Esta etapa é **apenas documentação** — nenhum comportamento do runtime deve mudar.

---

## 2. Arquivos permitidos (whitelist estrita)

O Codex **só pode modificar**:

```
docs/dev/RUNTIME_OVERVIEW.md
docs/dev/ASK_PIPELINE_REFACTOR_PLAN.md
```

Nenhum outro arquivo deve ser alterado.

---

## 3. Arquivos proibidos (blacklist total)

O Codex **não pode modificar**:

* qualquer arquivo dentro de `app/`
* qualquer arquivo dentro de `data/`
* qualquer arquivo dentro de `scripts/`
* qualquer arquivo dentro de `tests/`
* qualquer Dockerfile
* qualquer configuração de Prometheus, Grafana, Tempo
* qualquer política YAML (`data/policies/*.yaml`)
* qualquer schema/contrato (`data/contracts/*.yaml`)
* qualquer template Jinja

Também é proibido:

❌ adicionar código Python
❌ remover código
❌ criar novos módulos
❌ alterar behavior de qualquer componente

Somente documentação textual.

---

## 4. Escopo específico do patch

### 4.1 Atualizar `docs/dev/RUNTIME_OVERVIEW.md`

O Codex deve:

1. Documentar o pipeline `/ask` **completo**, incluindo:

   * ask.py → planner → orchestrator → builder → executor → rows → presenter → narrator → resposta
2. Mapear todos os campos de `meta` atuais, incluindo:

   * `meta.planner`
   * `meta.orchestrator`
   * `meta.cache`
   * `meta.analytics`
   * `meta.rag`
   * `meta.narrator`
3. Incluir um **diagrama sequencial** (em Markdown ASCII), seguindo o padrão existente nos docs.
4. Adicionar uma seção **"Estrutura completa do payload de resposta do /ask (canônica)"** refletindo o JSON real observado no runtime.
5. Adicionar uma subseção explicando:

   * Onde cada parte do `meta` é construída.
   * Como os módulos se relacionam.
   * Quais políticas influenciam cada etapa (planner_thresholds, rag.yaml, narrator.yaml, cache.yaml).

### 4.2 Revisar e complementar `ASK_PIPELINE_REFACTOR_PLAN.md`

* Garantir consistência com o texto mais recente do plano.
* Ajustar seções de responsabilidades.
* Expandir a parte de orquestração e dependências.
* Incluir um resumo operacional para devs novos no projeto.

---

## 5. Regras de Estilo e Conformidade (obrigatórias)

O Codex deve seguir:

* **Guardrails Araquem v2.1.1**
* **Tom técnico e cirúrgico**, sem opiniões pessoais
* Linguagem objetiva, estilo dos documentos atuais do repositório
* Nada de alterar arquitetura, nada de sugerir código
* Documentação deve refletir *exatamente* o comportamento atual do sistema (código do zip)
* Pode adicionar diagramas, tabelas, bullets, mas sem alterar o sentido funcional

---

## 6. Critérios de aceitação

✔ Apenas os arquivos permitidos foram alterados
✔ O patch não altera nenhum arquivo de código
✔ O RUNTIME_OVERVIEW.md passa a refletir 100% do fluxo real
✔ O patch lista corretamente todos os campos de `meta`
✔ O plano de refatoração está coerente com o RUNTIME_OVERVIEW atualizado
✔ O estilo segue o padrão dos docs dev já presentes

---

## 7. Output esperado do PR do Codex

O Codex deve retornar:

* Um **diff unificado** apenas dos arquivos permitidos
* Sem criação de novos arquivos fora dessa whitelist
* Mensagem de commit no padrão Araquem:

```
docs(ask): update runtime overview and consolidate ask pipeline documentation
```

---

## 8. Observação final

Este é o *primeiro passo oficial* da estabilização do /ask.
Nenhum risco de impacto em produção deve ser introduzido.
Apenas documentação.

---

**Fim do arquivo.**
