# M13 – Mapeamento Técnico do Contexto Atual

## 1. Visão Geral do Contexto no Araquem
- O "contexto" corresponde à memória conversacional mantida por `ContextManager`, que encapsula a lista de `ConversationTurn` (papel, conteúdo, timestamp e `meta`).【F:app/context/context_manager.py†L29-L64】【F:app/context/context_manager.py†L114-L189】
- A instância canônica fica em `app/core/context.py` como `context_manager`, inicializada com backend in-memory e política carregada de `data/policies/context.yaml`. O recurso só surte efeito se `context.enabled` estiver ativo.【F:app/core/context.py†L9-L35】
- O payload externo do `/ask` não carrega contexto: o cliente fornece apenas `{question, conversation_id, nickname, client_id}` e nenhum campo de contexto é aceito ou retornado ao cliente.【F:app/api/ask.py†L107-L137】【F:app/api/ask.py†L358-L409】
- O servidor mantém o contexto por par `(client_id, conversation_id)`; cada turno é armazenado com essa chave e usado apenas internamente.【F:app/context/context_manager.py†L205-L246】

## 2. Fluxo Completo do Contexto no /ask
1. **Criação do contexto (registro do usuário):** Assim que `/ask` recebe a requisição, registra um turno `user` com pergunta, `intent`, `entity` e `request_id` no `ContextManager`.【F:app/api/ask.py†L112-L146】
2. **Planejamento (Planner) e orquestração:** O planner roda (`planner.explain`) e o Orchestrator (`route_question`) decide rota e monta `meta`, sem ler ou modificar contexto conversacional.【F:app/api/ask.py†L120-L198】【F:app/orchestrator/routing.py†L181-L368】【F:app/orchestrator/routing.py†L368-L598】
3. **Executor:** O executor SQL é chamado dentro do Orchestrator conforme necessidade; nenhuma chamada ao contexto conversacional ocorre nessa camada.【F:app/orchestrator/routing.py†L368-L598】
4. **Presenter (leitura do contexto):** Antes de acionar o Narrator, o Presenter carrega o histórico recente via `context_manager.load_recent` e converte para wire format, somente se o contexto estiver habilitado e permitido para a entidade. Esse histórico é adicionado ao `meta_for_narrator` sob a chave `history`.【F:app/presenter/presenter.py†L104-L158】【F:app/presenter/presenter.py†L203-L260】
5. **Resposta / Narrator:** O Narrator recebe o meta (com `history` quando disponível) para gerar texto. Mesmo com Narrator desligado, o Presenter segue o fluxo determinístico usando `legacy_answer`.【F:app/presenter/presenter.py†L158-L260】
6. **Registro do turno do assistant:** Após gerar a resposta (ou vazio quando unroutable), o `/ask` registra um turno `assistant` com a resposta final e metadados no `ContextManager`.【F:app/api/ask.py†L146-L199】【F:app/api/ask.py†L409-L439】

## 3. Estrutura Atual do Contexto
- Cada turno é um `ConversationTurn` com campos: `role` ("user"/"assistant"/"system"), `content` (texto), `created_at` (timestamp), `meta` (dict opcional).【F:app/context/context_manager.py†L29-L64】
- O histórico retornado por `ContextManager.to_wire` é uma lista de dicionários derivada dos atributos do dataclass.【F:app/context/context_manager.py†L247-L254】
- Não há campos extras como `last_ticker` ou `last_entity`; apenas os atributos listados acima compõem o contexto atual.【F:app/context/context_manager.py†L29-L64】

## 4. Persistência e Carregamento
- Backend atual: `InMemoryBackend`, que mantém os turns em um dicionário de processo; não há persistência entre processos e não usa Redis ou disco.【F:app/context/context_manager.py†L171-L213】
- Chave de armazenamento: string `${client_id}:${conversation_id}` gerada por `_key`, usada para `load` e `save`.【F:app/context/context_manager.py†L179-L213】
- Políticas: controladas por `data/policies/context.yaml`, com `enabled`, `max_turns`, `ttl_seconds`, `max_chars` e blocos específicos de planner/narrator. O carregamento mescla `DEFAULT_POLICY` e aplica fallback quando o arquivo está ausente ou inválido.【F:app/context/context_manager.py†L66-L159】
- Corte e TTL: `load_recent` filtra turns expirados por TTL e limita a `max_turns`; `append_turn` reaplica as mesmas políticas antes de salvar.【F:app/context/context_manager.py†L215-L246】【F:app/context/context_manager.py†L228-L246】
- Persistência ocorre somente se `context.enabled` for verdadeiro; caso contrário, operações são no-op e retornam listas vazias.【F:app/context/context_manager.py†L202-L246】

## 5. Papel do Presenter e History
- O Presenter monta `meta_for_narrator` com intent/entity/compute e injeta `history` apenas quando o `ContextManager` está habilitado e a política do narrador permite a entidade (`narrator_allows_entity`).【F:app/presenter/presenter.py†L104-L158】【F:app/context/context_manager.py†L138-L169】
- O histórico injetado é a lista serializada de turns (`ContextManager.to_wire`).【F:app/presenter/presenter.py†L138-L158】【F:app/context/context_manager.py†L247-L254】
- Quando o Narrator está desligado ou falha, o Presenter mantém `legacy_answer` como resposta final; o histórico não altera o payload externo nem muda o caminho determinístico.【F:app/presenter/presenter.py†L158-L260】

## 6. Imutabilidade do Payload do /ask
- O contrato de entrada aceita exclusivamente `question`, `conversation_id`, `nickname` e `client_id` (modelo `AskPayload`).【F:app/api/ask.py†L99-L137】
- A resposta enviada ao cliente contém `status`, `results`, `meta`, `answer`; nenhum dado de contexto (turns, history) é exposto ou anexado ao payload externo.【F:app/api/ask.py†L358-L439】
- O histórico e metadados do contexto são usados apenas internamente (Planner/Presenter/Narrator) e não retornam ao cliente.【F:app/presenter/presenter.py†L138-L260】

## 7. Limitações Atuais
- O Orchestrator, Planner e executor não consultam o contexto conversacional; decisões de rota e inferência de parâmetros não consideram turns anteriores.【F:app/orchestrator/routing.py†L181-L368】【F:app/orchestrator/routing.py†L368-L598】
- O `ContextManager` usa somente backend in-memory; não há persistência compartilhada nem integração com Redis/DB.【F:app/context/context_manager.py†L171-L213】
- O contexto não participa de `param_inference`, não altera thresholds ou gating, e não modifica o builder/formatter.【F:app/presenter/presenter.py†L158-L260】【F:app/orchestrator/routing.py†L181-L368】
- O histórico não é usado para alterar rota do Planner nem para inferir ticker ou entidades automaticamente; apenas registro e fornecimento ao Narrator quando habilitado.【F:app/presenter/presenter.py†L104-L158】【F:app/api/ask.py†L112-L199】

## 8. Possíveis Pontos de Integração para M13 (sem implementação)
- `ContextManager` expõe `load_recent` e `to_wire`, já usados no Presenter; esses pontos podem receber novos campos como `last_reference` no futuro.【F:app/context/context_manager.py†L215-L254】【F:app/presenter/presenter.py†L104-L158】
- `present` recebe `identifiers` e `aggregates` separados do contexto; o fluxo mostra onde `param_inference` poderia ler histórico se futuramente for conectado (hoje não lê).【F:app/presenter/presenter.py†L80-L157】
- O Orchestrator roda antes do Presenter e poderia acessar o `context_manager` (a instância está disponível em `app/core/context.py`), mas atualmente não faz leitura; este é um ponto potencial para enriquecimento sem alterar o contrato externo.【F:app/core/context.py†L9-L35】【F:app/orchestrator/routing.py†L181-L368】
