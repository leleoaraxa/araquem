# ADR — Remoção definitiva do classificador de buckets

## Contexto

O bucket A/B/C/D é uma taxonomia estrutural definida exclusivamente no catálogo de entidades
(`data/entities/*/{entity}.yaml`, campo `bucket`). Não é permitido inferir bucket por texto ou
heurísticas, e o contrato do `/ask` deve permanecer estável.

## Decisão

- Remover definitivamente qualquer classificador textual de buckets.
- `bucket_rules.yaml` foi **REMOVIDO** e não deve ser reintroduzido.
- O Planner só considera bucket quando fornecido explicitamente por plano/meta/contexto.
- Sem bucket explícito, o comportamento é neutro (`selected=""`).

## Consequências

- O `bucket_index` permanece como único mecanismo para restringir intents e entidades quando
  um bucket explícito é fornecido.
- Sem bucket explícito, entidades/intents permanecem sem filtragem e `bucket_gate.applied`
  permanece `false`.
- Toda telemetria/explain deve refletir bucket neutro quando não houver bucket explícito.
