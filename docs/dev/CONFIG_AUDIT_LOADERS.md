# Auditoria de Loaders de Configuração — Araquem

## 1. Sumário Executivo

- 16 loaders analisados em app/** e data/** que consomem YAML ou variáveis de ambiente para comportamento interno.
- Classificação sugerida: 6 críticas, 6 importantes e 4 opcionais.
- Maior risco em carregamentos de entidades/ontologia, thresholds do planner e policies do narrador/RAG quando caem em fallback silencioso ou sem validação de ambiente.

## 2. Tabela de Loaders Analisados

| Módulo | Função | Tipo de config | Classificação | Anti-padrões detectados | Observações |
| --- | --- | --- | --- | --- | --- |
| app/formatter/rows.py | render_rows_template | apresentação por entidade (entity.yaml) | 🟦 OPCIONAL | Fallback silencioso para `{}`/string vazia | Não sinaliza ausência ou schema inválido. |
| app/builder/sql_builder.py | _load_entity_yaml | entidade (entity.yaml) | 🟥 CRÍTICA | — | Falha rápida com log/exception se YAML ausente ou vazio. |
| app/rag/context_builder.py | load_rag_policy | política RAG (env RAG_POLICY_PATH) | 🟦 OPCIONAL | — | Fail-fast se arquivo existe e é inválido; trata ausência como RAG desabilitado. |
| app/rag/context_builder.py | build_context | índice RAG (env RAG_INDEX_PATH) | 🟦 OPCIONAL | Leitura de env sem validação de path/exists antes de uso do store | Trava só quando arquivo não existe; max_tokens/min_score toleram tipos inválidos. |
| app/orchestrator/routing.py | _load_entity_config | entity.yaml para roteamento/presenter | 🟧 IMPORTANTE | Hardened (status/log); fallback `{}` somente após warning/error | Riscos mitigados; mantém compatibilidade com chamadas antigas. |
| app/orchestrator/routing.py | _load_thresholds | thresholds do planner (env PLANNER_THRESHOLDS_PATH) | 🟧 IMPORTANTE | Reusa loader crítico do planner; logs de ausência/erro antes de fallback controlado | Fallback `{}` apenas após warning/error explícito; mantém compatibilidade do roteamento. |
| app/api/ask.py | _load_narrator_flags | narrador (data/policies/narrator.yaml) | 🟥 CRÍTICA | — | Fail-fast: exige arquivo e tipos corretos. |
| app/narrator/narrator.py | _load_narrator_policy | narrador (data/policies/narrator.yaml) | 🟧 IMPORTANTE | — | Fail-fast para arquivo ausente/YAML inválido e blocos malformados; usa apenas policies válidas, sem fallback silencioso. |
| app/planner/planner.py | _load_thresholds | thresholds + rag | 🟥 CRÍTICA | — | Fail-fast com validação de blocos/numéricos. |
| app/planner/planner.py | _load_context_policy | política de contexto | 🟧 IMPORTANTE | — | Implementa padrão de status/error; mantém defaults. |
| app/planner/param_inference.py | _load_yaml | param_inference.yaml | 🟦 OPCIONAL | Fallback `{}` sem log | Usado para defaults de agregação; ausência aceita. |
| app/context/context_manager.py | _load_policy | context.yaml | 🟧 IMPORTANTE | Hardened (status/log + DEFAULT_POLICY explícito) | Mantém merge com defaults; expõe policy_status/policy_error. |
| app/cache/rt_cache.py | CachePolicies.__init__ | cache.yaml | 🟧 IMPORTANTE | Hardened (status/log + validação de mapping) | Mantém `_policies` vazio em falha; status ok/missing/invalid. |
| app/observability/runtime.py | load_config | observability.yaml (env OBSERVABILITY_CONFIG) | 🟥 CRÍTICA | — | Fail-fast com mensagens claras para arquivo ausente/YAML inválido; logs estruturados e validação mínima de schema. |
| app/api/ops/quality.py | quality_report → _load_candidate | quality.yaml ou planner_thresholds.yaml | 🟧 IMPORTANTE | Erros acumulam, mas retorno 500 só se nenhum arquivo carregado | Leitura com fallback; ausência de schema não validada. |
| app/planner/ontology_loader.py | load_ontology | ontology/entity.yaml | 🟥 CRÍTICA | — | Fail-fast para arquivo ausente ou YAML inválido, com validação mínima de mapeamento e blocos usados pelo Planner. |

## 3. Casos de atenção (detalhados)

### 3.1 app/orchestrator/routing.py — função `_load_entity_config`

- **Tipo de config:** entity.yaml para ask/routing/presenter.
- **Classificação sugerida:** 🟧 IMPORTANTE.
- **Status:** Endurecido. Agora diferencia ausência (warning) de YAML inválido (error) e mantém fallback `{}` apenas após log explícito.

### 3.2 app/orchestrator/routing.py — função `_load_thresholds`

- **Tipo de config:** thresholds do planner (env `PLANNER_THRESHOLDS_PATH`).
- **Classificação sugerida:** 🟧 IMPORTANTE.
- **Status:** Endurecido. Agora delega parsing/validação para `planner._load_thresholds`, logando ausência (warning) ou YAML inválido (error com `exc_info`) antes de recorrer a fallback `{}` mínimo para manter compatibilidade do roteamento.

### 3.3 app/narrator/narrator.py — função `_load_narrator_policy`

- **Tipo de config:** política do Narrator.
- **Classificação sugerida:** 🟧 IMPORTANTE.
- **Status:** Endurecido. Falha rápido se o arquivo estiver ausente, se o YAML não for um mapeamento ou se o bloco `narrator`/campos obrigatórios (`model`, `llm_enabled`, `shadow`) estiverem malformados. Logs estruturados em português antes de levantar exceções; retorna apenas policies válidas sem fallback silencioso.

### 3.4 app/context/context_manager.py — função `_load_policy`

- **Tipo de config:** política de contexto (planner/narrator).
- **Classificação sugerida:** 🟧 IMPORTANTE.
- **Status:** Endurecido. Implementa status ok/missing/invalid, valida mapeamentos básicos, loga warning/error e expõe `policy_status`/`policy_error` preservando `DEFAULT_POLICY` como rede de segurança.

### 3.5 app/cache/rt_cache.py — método `CachePolicies.__init__`

- **Tipo de config:** política de cache.
- **Classificação sugerida:** 🟧 IMPORTANTE.
- **Status:** Endurecido. Diferencia ausência (warning) de YAML inválido (error), valida mapeamentos e mantém `_policies` vazio em falha, com `_status`/`_error` para telemetria.

### 3.6 app/observability/runtime.py — função `load_config`

- **Tipo de config:** observability.yaml (tracing/metrics exporter).
- **Classificação sugerida:** 🟥 CRÍTICA.
- **Status:** Endurecido. Resolve caminho via env ou default com `Path`, falha rápida se arquivo estiver ausente ou YAML inválido e registra logs estruturados (com `exc_info` em parse). Valida blocos mínimos (`services.gateway.tracing/metrics`, `global.exporters.otlp_endpoint`) antes de devolver a config.

### 3.7 app/api/ops/quality.py — função interna `_load_candidate`

- **Tipo de config:** políticas de qualidade / thresholds.
- **Classificação sugerida:** 🟧 IMPORTANTE.
- **Problemas encontrados:**
  - Fallbacks múltiplos sem validação de schema; erros acumulados apenas em mensagem final.
  - Retorna `{}` em malformação parcial, possivelmente mascarando políticas críticas.
- **Recomendação futura:**
  - Validar estrutura (targets/quality_gates) antes de aceitar; expor status ok/missing/invalid.
  - Aderir ao padrão de fail-fast ou status explícito com telemetria.

### 3.8 app/planner/ontology_loader.py — função `load_ontology`

- **Tipo de config:** ontologia de intents/entidades.
- **Classificação sugerida:** 🟥 CRÍTICA.
- **Problemas encontrados:**
  - Sem validação de campos obrigatórios; defaults embutidos em código (`weights`, `token_split`).
  - Falha apenas se arquivo ausente; valores incorretos passam silenciosamente.
- **Recomendação futura:**
  - Validar schema completo (intents, tokens, phrases, entities) e tipos numéricos.
  - Remover defaults de negócio do código, movendo-os para YAML validado.

## 4. Conclusão

- Loaders alinhados aos guardrails: `_load_narrator_flags`, `_load_thresholds` (planner), `_load_context_policy` e `load_rag_policy` já incorporam fail-fast ou status/erro explícito.
- Principais candidatos a endurecimento: `_load_thresholds` do orchestrator, `_load_narrator_policy`, `CachePolicies.__init__`, `load_config` de observability e `load_ontology` (ontologia/entidades), por combinarem ausência de validação com fallbacks silenciosos ou falhas abruptas.
