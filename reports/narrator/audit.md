# Auditoria de Prontidão – Narrator / Ontologia / FACTS

## 1. Ontologia — Estado Atual
- **Status:** Parcialmente estável. Buckets e intents existem, mas há sobreposições e redundâncias que podem gerar ambiguidade.
- **Colisões/Exemplos:**
  - `ticker_query` inclui `fiis_dividends_yields` duas vezes e mistura entidades heterogêneas (preço, dividendos, riscos, imóveis), ampliando a superfície de roteamento 【F:data/ontology/entity.yaml†L41-L64】.
  - Termos amplos em `client_fiis_positions` incluem `<ticker>` com intenções de peso/quantidade, mas excluem palavras de risco/benchmark; ainda assim, a cobertura extensa pode capturar perguntas sobre desempenho ou rankings por engano 【F:data/ontology/entity.yaml†L66-L160】.
- **Amplitude vs. especificidade:**
  - Entidades de bucket A são específicas (preços, dividendos, rankings), mas agrupadas em uma única intent “ticker_query”, tornando-a muito ampla para desambiguação fina.
  - `client_fiis_positions` é ampla (posições, alocação, prejuízo/ganho) e pode sobrepor perguntas de performance e dividendos apesar das exclusões.
- **Impacto de novas entidades:** inclusão de novas métricas ou intents ligadas a FIIs pode colidir com `ticker_query` por regex genérica `[A-Za-z]{4}11` sem filtros adicionais.
- **Previsibilidade para Narrator:** Ontologia fornece entidades focadas, porém a intent “catch-all” para tickers e a amplitude de tokens em posições mantêm risco de seleção incorreta de entidade, prejudicando previsibilidade do Narrator.

## 2. FACTS / Formatter — Estado Atual
- **Status:** Parcialmente consistentes. A maioria segue blocos tabulares/listas, mas há narrativa embutida.
- **Padrão e prontidão:**
  - Templates de tabela geralmente apresentam cabeçalho Markdown e iteração de `rows`, com mensagem de vazio. Ex.: `fiis_quota_prices` abre com frase narrativa antes da tabela 【F:data/entities/fiis_quota_prices/responses/table.md.j2†L1-L16】.
  - Alguns templates misturam resumo textual e bullets com métricas (ex.: snapshot financeiro) em vez de tabela pura, o que exige cautela para Narrator consumir diretamente 【F:data/entities/fiis_financials_snapshot/responses/table.md.j2†L1-L27】.
- **Entidades OK (padrão tabular/lista simples):** `fiis_legal_proceedings`, `fiis_rankings`, `history_b3_indexes`, `history_currency_rates`, `history_market_indicators`, `macro_consolidada`, `client_fiis_dividends_evolution`, `client_fiis_performance_vs_benchmark`, `client_fiis_enriched_portfolio` (seguem tabela ou lista com empty message).
- **Entidades problemáticas:**
  - `fiis_quota_prices`: narrativa inicial com preço e variação antes da tabela, pode conflitar com camada de Narrator.【F:data/entities/fiis_quota_prices/responses/table.md.j2†L1-L16】
  - `fiis_financials_snapshot`: bullet list rica em narrativa e interpretação, não apenas FACTS tabulares.【F:data/entities/fiis_financials_snapshot/responses/table.md.j2†L1-L27】
  - `fiis_news`/`fiis_registrations` (listas) podem trazer textos longos; necessidade de garantir que o Narrator mantenha factualidade.

## 3. Narrator — Prontidão Real
- **Status:** Pronto, mas com ressalvas. Existe Modelfile dedicado e prompt claro, porém depende de FACTS limpos.
- **Riscos:**
  - Alucinação baixa (prompts orientam uso estrito de FACTS), mas há risco de perda de precisão se FACTS já tiverem narrativa embutida ou se ontologia roteia para entidade errada.【F:app/narrator/prompts.py†L11-L105】
  - Estilo é controlado por templates `summary`, `list`, `table`, `concept`, mas depende de meta correta na chamada.【F:app/narrator/prompts.py†L26-L50】
- **Padrão “resumo humano curto + bloco factual imutável”:** ainda não está explícito no formatter; templates atuais já geram narrativa + tabela, mas não separam bloco imutável. Exigirá ajustes no formatter para fornecer FACTS puros para Narrator compor o resumo.

## 4. Integração Geral (Pipeline)
- **Suporte a humanização opcional:** Parcial. Narrator tem prompts e few-shots; formatter fornece FACTS, mas alguns já humanizados. Auditabilidade/determinismo ficam frágeis quando FACTS trazem texto interpretativo (ex.: preço resumido, snapshot financeiro), reduzindo ganho do Narrator.
- **Ponto provável de falha:**
  - **Ontologia:** intent “ticker_query” muito ampla pode selecionar entidade errada ao entrar novas métricas.
  - **Formatter:** presença de narrativa embutida gera risco de dupla humanização e inconsistência.
  - Narrator e integração parecem sólidos, desde que recebam FACTS limpos e meta correta.

## 5. Conclusão Executiva
- **Pronto (safe to proceed):** Arquitetura do Narrator, prompts e few-shots dedicados; maioria dos templates segue padrão tabular/lista com mensagens de vazio.
- **Quase pronto (ajustes pontuais):** Revisão dos templates que misturam narrativa (preços, snapshot) para separar FACTS puros; reforçar ontologia para reduzir sobreposições em intents de ticker e posições.
- **Bloqueios:** Ambiguidade da intent “ticker_query” e FACTS com narrativa prévia comprometem auditabilidade e previsibilidade do Narrator.
- **Veredito:** Sim, com condições — avançar para humanização controlada somente após limpar FACTS de narrativa e refinar ontologia para desambiguação de novas entidades.
