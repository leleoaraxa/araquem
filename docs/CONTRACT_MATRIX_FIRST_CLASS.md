# CONTRACT_MATRIX_FIRST_CLASS.md
# Araquem — Matriz de Contratos First-Class (Conceitos / Institucional / Suporte UI)

> **Objetivo**: definir o **contrato** (intents + entidades + templates + policies + qualidade) para os três domínios first-class acordados, **antes** de qualquer implementação.
>
> **Premissas (contratos de produto)**
> 1) **Conceitos = FIRST-CLASS** (determinístico; RAG apenas enriquecimento opcional).
> 2) **Institucional = FIRST-CLASS (escopo mínimo)**: sobre, privacidade, termos, limites, pricing.
> 3) **Suporte UI = FIRST-CLASS (escopo fechado)**: “como fazer” do core do produto acionado pelo `?` na UI.
> 4) **Suporte UI não conta uso**: não decrementa saldo/cota, não entra em métricas de consumo do chatbot (tratamento como interação assistiva).

---

## 0) Taxonomia e convenções

### 0.1 Domínios (contracts)
- **concepts**: glossário + interpretação + limitações + “onde aparece na plataforma”.
- **institutional**: políticas, posicionamento, termos e planos (texto oficial, auditável).
- **support_ui**: instruções “como fazer” para fluxos principais (contexto via UI).

### 0.2 Padrões de naming (propostos para contrato)
> *Nomes exatos podem ser ajustados na implementação; aqui são canônicos para a discussão.*
- **Intents**
  - `concept_lookup`
  - `institutional_about`
  - `institutional_privacy`
  - `institutional_terms`
  - `institutional_limits`
  - `institutional_pricing`
  - `support_howto`
- **Entidades**
  - `concepts_catalog`
  - `institutional_about`
  - `institutional_privacy`
  - `institutional_terms`
  - `institutional_limits`
  - `institutional_pricing`
  - `support_howto_core`

### 0.3 Regras de determinismo
- Resposta base **sempre determinística** via templates (`responses/<kind>.md.j2`).
- RAG:
  - **Conceitos**: pode anexar “ver também / exemplos” (opcional).
  - **Institucional**: RAG **não** é fonte primária (apenas navegação/trechos, opcional).
  - **Suporte UI**: RAG **desligado** por padrão (evitar variação).
- Narrator:
  - permitido **somente** em modo “safe rewrite” se policy permitir, mas contrato assume **LLM off** por default.

---

## 1) Matriz de contratos (visão geral)

| domínio | intent | entidade | tipo de resposta | RAG | Narrator | conta uso? | fonte de verdade | exemplos de pergunta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| concepts | `concept_lookup` | `concepts_catalog` | tabela/lookup + explicação determinística | opcional (enriquecimento) | opcional (guardrail) | **sim** | `data/entities` + (opcional) `data/concepts` indexado | “o que é drawdown?”, “o que significa ifix?”, “como calcular sharpe?” |
| institutional | `institutional_about` | `institutional_about` | texto determinístico (seções) | opcional (navegação) | off por default | **sim** | docs institucionais versionados em `data/entities/...` | “o que é a sirios?”, “qual o objetivo da plataforma?” |
| institutional | `institutional_privacy` | `institutional_privacy` | texto determinístico | **off** (primário) | off | **sim** | texto oficial | “vocês guardam meus dados?”, “lgpd”, “privacidade” |
| institutional | `institutional_terms` | `institutional_terms` | texto determinístico | **off** (primário) | off | **sim** | texto oficial | “quais termos de uso?”, “responsabilidade”, “recomendação?” |
| institutional | `institutional_limits` | `institutional_limits` | texto determinístico | opcional | off | **sim** | fonte oficial de planos/limites | “qual limite do free?”, “o que muda no pro?” |
| institutional | `institutional_pricing` | `institutional_pricing` | texto determinístico | opcional | off | **sim** | fonte oficial de pricing | “quanto custa?”, “planos e preço” |
| support_ui | `support_howto` | `support_howto_core` | texto determinístico por tópico | **off** | off | **não** | catálogo de how-to do core | “como usar este filtro?”, “como interpretar este gráfico?” (enviado pelo `?`) |

---

## 2) Contratos detalhados por domínio

## 2.1 Conceitos — `concept_lookup` / `concepts_catalog`

### a) Escopo do conteúdo
- Definição objetiva (“o que é”)
- Interpretação (“como ler” / “quando é bom ou ruim” de forma **não recomendatória**)
- Limitações/metodologia (quando aplicável)
- Onde aparece na plataforma (ex.: em quais telas/campos)
- “Ver também” (conceitos relacionados)

### b) Interface de pergunta esperada
- Usuário livre: “o que é X?”, “explique X”, “qual a diferença entre X e Y?”
- Sem ticker → priorizar modo conceito.
- Com ticker → responder conceito e, se houver entidade de dados, pode apontar onde ver (sem executar dados aqui).

### c) Artefatos do contrato (a tocar na implementação)
- `data/ontology/entity.yaml`: intent `concept_lookup` + tokens/phrases/anti_tokens.
- `data/entities/concepts_catalog/concepts_catalog.yaml`: presentation + ask + response kind.
- `data/entities/concepts_catalog/responses/<kind>.md.j2`: template determinístico.
- `data/policies/narrator.yaml`: policy para concept_mode (com LLM off por default).
- `data/policies/rag.yaml`: coleção `concepts-*` (opcional) e allow/deny por intent.
- `data/embeddings/index.yaml`: incluir docs de conceitos (se RAG for usado).

### d) Qualidade mínima (suites)
- Routing suite:
  - “o que é sharpe?” → `concept_lookup`
  - “o que é ifix?” → `concept_lookup`
  - “o que é vacância?” → `concept_lookup`
- Contract suite:
  - resposta deve conter seção “Definição” e “Onde aparece na plataforma”.

---

## 2.2 Institucional (mínimo) — `institutional_*`

### a) Escopo e governança
- Texto **oficial**, versionado, auditável.
- Não depender de embeddings para produzir o conteúdo principal.

### b) Entidades (escopo mínimo)
1) `institutional_about`
2) `institutional_privacy`
3) `institutional_terms`
4) `institutional_limits`
5) `institutional_pricing`

> **Nota:** pode ser uma única entidade “institutional” com seções e roteamento por seção, mas aqui mantemos separado para roteamento/qualidade mais previsível.

### c) Artefatos do contrato
- `data/ontology/entity.yaml`: intents `institutional_*`.
- `data/entities/institutional_*/*.yaml`: templates determinísticos em `responses/`.
- `data/policies/rag.yaml`: RAG opcional apenas para navegação/trechos, nunca como primário.
- `data/policies/narrator.yaml`: LLM off por default.

### d) Qualidade mínima (suites)
- Routing suite:
  - “o que é a sirios?” → `institutional_about`
  - “lgpd / privacidade” → `institutional_privacy`
  - “termos de uso / recomendação” → `institutional_terms`
  - “limite free / pro” → `institutional_limits`
  - “preço / planos” → `institutional_pricing`
- Contract suite:
  - resposta deve incluir “Última atualização” (metadata) e “Escopo”.

---

## 2.3 Suporte UI determinístico — `support_howto` / `support_howto_core`

### a) Escopo fechado
- Apenas “como fazer” do core do produto (fluxos principais).
- Perguntas disparadas pela UI via `?` são **assistivas**.

### b) Regra comercial/telemetria (invariável)
- **Não conta como pergunta do usuário**
- **Não decrementa saldo/cota**
- **Não entra em métricas de consumo do chatbot**
- Pode ter logging técnico (observabilidade), mas separado de billing.

### c) Modelo de pergunta (UI)
- Perguntas precisam carregar contexto do elemento clicado.
- Padrão recomendado para a pergunta enviada pela UI (exemplos):
  - “Como usar o filtro **Classificação** nesta tela?”
  - “O que significa o campo **DY 12m** nesta tabela?”
  - “Como interpretar o gráfico **Carteira vs IFIX**?”

> **Observação:** o contrato aqui assume que o “contexto” vem no texto; não cria novos campos no payload do `/ask` (imutável). O front embute contexto na pergunta.

### d) Artefatos do contrato
- `data/ontology/entity.yaml`: intent `support_howto` com tokens específicos (como usar/onde fica/como interpretar + UI terms).
- `data/entities/support_howto_core/support_howto_core.yaml`: coleção de tópicos (lookup determinístico por slug/título).
- `data/entities/support_howto_core/responses/<kind>.md.j2`: template determinístico por tópico.
- `data/policies/rag.yaml`: **deny** para `support_howto` (RAG off).
- `data/policies/narrator.yaml`: LLM off.
- (Opcional) `data/embeddings/index.yaml`: só se desejar busca semântica interna de tópicos, mas **não recomendado no início**.

### e) Qualidade mínima (suites)
- Routing suite:
  - “como usar o filtro classificação?” → `support_howto`
  - “como interpretar este gráfico?” → `support_howto`
- Contract suite:
  - resposta deve conter “Passo a passo” e “Dica rápida”.

---

## 3) Decisões pendentes (para travar antes de implementar)

1) **Modelagem de conceitos**:
   - (A) `concepts_catalog` único com lookup por “slug”
   - (B) uma entidade por conceito (granular)
2) **Institucional**:
   - (A) 5 entidades separadas (roteamento simples)
   - (B) 1 entidade “institutional” com seções (menos arquivos)
3) **Suporte UI**:
   - (A) catálogo fechado por tópicos (determinístico)
   - (B) catálogo fechado + busca semântica local (mais complexo)

---

## 4) Checklist de implementação (quando autorizado)

> **Não executar agora.** Apenas referência para o próximo passo.

- [ ] Atualizar `data/ontology/entity.yaml` com intents novas.
- [ ] Criar entidades em `data/entities/*` com `presentation.kind`.
- [ ] Criar templates determinísticos em `responses/`.
- [ ] Ajustar `data/policies/narrator.yaml` (LLM off; concept_mode).
- [ ] Ajustar `data/policies/rag.yaml` (coleções e allow/deny).
- [ ] Criar/ajustar quality suites (routing + contract).
- [ ] (Opcional) Indexar docs e rebuild embeddings store.

---
