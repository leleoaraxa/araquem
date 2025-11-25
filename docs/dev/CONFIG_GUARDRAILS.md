📘 CONFIG_GUARDRAILS.md

Contratos Rígidos de Configuração — Araquem v2.2.0

Local: docs/dev/CONFIG_GUARDRAILS.md
Escopo: Configs críticas, modo degradado e políticas YAML obrigatórias.


---

📌 Visão Geral

A partir do Guardrails Araquem v2.2.0, componentes centrais do pipeline NL→SQL→Presenter adotam contratos rígidos de configuração, removendo fallback silencioso e evitando heurísticas embutidas em código.

Este documento define:

Quais configs são críticas

Quando o sistema deve falhar (fail-fast)

Quando é permitido modo degradado

Como cada política expõe status e erros

Como validar e manter previsibilidade do /ask


Essas regras são vinculantes e auditáveis para todos os módulos.


---

1. 🟥 CONFIGURAÇÕES CRÍTICAS

Essas configs devem existir, ser válidas e tipadas corretamente.
Se estiverem ausentes ou malformadas → a aplicação não deve iniciar.

1.1 Narrator — data/policies/narrator.yaml

Contrato rígido

O arquivo deve existir.

O YAML deve ser um dict.

Deve conter um bloco narrator bem formado.

model deve ser string não vazia.

llm_enabled e shadow devem ser booleanos reais (não "true" etc.).


Comportamento

Em caso de erro → RuntimeError no import de _load_narrator_flags()
(API não sobe, fail-fast).


Por quê?

Garante que a camada M10/Narrator nunca opere em estado indeterminado.


---

1.2 Planner Thresholds — data/ops/planner_thresholds.yaml

Regras rígidas

O arquivo deve existir.

Estrutura obrigatória:

planner:
  thresholds:
    defaults:
      min_score: <num>
      min_gap: <num>
    apply_on: base|final
  rag:
    enabled: bool
    k: int>0
    min_score: num>=0
    weight: num>=0
    re_rank:
      enabled: bool
      mode: blend|additive|...
      weight: num>=0


Validações tipadas

k → inteiro positivo

todos os pesos/score → numéricos e não negativos

nada de bool disfarçado de número


Comportamento

Qualquer violação → ValueError ao carregar _load_thresholds().

Carregado uma vez e armazenado em cache em _THRESHOLDS_CACHE.



---

2. 🟧 CONFIGURAÇÕES IMPORTANTES (não críticas)

Essas configs podem faltar, mas devem sinalizar explicitamente o estado degradado.

2.1 Context Policy — data/policies/context.yaml

Contrato

Se o arquivo não existir → permitido, mas:

status: "missing"

planner.explain.context.status = "missing"


Se existir mas estiver inválido:

status: "invalid"

error: "<mensagem>"

nunca deve falhar silenciosamente



Nunca altera roteamento

Contexto é telemetria, não parte da decisão do planner.


---

3. 🟦 CONFIGURAÇÕES OPCIONAIS, MAS CONTROLADAS

3.1 RAG Policy — data/policies/rag.yaml

Regras

Se não existir:

Warning

RAG desabilitado: {}


Se existir e estiver inválido:

RuntimeError (falha de config explícita)



→ Isso diferencia “não quero RAG” de “RAG mal configurado”.

3.2 RAG Index — RAG_INDEX_PATH

Obrigações

Se rag.yaml habilitar RAG → o índice deve existir.


Se o índice faltar:

Fallback seguro:

{
  "enabled": false,
  "error": "FileNotFoundError..."
}

Logged with warning.


→ O sistema segue, mas RAG nunca é silenciosamente ignorado.


---

4. 🟩 COMO O STATUS É EXPERSSO NO /ask → explain

4.1 Narrator

Só aparece via meta.narrator já gerado pelo presenter.
Responsabilidade: validação rígida no carregamento.

4.2 Context Policy

Em /ask?explain=true:

"context": {
  "enabled": true|false,
  "planner_enabled": true|false,
  "entity_allowed": true|false,
  "status": "ok" | "missing" | "invalid",
  "error": "..." (se aplicável)
}

4.3 RAG

Em meta.rag:

enabled: false quando desabilitado por política

error: "<msg>" quando houver falha de store/embedding/index



---

5. 📐 PRINCÍPIOS DO GUARDRAILS v2.2.0

❌ Nunca:

Fallback silencioso

Heurísticas hardcoded em código

Defaults implícitos para configs centrais

Tentar “adivinhar” parâmetros faltantes


✅ Sempre:

Fail-fast para políticas críticas

Tipagem forte

Modos degradados explícitos

Logging completo com exc_info

Config-driven (YAML é a fonte da verdade)



---

6. 📌 CHECKLIST PARA FUTUROS MÓDULOS

Quando criar um novo módulo/config:

1. Classifique como:

Crítica (falhar se inválida)

Importante (modo degradado explícito)

Opcional (fallback controlado)



2. Pergunte:

“Se isso estiver inválido, o sistema deve subir?”

“Se seguir em modo degradado, o usuário fica seguro?”

“Quais campos de status devem ser expostos em explain?”



3. Implemente:

validação rígida

fallback declarado

logs estruturados

proibição de heurística em código




---

7. 📦 Referências cruzadas

app/api/ask.py – _load_narrator_flags

app/planner/planner.py – _load_thresholds, _load_context_policy

app/rag/context_builder.py – load_rag_policy, build_context

Guardrails Araquem v2.2.0 — diretiva “no heuristics / no silent fallback”



---
