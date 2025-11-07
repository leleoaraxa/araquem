# ==============================================================
# 🌅 ARAQUEM OPS — CHECKLIST DIÁRIO + KIT DE PRIMEIROS SOCORROS
# Compatível com PowerShell (Windows) e Linux/macOS
# ==============================================================
# Comando                		| Ação
# --------------------------|--------------------------------------
# make daily-check       		| Rotina de verificação geral da stack
# make quick-health      		| Checagem rápida de /healthz e /metrics
# make full-ci           		| CI completo (dashboards + alerts + tests)
# make sos-restart       		| Reinicia serviços principais e crons
# make sos-refresh       		| Reindexa RAG e roda quality gate
# make sos-rebuild       		| Reconstrói dashboards, alerts e quality
# --------------------------------------------------------------
# ⚙️ BASE DE OBSERVABILIDADE
# --------------------------------------------------------------
# make dashboards        		| Gera **apenas** dashboards Grafana a partir do YAML
# make regen-observability 	| Gera dashboards **e** rules Prometheus (recording/alerting)
# make alerts            		| Gera **apenas** recording/alerting rules Prometheus
# make audit             		| Audita se artefatos estão mais novos que o YAML
# make ci                		| Dashboards + Alerts + Audit + Testes (pipeline curto)
# make obs-check         		| Smoke tests de observabilidade + /metrics inspeção
# ==============================================================

.PHONY: dashboards alerts audit ci obs-check \
        daily-check quick-health full-ci \
        sos-restart sos-refresh sos-rebuild \
        quality-gate metrics-peek regen-observability

# --------------------------------------------------------------
# 🔧 Cross-OS helpers (curl/grep em Windows/Linux)
# --------------------------------------------------------------
OS_NAME := $(shell uname 2>/dev/null || echo Windows)
IS_WINDOWS := $(findstring Windows,$(OS_NAME))
ifeq ($(IS_WINDOWS),Windows)
  CURL = curl.exe -fsS
  PS   = powershell -NoProfile -Command
  # Em PS, usamos Select-String como grep
  METRICS_FILTER = ^# HELP|api_requests_total|cache_hits_total|rag_index_|rag_eval_
  GREP_METRICS = $(PS) "(Invoke-WebRequest -UseBasicParsing http://localhost:8000/metrics).Content | Select-String -Pattern '$(METRICS_FILTER)' | ForEach-Object { \$_.Line }"
else
  CURL = curl -fsS
  GREP_METRICS = $(CURL) http://localhost:8000/metrics | grep -E '^# HELP|api_requests_total|cache_hits_total|rag_index_|rag_eval_'
endif

# --------------------------------------------------------------
# 🧭 CHECKLIST DIÁRIO
# --------------------------------------------------------------
daily-check:
	@echo "[1/5] Verificando containers base..."
	docker compose ps
	@echo "[2/5] Checando /healthz e /metrics..."
	$(CURL) http://localhost:8000/healthz > /dev/null
	$(MAKE) metrics-peek
	@echo "[3/5] Conferindo Prometheus targets..."
	$(CURL) http://localhost:9090/-/ready > /dev/null
	@echo "[4/5] Validando quality gate (no container api)..."
	-$(MAKE) quality-gate
	@echo "[5/5] Testando observabilidade (subset seguro)..."
	-$(MAKE) obs-check
	@echo "[OK] Checklist diário finalizado."

quick-health:
	@echo "[Fast] Checando API e métricas essenciais..."
	$(CURL) http://localhost:8000/healthz > /dev/null
	$(MAKE) metrics-peek

full-ci: dashboards alerts audit
	@echo "[CI] Rodando pipeline completo..."
	pytest -q

# --------------------------------------------------------------
# ⚙️ BASE DE OBSERVABILIDADE
# - dashboards: renderiza .json do Grafana a partir do YAML
# - regen-observability: dashboards + Prometheus rules (recording/alerting)
# - alerts: renderiza somente Prometheus rules
# - audit: confere se artefatos estão atualizados vs YAML
# - ci: pipeline curto (dashboards+alerts+audit+tests)
# - obs-check: auditoria + testes focados + amostra de /metrics
# --------------------------------------------------------------
dashboards:
	python scripts/observability/gen_dashboards.py --config data/ops/observability.yaml --out grafana/dashboards

regen-observability:
	python scripts/observability/gen_dashboards.py --config data/ops/observability.yaml --out grafana/dashboards
	python scripts/observability/gen_alerts.py --config data/ops/observability.yaml

alerts:
	python scripts/observability/gen_alerts.py --config data/ops/observability.yaml

audit:
	python scripts/observability/obs_audit.py

ci: dashboards alerts audit
	pytest -q

obs-check:
	python scripts/observability/obs_audit.py
	pytest -q -k "metrics or planner or cache or executor or ask"
	$(MAKE) metrics-peek || true

# --------------------------------------------------------------
# 🔎 UTILITÁRIOS
# --------------------------------------------------------------
quality-gate:
	# Executa o gate DENTRO do container da API (Python garantido)
	docker compose exec api bash -lc "bash scripts/quality/quality_gate_check.sh"

metrics-peek:
	# Amostra útil do /metrics (Windows usa Select-String; Linux usa grep)
	@$(GREP_METRICS) || true

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
	- docker compose run --rm rag-indexer
	- $(CURL) -X POST http://localhost:8000/ops/rag/refresh
	- $(MAKE) quality-gate
	@echo "[OK] Refresh completo."

sos-rebuild:
	@echo "[Rebuild] Observabilidade (dash + alerts) e quality..."
	$(MAKE) dashboards alerts
	python scripts/observability/obs_audit.py
	- python scripts/quality/quality_push_cron.py --dry-run
	- $(MAKE) quality-gate
	@echo "[OK] Rebuild completo."
