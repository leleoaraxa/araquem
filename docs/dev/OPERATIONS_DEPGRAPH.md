```mermaid
graph TD
  Redis --> API
  Postgres --> API
  API --> Prometheus
  API --> Grafana
  API --> QualityCron
  API --> RAGRefresh
  Prometheus --> Grafana
```
