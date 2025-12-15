# app/narrator/prompts.py
from __future__ import annotations

import json
import re
from typing import Any, Dict, List
from textwrap import dedent

from app.narrator.canonical import extract_canonical_value

# Limite padrão de caracteres por snippet de RAG enviado ao Narrator.
# Ajuda a evitar prompts gigantes e manter o foco em trechos curtos.
RAG_SNIPPET_MAX_CHARS = 320


def _extract_rendered_text(facts: dict) -> str:
    """
    O pipeline já injeta `facts.rendered_text` com o baseline determinístico.
    Quando disponível, tratamos como fonte textual primária para evitar deriva/alucinação.
    """
    if not isinstance(facts, dict):
        return ""
    for k in ("rendered_text", "rendered", "text"):
        v = facts.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _has_rewrite_baseline(facts: dict) -> bool:
    return bool(_extract_rendered_text(facts))


SYSTEM_PROMPT = """Você é o Narrator do Araquem.

IMPORTANTE: nunca exponha ou repita blocos técnicos do prompt.
NUNCA mencione ou reproduza rótulos como [FACTS], [RAG_CONTEXT], [MODEL], [INTENT], [ENTITY], [FOCUS_METRIC_KEY] ou similares.


As regras principais de comportamento, estilo, segurança e uso de dados já estão
definidas no seu system prompt interno (modelo sirios-narrator). Aqui você deve:

- Ler a pergunta original do usuário.
- Usar os dados fornecidos como fonte primária para números e fatos objetivos.
- Usar contexto auxiliar apenas como apoio conceitual, sem copiar trechos literais.
- Respeitar o modo de resposta indicado (por exemplo, narrador_mode="concept").

Responda sempre em linguagem natural, como se estivesse falando diretamente
com o usuário final. Nunca explique estruturas internas, schemas ou metadados.

REGRAS DE SAÍDA (OBRIGATÓRIAS):
- Entregue APENAS o texto final ao usuário (sem cabeçalhos, sem seções técnicas).
- NÃO inclua rótulos como: "PERGUNTA", "FACTS", "RAG_CONTEXT", "FOCUS_METRIC_KEY",
  "NARRADOR_MODE", "MODEL", "ESTILO", "LLM_ENABLED", "SHADOW", "INTENT", "ENTITY".
- NÃO descreva schema/colunas ("a coluna X significa...") e NÃO explique “campos do dataset”.
- Não invente números. Use apenas valores presentes nos dados fornecidos.

PROIBIÇÕES EXPLÍCITAS (saída):
- NÃO comece a resposta com "Facts:", "Fatos:", "Contexto:", "Resumo:", "Notas:" ou similares.
- NÃO crie uma seção introdutória com bullet points de “fatos” antes de responder.
- NÃO diga como você chegou na resposta. Apenas responda.
- NÃO invente “campos auxiliares” (ex.: causas, decisões, explicações) se eles não estiverem explicitamente nos dados.

FORMATO RECOMENDADO:
- 1ª frase: responda diretamente (sim/não/valor/quantidade).
- Depois: detalhe apenas o que é relevante para a pergunta.
"""


PROMPT_TEMPLATES: Dict[str, str] = {
    "summary": """Produza uma resposta curta, em até 3 parágrafos:
- Comece respondendo diretamente à pergunta, priorizando a métrica em foco (se houver).
- Em seguida, explique em 2–3 frases como interpretar a métrica no contexto do fundo.
- Use apenas números presentes nos dados factuais. Não invente valores.
- Mantenha tom neutro, sem recomendar compra ou venda.""",
    "list": """Produza uma resposta em Markdown no formato de lista:
- Comece com uma frase direta respondendo a pergunta.
- Em seguida, use os itens das linhas retornadas (na mesma ordem).
- Em cada item, destaque os campos principais em **negrito**.
- Não crie campos adicionais e não invente números ou categorias que não existam em FACTS.""",
    "table": """Descreva os dados tabulares de forma sucinta:
Produza uma resposta direta à pergunta do usuário:
- Comece respondendo objetivamente à pergunta.
- Em seguida, cite os dados relevantes em linguagem natural.
- NÃO explique o significado de colunas, campos ou estrutura da tabela.
- NÃO descreva o schema nem a organização interna dos dados.
- NÃO dê recomendação de investimento.
- Use apenas informações presentes nos dados factuais, sem extrapolar.
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


def _truncate_snippet(text: str, max_chars: int = RAG_SNIPPET_MAX_CHARS) -> str:
    """Shortens long snippets to keep the prompt focused."""
    if not isinstance(text, str):
        return ""
    stripped = text.strip()
    if not stripped:
        return ""
    try:
        limit = int(max_chars)
    except (TypeError, ValueError):
        limit = RAG_SNIPPET_MAX_CHARS
    if limit <= 0:
        return stripped
    if len(stripped) <= limit:
        return stripped
    truncated = stripped[:limit]
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return f"{truncated.strip()}..."


def _prepare_rag_payload(
    rag: dict | None,
    max_snippet_chars: int | None = None,
) -> dict | None:
    """
    Converte o contexto de RAG em um payload direto para o prompt do Narrator.

    Usa exatamente os chunks fornecidos, respeitando apenas o limite declarado em
    `policy.max_chunks` quando presente.
    """
    if not isinstance(rag, dict):
        return None
    if not rag.get("enabled"):
        return None

    chunks = rag.get("chunks") or []
    if not isinstance(chunks, list) or not chunks:
        return None

    try:
        effective_max_chars = (
            RAG_SNIPPET_MAX_CHARS
            if max_snippet_chars is None
            else int(max_snippet_chars)
        )
    except (TypeError, ValueError):
        effective_max_chars = RAG_SNIPPET_MAX_CHARS

    policy = rag.get("policy") or {}
    max_items: int | None = None
    if isinstance(policy, dict) and "max_chunks" in policy:
        try:
            parsed_max = int(policy.get("max_chunks"))
            if parsed_max > 0:
                max_items = parsed_max
        except Exception:
            max_items = None

    limited_chunks = chunks[:max_items] if max_items is not None else chunks

    snippets: List[Dict[str, Any]] = []
    for ch in limited_chunks:
        if not isinstance(ch, dict):
            continue
        raw_text = ch.get("text") or ""
        snippet = _truncate_snippet(raw_text, max_chars=effective_max_chars)
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

    presentation = (meta or {}).get("presentation_kind") or (facts or {}).get(
        "presentation_kind"
    )
    if isinstance(presentation, str):
        normalized = presentation.strip().lower()
        if normalized in PROMPT_TEMPLATES:
            return normalized
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

    policy_cfg = effective_policy if isinstance(effective_policy, dict) else {}
    narrator_style = policy_cfg.get("style") or style
    narrator_model = policy_cfg.get("model")
    llm_enabled = policy_cfg.get("llm_enabled")
    shadow_enabled = policy_cfg.get("shadow")
    max_prompt_tokens = policy_cfg.get("max_prompt_tokens")
    max_output_tokens = policy_cfg.get("max_output_tokens")

    snippet_max_chars = None
    if isinstance(effective_policy, dict):
        raw_limit = effective_policy.get("rag_snippet_max_chars")
        try:
            if raw_limit is not None:
                snippet_max_chars = int(raw_limit)
        except (TypeError, ValueError):
            snippet_max_chars = None

    intent = (meta or {}).get("intent", "")
    entity = (meta or {}).get("entity", "")
    template_key = _pick_template(meta, facts)

    focus_metric_key = ""
    focus_block = (meta or {}).get("focus")
    if isinstance(focus_block, dict):
        mk = focus_block.get("metric_key")
        if isinstance(mk, str):
            focus_metric_key = mk.strip()

    canonical_value = facts.get("llm_canonical_value")
    if canonical_value is None:
        canonical_value = extract_canonical_value(facts, focus_metric_key)
    if canonical_value:
        facts["llm_canonical_value"] = canonical_value
        facts["llm_focus_metric_key"] = focus_metric_key

    base_instruction = PROMPT_TEMPLATES.get(template_key, PROMPT_TEMPLATES["summary"])

    # ------------------------------------------------------------------
    # Modo rewrite-only (anti-deriva):
    # Se existir baseline determinístico em facts.rendered_text, o LLM deve
    # apenas entregar um prefácio curto antes do texto-base.
    # ------------------------------------------------------------------
    rendered_text = _extract_rendered_text(facts or {})
    rewrite_only = _has_rewrite_baseline(facts or {})
    if rewrite_only:
        anchor_block = ""
        if canonical_value:
            anchor_block = dedent(
                f"""
                METRICA_FOCO: {focus_metric_key}
                VALOR_CANONICO: {canonical_value}
                INSTRUÇÃO: cite apenas esse valor (uma única vez). Qualquer outro número, data ou percentual é proibido.
                """
            ).strip()

        numbers_rule = (
            "SE VALOR_CANONICO existir: cite somente esse número (no máximo uma vez). PROIBIDO qualquer outro número, data ou percentual."
            if canonical_value
            else "SEM VALOR_CANONICO: PROIBIDO introduzir números, percentuais ou datas (deixe os números para o TEXTO_BASE que será exibido depois)."
        )

        rewrite_block = dedent(
            f"""
            MODO REWRITE-ONLY (INTRO-ONLY):
            - Você deve retornar APENAS um prefácio curto (máx. 5 linhas).
            - PROIBIDO: tabelas, pipes `|`, Markdown table, reproduzir TEXTO_BASE, bullets de facts, JSON.
            - {numbers_rule}
            - Use o TEXTO_BASE abaixo apenas como referência de fatos; não copie ou reescreva o bloco.
            - Cite no máximo 1–2 valores do TEXTO_BASE no prefácio, se necessário, sempre em texto corrido.

            {anchor_block}

            TEXTO_BASE (não deve ser reproduzido, apenas usado como evidência):
            {rendered_text}
            """
        ).strip()

        return dedent(
            f"""
            {SYSTEM_PROMPT}

            O usuário perguntou: {question}

            {rewrite_block}

            SAÍDA: devolva apenas o prefácio.
            """
        ).strip()

    # Modo conceitual: não precisa de RAG, reduzimos o prompt ao essencial
    compute_block = (meta or {}).get("compute") or {}
    if isinstance(compute_block, dict):
        mode = compute_block.get("mode")
        if isinstance(mode, str) and mode.strip().lower() == "concept":
            rag = None

    if isinstance(effective_policy, dict) and not effective_policy.get(
        "use_rag_in_prompt", False
    ):
        rag = None

    facts_json = json.dumps(facts or {}, ensure_ascii=False, indent=2)

    rag_payload = _prepare_rag_payload(rag, max_snippet_chars=snippet_max_chars)
    if rag_payload is not None:
        rag_json = json.dumps(rag_payload, ensure_ascii=False, indent=2)
    else:
        rag_json = "(nenhum contexto adicional relevante foi encontrado.)"

    # Importante: reduzir ao máximo “seções” imitáveis. Mantém controle em JSON,
    # mas sem títulos com cara de cabeçalho.
    control = {
        "style": narrator_style,
        "template": template_key,
        "intent": intent,
        "entity": entity,
        "focus_metric_key": focus_metric_key,
        "llm_enabled": llm_enabled,
        "shadow": shadow_enabled,
        "max_prompt_tokens": max_prompt_tokens,
        "max_output_tokens": max_output_tokens,
        "model": narrator_model,
    }
    control_json = json.dumps(control, ensure_ascii=False, indent=2)

    return dedent(
        f"""
        {SYSTEM_PROMPT}

        Controle interno (não imprimir; apenas para orientar):
        {control_json}

        O usuário perguntou: {question}

        Dados factuais (JSON interno; não reproduzir como JSON; use apenas para extrair fatos):
        {facts_json}

        Contexto auxiliar (não imprimir; não copiar trechos):
        {rag_json}

        {rewrite_block}

        Instruções específicas de resposta (não citar literalmente):
        {base_instruction}

        Entregue somente a resposta final ao usuário.
        """
    ).strip()


# ---------------------------------------------------------------------------
# Deterministic renderers (sem LLM)
# ---------------------------------------------------------------------------


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


def _get_entity_policy(
    meta: dict | None, facts: dict | None, policy: dict | None
) -> tuple[str, dict]:
    entity = (meta or {}).get("entity") or ""
    result_key = (facts or {}).get("result_key") or ""

    entities_cfg = policy.get("entities") if isinstance(policy, dict) else {}
    if not isinstance(entities_cfg, dict):
        return "", {}

    for key in (entity, result_key):
        if isinstance(key, str) and key in entities_cfg:
            cfg = entities_cfg.get(key)
            if isinstance(cfg, dict):
                return key, cfg

    return "", {}


def render_narrative(
    meta: Dict[str, Any], facts: Dict[str, Any], policy: Dict[str, Any]
) -> str:
    entity_key, entity_policy = _get_entity_policy(meta, facts, policy)
    if not entity_key:
        return ""

    # Quando a policy desabilita o LLM, não geramos texto próprio e deixamos
    # o Presenter usar o baseline determinístico (technical/template).
    if not entity_policy.get("llm_enabled"):
        return ""

    return ""


def build_bucket_d_global_prompt(
    *,
    question: str,
    entity: str,
    bucket: str,
    facts_payload: dict,
    policy: dict | None = None,
    meta: dict | None = None,
) -> str:
    """Prompt seguro para narrativas globais (bucket D, pós-SQL)."""

    facts_json = json.dumps(facts_payload or {}, ensure_ascii=False, indent=2)
    temperature = None
    max_tokens = None
    if isinstance(policy, dict):
        temperature = policy.get("temperature")
        max_tokens = policy.get("max_tokens")

    context_block = meta if isinstance(meta, dict) else {}
    context_json = json.dumps(context_block or {}, ensure_ascii=False, indent=2)

    return f"""Você é o Narrator do Araquem, especializado em análises macro.

Você recebeu fatos já consolidados via SQL (bucket={bucket}, entidade={entity}).
Gere uma narrativa global em português do Brasil, com tom executivo e acessível.

Regras obrigatórias:
- Use APENAS os valores presentes em [DADOS_FACTUAIS]. Não invente números.
- Se algum dado estiver ausente ou inconclusivo, apenas informe isso de forma clara.
- Não recomende compra/venda. Foque em explicar tendências e contexto macro.
- Priorize clareza: frases curtas, sem jargão desnecessário.

Parâmetros do LLM: temperatura={temperature} | max_tokens={max_tokens}
Pergunta original: {question}

[DADOS_FACTUAIS]:
{facts_json}

[META_CONTEXTO]:
{context_json}
"""
