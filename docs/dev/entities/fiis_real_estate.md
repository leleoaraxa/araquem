# Entidade `fiis_real_estate`

## 1. Visão geral

`fiis_real_estate` lista os imóveis e ativos operacionais de cada FII, com informações de nome, classe, endereço, área, unidades, vacância e status. Base D-1, com múltiplas linhas por fundo.

Perguntas típicas:
- “Quais imóveis compõem o HGLG11?”
- “Qual a vacância dos ativos do XPML11?”
- “Quantas unidades o VISC11 tem e quais endereços?”

## 2. Origem dos dados e contrato

- **View/Tabela base**: `fiis_real_estate`.
- **Chave lógica**: `(ticker, asset_name)`.
- **Granularidade**: nível de ativo/imóvel do FII.

Campos principais (do contrato `fiis_real_estate.schema.yaml`):
- Identificação: `ticker`, `asset_name`, `asset_class`, `asset_address`.
- Métricas físicas: `total_area`, `units_count`.
- Ocupação e risco: `vacancy_ratio`, `non_compliant_ratio`, `assets_status`.
- Metadados: `created_at`, `updated_at`.

## 3. Identificadores

- **ticker**: obrigatório, suporta múltiplos.

## 4. Grupos de colunas

- **Descrição do ativo**: `asset_name`, `asset_class`, `asset_address`.
- **Capacidade física**: `total_area`, `units_count`.
- **Ocupação/risco**: `vacancy_ratio`, `non_compliant_ratio`, `assets_status`.
- **Metadados**: `created_at`, `updated_at`.

## 5. Exemplos de perguntas que devem cair em `fiis_real_estate`

- “Quais imóveis o HGLG11 possui?”
- “Vacância dos ativos do XPML11.”
- “Quais endereços fazem parte do VISC11?”
- “Qual o tamanho (m²) dos imóveis do KNRI11?”
- “Quais ativos do fundo estão inadimplentes?”

## 6. Observações

- Foco operacional por ativo; indicadores financeiros consolidados ficam em outras entidades (`fiis_financials_snapshot`, etc.).
