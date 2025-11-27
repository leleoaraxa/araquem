## Descrição
Portfólio físico de imóveis dos FIIs, com classe, localização, área e indicadores de ocupação.

## Exemplos de perguntas
- "quais imóveis compõem o HGLG11?"
- "qual a vacância do portfólio do VISC11?"
- "onde ficam os ativos do XPML11?"

## Respostas usando templates
### list_basic
{ticker}: {asset_name} — {asset_class} — {asset_address} — {total_area|number_br} m², {units_count|int_br} unid, vacância {vacancy_ratio|percent_br}, inadimplência {non_compliant_ratio|percent_br}, status {assets_status}.

### FALLBACK_row
Dados de imóveis do {ticker} não disponíveis no momento.
