# Auditoria de Embeddings / Índices RAG (Araquem)

## Resumo executivo (para Leleo)
- Índice único `araquem-core` centraliza conceitos, contratos de entidades, policies e amostras de qualidade; vetores presentes e consistentes (184 chunks, dimensão 768) usando `nomic-embed-text`. 
- Manifesto e index.yaml alinham coleção/modelo, mas data de geração (2025-12-02) e `last_refresh_epoch` futuro sugerem carimbo artificial; não há trilhas operacionais claras de refresh.
- Cobertura privilegia FIIs e amostras de qualidade; RAG policy habilita apenas domínios macro/índices/moedas, criando desalinhamento entre coleções indexadas e rotas autorizadas.
- Textos de vários contratos YAML/JSON trazem pouco contexto (1–6 chunks), enquanto `routing_samples` domina (33 chunks), gerando distribuição desequilibrada e risco de hints enviesados.
- Não há coleções para conceitos críticos adicionais (ex.: overview FIIs, metodologia de indicadores) nem para dados reais de mercado; somente descrições declarativas.

## Relatório técnico de auditoria

### Stack de embeddings/RAG
- Construção do índice via `scripts/embeddings/embeddings_build.py` com chunking 1200/120 caracteres e uso de `OllamaClient` (`nomic-embed-text` por padrão). O script lê `data/embeddings/index.yaml`, gera `embeddings.jsonl` + `manifest.json` e inclui metadados de entidade a partir de tags `entity:*`. 【F:scripts/embeddings/embeddings_build.py†L11-L120】【F:scripts/embeddings/embeddings_build.py†L137-L201】
- Cliente de embeddings chama endpoints `/api/embed` e `/api/embeddings` do Ollama, garantindo alinhamento 1:1 e dimensionamento fornecido pelo modelo (vetores observados de 768 posições). 【F:app/rag/ollama_client.py†L12-L115】
- Consumo em runtime feito por `EmbeddingStore` (carrega JSONL e aplica busca por cosseno) e política RAG carregada de `data/policies/rag.yaml`. 【F:app/rag/index_reader.py†L25-L77】【F:app/rag/context_builder.py†L12-L83】【F:data/policies/rag.yaml†L1-L82】

### Mapa de `data/embeddings/*`
- `data/embeddings/index.yaml`: define coleção `araquem-core`, modelo `nomic-embed-text`, chunk 1200/120, filtros de hints e 52 documentos incluídos (conceitos, ontologia, entidades FIIs, policies, golden sets, projeções de qualidade e entidades macro/FX). 【F:data/embeddings/index.yaml†L1-L223】
- `data/embeddings/store/manifest.json`: confirma coleção/modelo, fonte `index.yaml`, timestamp futuro, e lista de documentos com contagem de chunks (total 184). Principais coleções: `routing_samples` (33 chunks), `ontology-entity` (16), `indicators-catalog` (15), `golden-m65-quality-yaml` (15), conceitos FIIs/risk (6 cada), macro (4), carteira (4), entidades FIIs/macro variando 2–6 chunks, projeções `q-*` com 1 chunk cada. 【F:data/embeddings/store/manifest.json†L1-L584】
- `data/embeddings/store/embeddings.jsonl`: 184 registros com vetores de dimensão 768; nenhum vetor vazio. Exemplo de chunk inclui texto bruto do YAML de catálogo de conceitos. 【F:data/embeddings/store/embeddings.jsonl†L1-L1】

### Checklist de qualidade
- **Integridade:** Arquivos `index.yaml`, `manifest.json` e `embeddings.jsonl` presentes e consistentes; vetores não vazios (0 vazios em 184). Timestamp de geração e `last_refresh_epoch` situados no futuro (2025-12-02 / 1764706644), indicando possível mock/manual, sem rastreabilidade operacional. 【F:data/embeddings/store/manifest.json†L1-L584】
- **Consistência com configs:** Modelo declarado nos três artefatos é `nomic-embed-text`; dimensão observada 768 compatível. Política RAG habilita apenas entidades macro/índices/moedas, mas índice contém majoritariamente FIIs e amostras de qualidade, sugerindo desalinhamento entre collections disponíveis e roteamento permitido. 【F:data/policies/rag.yaml†L29-L82】【F:data/embeddings/index.yaml†L18-L223】
- **Cobertura:** Coleções contemplam conceitos FIIs, risco, macro, carteira, indicadores, ontologia e múltiplas entidades FIIs + macro. Entretanto, política RAG bloqueia intents FIIs; macro recebe apenas `concepts-macro` (4 chunks). Não há embeddings para conteúdos operacionais adicionais (ex.: docs do planner/orchestrator, metodologias detalhadas). 【F:data/embeddings/index.yaml†L31-L207】【F:data/policies/rag.yaml†L29-L82】
- **Qualidade dos textos:** Textos são majoritariamente dumps de YAML/JSON e listas de samples; chunks curtos (1–6) para contratos de entidade e projeções `q-*` (1 linha cada), oferecendo pouco contexto sem narrativa. Dominância de `routing_samples` (33 chunks) pode enviesar hints. Exemplo de chunk mostra cabeçalho de caminho em vez de narrativa contextual. 【F:data/embeddings/store/embeddings.jsonl†L1-L1】【F:data/embeddings/store/manifest.json†L322-L520】
- **Distribuição:** Forte concentração em amostras de roteamento e artefatos de qualidade (q-*, golden) versus baixo volume para conceitos macro (4 chunks) e entidades críticas (2–5). Risco de recuperação priorizar samples/quality em detrimento de conhecimento de domínio real. 【F:data/embeddings/store/manifest.json†L322-L520】【F:data/embeddings/store/manifest.json†L545-L581】

## Plano de ação sugerido (sem código)

### Ações rápidas
1. **Corrigir metadados de geração**: ajustar pipeline para gravar `generated_at` e `last_refresh_epoch` reais a cada refresh; adiciona confiabilidade operacional e permite detectar índice stale. Afeta `scripts/embeddings/embeddings_build.py` e job de refresh.
2. **Alinhar collections com política RAG**: ou atualizar `rag.yaml` para permitir coleções FIIs essenciais, ou reduzir `index.yaml` para apenas coleções autorizadas; evita gastos de embedding desnecessários e resoluções vazias.
3. **Equalizar distribuição**: aumentar chunks para `concepts-macro` e indicadores (seções descritivas) para evitar que `routing_samples`/`golden` dominem scores; requer revisão de fontes em `data/concepts` e `data/raw/indicators`.

### Ações estruturais
1. **Cobertura de domínio macro e risco**: criar novos textos explicativos (NOVO: ex. `data/concepts/concepts-macro-methodology.yaml`) descrevendo série, periodicidade, fontes, limitações e exemplos; chunkar com 800–1000 chars/20% overlap para maximizar contexto sem ruído.
2. **Enriquecimento de entidades FIIs**: gerar narrativas resumidas para cada entidade FIIs (cadastro, preços, dividendos, risk) com propósito/colunas/cálculos; usar hints dedicados (NOVO: `data/entities/<entity>/hints.md`) ao invés de dumps YAML. Chunking 600–800 chars com overlap 100 para coerência.
3. **Higienização de amostras e qualidade**: deduplicar `routing_samples` e `q-*` removendo exemplos redundantes ou reformatando para frases completas; regra objetiva: excluir chunks com menos de 20 tokens ou compostos majoritariamente por listas/json cru.
4. **Health-check automatizado**: NOVO script (`scripts/embeddings/health_check.py`) para validar: (a) dimensão uniforme, (b) contagem por coleção vs. `manifest.json`, (c) presença de vetores vazios, (d) datas de refresh coerentes. Integração opcional em métricas existentes (`data/ops/observability.yaml`).
5. **Rastreabilidade de fonte SQL**: para entidades baseadas em dados numéricos, complementar embeddings com documentação operacional (tabelas, joins, periodicidade) derivada de ontologia/contratos, mantendo alinhamento com guardrails de não usar heurísticas.
