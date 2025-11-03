.PHONY: obs-check

obs-check:
	python scripts/obs_audit.py && \
	pytest -q -k "metrics or planner or cache or executor or ask" && \
	curl -s http://localhost:8000/metrics | grep -E "sirios_|planner_"
