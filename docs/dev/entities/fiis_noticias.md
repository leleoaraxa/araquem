# fiis_noticias

## Overview

- `id`: `fiis_noticias`
- `result_key`: `noticias_fii`
- `sql_view`: `fiis_noticias`
- `private`: `false`
- `description`: Notícias e matérias relevantes sobre FIIs (fonte externa consolidada D-1)

### Identifiers

- `ticker`: Ticker do FII normalizado (AAAA11)

## Columns

| Column | Alias | Description |
| --- | --- | --- |
| `ticker` | Código FII | Código do fundo na B3 (AAAA11). |
| `source` | Fonte | Fonte ou veículo da notícia. |
| `title` | Título | Título da matéria/notícia. |
| `tags` | Tags | Palavras-chave associadas à notícia. |
| `description` | Descrição | Resumo curto ou descrição da notícia. |
| `url` | URL | Link completo para a notícia. |
| `image_url` | URL da imagem | URL de imagem de destaque da notícia. |
| `published_at` | Publicada em | Data/hora de publicação da notícia. |
| `created_at` | Criado em | Data de criação do registro. |
| `updated_at` | Atualizado em | Data da última atualização do registro. |

## Presentation

- `kind`: `list`
- `fields.key`: `title`
- `fields.value`: `url`
- `empty_message`: Nenhuma notícia encontrada.

## Response Templates

- `data/entities/fiis_noticias/responses/list.md.j2`

## Ask Routing Hints

- `intents`: ``noticias``
- `keywords`: ``noticia, notícias, materia, reportagem, atualização, últimas, novidades``
- `synonyms`:
  - `ticker` → ativo, papel, fundo, fii
- `weights`:
  - `identifiers`: 2.0
  - `keywords`: 1.0
  - `synonyms`: 0.5
