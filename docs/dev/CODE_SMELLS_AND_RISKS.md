# Araquem — Code Smells, Riscos e Débitos Técnicos

## 🔥 Alta severidade (impacta previsibilidade M10)
1. **Funções monolíticas no endpoint `/ask`**
   - `app/api/ask.py` define `ask()` com ~320 linhas, misturando planejamento, cache, narrativa e analytics.
   - Risco: difícil instrumentar shadow mode do Narrator sem duplicar lógica; alto acoplamento com políticas de cache e explain.
2. **`Orchestrator.route_question` excessivamente grande**
   - Mistura gating, cache de métricas, execução SQL, formatação e telemetria (~400 linhas).
   - Erros propagam silenciosamente (ex.: cache miss ignora falhas), tornando testes pontuais complexos.
3. **Dependência direta de arquivos YAML sem validação centralizada**
   - `app/builder/sql_builder`, `app/planner/planner`, `app/cache/rt_cache`, `app/planner/param_inference` leem YAMLs via `load_yaml_cached` e assumem estrutura.
   - Um YAML inválido derruba o fluxo em runtime (ValueError ou retorno `{}` silencioso), sem camada de validação única.
4. **Duplicidade de inferência de parâmetros**
   - `infer_params` é chamado tanto no endpoint quanto no orchestrator, com efeitos colaterais em métricas de cache.
   - Divergência futura entre os dois contextos pode gerar inconsistência de `facts` vs SQL executado.
5. **Inserção em `explain_events` dentro do endpoint**
   - `app/api/ask` abre conexão `psycopg` diretamente e insere na tabela, ignorando falhas (apenas métrica de erro).
   - Falhas silenciosas geram lacunas de auditoria; lógica deveria residir em gateway único e resiliente.

## 🔶 Severidade média
1. **Acoplamento forte Planner ↔ Observabilidade/RAG**
   - `planner.py` importa `emit_counter`, `histogram`, `OllamaClient`. Em ambientes sem RAG, exceções são tratadas, porém o módulo permanece responsável por telemetria.
   - Risco: testes locais precisam de mocks específicos; dificulta isolar algoritmo.
2. **`read_through` com lógica legada de limpeza**
   - Contém scanning de chaves (`legacy_cleanup_scan`) e guardas `hit_once/miss_once`. Essa lógica operacional pertence a camada de infraestrutura, mas hoje impacta toda leitura.
3. **Formatter silencioso**
   - `render_rows_template` retorna `""` em qualquer erro (template inexistente, exceção Jinja). Falhas passam despercebidas.
4. **Narrator fallback automático**
   - `_NARR` é instanciado com try/except amplo; qualquer erro desabilita Narrator silenciosamente (`_NARRATOR_ENABLED=False`).
   - Sem observabilidade adicional, shadow mode pode ser desligado sem perceber.
5. **`app/utils/filecache` sem TTL**
   - Cache em memória depende apenas de mtime; mudanças externas não são detectadas se mtime não variar (ex.: copy sobre arquivo existente).
6. **Falta de tipagem explícita**
   - Grande parte das funções usa `Dict[str, Any]`, dificultando validação estática. Exemplos: `orchestrator.route_question`, `planner.explain`.

## ⚠️ Severidade baixa
1. **Falta de docstrings/módulos comentados**
   - Vários arquivos (ex.: `app/orchestrator/routing.py`, `app/cache/rt_cache.py`) carecem de docstrings formais apesar da complexidade.
2. **Repetição de lógica de geração de cache key**
   - Endpoint `/ask` reconstrói identificadores para cache mesmo após orchestrator fazer o mesmo.
3. **Comentários defasados**
   - `app/api/ask.py` contém comentários sobre "Narrator M10" e "arquivo novo" que já estão na base, gerando ruído.
4. **Pontos não testados explicitamente**
   - Caminhos de erro do Narrator (`_NARR.render` exceptions) apenas registram métricas; sem testes automatizados conhecidos.
5. **Variáveis mutáveis em fluxo crítico**
   - `facts` e `meta_for_narrator` são dicts mutáveis compartilhados; mutações futuras podem impactar Narrator/Responder simultaneamente.

## Gargalos invisíveis potenciais
- **Latência encadeada**: sem cache, pipeline executa planner duas vezes (endpoint + orchestrator). Shadow mode vai duplicar trabalho do Narrator.
- **Falta de isolamento do cache**: se Redis indisponível, `read_through` lança exceção interrompendo resposta (não há fallback local).
- **Carga no banco**: `PgExecutor` executa queries com `autocommit=True` mas sem timeouts específicos; `connect_timeout` depende da DSN.

## Recomendações imediatas
- Refatorar `app/api/ask` e `app/orchestrator/routing` em etapas menores com contratos explícitos (ex.: separar builder call, cache policy, answer rendering).
- Implementar validação única dos YAMLs essenciais no bootstrap (`app/core/context`).
- Criar adaptador para persistência de explain analytics, removendo acesso direto a Postgres do endpoint.
- Introduzir tipos (`TypedDict`/Pydantic) para `plan`, `aggregates`, `results`, reduzindo riscos de chave errada.
