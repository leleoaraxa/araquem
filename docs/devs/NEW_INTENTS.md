# Passo a passo — Como adicionar **novas intenções/entidades** no Araquem

1. **SQL/View (compute-on-read)**

   * Crie/ajuste a *view* (ou *materialized view*) real no Postgres.
   * Nomeie de forma semântica e estável (ex.: `history_algo`).

2. **Contrato da entidade** (`data/contracts/entities/<nome>.schema.yaml`)

   * Defina `entity`, `kind`, `version` e **todas as colunas** com `type`, `nullable`, `desc`.
   * Travar `tolerance` (sem colunas extras/faltando) quando fizer sentido.

3. **YAML da entidade** (`data/entities/<nome>/entity.yaml`)

   * Preencha `id`, `sql_view`, `result_key`, `description`, `d_minus: 1` (quando for D-1), `default_date_field`.
   * Liste colunas com `alias`/`description`.
   * Configure `presentation`, `ask` (intents/keywords/synonyms/weights), `order_by_whitelist` e `aggregations`.

4. **Templates/Responses**

   * `data/entities/<nome>/templates.md` e `responses/list.md.j2` para formatação de saída.

5. **Ontologia** (`data/ontology/entity.yaml`)

   * Adicione uma **nova intent** no bloco `intents:` apontando `entities: [<nome>]`.
   * Preencha `tokens.include/phrases.include` com vocabulário que o usuário realmente usa.

6. **Embeddings** (`data/embeddings/index.hml`)

   * Acrescente a entidade no bloco `include:` com `id`, `path` e `tags`.
   * **Rebuild embeddings:**

     ```
     python scripts/embeddings_build.py --index data/embeddings/index.hml --out data/embeddings/store
     ```

7. **Quality (opcional, recomendado)**

   * Crie `data/ops/quality/projection_<nome>.json` com `must_have_columns` e exemplos de perguntas.
   * Rode:

     ```
     python scripts/quality_push.py data/ops/quality/projection_<nome>.json
     ```

8. **Verificações rápidas**

   * `GET /ops/quality/report` → checar métricas.
   * Perguntas via `/ask` usando vocabulário da nova intent.
   * Observar métricas em `/metrics`/Grafana, se aplicável.

---
