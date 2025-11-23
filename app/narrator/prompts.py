# app/narrator/prompts.py
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List

SYSTEM_PROMPT = """Você é o Narrator do Araquem.

As regras principais de comportamento, estilo, segurança e uso de dados já estão
definidas no seu system prompt interno (modelo sirios-narrator). Aqui você deve:

- Ler a pergunta original do usuário ([PERGUNTA]).
- Usar os dados em [FACTS] como fonte primária para números e fatos objetivos.
- Usar [RAG_CONTEXT] apenas como apoio conceitual, sem copiar trechos literais.
- Respeitar o modo de resposta indicado (por exemplo, narrador_mode="concept").

A seguir, você receberá detalhes específicos (FACTS, RAG_CONTEXT, FOCUS_METRIC_KEY
e instruções de formato) que devem orientar APENAS esta resposta.
"""


PROMPT_TEMPLATES: Dict[str, str] = {
    "summary": """Produza uma resposta curta, em até 3 parágrafos:
- Comece respondendo diretamente à pergunta, priorizando a métrica em foco (se houver).
- Em seguida, explique em 2–3 frases como interpretar a métrica no contexto do fundo.
- Use apenas números presentes em FACTS. Não invente valores.
- Mantenha tom neutro, sem recomendar compra ou venda.""",
    "list": """Produza uma resposta em Markdown no formato de lista:
- Use os itens de `facts.rows` na mesma ordem.
- Em cada item, destaque os campos principais em **negrito**.
- Não crie campos adicionais e não invente números ou categorias que não existam em FACTS.""",
    "table": """Descreva os dados tabulares de forma sucinta:
- Explique o que cada coluna principal representa.
- Selecione apenas as colunas mais relevantes para a pergunta.
- Não extrapole conclusões além do que os dados fornecem.""",
    "concept": """Produza uma explicação **conceitual**, SEM mencionar fundos ou tickers específicos e SEM apresentar valores numéricos individuais.

Guia:
- Se [FOCUS_METRIC_KEY] estiver preenchido, explique apenas essa métrica (ex.: Sharpe, Beta,
  Sortino, volatilidade, MDD, R²): o que mede, como interpretar sinais/valores, e como é usada
  na análise de risco/retorno.
- Se não houver foco explícito, explique a métrica (ou conjunto de métricas) citada na pergunta.
- Traga uma interpretação prática para o investidor, sem dizer se um fundo é “bom” ou “ruim”.
- Não dê recomendação de investimento.
""",
}

FEW_SHOTS: Dict[str, str] = {
    "summary": """[EXEMPLO RESUMIDO]
Pergunta: explique as métricas de risco do HGLG11
FACTS (resumido):
{
  "primary": {
    "ticker": "HGLG11",
    "volatility_ratio": "1,44%",
    "sharpe_ratio": "-1,07%",
    "treynor_ratio": "-0,13%",
    "jensen_alpha": 0.0,
    "beta_index": 0.403,
    "sortino_ratio": "-10,19%",
    "max_drawdown": 0.1132,
    "r_squared": 0.0781
  }
}
RAG_CONTEXT (resumido):
- Texto explica que as principais métricas de risco são: volatilidade histórica,
  índices de Sharpe e Sortino, índice de Treynor, alfa de Jensen, beta, drawdown (MDD) e R².

Resposta esperada:
As principais métricas de risco utilizadas em FIIs incluem **volatilidade histórica**,
índices de **Sharpe** e **Sortino**, **Treynor**, **alfa de Jensen**, **beta**,
**máximo drawdown (MDD)** e **R²**, que medem, em conjunto, a relação entre retorno,
risco e aderência ao índice de referência.

No caso do **HGLG11**, os dados mais recentes indicam volatilidade em torno de 1,44%,
índices de Sharpe e Treynor negativos, beta próximo de 0,40, Sortino negativo e um
MDD de aproximadamente 11%. O R² baixo sugere que o fundo não acompanha de forma
muito próxima o índice usado como referência.
""",
    "concept": """[EXEMPLO CONCEITUAL]
Pergunta: Sharpe negativo em um FII quer dizer que ele é ruim?

FACTS:
- Sem uso de rows ou valores numéricos (modo conceitual).

RAG_CONTEXT:
- Explica que Sharpe mede o retorno excedente em relação a um ativo livre de risco,
  dividido pela volatilidade, e que valores negativos indicam desempenho abaixo do
  ativo livre de risco no período.

Resposta esperada:
O índice de Sharpe mede quanto de retorno excedente um investimento entregou em relação
a um ativo livre de risco, ajustando esse resultado pela volatilidade. Quando o Sharpe
fica negativo, significa que, no período analisado, o investidor assumiu risco, mas
recebeu menos do que receberia em uma aplicação de referência de baixo risco.

Isso não quer dizer, por si só, que o fundo seja “ruim” de forma definitiva, e sim
que, naquela janela de tempo, o retorno não compensou o risco. Por isso, o Sharpe
costuma ser avaliado em conjunto com outras métricas e em diferentes períodos.
""",
}


def _parse_number(value: Any) -> float | None:
    """Convert loosely formatted strings (currency/percent) into a float."""

    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except Exception:
            return None

    if not isinstance(value, str):
        return None

    text = value.strip()
    if not text:
        return None

    cleaned = (
        text.replace("R$", "").replace("%", "").replace(" ", "").replace("\u00a0", "")
    )

    if "," in cleaned and "." in cleaned:
        # Formato pt-BR: 1.234,56 → 1234.56
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")

    try:
        return float(cleaned)
    except Exception:
        return None


def _format_currency(value: Any) -> str:
    num = _parse_number(value)
    if num is None:
        return str(value)
    formatted = f"{num:,.2f}"
    # Ajuste para pt-BR: milhar com ponto, decimal com vírgula
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def _format_percent(
    value: Any, *, decimals: int = 2, assume_fraction: bool = False
) -> str:
    num = _parse_number(value)
    if num is None:
        return str(value)
    if assume_fraction:
        num *= 100.0
    formatted = f"{num:.{decimals}f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted}%"


def _format_decimal(value: Any, *, decimals: int = 3) -> str:
    num = _parse_number(value)
    if num is None:
        return str(value)
    formatted = f"{num:.{decimals}f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def _format_date(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, str) and len(value) >= 10:
        try:
            return datetime.fromisoformat(value.strip().replace(" ", "T", 1)).strftime(
                "%d/%m/%Y"
            )
        except Exception:
            try:
                return datetime.strptime(value[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                return value
    return str(value)


def _truncate(text: str, limit: int = 300) -> str:
    if not isinstance(text, str):
        return ""
    if len(text) <= limit:
        return text.strip()
    return text[: limit - 1].rstrip() + "…"


def _extract_city_state(address: str) -> str:
    if not isinstance(address, str) or not address.strip():
        return ""
    if " - " in address:
        parts = [p.strip() for p in address.split(" - ") if p.strip()]
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
    if "," in address:
        comma_parts = [p.strip() for p in address.split(",") if p.strip()]
        if len(comma_parts) >= 2 and len(comma_parts[-1]) == 2:
            return f"{comma_parts[-2]}/{comma_parts[-1]}"
        if comma_parts:
            return comma_parts[-1]
    return ""


def _prepare_rag_payload(rag: dict | None) -> dict | None:
    """
    Normaliza o contexto de RAG para o prompt do Narrator.

    Espera um dict no formato produzido por app/rag/context_builder.build_context:
      - enabled: bool
      - chunks: List[Dict[str, Any]] (cada um com 'text', 'score', 'doc_id', 'tags', etc.)
      - policy: Dict[str, Any] (incluindo max_chunks, collections, ...)

    Retorna um payload enxuto com:
      {
        "enabled": true,
        "source": { "intent": ..., "entity": ..., "collections": [...] },
        "snippets": [
          { "doc_id": "...", "score": 0.87, "snippet": "trecho truncado...", "tags": [...] },
          ...
        ]
      }
    """
    if not isinstance(rag, dict):
        return None
    if not rag.get("enabled"):
        return None

    chunks = rag.get("chunks") or []
    if not isinstance(chunks, list) or not chunks:
        return None

    policy = rag.get("policy") or {}
    max_items = 5
    try:
        max_items = int(policy.get("max_chunks", max_items))
    except Exception:
        pass

    snippets: List[Dict[str, Any]] = []
    for ch in chunks[:max_items]:
        if not isinstance(ch, dict):
            continue
        text = ch.get("text") or ""
        snippet = _truncate(text, 600)
        if not snippet:
            continue
        snippets.append(
            {
                "doc_id": ch.get("doc_id"),
                "score": ch.get("score"),
                "snippet": snippet,
                "tags": ch.get("tags"),
            }
        )

    if not snippets:
        return None

    return {
        "enabled": True,
        "source": {
            "intent": rag.get("intent"),
            "entity": rag.get("entity"),
            "collections": (policy.get("collections") or rag.get("used_collections")),
        },
        "snippets": snippets,
    }


def _pick_template(meta: dict, facts: dict) -> str:
    # Modo conceitual força o template "concept"
    compute = (meta or {}).get("compute") or {}
    if isinstance(compute, dict):
        mode = compute.get("mode")
        if isinstance(mode, str) and mode.strip().lower() == "concept":
            return "concept"

    narrator_mode = (facts or {}).get("narrator_mode") or (meta or {}).get(
        "narrator_mode"
    )
    if isinstance(narrator_mode, str) and narrator_mode.strip().lower() == "concept":
        return "concept"

    presentation = (facts or {}).get("presentation_kind") or (meta or {}).get(
        "presentation_kind"
    )
    if isinstance(presentation, str):
        normalized = presentation.strip().lower()
        if normalized in PROMPT_TEMPLATES:
            return normalized
    if (facts or {}).get("rows"):
        return "list"
    return "summary"


def build_prompt(
    question: str,
    facts: dict,
    meta: dict,
    style: str = "executivo",
    rag: dict | None = None,
    effective_policy: dict | None = None,
) -> str:
    """Compose the final prompt string for the LLM."""

    intent = (meta or {}).get("intent", "")
    entity = (meta or {}).get("entity", "")
    template_key = _pick_template(meta, facts)

    # Métrica foco (quando houver), vinda de meta.focus.metric_key
    focus_metric_key = ""
    focus_block = (meta or {}).get("focus")
    if isinstance(focus_block, dict):
        mk = focus_block.get("metric_key")
        if isinstance(mk, str):
            focus_metric_key = mk.strip()

    strict_mode = False
    if isinstance(effective_policy, dict):
        strict_mode = bool(effective_policy.get("strict_mode", False))

    base_instruction = PROMPT_TEMPLATES.get(template_key, PROMPT_TEMPLATES["summary"])
    fewshot = FEW_SHOTS.get(template_key, "")
    # Em modo conceitual, evitamos few-shots para reduzir ruído e tamanho do prompt
    if template_key == "concept":
        fewshot = ""

    facts_payload = dict(facts or {})
    # Em modo conceitual, FACTS servem apenas para sinalização mínima:
    # não enviamos linhas, valores numéricos ou blobs grandes.
    if template_key == "concept":
        minimal_facts: Dict[str, Any] = {}
        for key in ("fallback_message", "requested_metrics"):
            if key in facts_payload:
                minimal_facts[key] = facts_payload[key]
        facts_payload = minimal_facts

    if "fallback_message" not in facts_payload and isinstance(entity, str):
        fallback = (meta or {}).get("fallback_message")
        if isinstance(fallback, str):
            facts_payload["fallback_message"] = fallback

    facts_json = json.dumps(facts_payload, ensure_ascii=False, indent=2)
    if len(facts_json) > 50000:
        facts_json = facts_json[:49000] + "\n... (truncado)\n"

    if isinstance(effective_policy, dict) and not effective_policy.get(
        "use_rag_in_prompt", False
    ):
        rag = None

    rag_payload = _prepare_rag_payload(rag)
    if rag_payload is not None:
        rag_json = json.dumps(rag_payload, ensure_ascii=False, indent=2)
        if len(rag_json) > 20000:
            rag_json = rag_json[:19000] + "\n... (truncado)\n"
    else:
        rag_json = "(nenhum contexto adicional relevante foi encontrado.)"

    additional_guard = ""
    # Guard-rail ultra restrito: só em modo estrito + métrica foco definida
    if strict_mode and focus_metric_key:
        additional_guard = f"""
Regras CRÍTICAS de foco em métrica:
- Você só pode responder sobre a métrica identificada em [FOCUS_METRIC_KEY].
- É proibido inventar nomes de métricas inexistentes ou diferentes da métrica foco.
- Não migre o foco para outras métricas principais (como VaR, volatilidade genérica
  ou qualquer termo não citado no contexto).
- Se você não conseguir responder falando exclusivamente dessa métrica foco,
  responda exatamente (sem variações):
  erro: métrica fora do foco
"""
    return f"""{SYSTEM_PROMPT}

[ESTILO]: {style}
[APRESENTACAO]: {template_key}
[INTENT]: {intent}
[ENTITY]: {entity}
[FOCUS_METRIC_KEY]: {focus_metric_key}

[PERGUNTA]: {question}

[FACTS]:
{facts_json}

[RAG_CONTEXT]:
{rag_json}

Instruções adicionais:
{base_instruction}
{additional_guard}

Few-shot de referência (opcional):
{fewshot}

Entregue apenas o texto final para o usuário.
"""


# ---------------------------------------------------------------------------
# Deterministic renderers (sem LLM)
# ---------------------------------------------------------------------------


def _render_client_fiis_positions(meta: dict, facts: dict) -> str:
    rows = [r for r in (facts or {}).get("rows", []) if isinstance(r, dict)]
    if not rows:
        return ""

    intro = f"Você tem **{len(rows)} posições em FIIs** registradas neste CPF/CNPJ."

    lines: List[str] = []
    total = 0.0
    for row in rows:
        ticker = row.get("ticker") or "—"
        qty_raw = row.get("qty")
        qty = int(_parse_number(qty_raw) or 0)
        price = _parse_number(row.get("closing_price")) or 0.0
        update_value_raw = row.get("update_value")
        update_value = _parse_number(update_value_raw)
        if update_value is None:
            update_value = qty * price
        total += update_value or 0.0
        line = (
            f"- **{ticker}** – {qty} cotas a {_format_currency(price)} "
            f"(valor aproximado de posição: {_format_currency(update_value)})"
        )
        lines.append(line)

    summary = f"Valor aproximado total da carteira em FIIs: {_format_currency(total)}."
    return "\n".join([intro, *lines, summary]).strip()


def _render_fiis_processos(meta: dict, facts: dict) -> str:
    rows = [r for r in (facts or {}).get("rows", []) if isinstance(r, dict)]
    if not rows:
        return ""
    ticker = (
        (facts or {}).get("ticker")
        or (facts or {}).get("primary", {}).get("ticker")
        or rows[0].get("ticker")
        or ""
    )
    intro = f"Sim, o **{ticker}** tem **{len(rows)} processos relevantes** registrados.".strip()

    items: List[str] = []
    probable_count = 0
    high_value_count = 0
    for idx, row in enumerate(rows, start=1):
        risk = row.get("loss_risk_pct") or "—"
        if isinstance(risk, str) and risk.strip().lower().startswith(
            "prov"
        ):  # provável
            probable_count += 1
        cause_amt_num = _parse_number(row.get("cause_amt"))
        if cause_amt_num and cause_amt_num >= 1e8:
            high_value_count += 1
        parts = [
            f"{idx}. **{row.get('process_number', 'N/I')}**",
            f"julgamento: {row.get('judgment') or 'N/I'}",
        ]
        if row.get("instance"):
            parts.append(f"instância: {row.get('instance')}")
        if row.get("initiation_date"):
            parts.append(f"ajuizado em {_format_date(row.get('initiation_date'))}")
        if row.get("cause_amt"):
            parts.append(f"valor da causa: {_format_currency(row.get('cause_amt'))}")
        parts.append(f"risco de perda: {risk}")
        facts_text = row.get("main_facts") or ""
        impact = row.get("loss_impact_analysis") or ""
        detail = f"Fatos principais: {_truncate(facts_text, 300)}"
        if impact:
            detail += f" | Impacto: {_truncate(impact, 200)}"
        items.append(" – ".join(parts) + f". {detail}")

    summary_parts = []
    if probable_count:
        summary_parts.append(
            f"{probable_count} processo(s) classificado(s) como perda provável"
        )
    if high_value_count:
        summary_parts.append("processos administrativos com valores muito elevados")
    summary = "Resumo: " + "; ".join(summary_parts) if summary_parts else ""

    output = [intro, *items]
    if summary:
        output.append(summary)
    return "\n".join(output).strip()


def _render_fiis_financials_revenue_schedule(meta: dict, facts: dict) -> str:
    primary = (facts or {}).get("primary") or {}
    if not isinstance(primary, dict) or not primary:
        rows = [r for r in (facts or {}).get("rows", []) if isinstance(r, dict)]
        primary = rows[0] if rows else {}
    if not primary:
        return ""
    ticker = primary.get("ticker") or ""

    buckets = [
        ("0–3 meses", primary.get("revenue_due_0_3m_pct")),
        ("3–6 meses", primary.get("revenue_due_3_6m_pct")),
        ("6–9 meses", primary.get("revenue_due_6_9m_pct")),
        ("9–12 meses", primary.get("revenue_due_9_12m_pct")),
        ("12–15 meses", primary.get("revenue_due_12_15m_pct")),
        ("15–18 meses", primary.get("revenue_due_15_18m_pct")),
        ("18–21 meses", primary.get("revenue_due_18_21m_pct")),
        ("21–24 meses", primary.get("revenue_due_21_24m_pct")),
        ("24–27 meses", primary.get("revenue_due_24_27m_pct")),
        ("27–30 meses", primary.get("revenue_due_27_30m_pct")),
        ("30–33 meses", primary.get("revenue_due_30_33m_pct")),
        ("33–36 meses", primary.get("revenue_due_33_36m_pct")),
        ("acima de 36 meses", primary.get("revenue_due_over_36m_pct")),
        ("prazo indeterminado", primary.get("revenue_due_undetermined_pct")),
    ]

    short_term = _format_percent(buckets[0][1] or 0)
    intro = (
        f"No **{ticker}**, cerca de **{short_term}** da receita contratada "
        f"vence nos **próximos 0–3 meses**."
    ).strip()

    structure = "; ".join(
        f"{label}: {_format_percent(val or 0)}" for label, val in buckets
    )

    long_term_share = _parse_number(primary.get("revenue_due_over_36m_pct")) or 0.0
    concentration_short = any((_parse_number(val) or 0) > 30 for _, val in buckets[:2])
    comments = []
    if long_term_share > 50:
        comments.append(
            "Mais da metade da receita é de longo prazo (além de 36 meses)."
        )
    if concentration_short:
        comments.append("Há concentração relevante de vencimentos no curto prazo.")

    output = [intro, f"Estrutura de vencimentos: {structure}."]
    if comments:
        output.append(" ".join(comments))
    return "\n".join(output).strip()


def _render_fiis_financials_risk(meta: dict, facts: dict) -> str:
    if (meta or {}).get("narrator_mode") == "concept":
        return ""

    primary = (facts or {}).get("primary") or {}
    if not isinstance(primary, dict) or not primary:
        rows = [r for r in (facts or {}).get("rows", []) if isinstance(r, dict)]
        primary = rows[0] if rows else {}
    if not primary:
        return ""

    ticker = primary.get("ticker") or ""
    treynor = _format_percent(primary.get("treynor_ratio") or 0)
    intro = (
        f"O **Índice de Treynor do {ticker}** está em aproximadamente **{treynor}**."
    )

    bullets = [
        f"- Volatilidade histórica: {_format_percent(primary.get('volatility_ratio') or 0)}",
        f"- Sharpe Ratio: {_format_percent(primary.get('sharpe_ratio') or 0)}",
        f"- Treynor Ratio: {treynor}",
        f"- Alfa de Jensen: {_format_decimal(primary.get('jensen_alpha') or 0, decimals=2)}",
        f"- Sortino Ratio: {_format_percent(primary.get('sortino_ratio') or 0)}",
        f"- Máximo Drawdown (MDD): {_format_percent(primary.get('max_drawdown') or 0, assume_fraction=True)}",
        f"- Beta em relação ao índice de referência: {_format_decimal(primary.get('beta_index') or 0, decimals=3)}",
        f"- R²: {_format_decimal(primary.get('r_squared') or 0, decimals=4)}",
    ]

    treynor_num = _parse_number(primary.get("treynor_ratio")) or 0.0
    sharpe_num = _parse_number(primary.get("sharpe_ratio")) or 0.0
    if treynor_num < 0 and sharpe_num < 0:
        comment = (
            "Os indicadores de retorno ajustado ao risco estão negativos, indicando que, "
            "no período analisado, o fundo não foi eficiente em transformar risco em retorno extra."
        )
    elif treynor_num > 0 and sharpe_num > 0:
        comment = "Os indicadores positivos sugerem boa relação retorno/risco no período analisado."
    else:
        comment = "Os indicadores apresentam sinais mistos de relação retorno/risco."

    return "\n".join([intro, *bullets, comment]).strip()


def _render_fiis_financials_snapshot(meta: dict, facts: dict) -> str:
    primary = (facts or {}).get("primary") or {}
    if not isinstance(primary, dict) or not primary:
        rows = [r for r in (facts or {}).get("rows", []) if isinstance(r, dict)]
        primary = rows[0] if rows else {}
    if not primary:
        return ""

    ticker = primary.get("ticker") or ""
    total_cash = _format_currency(primary.get("total_cash_amt") or 0)
    intro = f"O **caixa disponível do {ticker}** é de aproximadamente **{total_cash}**."

    equity_value = _parse_number(primary.get("equity_value")) or 0.0
    cash_value = _parse_number(primary.get("total_cash_amt")) or 0.0
    equity_ratio_text = ""
    if equity_value > 0:
        equity_pct = cash_value / equity_value * 100
        equity_ratio_text = (
            f" (~{_format_percent(equity_pct, decimals=1)} do patrimônio líquido)"
        )

    bullets = [
        f"- Market Cap: {_format_currency(primary.get('market_cap_value'))}",
        f"- Enterprise Value: {_format_currency(primary.get('enterprise_value'))}",
        "- Dividend yield 12m: "
        f"{_format_percent(primary.get('dy_pct') or 0)}; último dividendo: "
        f"{_format_currency(primary.get('last_dividend_amt'))} em {_format_date(primary.get('last_payment_date'))}",
        f"- Alavancagem: {_format_percent(primary.get('leverage_ratio') or 0)}",
        f"- Receita esperada: {_format_currency(primary.get('expected_revenue_amt'))}",
        f"- Passivos totais: {_format_currency(primary.get('liabilities_total_amt'))}",
    ]

    return "\n".join([intro + equity_ratio_text, *bullets]).strip()


def _render_fiis_imoveis(meta: dict, facts: dict) -> str:
    rows = [r for r in (facts or {}).get("rows", []) if isinstance(r, dict)]
    if not rows:
        return ""
    ticker = (
        (facts or {}).get("ticker")
        or (facts or {}).get("primary", {}).get("ticker")
        or rows[0].get("ticker")
        or ""
    )
    asset_class = rows[0].get("asset_class") or "imóveis"
    intro = (
        f"O **{ticker}** possui atualmente **{len(rows)} imóveis** na carteira, "
        f"todos classificados como '{asset_class}'."
    )

    lines: List[str] = []
    vacancy_high = 0
    for idx, row in enumerate(rows, start=1):
        city_state = _extract_city_state(row.get("asset_address") or "")
        vacancy_val = row.get("vacancy_ratio")
        vacancy_num = _parse_number(vacancy_val) or 0.0
        if vacancy_num > 0:
            vacancy_high += 1
        line = (
            f"{idx}. **{row.get('asset_name', 'N/I')}** – {city_state or 'localidade não informada'} "
            f"– área: {row.get('total_area')} m² – vacância: {_format_percent(vacancy_val or 0)}"
        )
        lines.append(line)

    summary = ""
    if vacancy_high:
        summary = (
            "Resumo: alguns ativos apresentam vacância ("
            f"{vacancy_high} com vacância positiva)."
        )
        if any((_parse_number(r.get("vacancy_ratio")) or 0) > 30 for r in rows):
            summary += " Há ativos com vacância elevada acima de 30%."

    output = [intro, *lines]
    if summary:
        output.append(summary)
    return "\n".join(output).strip()


def _fallback_render(entity: str, facts: dict) -> str:
    rows = [r for r in (facts or {}).get("rows", []) if isinstance(r, dict)]
    result_key = (facts or {}).get("result_key") or ""
    header = (
        f"Foram encontrados {len(rows)} registros para a entidade "
        f"{entity or result_key or 'desconhecida'}."
    )
    if not rows:
        return header

    def _row_to_line(row: dict) -> str:
        parts: List[str] = []
        for k, v in row.items():
            if v is None or k == "meta":
                continue
            parts.append(f"{k}: {v}")
        return "; ".join(parts)

    body_lines = []
    for r in rows:
        line = _row_to_line(r)
        if line:
            body_lines.append(f"- {line}")
    body = "\n".join(body_lines)
    return "\n".join([header, body]).strip()


def render_narrative(
    meta: Dict[str, Any], facts: Dict[str, Any], policy: Dict[str, Any]
) -> str:
    entity = (meta or {}).get("entity") or ""
    result_key = (facts or {}).get("result_key") or ""

    mapping = {
        "client_fiis_positions": _render_client_fiis_positions,
        "fiis_processos": _render_fiis_processos,
        "fiis_financials_revenue_schedule": _render_fiis_financials_revenue_schedule,
        "fiis_financials_risk": _render_fiis_financials_risk,
        "fiis_financials_snapshot": _render_fiis_financials_snapshot,
        "fiis_imoveis": _render_fiis_imoveis,
    }

    # rota principal por entidade
    if entity in mapping:
        rendered = mapping[entity](meta, facts)
        if rendered:
            return rendered

    # rota secundária por result_key (caso meta.entity não esteja presente)
    if result_key in mapping:
        rendered = mapping[result_key](meta, facts)
        if rendered:
            return rendered

    return _fallback_render(entity, facts)
