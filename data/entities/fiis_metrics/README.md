# fiis_metrics — projeções compute-on-read

`fiis_metrics` é um módulo de projeções SQL (SELECT) sem tabela ou view materializada. O planner/builder injeta parâmetros como ticker, janela, agregação, índice de referência e taxa alvo para calcular métricas no momento da leitura. Os templates deste diretório descrevem apenas o formato das respostas esperadas para cada projeção.
