# Araquem — Roadmap Técnico (M9 → M10)

## Objetivo
Preparar a base atual para a camada Narrator/Responder (M10) mantendo previsibilidade e rastreabilidade.

## Fases e ações

### Fase 1 — Normalização de contratos (curto prazo)
1. **Catalogar contratos YAML essenciais**
   - Arquivos: `data/ontology/entity.yaml`, `data/entities/**/<entity>.yaml`, `data/ops/param_inference.yaml`, `data/policies/cache.yaml`.
   - Ação: criar validador único (script ou rotina de bootstrap) que garanta presença de chaves obrigatórias.
2. **Definir TypedDicts/Pydantic para payloads internos**
   - Arquivos: `app/planner/planner.py`, `app/orchestrator/routing.py`, `app/api/ask.py`.
   - Ação: introduzir modelos imutáveis (Pydantic `BaseModel` ou `TypedDict`) para `PlanResult`, `Aggregates`, `OrchestratorOutput`, `NarratorFacts`.
3. **Extrair construção de `facts` para função isolada**
   - Arquivo alvo: novo módulo em domínio de apresentação (ex.: `app/presenter/facts.py`).
   - Ação: mover lógica que gera `facts` e `meta_for_narrator` do endpoint para essa função, retornando estrutura imutável.

### Fase 2 — Camada Presenter (pré-M10)
1. **Criar adaptador `present(question, plan, orchestrator_output, narrator_cfg)`**
   - Arquivos: novo módulo `app/presenter/__init__.py` (a ser criado), atualizar `app/api/ask.py` para delegar.
   - Ação: encapsular chamadas a `render_answer`, `render_rows_template`, `Narrator.render` e construir `narrator_meta`.
2. **Instrumentar métricas específicas da camada**
   - Arquivos: `app/observability/metrics.py`, novo adaptador presenter.
   - Ação: registrar `sirios_presenter_total` (outcome=`legacy|narrator|error`) e histogram de latência.
3. **Implementar shadow mode configurável**
   - Arquivos: presenter, `app/narrator/narrator.py` (expor método estático p/ avaliar sem alterar resposta).
   - Ação: permitir habilitar Narrator apenas para telemetria, com persistência opcional dos textos.

### Fase 3 — Gateway Narrator/Responder (M10)
1. **Persistir facts/narrativas para auditoria**
   - Arquivos: presenter, nova tabela (ex.: `narrator_events`).
   - Ação: gravar `facts` + `meta` + texto Narrator quando shadow/ativo para rastreabilidade determinística.
2. **Suporte a múltiplos canais**
   - Arquivos: presenter + `app/responder` (refatorar para aceitar `channel`).
   - Ação: definir estratégia de templates por canal (Markdown, HTML, WhatsApp) e ajustar `render_answer` para selecionar fallback adequado.
3. **Feature flag granular**
   - Arquivos: presenter, `app/core/context` (para carregar config), `app/api/ask.py` (remover flags diretas).
   - Ação: centralizar leitura de flags (enabled/shadow/model) em config YAML/ENV e disponibilizar via presenter.

## Dependências entre tarefas
- Validação de YAML (Fase 1.1) → pré-requisito para Presenter consumir contratos confiáveis.
- Definição de modelos tipados (Fase 1.2) → necessária para presenter operar com dados seguros.
- Extração de `facts` (Fase 1.3) → base para Fase 2 (presenter).
- Persistência e canais (Fase 3) dependem da existência do presenter consolidado.

## Riscos e mitigação
| Risco | Impacto | Mitigação |
| --- | --- | --- |
| Mudança de contrato quebrar templates | Falha de resposta ao usuário | Testes automatizados que rendereizem todos os `templates.md` e `responses/*.md.j2` usando `Facts` tipado. |
| Narrator introduzir latência alta | Experiência ruim | Shadow mode com métricas, fallback deterministic e timeouts configuráveis no presenter. |
| Falha na gravação de auditoria | Perda de rastreabilidade | Utilizar fila assíncrona/retentativas; não bloquear resposta em caso de falha controlada. |
| YAML inválido em produção | Pipeline quebra | Validador de bootstrap + CI executando lint de contratos. |

## Estratégia de rollout (shadow → ativo)
1. **Shadow global**: presenter chama Narrator, registra `narrator_meta` porém mantém `answer = legacy`.
2. **Shadow segmentado**: habilitar por entidade/intenção conforme métricas de qualidade (`sirios_narrator_shadow_total`).
3. **Active w/ fallback**: permitir Narrator substituir `answer`, mantendo fallback determinístico em caso de erro/timeouts.
4. **Canal adicional**: introduzir canal secundário (ex.: WhatsApp) usando mesmo presenter, validando formato.

## Checklist de validação (quality + narrative gates)
- [ ] Todos os `data/entities/<entity>/<entity>.yaml` passam em validador (chaves obrigatórias presentes).
- [ ] `PlanResult` tipado cobre intents sem entidade (`None`).
- [ ] Presenter retorna `PresentResult` consistente com/sem Narrator.
- [ ] Métricas `sirios_presenter_total` e `sirios_narrator_latency_ms` monitoradas em Grafana.
- [ ] Shadow mode registra 100% das narrativas e latências sem erro.
- [ ] Auditoria: eventos gravados contêm hash dos facts e texto final.
- [ ] Testes automatizados rendereiam templates para cada entidade e comparam com baseline conhecido.

## Roadmap resumido (linha do tempo)
1. **Semana 1-2 (M9)**: validação de contratos, tipos canônicos, extração de facts.
2. **Semana 3-4 (M9)**: implementação do presenter com shadow mode e métricas.
3. **Semana 5 (M10 início)**: auditoria + persistência de narrativas, suporte a múltiplos canais.
4. **Semana 6 (M10)**: ativação controlada do Narrator, tuning de templates/canais, hardening de observabilidade.
