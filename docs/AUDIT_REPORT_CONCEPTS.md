# Auditoria fria: `data/concepts` × esteira `/ask`

> **Scope:** leitura do repositório, sem suposições externas.

## 0) Inventário cirúrgico de `data/concepts/`

**Árvore (até 4 níveis)**
```
data/concepts
data/concepts/concepts-carteira.yaml
data/concepts/concepts-macro.yaml
data/concepts/concepts-risk.yaml
data/concepts/concepts-fiis.yaml
data/concepts/concepts-risk-metrics-methodology.yaml
data/concepts/catalog.yaml
data/concepts/concepts-macro-methodology.yaml
```

**Tabela — arquivos**

| path | tipo | função (1 frase) | evidência |
| --- | --- | --- | --- |
| data/concepts/catalog.yaml | YAML | Catálogo de domínios/arquivos de conceitos e seções de conteúdo. | data/concepts/catalog.yaml:1-51 (lista arquivos e seções por domínio). |
| data/concepts/concepts-fiis.yaml | YAML | Glossário conceitual por seção para FIIs (identidade, preços, risco, etc.). | data/concepts/concepts-fiis.yaml:1-168 (sections/concepts). |
| data/concepts/concepts-risk.yaml | YAML | Glossário conceitual de risco (Sharpe, Treynor, drawdown, etc.). | data/concepts/concepts-risk.yaml:1-176 (concepts). |
| data/concepts/concepts-macro.yaml | YAML | Glossário macroeconômico (índices B3, juros, inflação, câmbio). | data/concepts/concepts-macro.yaml:1-108 (concepts). |
| data/concepts/concepts-carteira.yaml | YAML | Glossário de carteira do investidor e privacidade. | data/concepts/concepts-carteira.yaml:1-100 (concepts). |
| data/concepts/concepts-macro-methodology.yaml | YAML | Metodologia textual de indicadores macro (fontes, limitações). | data/concepts/concepts-macro-methodology.yaml:1-74 (methodology). |
| data/concepts/concepts-risk-metrics-methodology.yaml | YAML | Metodologia textual de métricas de risco. | data/concepts/concepts-risk-metrics-methodology.yaml:1-71 (abordagem/metricas). |

**Checklist (status)**
- [x] Inventário completo da pasta `data/concepts` (status: **USED** em embeddings; **NOT_USED** direto no runtime de templates). Ver seções 2–3.

---

## 1) Quem escreve em `data/concepts/` (pipelines de geração/ingestão)

**Comandos executados (como solicitado):**
- `rg -n "data/concepts" -S .`
- `rg -n "concepts" -S app scripts data docs`
- `rg -n "index_concepts|concepts_index|concept" -S .`

**Achados relevantes (writer vs reader)**

1. **Writer indireto (gera embeddings a partir de `data/concepts`)**
   - `scripts/embeddings/embeddings_build.py` lê `data/embeddings/index.yaml` e gera `data/embeddings/store/embeddings.jsonl` + `manifest.json`. O index inclui `data/concepts/*.yaml`, portanto esses arquivos são **fontes** para embeddings. (scripts/embeddings/embeddings_build.py:85-215 + data/embeddings/index.yaml:17-45).
   - **Quando roda:** script manual/CLI de build (não automático). O próprio script é CLI e escreve o índice no diretório de saída (scripts/embeddings/embeddings_build.py:1-220).

2. **Reader/diagnóstico (auditoria)**
   - `scripts/dev/entities_audit.py` inclui `data/concepts/*.yaml` na coleta de arquivos do bloco “narrator_files”, portanto lê/varre conceitos para auditoria. (scripts/dev/entities_audit.py:222-239).
   - **Quando roda:** script manual de auditoria (não automático).

3. **Sem writers diretos para `data/concepts/`**
   - Não há scripts que **gerem** YAMLs em `data/concepts/` no runtime; esses arquivos são tratados como conteúdo estático.

**Checklist (status)**
- [x] Writers/Readers identificados (status: **USED** como fonte de embeddings; **NOT_USED** como saída de pipeline).

---

## 2) Quem lê `data/concepts/` durante `/ask` (runtime path real)

### 2.1 Ponto de entrada `/ask` → Planner → Orchestrator → Presenter → Narrator

**Callgraph textual (hot path):**
1. **Endpoint** `/ask`: `app/api/ask.py` chama `planner.explain(...)` → `orchestrator.prepare_plan(...)` → `orchestrator.route_question(...)`. (app/api/ask.py:194-429).
2. **Orchestrator** monta `meta` e sempre injeta `meta["rag"]` via `build_rag_context(...)`. (app/orchestrator/routing.py:1023-1114).
3. **Presenter** recebe `meta`/`results` e, se não houver `meta["rag"]`, chama `build_context(...)`. Em seguida monta `meta_for_narrator` e passa `rag` para o Narrator. (app/presenter/presenter.py:352-490).
4. **Narrator** consome `meta["rag"]` para decidir chunks e modos (concept/data) e integrar texto do RAG em modo conceitual. (app/narrator/narrator.py:1000-1237).

**Hot path vs optional:**
- **Hot path:** `build_rag_context` é sempre chamado no `orchestrator.route_question`, mas a política pode desabilitar o RAG e retornar `enabled: false`. (app/orchestrator/routing.py:1053-1075 + app/rag/context_builder.py:231-251).
- **Optional:** se a policy bloquear o RAG por intent/entity, o RAG não consulta embeddings. (app/rag/context_builder.py:71-90, 231-251).

### 2.2 Existe leitura direta de `data/concepts/` no runtime `/ask`?

- **Único leitor direto** é o fallback de templates legado: `app/templates_answer/__init__.py` procura `data/concepts/<entity>_templates.md`. (app/templates_answer/__init__.py:9-22).
- **Evidência de potencialmente morto:** não há arquivos `*_templates.md` em `data/concepts/` (comando `rg --files -g '*_templates.md' data/concepts` não retornou resultados). **Status:** potencialmente morto no runtime.

**Checklist (status)**
- [x] `/ask` mapeado até Planner/Orchestrator/Presenter/Narrator (status: **USED**).
- [x] Leitura direta de `data/concepts/` no runtime: apenas template legado; sem arquivos → **NOT_USED** efetivo.

---

## 3) Relação entre `data/concepts/` e `data/embeddings/`

**Resposta curta:** `data/concepts/` **alimenta** o índice de embeddings; o runtime usa **apenas** o store gerado (`embeddings.jsonl`), não abre os YAMLs diretamente.

**Evidências:**
- `data/embeddings/index.yaml` inclui explicitamente todos os arquivos `data/concepts/*.yaml` como fontes. (data/embeddings/index.yaml:17-45).
- `data/embeddings/store/manifest.json` confirma que o store contém docs com `path` em `data/concepts/...`. (data/embeddings/store/manifest.json:8-87).
- Runtime do RAG carrega o store a partir de `RAG_INDEX_PATH` e consulta vetores via `EmbeddingStore` (app/rag/context_builder.py:15-338; app/rag/index_reader.py:31-84).

**Conclusão da seção:**
- `data/concepts/` → **index.yaml** → **embeddings.jsonl** → **/ask via RAG** (se policy habilitar). Esse é o único acoplamento funcional explícito.

**Checklist (status)**
- [x] Relação concepts → embeddings mapeada (status: **USED** via index/store).

---

## 4) Flags/policies que podem desabilitar o uso

**Policies que governam RAG e modos conceituais**
- `data/policies/rag.yaml` define `routing.deny_intents` e declara coleções `concepts-*` por entidade; notas dizem que o RAG permanece efetivamente desligado sem intents elegíveis. (data/policies/rag.yaml:29-90).
- `data/policies/narrator.yaml` define `prefer_concept_when_no_ticker`, `rag_fallback_when_no_rows` e `concept_with_data_when_rag` (default e por entidade). (data/policies/narrator.yaml:40-124).
- `app/narrator/narrator.py` aplica essas flags e ativa o **concept_mode** quando apropriado (com ou sem RAG). (app/narrator/narrator.py:1049-1237).

**Env vars relevantes**
- `RAG_POLICY_PATH` e `RAG_INDEX_PATH` (apontam para `data/policies/rag.yaml` e `data/embeddings/store/embeddings.jsonl`). (app/rag/context_builder.py:15-16).
- `FILECACHE_DISABLE` controla cache de YAML/JSONL e embedding store (app/utils/filecache.py:12-116).

**Checklist (status)**
- [x] Flags/policies listadas (status: **USED** quando `rag.yaml` e narrator policy habilitam; **NOT_USED** se bloqueadas).

---

## 5) Evidência de cobertura por testes e diagnósticos

**Testes**
- `tests/narrator/test_concept_mode.py` valida `concept_mode` e uso de chunk de RAG no Narrator (meta.rag), mas **não** valida presença/estrutura de `data/concepts/`. (tests/narrator/test_concept_mode.py:13-243).

**Diagnósticos/scripts**
- `scripts/embeddings/embeddings_health_check.py` valida consistência do `embeddings.jsonl` vs `manifest.json` (não abre diretamente `data/concepts/`, mas falha se o store estiver inconsistente). (scripts/embeddings/embeddings_health_check.py:1-129).

**Se eu quebrar `data/concepts` agora, algo falha?**
- **/ask runtime:** não lê YAMLs de `data/concepts` diretamente; só o store de embeddings é lido. (app/rag/context_builder.py:271-339; app/templates_answer/__init__.py:9-26).
- **Build de embeddings:** `embeddings_build.py` **pula** arquivos ausentes (`path` não encontrado) e segue; isso reduz cobertura no store, mas não quebra o runtime. (scripts/embeddings/embeddings_build.py:123-135).

**Checklist (status)**
- [x] Testes/diagnósticos listados (status: **USED** para Narrator/RAG; **NOT_USED** para validar `data/concepts` diretamente).

---

## 6) Conclusão objetiva: utilidade real hoje

**Veredito por tópico**

1. **`data/concepts/` é USED no `/ask`?**
   - **Status:** **USED (indireto/condicional)**.
   - **Evidência:** `/ask` sempre monta `meta.rag` e consulta `embeddings.jsonl` quando policy permite; o store contém docs com `path` em `data/concepts`. (app/orchestrator/routing.py:1053-1075 + app/rag/context_builder.py:231-339 + data/embeddings/store/manifest.json:8-87).
   - **Condição:** depende de `data/policies/rag.yaml` (intents/entidades) e dos envs `RAG_POLICY_PATH`/`RAG_INDEX_PATH`. (data/policies/rag.yaml:29-90; app/rag/context_builder.py:15-16).

2. **Uso direto de YAMLs `data/concepts/*.yaml` no runtime**
   - **Status:** **NOT_USED** (exceto fallback legado de templates, sem arquivos presentes).
   - **Evidência:** único leitor direto é o fallback `data/concepts/<entity>_templates.md` (não existem arquivos). (app/templates_answer/__init__.py:9-26).

3. **“Só indexa e nunca é usado”?**
   - **Status:** **DEPENDE**. O store gerado é consumido pelo RAG quando habilitado, mas `rag.yaml` possui bloqueios de intents e nota de uso restrito. (data/policies/rag.yaml:29-90; app/rag/context_builder.py:71-90).

4. **Candidatos a remoção/merge/renomeação**
   - **Potencialmente mortos:** fallback de `data/concepts/*_templates.md` (não há arquivos). (app/templates_answer/__init__.py:9-26 + ausência confirmada por `rg --files -g '*_templates.md' data/concepts`).
   - **Risco:** remover o fallback só afeta casos onde `data/entities/<entity>/template.md` ou `templates.md` não existam, mas esse fallback está legado e sem uso atual.

**Checklist (status)**
- [x] Veredito por tópico (status: **USED** via embeddings store; **NOT_USED** direto no runtime).

---

## 7) Base para refatoração grande (diagnóstico, sem implementar)

**Onde encaixaria no estado atual**
- **Planner/Orchestrator:** roteamento por intent/entity; definir novas entidades/intents para “institucional”, “suporte/ajuda”, “uso da plataforma” e “chit-chat”. (app/api/ask.py:237-428 + app/orchestrator/routing.py:1023-1114).
- **RAG:** ampliar `rag.yaml` e `data/embeddings/index.yaml` para novas coleções (conceitos/institucional/suporte/chitchat) com novos documentos. (data/policies/rag.yaml:29-90; data/embeddings/index.yaml:17-45).
- **Narrator:** `prefer_concept_when_no_ticker` e `concept_with_data_when_rag` já oferecem hooks para respostas conceituais (app/narrator/narrator.py:1049-1237; data/policies/narrator.yaml:60-124).
- **Presenter:** ponto de acoplamento para injetar `meta.rag` no Narrator e fallback determinístico. (app/presenter/presenter.py:352-490).

**Lacunas observáveis (sem conjectura arquitetural)**
- **Sem configuração explícita** em `rag.yaml` para domínios institucionais/suporte/chitchat; hoje só há coleções `concepts-*` e entidades macro default. (data/policies/rag.yaml:65-90).
- **Sem templates legados** em `data/concepts/*_templates.md` para uso direto no Presenter. (app/templates_answer/__init__.py:9-26).

**Checklist (status)**
- [x] Mapa de encaixe e lacunas (status: **UNKNOWN** para novos domínios até criação de intents/coleções).
