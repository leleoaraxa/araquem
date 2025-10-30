# 🧩 Araquem — M4: Cache Read-Through (Redis + Policies)

> Camada de cache por entidade, YAML-driven, com métricas Prometheus.

---

## 🎯 Objetivo

Adicionar cache transparente no `/ask` para reduzir latência e aliviar o Postgres.

Fluxo:
```

planner → identifiers → cache.read_through() → orchestrator

```

---

## 🧠 Arquitetura

```

app/
├── cache/
│   ├── rt_cache.py          # Engine read-through (Redis + TTL)
│   └── **init**.py
└── main.py                  # /ask com cache + métricas + /ops/cache/bust

```

---

## ⚙️ Componentes

### `CachePolicies`
Lê `data/entities/cache_policies.yaml`:
```yaml
policies:
  fiis_cadastro:
    ttl_seconds: 86400
    refresh_at: "00:15"
    scope: pub
```

### `RedisCache`

Abstrai `redis.from_url()` com helpers JSON (`get_json`, `set_json`, `delete`, `ping`).

### `read_through()`

```python
read_through(cache, policies, entity, identifiers, fetch_fn)
```

* Verifica se a entidade possui política ativa.
* Gera chave:
  `araquem:{build_id}:{scope}:{entity}:{sha1(identifiers)}`
* Retorna valor e status (`hit`/`miss`).

---

## 📡 Endpoints operacionais

| Rota                   | Descrição                 | Autenticação         |
| ---------------------- | ------------------------- | -------------------- |
| `GET /health/redis`    | Testa conexão com Redis   | livre                |
| `POST /ops/cache/bust` | Invalida chave específica | Header `X-OPS-TOKEN` |

### Exemplo — Bust manual

```bash
curl -X POST http://localhost:8000/ops/cache/bust \
  -H "Content-Type: application/json" \
  -H "X-OPS-TOKEN: araquem-secret-bust-2025" \
  -d '{"entity":"fiis_cadastro","identifiers":{"ticker":"VINO11"}}'
```

---

## 📊 Métricas Prometheus

| Métrica              | Descrição                 | Labels |
| -------------------- | ------------------------- | ------ |
| `cache_hits_total`   | Total de acertos no cache | entity |
| `cache_misses_total` | Total de misses           | entity |

Exemplo de painel Grafana:

```
sum(rate(cache_hits_total[1m])) by (entity)
sum(rate(cache_misses_total[1m])) by (entity)
```

---

## 🧪 Testes

| Arquivo                                    | Tipo       | Descrição                 |
| ------------------------------------------ | ---------- | ------------------------- |
| `tests/test_cache_readthrough.py`          | Integração | Confirma ciclo MISS → HIT |
| `tests/test_cache_bust_auth.py` (opcional) | Segurança  | Testa 403/200 com token   |

Executar:

```bash
docker compose exec api sh -lc "pytest -q tests/test_cache_readthrough.py"
```

---

## 🔐 Configuração de ambiente

| Variável          | Descrição              | Exemplo                    |
| ----------------- | ---------------------- | -------------------------- |
| `REDIS_URL`       | Conexão Redis          | `redis://redis:6379/0`     |
| `CACHE_OPS_TOKEN` | Token de invalidação   | `araquem-secret-bust-2025` |
| `BUILD_ID`        | Identificador de build | `20251030`                 |

---

## 💡 Verificação manual

PowerShell:

```powershell
$body = @{ question="Qual o CNPJ do VINO11?"; conversation_id="c1"; nickname="@leleo"; client_id="66140994691" } | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/ask -Method Post -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 8 | Out-Host
```

Observe o campo `meta.cache`:

* 1ª vez → `"hit": false`
* 2ª vez → `"hit": true"`

---

## 🧰 Scripts de apoio (Windows)

| Script                 | Descrição                     |
| ---------------------- | ----------------------------- |
| `scripts/db_check.ps1` | Testa conexão Postgres        |
| `scripts/try_m3.ps1`   | Roda orquestrador local       |
| `scripts/warmup.ps1`   | Pré-carrega cache e mede hits |

---

## ✅ DoD — Definition of Done

* `/ask` opera com cache read-through ativo.
* Métricas `cache_hits_total` e `cache_misses_total` visíveis no Grafana.
* `/health/redis` responde `ok`.
* `/ops/cache/bust` protegido via `CACHE_OPS_TOKEN`.
* Teste de integração MISS → HIT passando.
* Nenhum hardcode (tudo YAML + ontologia).

```
