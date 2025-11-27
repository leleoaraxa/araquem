## Descrição
Dados cadastrais básicos do FII, incluindo nomes oficiais, CNPJ e administrador.

## Exemplos de perguntas
- "qual o CNPJ do HGLG11?"
- "quem administra o VISC11?"
- "qual o site oficial do MXRF11?"

## Respostas usando templates
### list_basic
{ticker} — {display_name} | CNPJ {fii_cnpj|cnpj_mask} — Adm. {admin_name} (CNPJ {admin_cnpj|cnpj_mask}) — {website_url}

### FALLBACK_row
Dados cadastrais do {ticker} não disponíveis no momento.
