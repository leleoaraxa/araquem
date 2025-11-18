# Quality datasets

Only production datasets used by the quality cron should live in this directory. Keep routing and projection samples here so the cron can load them via the single `data/ops/quality/*.json` glob.

Move any experimental, evaluation, or ad-hoc datasets to `../quality_experimental/` so they are not processed automatically.
