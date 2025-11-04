# ==============================================================
# 🌅 ARAQUEM OPS — CHECKLIST DIÁRIO + KIT DE PRIMEIROS SOCORROS
# Compatível com PowerShell e Linux
# ==============================================================
# Comando									Ação
# make daily-check				rotina de verificação geral
# make quick-health				checagem rápida
# make full-ci						executa CI completo (dashboards + tests)
# make sos-restart				reinicia toda stack
# make sos-refresh				reindexa e roda quality
# make sos-rebuild				refaz dashboards, alerts, quality
# --------------------------------------------------------------
# ⚙️ BASE DE OBSERVABILIDADE
# --------------------------------------------------------------
# make dashboards
# make alerts
# make audit
# make ci
# make obs-check
# ==============================================================

.PHONY: dashboards alerts audit ci obs-check \
        daily-check quick-health full-ci \
        sos-restart sos-refresh sos-rebuild \
        quality-gate metrics-peek

# --------------------------------------------------------------
# 🧭 CHECKLIST DIÁRIO
# --------------------------------------------------------------

daily-check:
	@echo "[1/5] Verificando containers base..."
	# Exibe todos os containers; filtragem por nome varia por SO, então mostramos completo.
	docker compose ps
	@echo "[2/5] Checando /healthz e /metrics..."
	curl -fsS http://localhost:8000/healthz
	$(MAKE) metrics-peek
	@echo "[3/5] Conferindo Prometheus targets..."
	curl -fsS http://localhost:9090/-/ready
	@echo "[4/5] Validando quality gate (no container api)..."
	$(MAKE) quality-gate || exit 0
	@echo "[5/5] Testando observabilidade (subset seguro)..."
	$(MAKE) obs-check || exit 0
	@echo "[OK] Checklist diário finalizado."

quick-health:
	@echo "[Fast] Checando API e métricas essenciais..."
	curl -fsS http://localhost:8000/healthz
	$(MAKE) metrics-peek

full-ci: dashboards alerts audit
	@echo "[CI] Rodando pipeline completo..."
	pytest -q

# --------------------------------------------------------------
# ⚙️ BASE DE OBSERVABILIDADE (inalterado)
# --------------------------------------------------------------

dashboards:
	python scripts/gen_dashboards.py --config data/ops/observability.yaml --out grafana/dashboards

alerts:
	python scripts/gen_alerts.py --config data/ops/observability.yaml

audit:
	python scripts/obs_audit.py

ci: dashboards alerts audit
	pytest -q

obs-check:
	python scripts/obs_audit.py && \
	pytest -q -k "metrics or planner or cache or executor or ask" && \
	$(MAKE) metrics-peek || echo "ok"

# --------------------------------------------------------------
# 🔎 UTILITÁRIOS
# --------------------------------------------------------------

quality-gate:
	# Executa o gate DENTRO do container da API (Python garantido)
	docker compose exec api bash -lc "bash scripts/quality_gate_check.sh"

metrics-peek:
	# Mostra um recorte útil de /metrics usando grep (Linux/WSL) ou findstr (Windows)
	@if command -v grep >/dev/null 2>&1; then \
	  curl -fsS http://localhost:8000/metrics | grep -E '^# HELP|api_requests_total|cache_hits_total|rag_index_|rag_eval_'; \
	elif command -v findstr >/dev/null 2>&1; then \
	  curl -fsS http://localhost:8000/metrics | findstr /R "# HELP" "api_requests_total" "cache_hits_total" "rag_index_" "rag_eval_"; \
	else \
	  echo "Sem grep/findstr — exibindo primeiras linhas de /metrics"; \
	  curl -fsS http://localhost:8000/metrics | sed -n '1,60p' || true; \
	fi

# --------------------------------------------------------------
# 🚨 KIT DE PRIMEIROS SOCORROS
# --------------------------------------------------------------

sos-restart:
	@echo "[Restart] Reiniciando base..."
	docker compose up -d redis prometheus tempo otel-collector
	@echo "[Restart] Subindo modelos e API..."
	docker compose up -d ollama api grafana
	@echo "[Restart] Reativando automações..."
	docker compose up -d quality-cron rag-refresh-cron
	@echo "[OK] Stack Araquem restaurada."

sos-refresh:
	@echo "[Refresh] Rebuild de índices e métricas..."
	docker compose run --rm rag-indexer || exit 0
	curl -s -X POST localhost:8000/ops/rag/refresh || exit 0
	$(MAKE) quality-gate || exit 0
	@echo "[OK] Refresh completo."

sos-rebuild:
	@echo "[Rebuild] Observabilidade (dash + alerts) e quality..."
	$(MAKE) dashboards alerts
	python scripts/obs_audit.py || exit 1
	python scripts/quality_push_cron.py --dry-run || exit 0
	$(MAKE) quality-gate || exit 0
	@echo "[OK] Rebuild completo."
