# Política de dados — Param vs Entidades

**Regra geral**  
- As intents (em `data/ops/param_inference.yaml`) definem **semântica** — palavras, padrões e janelas padrão.  
- As entidades (em `data/entities/<entidade>/entity.yaml`) definem **capacidades** — o que pode ser agregado, listado, ou calculado.

**Princípio**  
> A intent decide, a entidade valida.

**Implicações**
- O Planner infere parâmetros textualmente (intent).
- O Builder valida os parâmetros contra o YAML da entidade.
- Não deve haver campos de capacidade (`windows_allowed`, `list.limit`, `order`) em `param_inference.yaml`.
- As capacidades vivem exclusivamente dentro de `aggregations.*` nas entidades.

**Auditoria**
- Os testes `test_param_inference.py` e `test_ask_aggregations_*` garantem coerência entre ambos.
