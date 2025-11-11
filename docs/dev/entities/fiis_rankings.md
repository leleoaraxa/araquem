# fiis_rankings

## Overview

- `id`: `fiis_rankings`
- `result_key`: `rankings_fii`
- `sql_view`: `fiis_rankings`
- `private`: `false`
- `description`: Contagens históricas de aparições e movimentos em rankings (usuários, Sírios, IFIX e IFIL) por FII — snapshot 1×1 por ticker.

### Identifiers

- `ticker`: Ticker do FII normalizado (AAAA11)

## Columns

| Column | Alias | Description |
| --- | --- | --- |
| `ticker` | Código FII | Código do fundo na B3 (AAAA11). |
| `users_rank_position` | ranking usuários | Número de vezes em que o FII apareceu em rankings de usuários. |
| `users_rank_net_movement` | movimentos no ranking usuários | Quantidade de movimentos (subidas/quedas) registrados em rankings de usuários. |
| `sirios_rank_position` | ranking Sírios | Número de aparições do FII em rankings da SIRIOS. |
| `sirios_rank_net_movement` | movimentos no ranking Sírios | Quantidade de movimentos (subidas/quedas) registrados em rankings da SIRIOS. |
| `ifix_rank_position` | ranking IFIX | Número de aparições em compilações/recortes de ranking do IFIX. |
| `ifix_rank_net_movement` | movimentos no ranking IFIX | Movimentos de posição do FII em recortes de ranking do IFIX. |
| `ifil_rank_position` | ranking IFIL | Número de aparições em compilações/recortes de ranking do IFIL. |
| `ifil_rank_net_movement` | movimentos no ranking IFIL | Movimentos de posição do FII em recortes de ranking do IFIL. |
| `created_at` | Criado em | Data de criação do registro. |
| `updated_at` | Atualizado em | Data da última atualização do registro. |

## Presentation

- `kind`: `table`
- `fields.key`: `ticker`
- `fields.value`: `users_rank_position`
- `empty_message`: Sem rankings disponíveis.

## Response Templates

- `data/entities/fiis_rankings/responses/table.md.j2`

## Ask Routing Hints

- `intents`: ``rankings``
- `keywords`: ``ranking, posicao, posições, top, aparicoes, aparições, movimentos, ifix, ifil, usuarios, sirios, vezes``
- `synonyms`:
  - `ticker` → ativo, papel, fundo, fii
  - `users_rank_position` → usuarios, usuários, ranking de usuarios, vezes usuarios
  - `users_rank_net_movement` → usuarios movimento, variacao usuarios, movimentos usuarios
  - `sirios_rank_position` → sirios ranking, ranking da sirios, vezes sirios
  - `sirios_rank_net_movement` → sirios movimento, variacao sirios, movimentos sirios
  - `ifix_rank_position` → ifix ranking, vezes ifix, aparicoes ifix
  - `ifix_rank_net_movement` → ifix movimento, variacao ifix, movimentos ifix
  - `ifil_rank_position` → ifil ranking, vezes ifil, aparicoes ifil
  - `ifil_rank_net_movement` → ifil movimento, variacao ifil, movimentos ifil
- `weights`:
  - `identifiers`: 2.0
  - `keywords`: 1.0
  - `synonyms`: 0.5
