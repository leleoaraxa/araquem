# SETUP_ARAQUEM.md

## Passo 1 — Contexto
Sirius, este e o novo projeto Araquem, sucessor do Mosaic/Sirios.
O objetivo e criar um nucleo NL->SQL + conversacional (Iris) robusto, auditavel e 100% YAML-driven.
Use o documento de fundacao (M0 Guardrails Araquem) como contrato permanente.

---

## Passo 2 — Documento de Fundacao
(cole aqui o conteudo completo do docs/dev/M0_GUARDRAILS_ARAQUEM.md)

---

## Passo 3 — Gravacao na Memoria
Sirius, grava este texto como o documento de fundacao permanente do projeto Araquem.
Ele define toda a estrutura, regras, guardrails e roadmap ate o final.
Tudo o que for desenvolvido deve respeitar este documento — sem heuristicas, sem hardcode, e sempre baseado em YAML, ontologia e SQL real.

---

## Passo 4 — Validacao
Aguarde a confirmacao:
"Registrado! O projeto Araquem foi configurado como base permanente."

Depois disso, siga com:
"Sirius, seguimos para M1."
ou
"Sirius, retoma a fase atual do Araquem."

---

## Passo 5 — Ambiente Dev (compose padrao)
1) Copie .env.sample para .env e preencha:
```
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://localhost:6379/0
OLLAMA_URL=http://localhost:11434
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000
```
2) Suba a stack:
```
docker compose -f deploy/docker/compose.dev.yml up -d
```
3) Verifique:
- API: curl -s http://localhost:8000/healthz
- Metricas: curl -s http://localhost:8000/metrics | head
- Grafana: http://localhost:3000 (dashboards provisionados)

---

## Passo 6 — Testes e Aquecimento de Cache
```
pytest -q
python scripts/cache_warmup.py --no-dry-run --only-ask --api-base http://localhost:8000
```

---

## Passo 7 — Fluxo de Trabalho (sempre)
- Fornecer latest dos arquivos a editar (nada de adivinhacao).
- Uma view por vez (subir/validar/medir), sem hardcodes.
- Commits padronizados: feat(core): ..., fix(gateway): ...
- Nao mergear sem pytest verde e painel sem warnings.
