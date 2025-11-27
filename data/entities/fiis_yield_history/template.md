{% if rows and rows|length > 0 -%}
  {%- set tickers = rows | map(attribute='ticker') | list | unique -%}
  {%- if tickers|length == 1 -%}
Histórico de dividendos e DY mensal do **{{ tickers[0] }}**:
  {%- else -%}
Histórico de dividendos e DY mensal dos FIIs consultados:
  {%- endif -%}

O DY mensal reflete o retorno em dividendos do mês em relação ao preço de referência da cota naquele período. Valores nulos indicam ausência de cotação ou cálculo de DY no mês.

{% include "responses/table.md.j2" %}
{%- else -%}
{{ empty_message or "Nenhum dado de dividend yield encontrado para os filtros informados." }}
{%- endif %}
