.PHONY: dashboards alerts audit ci obs-check

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
	curl -s http://localhost:8000/metrics | grep -E "sirios_|planner_"
