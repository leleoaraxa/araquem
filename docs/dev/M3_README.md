# 🧩 Araquem — M3: Orquestração (planner → builder → executor → formatter)

> Integração completa do fluxo NL→SQL com consulta real no Postgres.

---

## 🎯 Objetivo

Transformar o protótipo de _planner_ (que só explicava intenções) em um pipeline funcional:
```

planner → sql_builder → executor → formatter → response

```

Com o M3, o `/ask` já:
- interpreta a pergunta;
- gera SQL a partir da ontologia (YAML);
- consulta o Postgres real (`fiis_cadastro`);
- retorna o JSON completo, compatível com o contrato do Mosaic/Sírios.

---

## 🧠 Arquitetura

```

app/
├── planner/
│   └── planner.py         # Ontologia → intenção/entidade
├── builder/
│   └── sql_builder.py     # Gera SELECT com base no YAML
├── executor/
│   └── pg.py              # Psycopg 3, read-only
├── formatter/
│   └── rows.py            # Normaliza colunas e campos
└── orchestrator/
└── routing.py         # Coordena o fluxo e mede latência

```

- **Normalização de ticker:** camada de entrada, regex `\b([A-Za-z]{4}11)\b`.
- **Entidade ativa:** `fiis_cadastro` (view no banco).
- **Intent ativa:** `cadastro`.

---

## 🔧 Fluxo de execução

1. **Planner:** lê `data/ontology/entity.yaml` e define `intent` + `entity`.
2. **SQL Builder:** monta o `SELECT` com as colunas de `return_columns` do YAML.
3. **Executor:** roda no Postgres via `DATABASE_URL`.
4. **Formatter:** retorna JSON tabular pronto.
5. **Response:** entregue no contrato `/ask`.

---

## 📜 Exemplo de resposta

```json
{
  "status": { "reason": "ok", "message": "ok" },
  "results": {
    "cadastro_fii": [
      {
        "ticker": "VINO11",
        "fii_cnpj": "12.516.185/0001-70",
        "display_name": "Vinci Offices Fundo Investimento Imobiliario",
        "admin_name": "Brl Trust Dtvm S.A.",
        "admin_cnpj": "13.486.793/0001-42",
        "website_url": ""
      }
    ]
  },
  "meta": {
    "planner_intent": "cadastro",
    "planner_entity": "fiis_cadastro",
    "rows_total": 1,
    "elapsed_ms": 123
  }
}
```

---

## 🧪 Testes

| Arquivo                          | Tipo       | Descrição                                     |
| -------------------------------- | ---------- | --------------------------------------------- |
| `tests/test_ask_cadastro_sql.py` | Integração | Confirma SQL real no Postgres                 |
| `tests/test_ontology_tokens.py`  | Unidade    | Verifica que “CNPJ” ativa intenção `cadastro` |
| `tests/test_planner_explain.py`  | Unidade    | Valida saída do `/debug/planner`              |

Executar:

```bash
docker compose exec api sh -lc "pytest -q"
```

---

## ⚙️ Variáveis de ambiente

| Variável          | Função                       |
| ----------------- | ---------------------------- |
| `DATABASE_URL`    | Conexão com Postgres         |
| `ONTOLOGY_PATH`   | Caminho do YAML da ontologia |
| `TEST_FII_TICKER` | Ticker padrão nos testes     |
| `BUILD_ID`        | Identificador do build atual |

---

## 🚀 Troubleshooting

| Sintoma              | Causa provável                 | Solução                                                    |
| -------------------- | ------------------------------ | ---------------------------------------------------------- |
| `getaddrinfo failed` | Host do Postgres não resolvido | Use `localhost` no host ou `sirios_db` dentro do container |
| `unroutable`         | Ontologia sem intent mapeado   | Verifique `entity.yaml`                                    |
| JSON vazio           | View não populada              | Confirme dados em `fiis_cadastro`                          |
| Teste skipado        | Banco inacessível no host      | Execute `pytest` dentro do container                       |

---

## ✅ DoD — Definition of Done

* `/ask` executa pipeline completo via orquestrador.
* Tests 100% verdes (incluindo integração SQL).
* Latência < 200 ms local.
* `VINO11` retorna 1 linha de dados reais.

```
