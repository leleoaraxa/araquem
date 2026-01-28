# Concepts Style Guide

Este guia define o padrão canônico para documentos em `data/concepts/`. Ele foi
extraído dos padrões já existentes no repositório e visa manter consistência
entre domínios (fiis, risk, macro, institutional, support).

## Objetivos

- Manter um único schema para todos os documentos de concepts.
- Preservar conteúdo existente com mudanças apenas estruturais.
- Facilitar indexação em RAG e auditoria de qualidade.

## Schema canônico

Todos os arquivos de `data/concepts/*.yaml` (exceto `catalog.yaml`) devem seguir
esta estrutura:

```yaml
version: 1
domain: <string>
owner: <string>
sections:
  - id: <kebab-case>
    title: <string>
    items:
      - name: <string>
        description: <string>
        aliases: [<string>, ...]
        related_entities: [<string>, ...]
        related_intents: [<string>, ...]
        typical_questions: [<string>, ...]
        typical_uses: [<string>, ...]
        interpretation: [<string>, ...]
        definition: <string>
        usage: <string>
        cautions: <string>
        notes: [<string>, ...]
        subitems:
          - name: <string>
            description: <string>
```

### Top-level obrigatório

- `version`: versão do schema (inteiro). Atualmente, `1`.
- `domain`: domínio lógico (kebab-case).
- `owner`: responsável pelo conteúdo (ex.: `research`).
- `sections`: lista de seções do documento.

### Seções

Cada seção representa um bloco temático.

Campos obrigatórios:

- `id`: identificador em kebab-case (ex.: `risco-quantitativo`).
- `title`: título exibível.
- `items`: lista de itens/conceitos.

### Itens (conceitos, políticas, how-to, metodologia)

Campos obrigatórios:

- `name`: nome do conceito/tema.

Campos opcionais (use apenas quando aplicável):

- `description`: descrição textual.
- `aliases`: variações de nome para busca semântica.
- `related_entities`: entidades do catálogo de dados.
- `related_intents`: intenções relacionadas.
- `typical_questions`: perguntas típicas.
- `typical_uses`: usos típicos.
- `interpretation`: interpretações (lista de frases).
- `definition`: definição formal (metodologias).
- `usage`: como o conceito é usado no produto.
- `cautions`: cuidados/limitações específicas.
- `notes`: lista de observações em bullet.
- `subitems`: subitens seguindo o mesmo formato de item, para agrupar métricas ou
  campos de dados.

## Convenções de naming

- `domain` e `sections.id`: kebab-case (ex.: `institutional-terms`, `metricas`).
- `items.name`: pode ser human-friendly (ex.: "Sharpe Ratio") ou o nome técnico
  de campo (ex.: `preco_fechamento`).
- Evitar duplicar conteúdo entre arquivos; preferir referências em `catalog.yaml`
  quando houver sobreposição temática.
