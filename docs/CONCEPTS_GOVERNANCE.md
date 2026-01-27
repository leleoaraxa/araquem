# Concepts Governance (Naming + Checklist)

Este documento define o contrato humano para criação de novos slices de concepts, mantendo aderência à taxonomia `domain:*` já existente e ao schema de facto observado no repositório.

## A) Naming: arquivos e domains

**Padrão de arquivo**
- `data/concepts/concepts-<area>-<subarea>.yaml` (quando houver subdomínio).
- `data/concepts/concepts-<area>.yaml` (núcleo/área principal).

**Convenções**
- Filenames: lowercase, sem acento, usar `-` como separador.
- `domain`: `snake_case` (lowercase, sem acento, `_` como separador).
  - Exemplos: `institutional`, `institutional_terms`, `support_troubleshooting`, `support_plans`.

**Regra de granularidade**
- PRs pequenos: no máximo **4 arquivos** novos/modificados por PR de conteúdo.
- Preferir fatiar por subdomínios quando um arquivo ultrapassar ~15–25 concepts.

## B) Schema de concepts (contrato de formato)

**Top-level (arquivo):**
- `domain`
- `owner`
- `concepts`

**Cada concept (item da lista):**
- `name`
- `aliases` (lista)
- `description` (scalar dobrado `>`)
- Campos opcionais já existentes no repositório (ex.: `typical_questions`, quando aplicável)

**Regras de estilo**
- `description` sempre em folded scalar `>` (evitar `>-`).
- `aliases` em lista, sem duplicatas; incluir formas sem acento quando útil.
- Evitar promessas técnicas ou afirmações não garantidas por documentação oficial do repositório.

## C) Tags e indexação (contrato humano; sem mudar runtime)

- Para cada novo arquivo de concepts, adicionar **1 entrada** correspondente em `data/embeddings/index.yaml`.
  - (Preferencialmente em PR separado do conteúdo.)
- **Padrão de id:** `concepts-<area>[-<subarea>]`.
- **Tags:**
  - Sempre lowercase.
  - Tags com `:` devem estar entre aspas.
  - Usar **exatamente 1** tag `"domain:<...>"` por arquivo, alinhada ao `domain` do YAML.
  - **Nunca** usar `rag:deny` em conteúdo voltado ao usuário final (somente engenharia).

## D) Checklist “Definition of Done” (novo concepts slice)

- [ ] Arquivo criado seguindo naming (`concepts-<area>[-<subarea>].yaml`).
- [ ] `domain`/`owner` definidos e coerentes com o escopo.
- [ ] Concepts seguem o schema existente; `description` com `>`.
- [ ] `aliases` sem duplicatas; incluir variações sem acento quando necessário.
- [ ] Conteúdo é descritivo (especialmente suporte) e evita prescrição forte/heurística.
- [ ] `data/concepts/catalog.yaml` atualizado **apenas se** ele já indexar o arquivo.
- [ ] `data/embeddings/index.yaml` atualizado com `id` e `tags` corretas.
- [ ] Validação leve: YAML bem formado (sem rodar runtime).

## E) Anti‑padrões (para reduzir regressões)

- Não colocar “Summary” editorial dentro do YAML de concepts.
- Não criar monolitos gigantes; fatiar por subdomínios quando crescer demais.
- Não criar novos `domain` sem também definir tag `domain:*` no index quando aplicável.
- Não introduzir novos campos no YAML sem decisão explícita e PR de schema separado.
