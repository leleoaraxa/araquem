# Entidade `fiis_news`

## 1. Visão geral

A entidade `fiis_news` concentra notícias e fatos relevantes públicos associados a fundos imobiliários (FIIs).
Ela é usada para responder perguntas do tipo:

- “Quais são as últimas notícias do HGLG11?”
- “Teve algum fato relevante recente do HGLG11?”
- “O que saiu na mídia sobre o XPLG11 nesta semana?”

Trata-se de uma visão textual, focada em títulos, resumos e metadados (fonte, data de publicação, URL).

> Observação: esta entidade **não** armazena conteúdo integral das matérias, apenas título, descrição resumida e metadados suficientes para exibir um resumo e apontar para a fonte original.

---

## 2. Origem e grain

- **View / tabela lógica**: `fiis_news`
- **Grain (nível de detalhe)**: 1 linha por **`ticker` + notícia** (título/URL únicos).
- **Chave natural** (conceitual):
  - `ticker` + `source` + `title` + `published_at`
- A ordenação típica de consumo (no Presenter/Narrator) é:
  - Por `ticker`, depois por `published_at` (do mais recente para o mais antigo).

---

## 3. Esquema (contrato)

### 3.1. Colunas

| Coluna        | Tipo        | Descrição                                                                                      | Exemplo                                                                                                           |
|---------------|------------|------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| `ticker`      | `text`     | Código do FII no padrão B3 (AAAA11).                                                           | `HGLG11`                                                                                                          |
| `source`      | `text`     | Fonte da notícia (veículo de mídia ou portal financeiro).                                      | `InfoMoney`, `Money Times`                                                                                       |
| `title`       | `text`     | Título da notícia ou fato relevante.                                                           | `FII HGLG11 preserva retorno anual acima de 8% e anuncia novos dividendos`                                       |
| `tags`        | `text`     | Lista de tags/tópicos associada à notícia (segmento, tema, tipo de evento etc.).               | `logístico; dividendos; contratos`                                                                               |
| `description` | `text`     | Resumo curto ou linha fina da notícia (quando disponível).                                     | `FII logístico mantém retorno anual acima de 8% e anuncia novo pagamento de dividendos aos cotistas.`            |
| `url`         | `text`     | URL da notícia na fonte original.                                                              | `https://www.infomoney.com.br/onde-investir/fii-hglg11-preserva-retorno-anual-acima-de-8-e-anuncia-novos-dividendos/` |
| `image_url`   | `text`     | URL de imagem de destaque associada à notícia (quando disponível).                            | `https://www.infomoney.com.br/.../hglg11-capa.jpg` (exemplo ilustrativo)                                        |
| `published_at`| `timestamp`| Data/hora de publicação da notícia na fonte original (zona normalmente em UTC ou padrão fonte).| `2025-11-28 00:00:00`                                                                                             |
| `created_at`  | `timestamp`| Data/hora em que o registro foi inserido no banco da SIRIOS.                                   | `2025-11-28 10:32:15`                                                                                             |
| `updated_at`  | `timestamp`| Data/hora da última atualização do registro no banco da SIRIOS.                                | `2025-11-28 10:32:15`                                                                                             |

### 3.2. Restrições e considerações

- `ticker` deve estar no formato normalizado `AAAA11` (normalização ocorre na camada de entrada, não na view).
- `url` deve ser única por `ticker` sempre que possível; se uma mesma notícia cobrir vários FIIs, haverá um registro por FII.
- `published_at` vem da fonte e pode não coincidir com `created_at`/`updated_at` (que são internos à SIRIOS).
- `tags` podem ser derivadas de:
  - metadados da fonte;
  - classificação própria da SIRIOS (pipeline de ingestão).

---

## 4. Uso típico no /ask

A entidade `fiis_news` é a **fonte principal** para perguntas de notícias e fatos relevantes.
No roteamento, ela é escolhida quando a pergunta contém termos como:

- “notícia”, “notícias”, “fato relevante”, “fatos relevantes”, “novidades”, “manchete”, “reportagem”, “o que saiu na mídia sobre…”.

Exemplos de perguntas que devem cair em `fiis_news`:

- “Quais são as últimas notícias do HGLG11?”
- “Teve algum fato relevante recente do HGLG11?”
- “O que saiu na imprensa sobre o XPLG11 neste mês?”
- “Tem alguma notícia negativa recente sobre o HGLG11?”
- “Quais são as últimas notícias sobre fundos imobiliários logísticos?”

Perguntas que **não** devem usar `fiis_news`:

- Sobre preços: “Quanto está o HGLG11 hoje?” → `fiis_precos`
- Sobre dividendos: “Quais foram os dividendos do HGLG11 este mês?” → `fiis_dividends`
- Sobre risco (Sharpe, drawdown etc.): → `fiis_financials_risk`
- Sobre snapshot financeiro (payout, alavancagem, vacância, PL etc.): → `fiis_financials_snapshot`
- Sobre processos judiciais: → `fiis_processos`

---

## 5. Exemplos de registros reais

Exemplo real de linha (HGLG11):

- `ticker`: `HGLG11`
- `source`: `InfoMoney`
- `title`: `FII HGLG11 preserva retorno anual acima de 8% e anuncia novos dividendos`
- `tags`: `logístico; dividendos; resultado`
- `url`: `https://www.infomoney.com.br/onde-investir/fii-hglg11-preserva-retorno-anual-acima-de-8-e-anuncia-novos-dividendos/`
- `image_url`: *(quando disponível, URL da imagem de capa)*
- `published_at`: `2025-11-28 00:00:00`
- `created_at` / `updated_at`: datas internas de ingestão.

---

## 6. Exemplos de perguntas canônicas (routing)

Sugestões de perguntas canônicas para uso em `routing_samples.json` e suítes de qualidade:

1. “Quais são as últimas notícias do HGLG11?”
2. “Teve algum fato relevante recente do HGLG11?”
3. “O que saiu na mídia sobre o HGLG11 no último mês?”
4. “Tem alguma notícia negativa recente sobre o HGLG11?”
5. “Quais foram as últimas notícias do XPLG11?”
6. “Quais são as últimas notícias sobre fundos imobiliários logísticos?”
7. “Me atualize com as notícias mais recentes sobre FIIs em geral.”
8. “Quais foram as últimas manchetes sobre o HGLG11?”
9. “Houve algum fato relevante envolvendo contratos ou locatários do HGLG11?”
10. “Quais notícias recentes destacaram o desempenho do HGLG11?”

Essas perguntas reforçam os tokens e frases definidas na ontologia (`fiis_news`) e ajudam a manter o roteamento estável.

---
