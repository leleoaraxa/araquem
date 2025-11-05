# Censo de Heurísticas e Hardcodes — M9

## 1. Resumo executivo
- Varredura completa em `app/*`, `scripts/*`, `tests/*` e `docs/*` identificou 9 heurísticas relevantes nos componentes críticos (Planner, Builder/SQL, Orchestrator/Responder, Formatter, API).
- A maioria dos problemas concentra-se em decisões de negócio embutidas no código Python, especialmente parametrizações de SQL, templates de resposta e formatação de dados.
- O `sql_builder` acumula desvios graves do contrato YAML-driven ao fixar colunas, limites e campos de período específicos para entidades FIIs.
- O responder e o formatter mantêm mapas estáticos de entidades/colunas que deveriam residir nos dicionários declarativos em `data/`.
- Há limiares e regex de roteamento codificados diretamente no Planner/Orchestrator, criando riscos de divergência e tornando ajustes operacionais lentos.
- Recomenda-se refatoração faseada priorizando remoção de heurísticas de SQL e apresentação, seguida pela externalização de thresholds e caches especiais.

## 2. Tabela geral de achados
| arquivo | linhas | categoria | resumo | severidade | fix_sugerido_curto |
| --- | --- | --- | --- | --- | --- |
| app/builder/sql_builder.py | 200-206 | SQL não governado por entidade YAML | Campo de período força `published_at` para `fiis_noticias` fora do YAML | Alta | Declarar `period_filter_field` no YAML da entidade e remover `elif` específico |
| app/builder/sql_builder.py | 244-255 | “Magic numbers/strings” e thresholds | Limites `LIMIT 100`/`limit=10` definidos no código | Média | Ler limites padrão de `aggregations.defaults` e validar via YAML |
| app/builder/sql_builder.py | 315-325 | Mapas estáticos de entidades/colunas | Seleção de coluna métrica fixa (`dividend_amt`/`close_price`) | Alta | Mover mapeamento de métricas para `aggregations` no YAML e consumir dinamicamente |
| app/responder/__init__.py | 10-48 | Templates/formatos fora de `data/concepts/*_templates.md` | Dicionário com templates e campos obrigatórios por entidade | Alta | Declarar metadados de template no YAML/concepts e carregar de forma declarativa |
| app/formatter/rows.py | 30-32 | Formatação de dados fora do formatter declarativo | Conjuntos de colunas de data/percentual/moeda codificados | Média | Criar mapa declarativo em YAML/ops e dirigir formatação por configuração |
| app/formatter/rows.py | 68-76 | Formatação de dados fora do formatter declarativo | Regras de formatação por métrica (`dividends_sum`, `dy_avg` etc.) | Média | Externalizar regras de métrica para config declarativa consumida pelo formatter |
| app/orchestrator/routing.py | 29-66 | Roteamento/Intents fora do YAML | Regex de ticker FII hardcoded para extrair identificadores | Média | Mover regex/padrões para ontologia/config e permitir atualização via YAML |
| app/api/ask.py | 115-121 | Mapas estáticos de entidades/colunas | Atalho de cache exclusivo para `fiis_metrics` | Média | Declarar políticas de cache por entidade em YAML/ops e aplicar dinamicamente |
| app/planner/planner.py | 20-34 | “Magic numbers/strings” e thresholds | Thresholds e pesos RAG default embutidos (_THRESH_DEFAULTS) | Média | Definir defaults no YAML de operações e falhar se ausentes, evitando fallback mágico |

## 3. Achados por categoria

### Categoria: SQL não governado por entidade YAML

#### Achado #1
**Arquivo/Linhas:** app/builder/sql_builder.py (L200-L206)  
**Categoria:** SQL não governado por entidade YAML  
**Objetivo aparente:** Forçar `published_at` como campo de período quando a entidade é `fiis_noticias`.  
**Risco/impacto:** Divergência entre YAML da entidade e o builder; ajustes de período exigem alteração de código e podem quebrar outras entidades que compartilhem o builder.  
**Trecho (c/ contexto 3–7 linhas):**
```python
# path: app/builder/sql_builder.py (L199-L206)
        if isinstance(raw_field, str) and raw_field.strip():
            period_field = raw_field.strip()
        elif entity == "fiis_noticias":
            period_field = "published_at"
        elif default_date_field:
            period_field = default_date_field
```
**Correção sugerida (alinhada ao guardrails):**
- Declarar `period_filter_field` para `fiis_noticias` (e demais entidades) no YAML `data/entities/*.yaml`.
- Adaptar o builder para confiar exclusivamente no YAML, sem condicionais por entidade.
- Adicionar validação que falha se a entidade não definir `period_filter_field` quando obrigatória.
- Cobrir com teste de regressão garantindo leitura declarativa do campo de período.

### Categoria: “Magic numbers/strings” e thresholds

#### Achado #2
**Arquivo/Linhas:** app/builder/sql_builder.py (L244-L255)  
**Categoria:** “Magic numbers/strings” e thresholds  
**Objetivo aparente:** Impor limites padrão de paginação (100 linhas para SELECT simples, limite inferido 10).  
**Risco/impacto:** Dificulta tuning via YAML; mudanças operacionais exigem deploy; risco de divergência com `aggregations.defaults.limit`.  
**Trecho (c/ contexto 3–7 linhas):**
```python
# path: app/builder/sql_builder.py (L244-L255)
    if not (agg_enabled and agg_params and isinstance(agg_params, dict)):
        where_sql = f" WHERE {' AND '.join(where)}" if where else ""
        cols_sql = base_cols_sql
        sql = f"SELECT {cols_sql} FROM {view_name}{where_sql} LIMIT 100"
        return sql, params, result_key, return_cols

    agg = (agg_params.get("agg") or "").lower()
    window = agg_params.get("window")
    order = (agg_params.get("order") or "desc").lower()
    limit = int(agg_params.get("limit") or 10)
```
**Correção sugerida (alinhada ao guardrails):**
- Ler limites padrão de `aggregations.defaults` no YAML da entidade (para list/avg/sum).
- Remover fallback `LIMIT 100`; usar valor declarativo ou falhar se ausente.
- Incluir validação que bloqueia limites fora do whitelist definido em YAML.
- Propagar limites configuráveis via arquivos `data/ops` quando não específicos por entidade.

#### Achado #3
**Arquivo/Linhas:** app/planner/planner.py (L20-L34)  
**Categoria:** “Magic numbers/strings” e thresholds  
**Objetivo aparente:** Fornecer defaults embutidos para thresholds e parâmetros RAG quando YAML não está disponível.  
**Risco/impacto:** Atualizações operacionais não propagam sem deploy; valores podem divergir de `data/ops/planner_thresholds.yaml`, reduzindo governança.  
**Trecho (c/ contexto 3–7 linhas):**
```python
# path: app/planner/planner.py (L20-L34)
_THRESH_DEFAULTS = {
    "planner": {
        "thresholds": {
            "defaults": {"min_score": 1.0, "min_gap": 0.5},
            "intents": {},
            "entities": {},
            "apply_on": "base",
        },
        "rag": {
            "enabled": False,
            "k": 5,
            "min_score": 0.20,
            "weight": 0.35,
            "re_rank": {"enabled": False, "mode": "blend", "weight": 0.25},
        },
    }
}
```
**Correção sugerida (alinhada ao guardrails):**
- Centralizar todos os defaults em `data/ops/planner_thresholds.yaml`, incluindo valores de RAG.
- Fazer o loader falhar explicitamente ou emitir alerta observável quando o YAML estiver ausente.
- Permitir override via variável de ambiente apenas apontando para outro YAML, não para valores embutidos.
- Criar teste que verifica consistência entre o YAML e os thresholds carregados (sem fallback mágico).

### Categoria: Mapas estáticos de entidades/colunas

#### Achado #4
**Arquivo/Linhas:** app/builder/sql_builder.py (L315-L325)  
**Categoria:** Mapas estáticos de entidades/colunas  
**Objetivo aparente:** Escolher colunas específicas para agregação média/soma conforme entidade (`dividend_amt`, `close_price`).  
**Risco/impacto:** Amarra contratos de métricas ao código; adicionar nova entidade exige alteração manual; risco de regressão se YAML definir colunas diferentes.  
**Trecho (c/ contexto 3–7 linhas):**
```python
# path: app/builder/sql_builder.py (L315-L325)
    if _entity_is_dividendos():
        metric_col = "dividend_amt"
        null_date_cast = "NULL::timestamp"
        other_null = "NULL::timestamp"
    else:
        # preços: usar close_price como métrica padrão (contrato simples)
        metric_col = "close_price"
        null_date_cast = "NULL::date"
        other_null = "NULL::date"
```
**Correção sugerida (alinhada ao guardrails):**
- Declarar no YAML da entidade qual coluna suporta `avg`/`sum` e quais casts aplicar.
- Permitir múltiplas métricas configuradas via `aggregations.metrics` ou similar, eliminando `if entity == ...`.
- Validar em tempo de load que a coluna existe na view e corresponde ao tipo esperado.
- Adicionar testes cobrindo entidades diferentes consumindo o mesmo builder sem alterar código.

#### Achado #5
**Arquivo/Linhas:** app/api/ask.py (L115-L121)  
**Categoria:** Mapas estáticos de entidades/colunas  
**Objetivo aparente:** Tratar `fiis_metrics` com política de cache diferenciada diretamente na API.  
**Risco/impacto:** Dificuldade para introduzir novas entidades com cache especial; viola governança declarativa de políticas operacionais.  
**Trecho (c/ contexto 3–7 linhas):**
```python
# path: app/api/ask.py (L115-L121)
    if entity == "fiis_metrics":
        # Compute-on-read metrics possuem cache especializado no Orchestrator
        rt = {"cached": False, "value": _fetch(), "key": None, "ttl": None}
        cache_outcome = "miss"
    else:
        rt = read_through(cache, policies, entity, identifiers, _fetch)
        cache_outcome = "hit" if rt.get("cached") else "miss"
```
**Correção sugerida (alinhada ao guardrails):**
- Declarar políticas de cache (incluir/excluir) em `data/ops/cache_policies.yaml` ou equivalente.
- Fazer a API consultar o Orchestrator/política declarativa em vez de condicionar pelo nome da entidade.
- Expor testes que garantam tratamento uniforme para novas entidades apenas ajustando config.
- Monitorar via métricas quando política declarativa resultar em cache miss/hit para ajustes futuros.

### Categoria: Templates/formatos fora de `data/concepts/*_templates.md`

#### Achado #6
**Arquivo/Linhas:** app/responder/__init__.py (L10-L48)  
**Categoria:** Templates/formatos fora de `data/concepts/*_templates.md`  
**Objetivo aparente:** Definir, por entidade, templates e campos obrigatórios para listas diretamente no código.  
**Risco/impacto:** Alterações na apresentação ou requisitos exigem deploy; dificulta governança centralizada de templates declarativos.  
**Trecho (c/ contexto 3–7 linhas):**
```python
# path: app/responder/__init__.py (L10-L42)
_LIST_TEMPLATE_CONFIG = {
    "fiis_imoveis": {
        "row_template": "list_basic",
        "fallback_template": "FALLBACK_row",
        "required_fields": [
            "ticker",
            "asset_name",
            "asset_class",
            "asset_address",
```
**Correção sugerida (alinhada ao guardrails):**
- Mover configuração de templates/listas para arquivos `data/concepts/*` ou `data/ops/responder.yaml`.
- Carregar metadados (required_fields, fallback) junto com os templates declarados, eliminando o dicionário estático.
- Permitir que cada entidade defina requisitos via YAML, inclusive validações de campos.
- Criar testes que confirmem que novas entidades são suportadas sem tocar no código Python.

### Categoria: Formatação de dados fora do formatter declarativo

#### Achado #7
**Arquivo/Linhas:** app/formatter/rows.py (L30-L32)  
**Categoria:** Formatação de dados fora do formatter declarativo  
**Objetivo aparente:** Mapear colunas específicas como datas, percentuais e moeda diretamente no código.  
**Risco/impacto:** Adição de novas colunas formatadas exige deploy; quebra a diretriz de mapear formatação via dicionários declarativos.  
**Trecho (c/ contexto 3–7 linhas):**
```python
# path: app/formatter/rows.py (L30-L32)
DATE_COLUMNS = {"published_at", "initiation_date", "updated_at", "created_at"}
PERCENT_COLUMNS = {"vacancy_ratio", "non_compliant_ratio", "loss_risk_pct"}
CURRENCY_COLUMNS = {"cause_amt"}
```
**Correção sugerida (alinhada ao guardrails):**
- Criar arquivo declarativo (ex.: `data/ops/formatting.yaml`) com tipos por coluna.
- Carregar o mapa declarativo no formatter, permitindo extensão sem alteração de código.
- Validar que colunas declaradas existem no retorno para evitar divergência silenciosa.
- Adicionar teste cobrindo inclusão de nova coluna formatada apenas via YAML.

#### Achado #8
**Arquivo/Linhas:** app/formatter/rows.py (L68-L76)  
**Categoria:** Formatação de dados fora do formatter declarativo  
**Objetivo aparente:** Definir regras de exibição específicas para métricas (`dividends_sum`, `dy_avg`, etc.) diretamente no código.  
**Risco/impacto:** Novas métricas ou ajustes de formato exigem deploy; impede customização por entidade ou métrica via `data/`.  
**Trecho (c/ contexto 3–7 linhas):**
```python
# path: app/formatter/rows.py (L68-L76)
    if metric in {"dividends_sum", "price_avg"}:
        return f"R$ {_format_decimal_br(decimal_value, 2)}"

    if metric == "dividends_count":
        integer_value = decimal_value.to_integral_value(rounding=ROUND_HALF_UP)
        return f"{integer_value}"

    if metric == "dy_avg":
        return f"{_format_decimal_br(decimal_value, 2)}%"
```
**Correção sugerida (alinhada ao guardrails):**
- Declarar formatos por métrica em `data/entities/fiis_metrics.yaml` ou arquivo dedicado a métricas.
- Converter o formatter para ler regras (tipo, casas, sufixo) desse dicionário declarativo.
- Permitir extensibilidade adicionando métricas sem editar o código Python.
- Criar teste cobrindo mapeamento de formato baseado em configuração externa.

### Categoria: Roteamento/Intents fora do YAML

#### Achado #9
**Arquivo/Linhas:** app/orchestrator/routing.py (L29-L66)  
**Categoria:** Roteamento/Intents fora do YAML  
**Objetivo aparente:** Detectar tickers de FIIs via regex fixa (`[A-Za-z]{4}11`) na camada de entrada.  
**Risco/impacto:** Não cobre variações declaradas; alteração de padrão exige deploy; quebra guardrail de extrair intents/identificadores da ontologia/config.  
**Trecho (c/ contexto 3–7 linhas):**
```python
# path: app/orchestrator/routing.py (L29-L66)
# Normalização de ticker na camada de ENTRADA (contrato Araquem)
TICKER_RE = re.compile(r"\b([A-Za-z]{4}11)\b")
...
    def extract_identifiers(self, question: str) -> Dict[str, Any]:
        m = TICKER_RE.search(question.upper())
        return {"ticker": m.group(1) if m else None}
```
**Correção sugerida (alinhada ao guardrails):**
- Declarar padrões/regex de identificadores em `data/ontology` ou `data/ops/identifiers.yaml`.
- Carregar a regex (ou lista de padrões) dinamicamente, permitindo múltiplos formatos.
- Permitir testes de regressão que adicionem novos identificadores sem tocar no código.
- Instrumentar métricas para detectar falhas de extração baseadas em configuração externa.

## 4. Plano de refatoração faseado
- **Fase 1 (baixo risco):** Externalizar mapas declarativos do formatter e responder (`app/formatter/rows.py`, `app/responder/__init__.py`) para arquivos em `data/`, adicionando testes de regressão que assegurem carregamento dinâmico.
- **Fase 2 (médio risco):** Ajustar `sql_builder` para consumir exclusivamente definições de `data/entities/*.yaml`, removendo limites mágicos e colunas fixas; mover política de cache de `app/api/ask.py` para YAML.
- **Fase 3 (alto risco):** Revisar thresholds do Planner e regex de identificadores no Orchestrator para depender 100% de configuração declarativa, com validação e fallback observável (não silencioso).

## 5. Apêndice A — Critérios de detecção e regex usadas
```
(?i)\b(fiis?_?\w*|im[oó]veis?|process(os)?|not[ií]cias?)\b
(?i)\bselect\b.*\bfrom\b
(?i)\border\s+by\b
(?i)\bbetween\b.*\band\b
(?i)\bif\s+.*\bin\b.*question
(?i)re\.(findall|search)\(
(?i)f["'].*{.*}.*["']
(?i)\b\d+(\.\d+)?\b
```

## 6. Apêndice B — Falsos positivos conhecidos
Nenhum falso positivo identificado durante a varredura desta iteração.
