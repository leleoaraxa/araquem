# Relatório Técnico — Guardrails Araquem v2.2.0

## Contexto
- Modo de diagnóstico no endpoint `/ask`, com habilitação do Narrator por variáveis de ambiente e fallback silencioso quando o módulo não está presente.
- Presença do modo "routing-only", que evita chamadas de orquestração e RAG.

## Achados
- Heurísticas embutidas no planner com pesos e thresholds padrão (pontuação mínima, gap mínimo, pesos de RAG/re-rank) definidos em código e não apenas em YAML.
- Carregamento tolerante a falhas no planner, retornando defaults de maneira silenciosa.

## Riscos
- Blocos `try/except` amplos ocultam falhas ao anexar contexto ou inicializar o Narrator.
- Ausência de validação explícita para variáveis de ambiente e arquivos de configuração, podendo mascarar erros operacionais.

## Evidências
- Comportamentos implícitos no endpoint `/ask`: habilitação do Narrator, fallback silencioso e modo "routing-only".
- Heurísticas e tolerância a falhas no planner, com defaults definidos em código e retorno silencioso quando há falhas de carregamento.
