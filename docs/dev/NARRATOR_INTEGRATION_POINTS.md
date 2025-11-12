# Araquem — Pontos de Integração do Narrator

## 1. Onde os facts estruturados estão disponíveis
- **Fonte primária:** `app/orchestrator/routing.route_question` retorna `results` (dict) e `meta['aggregates']`, além de `identifiers` locais (não retornados explicitamente hoje).
- **No endpoint `/ask`:** após chamar `orchestrator.route_question`, o código monta:
  ```python
  facts = {
      "result_key": result_key,
      "rows": rows,
      "primary": rows[0] if rows else {},
      "aggregates": agg_params,
      "identifiers": identifiers,
      "ticker": primary.get("ticker") or identifiers.get("ticker"),
      "fund": primary.get("fund"),
  }
  ```
  Estes dados já estão formatados (`rows` passam por `render_rows_template`/`format_rows`).

## 2. Onde a resposta final é montada hoje
- `legacy_answer = render_answer(entity, rows, identifiers, aggregates)`
- `rendered_response = render_rows_template(entity, rows)` (não enviado ao cliente, mas usado como baseline).
- `final_answer` inicializado com `legacy_answer` e possivelmente sobrescrito por `Narrator.render`.
- `payload_out['answer'] = final_answer`.

## 3. Funções atuais relevantes
- `app.responder.render_answer`: gera texto determinístico baseado em templates Markdown.
- `app.formatter.render_rows_template`: gera Markdown a partir de templates Jinja declarativos.
- `app.narrator.narrator.Narrator.render`: produz narrativa LLM com fallback seguro.

## 4. Candidatos a ponto de acoplamento
| Ponto | Descrição | Prós | Contras |
| --- | --- | --- | --- |
| **A. Dentro de `app/api/ask` (atual)** | Após montar `facts`, antes de `final_answer`. | Já possui todos os dados, inclui métricas e controle de feature flag. | Endpoint fica sobrecarregado; difícil reutilizar em outros canais (WhatsApp/Web). |
| **B. Após `orchestrator.route_question` (novo serviço de apresentação)** | Criar função `present_answer(entity, rows, identifiers, aggregates, plan, narrator_opts)` em módulo dedicado. Endpoint apenas delega. | Permite reutilizar para Narrator/Responder, injeta métricas em um lugar, facilita shadow mode. | Exige mover lógica atual (Responder + Narrator) e tratar dependência de `render_rows_template`. |
| **C. Dentro do Orchestrator** | Fazer orchestrator retornar também `answer` textual. | Centraliza pipeline completo; garante que qualquer consumidor (API, CLI) receba resposta final. | Mistura responsabilidades core (dados) com apresentação; orquestrador teria que conhecer Narrator/Responder. |
| **D. Camada pós-formatter** | Criar adaptador que receba `results` + `meta` e devolva `answer`/`meta.narrator`. | Mantém orchestrator puro, favorece plug de múltiplos canais. | Necessário definir contrato estável `Facts` (TypedDict/Pydantic) e mover geração de `facts`. |

## 5. Melhor ponto sugerido
- **Opção D (camada pós-formatter dedicada)**
  - **Justificativa técnica:**
    - `orchestrator.route_question` já produz dados normalizados. Extraindo a montagem de `facts` e decisão Narrator/Responder para função dedicada, preservamos core puro e evitamos duplicação em outros endpoints.
    - Shadow mode pode ser habilitado neste adaptador, desacoplado da API HTTP.
    - Permite acoplar novos canais (WhatsApp, dashboards) apenas chamando essa camada.
  - **Requisitos:**
    - Definir estrutura canônica `FactsPayload` com `rows`, `aggregates`, `identifiers`, `planner`.
    - Expor função `generate_answer(question, plan, orchestrator_output, narrator_cfg)` que retorna `(answer, narrator_meta, legacy_answer, rendered_template)`.
    - Endpoint `/ask` passaria a apenas serializar resposta e anexar `narrator_meta`.

## 6. Responsabilidades propostas
| Componente | Hoje | Visão futura |
| --- | --- | --- |
| **Formatter atual** | Renderiza rows (lista) + template Markdown Jinja. | Continua responsável por formatação determinística de dados tabulares. |
| **Narrator novo** | Classe `Narrator.render` chamada diretamente pelo endpoint. | Passa a ser acionado por camada de apresentação, recebendo `facts` enriquecidos e retornando texto + telemetria. |
| **Responder novo** | Função legada `render_answer`. | Evoluir para adaptador dentro da camada de apresentação; fornece baseline determinístico, fallback e variações por canal. |

## 7. Funções a serem chamadas na integração futura
- `orchestrator.route_question(question, explain)` → mantém contrato de dados.
- `format_rows` / `render_rows_template` já são usados; camada nova deve consumi-los como serviços.
- `Narrator.render` e `Responder.render_answer` devem ser encapsulados por nova função (ex.: `compose_answer`).
- `analytics.explain.explain` continuará sendo chamado pelo orchestrator; camada narrativa só consome `plan`/`meta` resultantes.

## 8. Rastreamento determinístico
- Todos os dados necessários para o Narrator estão disponíveis nos dicts `results`, `meta`, `identifiers`, `aggregates`. Registrar esses objetos antes de chamar LLM garante trilha de auditoria (podendo persistir JSON em storage).
- Evitar mutações posteriores: a camada proposta deve operar sobre cópias imutáveis (deepcopy) antes de entregar ao Narrator.

## 9. Integração do Responder (Markdown/HTML/WhatsApp)
- Estruturar adaptador com assinatura:
  ```python
  def present(question: str, *, plan: Dict[str, Any], orchestrator_output: Dict[str, Any], channel: str, narrator: Optional[Narrator]) -> PresentResult
  ```
  onde `PresentResult` contém `answer`, `legacy_answer`, `rendered_template`, `narrator_meta`, `facts` normalizados.
- Para canais diferentes:
  - **Markdown (web/app):** usar `render_rows_template` + Narrator Markdown.
  - **HTML:** converter Markdown via renderer dedicado (não existente hoje).
  - **WhatsApp/SMS:** usar variantes de templates no `Responder` com placeholders simplificados.

## 10. Próximos passos imediatos
1. Mapear exatamente quais campos de `rows` cada template `templates.md` e `responses/*.md.j2` consome → garante que `facts` contenham esses atributos.
2. Criar contrato `Facts` declarativo (TypedDict ou Pydantic) compartilhado entre Formatter, Responder e Narrator.
3. Migrar geração de `facts` para função reutilizável (`build_facts(question, orchestrator_payload)`), mantendo rastreabilidade.
4. Instrumentar métrica dedicada `sirios_presenter_total` para monitorar camada futura.
