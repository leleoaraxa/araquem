# FactsPayload — Contrato Canônico

O `FactsPayload` é o envelope estruturado produzido pelo Presenter (`build_facts`) e
consumido por Narrator, Responder e templates Jinja. Todos os campos são
determinísticos e derivados apenas de entradas já presentes em `plan`, `results`,
`meta`, `identifiers` e `aggregates`.

## Campos e origens
- **question** (`str`): pergunta original recebida pelo endpoint.
- **intent** (`str`): `plan['chosen']['intent']` retornado pelo Planner.
- **entity** (`str`): `plan['chosen']['entity']` retornado pelo Planner.
- **score** (`float`): `meta['planner_score']` quando fornecido; fallback para
  `plan['chosen']['score']`.
- **planner_score** (`float`): espelho de `score` para compatibilidade retroativa
  com consumidores que ainda esperam o nome antigo.
- **result_key** (`str | None`): `meta['result_key']` quando disponível e presente
  em `results`; caso contrário, a primeira chave encontrada em `results`.
- **rows** (`List[Dict[str, Any]]`): `results[result_key]` já formatado pelo
  orchestrator.
- **primary** (`Dict[str, Any]`): primeira linha de `rows` (ou `{}` quando vazio).
- **aggregates** (`Dict[str, Any]`): parâmetros inferidos (`infer_params`).
- **identifiers** (`Dict[str, Any]`): identificadores extraídos pelo orchestrator
  (`extract_identifiers`).
- **requested_metrics** (`List[str]`): métricas solicitadas pelo usuário,
  propagadas via `meta['requested_metrics']`.
- **ticker** (`str | None`): atalho extraído de `primary` ou `identifiers`.
- **fund** (`str | None`): atalho extraído de `primary` ou `identifiers`.

## Garantias mínimas
- `facts.rows == results[facts.result_key]` sempre que a chave existir em
  `results`.
- `facts.intent == plan['chosen']['intent']` e `facts.entity == plan['chosen']['entity']`.
- `facts.score == meta['planner_score']` (ou `plan['chosen']['score']` quando
  ausente em `meta`).
- `facts.primary` é sempre uma `dict` (vazia quando não há linhas).

## Exemplo (risco — `fiis_financials_risk`)
```json
{
  "question": "qual o sharpe e beta do abc11?",
  "intent": "fiis_financials_risk",
  "entity": "fiis_financials_risk",
  "score": 0.78,
  "planner_score": 0.78,
  "result_key": "financials_risk",
  "rows": [
    {
      "ticker": "ABC11",
      "volatility_ratio": 0.22,
      "sharpe_ratio": 0.51,
      "treynor_ratio": 0.35,
      "jensen_alpha": 0.04,
      "beta_index": 1.12,
      "sortino_ratio": 0.48,
      "max_drawdown": 0.17,
      "r_squared": 0.72
    }
  ],
  "primary": {
    "ticker": "ABC11",
    "volatility_ratio": 0.22,
    "sharpe_ratio": 0.51,
    "treynor_ratio": 0.35,
    "jensen_alpha": 0.04,
    "beta_index": 1.12,
    "sortino_ratio": 0.48,
    "max_drawdown": 0.17,
    "r_squared": 0.72
  },
  "aggregates": {"limit": 1},
  "identifiers": {"ticker": "ABC11"},
  "requested_metrics": ["sharpe_ratio", "beta_index"],
  "ticker": "ABC11",
  "fund": null
}
```
