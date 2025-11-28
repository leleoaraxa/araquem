# Codex Prompts – Araquem Edition (Sirius v1.0)

Este documento define os prompts padronizados para uso com o Codex no contexto do Araquem,
seguindo o Guardrails Araquem v2.2.0 (sem heurísticas, sem hardcodes, YAML/SQL como fonte
de verdade).

Use estes modos como _contrato_ sempre que for pedir algo ao Codex.

---

## 1. Modo Curto e Objetivo (uso diário)

**Objetivo:** refatoração rápida, segura e determinística, sem invenções.

**Quando usar:** ajustes pequenos em arquivos específicos (ex.: `prompts.py`), quando você já
sabe exatamente o que quer.

```text
Refatore app/narrator/prompts.py para remover TODAS as heurísticas.
Use exclusivamente valores de data/policies/narrator.yaml.
Não invente regras, funções, variáveis ou textos.
Não modifique nada fora de prompts.py.
O comportamento deve ser 100% determinístico.

Saída: patch/diff Git pronto para commit.
```

---

## 2. Modo Ultra Restrito (Codex Mode – máxima segurança)

**Objetivo:** garantir conformidade rígida com o Guardrails, impedindo o Codex de “pensar demais”.

**Quando usar:** código crítico (Narrator, Planner, Builder, entidades sensíveis), onde qualquer
invenção é inaceitável.

```text
Tarefa: limpar heurísticas de app/narrator/prompts.py.

REGRAS ABSOLUTAS:
- ZERO heurística.
- ZERO inferência.
- ZERO criatividade.
- Não invente NADA.
- Não crie funções.
- Não altere assinaturas.
- Não modifique módulos externos.
- NÃO deduza nada que não esteja no data/policies/narrator.yaml.
- Se não estiver no YAML, assuma um valor vazio ou minimalista.

Saída: patch Git completo e seguro.
```

---

## 3. Modo Debug-Friendly (investigar antes de mexer)

**Objetivo:** entender o problema antes de refatorar.

**Quando usar:** quando você quer ver onde estão as heurísticas e como violam o Guardrails,
antes de deixar o Codex aplicar o patch.

```text
Etapa 1: Liste e explique TODAS as heurísticas existentes em app/narrator/prompts.py.
Etapa 2: Mostre como cada uma viola o Guardrails Araquem v2.2.0.
Etapa 3: Aguarde minha confirmação.
Etapa 4: Só então gere o patch removendo as heurísticas, usando apenas data/policies/narrator.yaml como fonte de verdade.

Regras:
- Nenhuma função nova.
- Nenhuma regra inventada.
- Não alterar assinaturas.
- Não modificar nenhum arquivo além de prompts.py.
```

---

## 4. Modo Auditoria (revisor técnico)

**Objetivo:** apenas inspecionar, sem mexer em nada.

**Quando usar:** quando você quer um diagnóstico do estado atual do arquivo.

```text
Realize auditoria completa em app/narrator/prompts.py:

- Encontre heurísticas
- Identifique comportamento implícito
- Liste regras não declaradas em YAML
- Aponte riscos de violação ao Guardrails Araquem v2.2.0

Não faça mudanças ainda.

Saída: relatório técnico somente.
```

---

## 5. Modo CI/CD (validação para PR/pipeline)

**Objetivo:** validar se o arquivo segue as políticas, sem gerar patch.

**Quando usar:** em revisões de PR ou scripts de automação.

```text
Valide se app/narrator/prompts.py está 100% em conformidade com:

1) data/policies/narrator.yaml
2) Guardrails Araquem v2.2.0
3) Zero heurística
4) Comportamento determinístico

Se houver violação, gere relatório técnico.
Não gere patches neste modo.
```

---

## 6. Modo Polícia Federal (ninguém passa sem justificar)

**Objetivo:** localizar qualquer linha “suspeita” e exigir justificativa.

**Quando usar:** quando você desconfia que já tem gambiarra ou heurística enfiada no meio.

```text
Inspecione app/narrator/prompts.py e identifique qualquer linha que:

- contenha heurística
- faça inferência
- altere comportamento sem backing do YAML
- introduza lógica “inteligente”

Para cada ocorrência:
- justifique por que é uma violação
- indique como corrigir
- não aplique a correção ainda
```

---

## 7. Modo Cirúrgico (alterar apenas o mínimo)

**Objetivo:** mudar o mínimo de linhas possível.

**Quando usar:** quando o arquivo é sensível ou muito grande, e você quer patch pequeno.

```text
Refatore app/narrator/prompts.py removendo heurísticas com impacto mínimo.

Regras:
- máximo 3 a 5 linhas modificadas.
- NÃO reestruture blocos.
- NÃO mude assinaturas.
- NÃO modifique o fluxo do Narrator.
- SOMENTE alinhe ao data/policies/narrator.yaml.

Saída: patch Git minimalista.
```

---

## 8. Modo Tutor (explica linha por linha)

**Objetivo:** aprender com a mudança.

**Quando usar:** quando você quer entender o racional de cada alteração.

```text
Refatore app/narrator/prompts.py removendo heurísticas.
Para cada mudança:

- explique o motivo
- mostre o trecho original
- mostre o novo trecho
- referencie a parte relevante do data/policies/narrator.yaml
- referencie o Guardrails Araquem v2.2.0

Saída: relatório + patch Git.
```

---

## 9. Modo Sandbox (simular sem aplicar)

**Objetivo:** ver o plano de refatoração sem aplicar.

**Quando usar:** quando você quer avaliar o impacto antes do patch real.

```text
Simule a refatoração de app/narrator/prompts.py removendo heurísticas,
mas NÃO gere patch Git ainda.

Quero ver:
- o plano de modificação
- cada mudança proposta
- seu efeito final no fluxo
- mapeamento para data/policies/narrator.yaml

Somente simulação.
```

---

## 10. Modo Blindado (sem risco de acionar LLM/RAG)

**Objetivo:** garantir que o código final não crie caminhos para chamadas indevidas de LLM/RAG.

**Quando usar:** em camadas sensíveis (Narrator, RAG, Orchestrator).

```text
Refatore app/narrator/prompts.py removendo heurísticas
sem qualquer risco de acionar LLM, RAG ou Ollama.

Regras:
- Não gere chamadas a modelos.
- Não crie prompts dinâmicos.
- Não infira comportamentos.
- Use somente data/policies/narrator.yaml.

Saída: patch Git estritamente determinístico.
```

```

---

## 2️⃣ `data/policies/codex_prompts.yaml`

```yaml
terms:
  - name: "codex_prompts"
    kind: "policy"
    scope: "codex"
    version: 1

modes:
  curto_objetivo:
    description: "Uso diário, refatoração rápida e determinística."
    target_files:
      - "app/narrator/prompts.py"
    rules:
      - "remover heurísticas"
      - "usar apenas data/policies/narrator.yaml"
      - "não inventar funções, variáveis ou textos"
      - "não alterar outros arquivos"
      - "comportamento 100% determinístico"
    output: "git_diff"

  ultra_restrito:
    description: "Modo máximo de segurança, zero inferência."
    rules:
      - "nenhuma heurística"
      - "nenhuma inferência"
      - "nenhuma criatividade"
      - "não criar funções novas"
      - "não alterar assinaturas"
      - "não modificar módulos externos"
      - "usar exclusivamente valores definidos em YAML"
      - "se não estiver no YAML, assumir valor vazio ou minimalista"
    output: "git_diff"

  debug_friendly:
    description: "Primeiro audita, depois refatora."
    steps:
      - "listar e explicar heurísticas"
      - "relacionar violações ao Guardrails Araquem v2.2.0"
      - "aguardar aprovação humana"
      - "só então gerar patch de remoção"
    rules:
      - "não criar funções novas"
      - "não inventar regras"
      - "não alterar assinaturas"
      - "não modificar arquivos além do alvo"
    output: "relatorio + git_diff"

  auditoria:
    description: "Modo apenas diagnóstico, sem modificações."
    rules:
      - "identificar heurísticas"
      - "identificar comportamento implícito"
      - "listar regras não declaradas em YAML"
      - "apontar riscos de violação ao Guardrails"
      - "não gerar patches"
    output: "relatorio"

  ci_cd:
    description: "Validação para pipelines e PRs."
    rules:
      - "verificar conformidade com data/policies/*.yaml"
      - "verificar alinhamento ao Guardrails Araquem v2.2.0"
      - "garantir ausência de heurísticas"
      - "garantir comportamento determinístico"
      - "não gerar patches"
    output: "relatorio"

  policia_federal:
    description: "Inspeção agressiva em busca de gambiarras."
    rules:
      - "localizar linhas com heurística"
      - "localizar inferências sem backing em YAML"
      - "identificar lógica 'inteligente' não declarada"
      - "explicar por que cada ocorrência é violação"
      - "indicar como corrigir, sem aplicar"
    output: "relatorio"

  cirurgico:
    description: "Alterar o mínimo possível."
    rules:
      - "modificar no máximo 3 a 5 linhas"
      - "não reestruturar blocos"
      - "não mudar assinaturas"
      - "não modificar fluxo externo"
      - "somente alinhar ao YAML"
    output: "git_diff_minimal"

  tutor:
    description: "Explicar cada alteração para fins educativos."
    rules:
      - "para cada mudança, mostrar trecho original e novo"
      - "explicar o motivo da alteração"
      - "referenciar YAML e Guardrails"
    output: "relatorio + git_diff"

  sandbox:
    description: "Simular refatoração sem aplicar."
    rules:
      - "apenas descrever plano de mudanças"
      - "explicar efeitos no fluxo"
      - "mapear cada alteração para YAML correspondente"
      - "não gerar git_diff real"
    output: "plano_refatoracao"

  blindado:
    description: "Garantir que o código não crie vias para LLM/RAG indevidos."
    rules:
      - "não introduzir chamadas a modelos"
      - "não criar prompts dinâmicos adicionais"
      - "não inferir comportamentos não declarados"
      - "usar exclusivamente YAML como fonte de parâmetros"
    output: "git_diff"
```

---

## 3️⃣ `.vscode/codex.code-snippets` (VSCode)

```json
{
  "Codex - Modo Curto e Objetivo": {
    "prefix": "codexCurto",
    "body": [
      "Refatore app/narrator/prompts.py para remover TODAS as heurísticas.",
      "Use exclusivamente valores de data/policies/narrator.yaml.",
      "Não invente regras, funções, variáveis ou textos.",
      "Não modifique nada fora de prompts.py.",
      "O comportamento deve ser 100% determinístico.",
      "",
      "Saída: patch/diff Git pronto para commit."
    ],
    "description": "Prompt curto e objetivo para uso diário no Araquem."
  },

  "Codex - Modo Ultra Restrito": {
    "prefix": "codexUltra",
    "body": [
      "Tarefa: limpar heurísticas de app/narrator/prompts.py.",
      "",
      "REGRAS ABSOLUTAS:",
      "- ZERO heurística.",
      "- ZERO inferência.",
      "- ZERO criatividade.",
      "- Não invente NADA.",
      "- Não crie funções.",
      "- Não altere assinaturas.",
      "- Não modifique módulos externos.",
      "- NÃO deduza nada que não esteja no data/policies/narrator.yaml.",
      "- Se não estiver no YAML, assuma um valor vazio ou minimalista.",
      "",
      "Saída: patch Git completo e seguro."
    ],
    "description": "Prompt ultra restrito, máxima segurança (sem invenção)."
  },

  "Codex - Modo Debug Friendly": {
    "prefix": "codexDebug",
    "body": [
      "Etapa 1: Liste e explique TODAS as heurísticas existentes em app/narrator/prompts.py.",
      "Etapa 2: Mostre como cada uma viola o Guardrails Araquem v2.2.0.",
      "Etapa 3: Aguarde minha confirmação.",
      "Etapa 4: Só então gere o patch removendo as heurísticas, usando apenas data/policies/narrator.yaml como fonte de verdade.",
      "",
      "Regras:",
      "- Nenhuma função nova.",
      "- Nenhuma regra inventada.",
      "- Não alterar assinaturas.",
      "- Não modificar nenhum arquivo além de prompts.py."
    ],
    "description": "Prompt para investigação antes da refatoração."
  },

  "Codex - Modo Auditoria": {
    "prefix": "codexAudit",
    "body": [
      "Realize auditoria completa em app/narrator/prompts.py:",
      "",
      "- Encontre heurísticas",
      "- Identifique comportamento implícito",
      "- Liste regras não declaradas em YAML",
      "- Aponte riscos de violação ao Guardrails Araquem v2.2.0",
      "",
      "Não faça mudanças ainda.",
      "",
      "Saída: relatório técnico somente."
    ],
    "description": "Prompt para diagnóstico sem alteração de código."
  },

  "Codex - Modo Blindado": {
    "prefix": "codexBlindado",
    "body": [
      "Refatore app/narrator/prompts.py removendo heurísticas",
      "sem qualquer risco de acionar LLM, RAG ou Ollama.",
      "",
      "Regras:",
      "- Não gere chamadas a modelos.",
      "- Não crie prompts dinâmicos.",
      "- Não infira comportamentos.",
      "- Use somente data/policies/narrator.yaml.",
      "",
      "Saída: patch Git estritamente determinístico."
    ],
    "description": "Prompt para garantir código sem vias indevidas para LLM/RAG."
  }
}
