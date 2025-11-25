# Laudo Técnico — Loaders de Configuração Críticos (Narrator, Planner, RAG)

## 1. Escopo e Motivação
Loaders de configuração são superfície crítica porque determinam, em tempo de execução, como o `/ask` decide habilitar LLMs, RAG e thresholds. Antes do endurecimento, havia risco de *fallbacks* silenciosos (por exemplo, YAML ausente caindo em defaults implícitos), heurísticas embutidas em código e ausência de validação estrutural/tipagem — todos fatores que mascaram má configuração e dificultam observabilidade.

## 2. Mudanças Implementadas
### Narrator Policy Loader
- **Antes:** `_load_narrator_policy` aceitava YAML sem validação rígida e podia operar com estruturas malformadas, permitindo habilitação/desabilitação implícita do LLM.
- **Depois:** leitura de `data/policies/narrator.yaml` com validação de mapeamento, campos booleanos/inteiros/strings e retorno estruturado com `status` (`ok`, `missing`, `invalid`) e `error`. YAML ausente ou inválido resulta em modo degradado (LLM desabilitado) sem *fallback* silencioso. `Narrator` persiste `_policy_status`/`_policy_error`, usa apenas a policy validada e recorre a defaults determinísticos quando inválida, preservando previsibilidade do fluxo `/ask`. 【F:app/narrator/narrator.py†L304-L405】【F:app/narrator/narrator.py†L445-L503】

### Planner Thresholds / Context Policy
- **Antes:** carregamento de thresholds tolerava ausência/estruturas incorretas e não cacheava resultados, reabrindo YAML em cada requisição; política de contexto não expunha estado explícito.
- **Depois:** `_load_thresholds` falha rápido se `data/ops/planner_thresholds.yaml` estiver ausente ou malformado, valida blocos `planner.thresholds`/`planner.rag` e tipos numéricos via `_require_number` e `_require_positive_int`, além de cachear em `_THRESHOLDS_CACHE` para evitar reparse. `_load_context_policy` expõe `status`/`error`, trata arquivo ausente como `missing` e erro de parse como `invalid`, retornando contexto desabilitado com log — evitando heurísticas escondidas no explain do Planner. 【F:app/planner/planner.py†L22-L138】【F:app/planner/planner.py†L48-L139】

### RAG Policy / Index
- **Antes:** ausência ou corrupção da política de RAG podia passar despercebida, e o builder de contexto assumia presença do índice, potencialmente quebrando o `/ask`.
- **Depois:** `load_rag_policy` trata ausência de arquivo como RAG desabilitado (warning + `{}`) e considera YAML inválido como erro fatal (RuntimeError, sem *fallback*). `build_context` verifica a existência do índice antes da busca e, em falhas de I/O ou busca, retorna payload com `enabled=False` e `error` descritivo, mantendo o fluxo do `/ask` sem ocultar a falha. 【F:app/rag/context_builder.py†L19-L143】【F:app/rag/context_builder.py†L154-L269】

## 3. Cobertura de Testes
- `TestNarratorConfig`: cobre ausência de arquivo, YAML não-mapeamento, blocos malformados, tipos inválidos e caminho feliz de `_load_narrator_flags`, garantindo que políticas inválidas não habilitam Narrator silenciosamente. 【F:tests/dev/test_config_guardrails.py†L10-L83】
- `TestPlannerThresholds`: valida ausência de arquivo, YAML inválido, blocos obrigatórios faltantes, defaults incompletos, tipos/valores negativos e reutilização de cache, evitando thresholds heurísticos ou inconsistentes. 【F:tests/dev/test_config_guardrails.py†L84-L188】
- `TestContextPolicy`: assegura `status` explícito para ausência (`missing`), YAML inválido (`invalid` + `error`) e caminho feliz (`ok`). 【F:tests/dev/test_config_guardrails.py†L189-L234】
- `TestRagPolicyAndIndex`: garante que política ausente desabilita RAG de forma explícita, política inválida falha rápido e ausência do índice retorna erro controlado sem quebrar o `/ask`. 【F:tests/dev/test_config_guardrails.py†L235-L265】
- `tests/narrator/test_concept_mode.py`: permanece verde, confirmando que modos conceitual/entidade e integração Narrator + RAG/metrics seguem intactos após o endurecimento. 【F:tests/narrator/test_concept_mode.py†L13-L144】

Resultado executado previamente: `pytest -q tests/dev/test_config_guardrails.py tests/narrator/test_concept_mode.py` ⇒ 33 passed (~2–3s, host e Docker).

## 4. Avaliação de Risco Residual
Os loaders cobertos agora falham rápido ou expõem `status`/`error`, reduzindo substancialmente o risco de *fallbacks* silenciosos no `/ask` e no Narrator. Persistem riscos em loaders mapeados em `CONFIG_AUDIT_LOADERS.md` (p.ex. `context_manager`, `CachePolicies`, `load_ontology`), que ainda não possuem validação estrutural/tipagem equivalente.

## 5. Próximos Passos
- Endurecer `_load_entity_config` do Narrator para validar estrutura de `entity.yaml` e sinalizar erros em vez de retornar `{}` silenciosamente.
- Fortalecer inicialização de `CachePolicies.__init__` e loaders correlatos (p.ex. `context_manager`) com validação de mapeamentos obrigatórios.
- Revisar `load_ontology` para falhar rápido em ontologias ausentes/malformadas, alinhando-se ao comportamento adotado em thresholds e RAG.
- Priorizar os itens remanescentes listados em `CONFIG_AUDIT_LOADERS.md` para padronizar guardrails em toda a superfície de configuração.
