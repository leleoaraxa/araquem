# Concepts Audit Report

## Inventário (estado atual)

Tabela com os arquivos reais em `data/concepts/`.

Árvore (até 4 níveis):

- data/concepts/catalog.yaml
- data/concepts/concepts-carteira.yaml
- data/concepts/concepts-fiis.yaml
- data/concepts/concepts-institutional-policies.yaml
- data/concepts/concepts-institutional-privacy.yaml
- data/concepts/concepts-institutional-product-positioning.yaml
- data/concepts/concepts-institutional-terms.yaml
- data/concepts/concepts-institutional.yaml
- data/concepts/concepts-macro-methodology.yaml
- data/concepts/concepts-macro.yaml
- data/concepts/concepts-risk-metrics-methodology.yaml
- data/concepts/concepts-risk.yaml
- data/concepts/concepts-support-errors.yaml
- data/concepts/concepts-support-howto.yaml
- data/concepts/concepts-support-plans.yaml
- data/concepts/concepts-support-troubleshooting.yaml
- data/concepts/concepts-support.yaml

| path | domínio | tipo | top-level keys | resumo |
| --- | --- | --- | --- | --- |
| data/concepts/catalog.yaml | catalog | catalog | concepts | Catálogo de arquivos e seções de concepts. |
| data/concepts/concepts-carteira.yaml | carteira | concepts | version, domain, owner, sections | Conceitos de carteira do investidor. |
| data/concepts/concepts-fiis.yaml | fiis | concepts | version, domain, owner, sections | Campos e conceitos base de FIIs. |
| data/concepts/concepts-institutional-policies.yaml | institutional | concepts | version, domain, owner, sections | Políticas e limites institucionais do /ask. |
| data/concepts/concepts-institutional-privacy.yaml | institutional | concepts | version, domain, owner, sections | Diretrizes de privacidade e proteção de dados. |
| data/concepts/concepts-institutional-product-positioning.yaml | institutional-product-positioning | concepts | version, domain, owner, sections | Posicionamento e diferenciais de produto. |
| data/concepts/concepts-institutional-terms.yaml | institutional-terms | concepts | version, domain, owner, sections | Glossário de termos institucionais. |
| data/concepts/concepts-institutional.yaml | institutional | concepts | version, domain, owner, sections | Visão geral institucional da SIRIOS e Íris. |
| data/concepts/concepts-macro-methodology.yaml | macro | methodology | version, domain, owner, sections | Metodologia macroeconômica e limitações. |
| data/concepts/concepts-macro.yaml | macro | concepts | version, domain, owner, sections | Conceitos macroeconômicos usados em FIIs. |
| data/concepts/concepts-risk-metrics-methodology.yaml | risk | methodology | version, domain, owner, sections | Metodologia para métricas de risco. |
| data/concepts/concepts-risk.yaml | risk | concepts | version, domain, owner, sections | Conceitos e métricas de risco em FIIs. |
| data/concepts/concepts-support-errors.yaml | support | concepts | version, domain, owner, sections | Erros comuns e correções. |
| data/concepts/concepts-support-howto.yaml | support | concepts | version, domain, owner, sections | Como fazer perguntas e interpretar respostas. |
| data/concepts/concepts-support-plans.yaml | support | concepts | version, domain, owner, sections | Planos e acesso. |
| data/concepts/concepts-support-troubleshooting.yaml | support | concepts | version, domain, owner, sections | Troubleshooting para perguntas no /ask. |
| data/concepts/concepts-support.yaml | support | concepts | version, domain, owner, sections | Orientações gerais de suporte. |

## Padrão canônico adotado

Resumo no arquivo `docs/dev/CONCEPTS_STYLE_GUIDE.md`.

## Auditoria de conformidade (lint lógico)

| arquivo | status | problemas encontrados | ação recomendada |
| --- | --- | --- | --- |
| data/concepts/catalog.yaml | OK | Catálogo incompleto antes da atualização (faltavam novos arquivos institucionais e suporte). | Atualizado para incluir 100% dos concepts atuais. |
| data/concepts/concepts-carteira.yaml | OK | Antes: ausência de `version` e uso de lista direta em `concepts`. | Padronizado para `sections` e `version: 1`. |
| data/concepts/concepts-fiis.yaml | OK | Antes: uso de `sections` em formato de mapa e itens sem estrutura consistente. | Estrutura convertida para `sections` + `items` canônicos. |
| data/concepts/concepts-institutional.yaml | OK | Antes: uso de `concepts` sem seções e ausência de versão. | Padronizado para `sections` e `version: 1`. |
| data/concepts/concepts-institutional-policies.yaml | OK | Antes: `concepts` sem seções. | Padronizado para `sections` canônicas. |
| data/concepts/concepts-institutional-privacy.yaml | OK | Antes: `concepts` sem seções. | Padronizado para `sections` canônicas. |
| data/concepts/concepts-institutional-product-positioning.yaml | OK | Antes: `domain` em snake_case e `concepts` sem seções. | `domain` normalizado (kebab-case) e `sections` canônicas. |
| data/concepts/concepts-institutional-terms.yaml | OK | Antes: `domain` em snake_case e `concepts` sem seções. | `domain` normalizado (kebab-case) e `sections` canônicas. |
| data/concepts/concepts-macro.yaml | OK | Antes: `concepts` sem seções e ausência de versão. | Padronizado para `sections` e `version: 1`. |
| data/concepts/concepts-macro-methodology.yaml | OK | Antes: estrutura própria (`methodology`, `series`, etc.). | Convertido para `sections` com itens e notas. |
| data/concepts/concepts-risk.yaml | OK | Antes: `concepts` sem seções e ausência de versão. | Padronizado para `sections` e `version: 1`. |
| data/concepts/concepts-risk-metrics-methodology.yaml | OK | Antes: estrutura própria (`abordagem_geral`, `metricas`). | Convertido para `sections` canônicas. |
| data/concepts/concepts-support.yaml | OK | Antes: `concepts` sem seções e ausência de versão. | Padronizado para `sections` e `version: 1`. |
| data/concepts/concepts-support-errors.yaml | OK | Antes: `concepts` sem seções e ausência de versão. | Padronizado para `sections` e `version: 1`. |
| data/concepts/concepts-support-howto.yaml | OK | Antes: `concepts` sem seções e ausência de versão. | Padronizado para `sections` e `version: 1`. |
| data/concepts/concepts-support-plans.yaml | OK | Antes: `domain` específico (`support_plans`) e `concepts` sem seções. | `domain` normalizado para `support` e `sections` canônicas. |
| data/concepts/concepts-support-troubleshooting.yaml | OK | Antes: `domain` específico (`support_troubleshooting`) e `concepts` sem seções. | `domain` normalizado para `support` e `sections` canônicas. |

### Decisões de unificação

- Conteúdo institucional e suporte foi mantido em arquivos separados para manter
  granularidade (políticas, privacidade, posicionamento, termos, erros, how-to,
  troubleshooting, planos). A unificação ocorreu no nível de schema, garantindo
  consistência sem remover conteúdo.
