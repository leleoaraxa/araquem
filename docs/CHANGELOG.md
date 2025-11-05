# CHANGELOG

## M9 – Entidades 1×N (imóveis, processos, notícias)
- Criados contratos das novas entidades em `data/entities/fiis_imoveis.yaml`, `data/entities/fiis_processos.yaml` e `data/entities/fiis_noticias.yaml`, com whitelists de ordenação e D-1 preservado.
- Atualizados builder, formatter, responder e ontologia (`app/builder/sql_builder.py`, `app/formatter/rows.py`, `app/responder/__init__.py`, `data/ontology/entity.yaml`) para suportar colunas reais, filtros de período e templates list_basic/FALLBACK.
- Inclusos templates determinísticos (`data/concepts/fiis_*_templates.md`), painel de observabilidade (`grafana/quality_dashboard.json`), amostras de roteamento e testes dedicados (`tests/test_fiis_*`, `tests/test_responder_*`).
- Contrato do `/ask` permanece inalterado (mesma chave de resposta, mesmos campos) e o recorte temporal segue D-1.
- Comandos de verificação:
  ```bash
  pytest -q -k "imoveis or processos or noticias or responder"
  python scripts/quality_push.py data/ops/quality/routing_samples.json
  curl -s http://localhost:8000/ops/quality/report | jq
  grep -H . data/entities/fiis_*yaml
  ```
