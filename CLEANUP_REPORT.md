# CLEANUP_REPORT — Auditoria de entradas (Araquem)

## Resumo
Esta limpeza foi executada **somente** onde havia evidência clara de não uso em runtime.

---

## Remoções executadas

### 1) Fallback legado para templates em `data/concepts/*_templates.md`
- **Arquivo/trecho removido:** fallback em `app/templates_answer._load_templates`.
- **Motivo:** não há nenhum arquivo `data/concepts/*_templates.md` no repositório; o fallback nunca é acionado.
- **Impacto esperado:** nenhum (apenas remove uma busca inútil).
- **Risco:** baixo.

---

## Itens POTENTIALLY_DEAD (não removidos)

- `data/ontology/bucket_rules.yaml`: aparece apenas em scripts de auditoria/qualidade, sem uso no runtime.
- `ask.intents` e campos semânticos em entity.yaml (keywords/synonyms/anti_tokens): não são consumidos pelo Planner, mas permanecem como documentação e insumo de embeddings.

---

## Diff

- `app/templates_answer/__init__.py`: removeu fallback legado de templates baseados em `data/concepts`.

