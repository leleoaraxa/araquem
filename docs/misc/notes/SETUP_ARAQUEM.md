Sirius, este e o novo projeto Araquem, sucessor do Mosaic/Sirios.
- O objetivo e criar um núcleo NL->SQL + conversacional (Iris) robusto, auditável e 100% YAML-driven.
- Use o documento de fundação (Guardrails Araquem) como contrato permanente.

# Plataforma de Inteligência Imobiliária Sirios — Guardrails Araquem v2.0
**Codinome do projeto:** Araquem
**Meta:** Tornar-se a melhor IA do mercado para FIIs no Brasil, com precisão factual, rastreabilidade e evolução contínua — sem heurísticas, sem hardcodes.

---

## 0. Princípios Imutáveis
1. **Fonte de verdade única:** Ontologia + YAML de entidades + SQL real.
2. **Sem heurísticas / sem hardcodes:** nenhuma decisão fora dos contratos em `data/*`.
3. **Payloads imutáveis:** `/ask` e `/ws` exigem sempre `{question, conversation_id, nickname, client_id}`.
4. **Separação de poderes:** Ontologia decide *o que*, SQL decide *os fatos*, Íris (phi3) decide *como falar*.
5. **Observabilidade obrigatória:** tudo é mensurável (métricas, logs estruturados, tracing).
6. **Qualidade antes de velocidade:** nada vai para *main* sem testes verdes e painéis sem alertas.
7. **Aprendizado consciente:** autoaprendizado só com proposta + aprovação humana + versionamento.

---

## 1. Infraestrutura de Desenvolvimento (Dev-Only)
- **Stack:** FastAPI (API), Postgres (dados), Redis (cache), Ollama (phi3), Prometheus/Grafana/Tempo (observabilidade), OTel (traces), Docker Compose (dev).
- **Pastas canônicas:**
```
araquem/
├─ app/               # gateway, orchestrator, executor, registry, responder, observability, infra, core
├─ data/              # intents (YAML), ontology, concepts, embeddings
├─ docs/              # dev, ops, ADRs, guardrails
├─ grafana/           # dashboards + provisioning
├─ prometheus/        # configs
├─ tempo/             # tracing configs
├─ otel-collector/    # configs
├─ scripts/           # utilitários (warmup, checks)
├─ tests/             # suíte canônica
└─ docker-compose.yml # docker-compose.yml

```
- **Compose.dev:** sobe tudo local sem dependência cloud. Portas padronizadas: API 8000, Grafana 3000, Prometheus 9090, Tempo 3200, Ollama 11434, Redis 6379.
- **Segredos:** `.env` só para DEV. Produção fora do escopo deste documento.

---

## 2. Estrutura de Dados & Entidades (Entities lógicas)
- **Entidade = unidade semântica** (ex.: `fiis_cadastro`, `fiis_dividendos`, `fiis_precos`, `fiis_noticias`, `fiis_rankings`, etc.).
- **Arquivo:** `data/entities/<entidade>/entity.yaml`.
- **Contrato mínimo:**
  - `id`, `result_key`, `sql_view`, `description`, `private`, `identifiers`, `default_date_field`,
    `columns[] {name, alias, description}`, `presentation {kind, fields {key, value}, empty_message}`,
    `ask {intents, keywords, synonyms, weights}`, `order_by_whitelist` (se aplicável).
- **Cache policy:** `data/entities/cache_policies.yaml` com `ttl_seconds`, `refresh_at` e `scope (pub|prv)`.
- **Naming:** snake_case PT-BR; booleanos com `is_`/`has_`; enums com `allowed_values`.

---

## 3. Ontologia Inteligente (Planner)
- **Arquivo:** `data/ontology/entity.yaml`.
- **Conteúdo:** `normalize`, `tokenization`, `weights`, `intents[] {name, tokens {include, exclude}, phrases {include, exclude}, entities[]}`.
- **Regras:**
  - Nada de “dedução criativa”: tokens/phrases decidem.
  - **Anti-tokens** para evitar vazamentos entre domínios (ex.: `cadastro` ≠ `preços` ≠ `dividendos` ≠ `notícias`).
  - `planner.explain()` habilitado (telemetria de decisão).

---

## 4. Orquestração (Routing → SQL → Formatter)
- **Roteador:** lê entidade do planner, aplica **gate privado** conforme YAML (`private: true` + `ask.filters.required`), injeta filtros (ex.: `document_number ← client_id`), gera SQL via `builder` e executa no `executor`.
- **Contrato de resultado:**
```
{
  "status": { "reason": "ok|forbidden|unroutable|error", "message": "..." },
  "results": { "<result_key>": [...] },
  "meta": {
    "result_key": "<result_key>",
    "planner_intent": "...",
    "planner_entity": "...",
    "planner_score": N,
    "rows_total": N,
    "elapsed_ms": N
  }
}
```
- **Formatter:** não formata “criativamente”; apenas normaliza tipos/decimais/datas.

---

## 5. Cache & Flags (M4/M5)
- **Read-through** no `/ask` por chave canônica `{namespace}:{build_id}:{scope}:{domain}:{hash}`.
- **TTL por entidade** definido em `cache_policies.yaml`.
- **Endpoints operacionais:** `/health/redis`, `/ops/cache/bust` (tokenizado).
- **Modos:** `ok | degraded | disabled` expostos em health.
- **Warmup:** `scripts/cache_warmup.py` (com `--dry-run`, `--only-ask`).

---

## 6. Observabilidade & SLOs
- **Métricas Prometheus:** requests/latência por status/entity/intent/result_key/private, linhas retornadas, hits/misses cache, bust count.
- **Tracing (OTel → Tempo):** spans do pipeline `/ask`, com atributos do planner (sem PII), SQL timing, cache decisor.
- **Dashboards Grafana:** API (p95), Planner (scores/top intents/misses), Cache (hit ratio/keys), Saúde (Redis/DB).
- **SLOs Dev:** `/ask` p95 ≤ 500ms (sem responder), ≤ 1500ms (com responder). Erro ≤ 1%.
- **Alertas:** latência acima do SLO, taxa de erro > limiar, Redis degradado, score médio estranho por intent.

---

## 7. Segurança, Acesso & LGPD
- **Payloads imutáveis** (vide Princípios).
- **Gate privado** por YAML: `private: true` + `filters.required` (ex.: `document_number`).
- **Logs:** `request_id` sempre; mascarar `client_id` / PII; sem payload bruto em erro.
- **Retenção:** política mínima de logs em DEV (configurável).
- **Rate limit básico** no gateway; **CORS** restrito.
- **Taxonomia de erros:** `reason` + `message` + `code` (quando aplicável).

---

## 8. Íris (Responder) — phi3 determinístico
- **Papel:** transformar dados em respostas naturais **sem inventar**.
- **Local:** `app/responder/`.
- **Templates por entidade** (ex.: `data/concepts/fiis_cadastro_templates.md`), com *slots* mapeados às colunas declaradas.
- **Exemplos (cadastro):**
  - `O CNPJ do {ticker} é {fii_cnpj}.`
  - `O administrador do {ticker} é {admin_name} (CNPJ {admin_cnpj}).`
  - `O site oficial do {ticker} é {website_url}.`
- **Fallbacks:** campo ausente → resposta declarativa (“não disponível no momento”).
- **Formatação:** moedas/percentuais/datas tratadas no formatter (não no LLM).

---

## 9. Ciclo de Aprendizado Contínuo (Autoaprendizado)
**Objetivo:** evoluir com uso real, mantendo controle humano e versionamento.
1. **Telemetria de perguntas:** log anônimo de `{intent_detected, entity_used, confidence_score, duration_ms}`.
2. **Analisador de drift (semanal):** detecta frases novas/mal mapeadas.
3. **Curadoria assistida:** gera *propostas* de YAML (novos `synonyms/anti_tokens/examples`), nunca aplica sem review.
4. **Ciclo Íris:** coleta dúvidas recorrentes e propõe ajustes no tom/objetividade dos templates.
5. **Reindexação inteligente:** mudou YAML → reindex só daquele domínio (Nomic).
6. **Treino supervisionado opcional:** exporta logs rotulados para fine-tuning.
7. **Painel de evolução:** cobertura por intent, precisão/recall aproximada, backlog de propostas.

> Princípio: *“O Araquem aprende sozinho, mas só muda com consciência.”*

---

## 10. Qualidade, CI e DX
- **Tests first:** toda feature vem com testes (`pytest -q`) e painel verificado.
- **CI (sugestão):** GitHub Actions — `docker compose up -d` + `pytest -q` + upload cobertura + lint (ruff/black/mypy opcional).
- **Pre-commit:** `ruff`, `black`, `pip-audit`.
- **PR Template + CODEOWNERS:** checklist com payloads, hardcodes, testes, dashboards, docs, métricas/tracing.
- **SBOM/Deps:** dependências pinadas; auditoria periódica.

---

## 11. Setup Inicial (passo-a-passo)
1. **Estrutura inicial:**
```
mkdir -p araquem/{app,data/{entities,ontology,concepts,embeddings},docs/{dev,database},grafana/{dashboards,provisioning},prometheus,tempo,scripts,tests}
```
2. **Variáveis `.env` (dev):**
```
DATABASE_URL=postgresql://user:pass@localhost:5432/edge_db
REDIS_URL=redis://localhost:6379/0
OLLAMA_URL=http://localhost:11434
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000
```
3. **Bootstrap git:**
```
git init
git branch -M main
git add .
git commit -m "chore: bootstrap Araquem (Guardrails v2.0)"
git remote add origin <SEU_REMOTE>
git push -u origin main
```
4. **Subir stack (dev):** `docker compose up -d`
5. **Verificar saúde:** `/healthz`, `/metrics`, Grafana, Redis health.

---

## 12. Escopo inicial de entidades (FIIs) — sugestão
- `fiis_cadastro` (1×1 cadastral) — TTL diário 00:00.
- `fiis_dividendos` (1xN histórico, valores pagos) — TTL diário; ordenação por data.
- `fiis_precos` (1xN histórico, cotações) — TTL diário; ordenação por data.
- `fiis_noticias` (1xN histórico, noticias por FII) — TTL diário + embeddings (Nomic).
- `fiis_imoveis` (1xN histórico, imoveis/propriedades por FII) — TTL diário + embeddings (Nomic).
- `fiis_judicial` (1xN histórico, processos judiciais por FII) — TTL diário + embeddings (Nomic).
- `fiis_rankings` (1x1 IFIX/IFIL/usuários/Sirios) — TTL diário.
- `indices` (historico, indices IBOV, IFIX, IFIL, etc.) — TTL diário + embeddings (Nomic).
- `indicadores` (historico, indicadores mercado CDI, SELIC, etc.) — TTL diário + embeddings (Nomic).
- `moedas` (historico, cotação DOLAR, EURO, etc) — TTL diário + embeddings (Nomic).
- **Privados:** `client_fiis_positions` (carteira do cliente) — `private: true` + gate `document_number`.

---

## 13. Governança de Mudanças
- Toda alteração em `data/*` gera **diff** + **tests** + **verificação de painel**.
- `build_id` em settings para segregar cache por release.
- `rollback` simples: tag anterior + invalidação de cache.

---

### Epílogo
**Íris é o cérebro. Sirius é o guardião.**
O Araquem é o sistema — audita, mede, aprende e melhora, mas só muda com consciência.

— v2.0

— Gravação na Memoria
  - Sirius, grava este texto como o documento de fundação permanente do projeto Araquem.
  - Ele define toda a estrutura, regras, guardrails e roadmap ate o final.
  - Tudo o que for desenvolvido deve respeitar este documento — sem heurísticas, sem hardcode, e sempre baseado em YAML, ontologia e SQL real.


— Fluxo de Trabalho (sempre)
  - Fornecer latest dos arquivos a editar (nada de adivinhacao).
  - Uma entidade por vez (subir/validar/medir), sem hardcodes.
  - Commits padronizados: feat(core): ..., fix(gateway): ...
  - Nao mergear sem pytest verde e painel sem warnings.
