# Índice do banco de dados

- Contratos: `data/contracts/entities/*.schema.yaml` (fonte única para esquemas e campos).
- Entidades: `data/entities/` (definições operacionais alinhadas aos contratos).
- Políticas: `data/policies/` (limites, qualidade e governança aplicadas às entidades).
- Ontologia: `data/ontology/` (relacionamentos e roteamento entre intents e entidades).
- Projeções: `fiis_metrics` é calculado sob demanda (compute-on-read) e não possui entidade física.

Os exemplos e DDLs permanecem neste diretório em `data_sample/` e `ddls/`.
