# NARRATOR_PATCH_SPEC.md

## 0. Instruções gerais (para o Codex)

**Objetivo deste patch:**
Endurecer o fluxo do Narrator para a entidade **`fiis_financials_risk`**, garantindo que:

1. A resposta final **não** copie texto de RAG.
2. A resposta numérica de risco seja **totalmente determinística**, baseada apenas em `FACTS`.
3. O LLM não seja chamado para esta entidade (por enquanto).
4. Nenhum comportamento de outras entidades seja alterado.

⚠️ **Regras importantes:**

- **Não** refatorar código fora do escopo detalhado abaixo.
- **Não** alterar comportamento de outras entidades além de `fiis_financials_risk`.
- **Não** introduzir hardcodes soltos no código (tudo que for específico de entidade deve vir de política/YAML sempre que possível).
- **Não** mexer em:
  - `planner`, `builder`, `executor`, `formatter`
  - `data/policies/rag.yaml`
  - `data/entities/*` (a não ser onde explicitamente mencionado — não é o caso aqui)
- Preserve o estilo de código existente (imports, logging, padrões de nome, etc.).

---

## 1. Comportamento desejado (pós-patch)

### 1.1. Para perguntas do tipo risco (exemplo real)

Pergunta:

```text
explique as métricas de risco do HGLG11
max drawdown do MXRF11
beta do MXRF11
```

Comportamento desejado:

1. O planner continua roteando para `fiis_financials_risk` normalmente.
2. O Orchestrator continua montando `results['financials_risk']` normalmente.
3. O Presenter continua montando `facts` normalmente (incluindo `primary`, `rows`, `ticker`, etc.).
4. **Narrator:**

   * Sempre usa o renderer determinístico `_render_fiis_financials_risk`.
   * **Não chama** o LLM para essa entidade (mesmo com 1 linha).
   * **Não usa** texto de RAG dentro do prompt (RAG pode continuar existindo em `meta['rag']` para explicabilidade, mas não entra na geração da resposta).
5. `meta['narrator']`:

   * Deve refletir que a estratégia usada foi **deterministic** (ou equivalente, conforme estrutura atual).
   * Se houver campos de debug (`strategy`, `used`, etc.), garantir que não indiquem uso de LLM para esta entidade.

---

## 2. Escopo de arquivos

Você deve alterar **apenas**:

1. `data/policies/narrator.yaml`
2. `app/narrator/narrator.py`
3. (Opcional mínimo) `app/narrator/prompts.py` **somente** se necessário para respeitar a política de RAG do Narrator (sem mudar textos do SYSTEM_PROMPT).

Nenhum outro arquivo deve ser modificado.

---

## 3. Patch por arquivo

### 3.1. `data/policies/narrator.yaml`

**Objetivo:** introduzir política específica por entidade para o Narrator, com foco em `fiis_financials_risk`, sem quebrar o que já existe.

1. Localize a raiz `narrator:` já existente (algo na linha de):

   ```yaml
   narrator:
     llm_enabled: true/false
     shadow: false
     model: llama3.1:latest
     style: executivo
     max_llm_rows: 0
     max_prompt_tokens: 4000
     max_output_tokens: 700
   ```

2. Adicione (ou complete) um bloco **filho** `entities:` dentro de `narrator`.
   Caso `entities:` já exista, **apenas acrescente** o item de risco abaixo:

   ```yaml
   narrator:
     # ... campos globais já existentes ...

     entities:
       fiis_financials_risk:
         # Desliga o LLM para esta entidade específica
         llm_enabled: false
         # Garante que, mesmo se globalmente estiver habilitado, esta entidade não chamará LLM
         max_llm_rows: 0

         # Controle específico de RAG na camada do Narrator
         use_rag_in_prompt: false
   ```

   **Regras:**

   * Não altere os valores globais já existentes (fora de `entities:`).
   * Não remova nenhuma entidade que eventualmente já exista em `entities:`.
   * Apenas adicione o bloco `fiis_financials_risk` dentro de `entities:`.

---

### 3.2. `app/narrator/narrator.py`

**Objetivo:**
Fazer o Narrator respeitar a política por entidade definida em `data/policies/narrator.yaml`, garantindo que:

* Para `fiis_financials_risk`, o LLM **não** será chamado.
* Para `fiis_financials_risk`, o RAG **não** será repassado ao prompt.

#### 3.2.1. Carregar política por entidade

1. Localize o ponto onde a policy do Narrator é carregada (algo como `load_yaml_cached("data/policies/narrator.yaml")` ou similar).
2. Crie uma função helper **pequena** (sem refatorar o restante) para resolver a política efetiva por entidade.

   Exemplo de assinatura (adaptar para o estilo atual):

   ```python
   def _get_effective_policy(entity: str | None, policy: dict) -> dict:
       """Retorna a policy do Narrator mesclando config global + específica da entidade."""
   ```

   Comportamento desejado:

   * Começar de uma cópia rasa da policy global (`policy.get("narrator", {})` ou estrutura equivalente).
   * Se existir `entities` e `entity` estiver presente (`entities.get(entity)`), sobrescrever **apenas** as chaves definidas no bloco da entidade (ex.: `llm_enabled`, `max_llm_rows`, `use_rag_in_prompt`).
   * Retornar sempre um dict resultante.

   Pseudo-lógica (não precisa ser exatamente assim, mas equivalente):

   ```python
   base = dict(global_cfg)  # sem entities
   entity_cfg = (global_cfg.get("entities") or {}).get(entity or "", {})
   base.update(entity_cfg)
   return base
   ```

   ⚠️ Não altere a estrutura externa da policy; apenas use-a.

#### 3.2.2. Ajustar `_should_use_llm` para usar a policy efetiva

1. Localize o método/função que decide se o LLM será usado (algo como `_should_use_llm`).
2. Ajuste a sua implementação para receber (ou internamente obter) a **policy efetiva por entidade**, usando `_get_effective_policy(...)`.

   Regras:

   * A decisão de uso do LLM deve ser baseada em:

     * `effective_policy["llm_enabled"]`
     * `effective_policy["max_llm_rows"]`
     * `len(facts["rows"])`, como já é hoje, mas agora usando a policy da entidade.
   * Para `fiis_financials_risk`, devido à policy, o resultado **deve ser sempre `False`** (porque `llm_enabled: false` e/ou `max_llm_rows: 0`).

   **Não** mude a assinatura pública de `render`; apenas injete o uso de `_get_effective_policy` dentro do fluxo existente.

#### 3.2.3. Respeitar `use_rag_in_prompt` na chamada ao `build_prompt`

1. Localize o ponto em que o Narrator monta o prompt do LLM (algo como):

   ```python
   prompt = build_prompt(question, prompt_facts, prompt_meta, style=self.style, rag=meta.get("rag"))
   ```

2. Antes de chamar `build_prompt`, recupere a policy efetiva da entidade:

   ```python
   effective_policy = _get_effective_policy(entity, narrator_policy)
   use_rag = effective_policy.get("use_rag_in_prompt", True)
   ```

3. Ajuste o valor de `rag` passado para `build_prompt`:

   ```python
   rag_payload = meta.get("rag") if use_rag else None

   prompt = build_prompt(
       question,
       prompt_facts,
       prompt_meta,
       style=self.style,
       rag=rag_payload,
   )
   ```

   Resultado desejado:

   * Para `fiis_financials_risk`, `use_rag_in_prompt: false` → `rag_payload = None`.
   * Para demais entidades, comportamento idêntico ao atual.

#### 3.2.4. Telemetria do Narrator (opcional, mas desejável)

Se o código já possui um campo como `meta['narrator']` com `strategy`, `used`, etc.:

* Garanta que, no caso de `fiis_financials_risk`, o campo `strategy` reflita algo como `"deterministic"` ou equivalente (não é obrigatório padronizar, apenas consistente com o padrão já existente).
* Não introduza novos campos de telemetria além do estritamente necessário.

---

### 3.3. `app/narrator/prompts.py` (mínimo necessário)

**Objetivo:**
Garantir que `build_prompt` seja robusto ao caso `rag=None` (que já é parcialmente suportado), sem mudar textos do SYSTEM_PROMPT.

Verificações / ajustes:

1. Confirme que `build_prompt(..., rag=None)` já funciona sem erro (o código atual já trata `rag_payload = _prepare_rag_payload(rag)` e retorna texto padrão quando `rag` é `None`).
2. Caso encontre qualquer ponto que assuma que `rag` é sempre dict, apenas:

   * Mantenha `_prepare_rag_payload` recebendo `dict | None` (como já está).
   * Garanta que, com `rag=None`, o bloco `[RAG_CONTEXT]` use a mensagem default (algo como “(nenhum contexto adicional relevante foi encontrado.)”).

⚠️ **Não** mexer em:

* Conteúdo textual de `SYSTEM_PROMPT`.
* Templates (`PROMPT_TEMPLATES`) e `FEW_SHOTS`.
* Renderizadores determinísticos (`_render_fiis_*`).

O objetivo deste patch **não** é reescrever o prompt, apenas garantir que `rag=None` funcione sem quebrar nada.

---

## 4. Testes esperados

Após aplicar o patch, rode **manualmente** os seguintes cenários (pode ser via `rag_debug.sh` ou `curl`):

### 4.1. Pergunta conceitual de risco (HGLG11)

```bash
# via /ask (com explain=true)
GET /ask?question=explique%20as%20métricas%20de%20risco%20do%20HGLG11&explain=true
```

Verificar:

* `meta.planner.intent == "fiis_financials_risk"`.

* `results.financials_risk[0].ticker == "HGLG11"`.

* `meta.narrator.strategy` (ou equivalente) **não** indicar uso de LLM.

* `meta.narrator.latency_ms` não mostrar chamada cara de LLM (deve cair apenas no caminho determinístico).

* `answer` **não** conter o texto:

  * `"Indicadores de risco do FII: volatilidade histórica..."`
    (esse é o snippet de RAG que antes era copiado).

* `answer` deve ser coerente com `_render_fiis_financials_risk` (lista de métricas numéricas e comentário final).

### 4.2. Pergunta focal em métrica única (MXRF11)

```bash
GET /ask?question=max%20drawdown%20do%20MXRF11&explain=true
```

Verificar:

* Mesmos pontos acima para `fiis_financials_risk`.
* **Não** deve aparecer texto literal de RAG nos primeiros parágrafos.
* A resposta deve enfatizar o valor de `max_drawdown` de forma numérica, conforme o renderer determinístico.

### 4.3. Regressão rápida em outra entidade (sanidade)

Exemplo:

```bash
GET /ask?question=imoveis%20do%20HGLG11&explain=true
```

Verificar:

* `fiis_imoveis` continua funcionando como antes.
* Se `llm_enabled` global estiver ativo, comportamento de LLM para outras entidades permanece inalterado (exceto risco, que foi explicitamente travado).

---

## 5. Resultado esperado pós-patch

* Perguntas de risco (`fiis_financials_risk`) passam a ser **100% determinísticas** na resposta.
* Nenhum texto de RAG é mais copiado para o usuário nesse fluxo específico.
* O Narrator passa a respeitar política por entidade em `data/policies/narrator.yaml`.
* RAG continua funcionando para:

  * Planner (hints)
  * Outras entidades, quando configurado
* O patch é estritamente localizado, sem marretas e sem efeitos colaterais fora de `fiis_financials_risk`.

---

## 6. Sugestão de mensagem de commit

```text
feat(narrator): enforce deterministic path for fiis_financials_risk and disable RAG in prompt
```
