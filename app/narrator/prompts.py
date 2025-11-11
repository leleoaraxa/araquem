# -*- coding: utf-8 -*-
"""Prompt scaffolds for the SIRIOS Narrator.
Generated: 2025-11-08T18:03:21
This module is self-contained and safe to add to the repo without touching existing code.
"""

from __future__ import annotations
import json

SYSTEM_PROMPT = """Você é o Narrator da SIRIOS. Sua função é transformar **fatos** em uma resposta clara,
humana e profissional, SEM inventar informações. Regras:
- Use exclusivamente os dados de `facts` (JSON fornecido abaixo).
- Nunca crie campos novos. Se faltar algo essencial, informe a limitação de forma elegante.
- Responda em pt-BR, com tom executivo: direto, cordial, objetivo.
- Formatação padrão: Markdown.
- Números e datas no padrão pt-BR.
- Evite jargões e redundâncias; frases curtas; voz ativa.
"""


def _fewshot_metricas_financials_risk() -> str:
    return """
[EXEMPLO 1]
Pergunta: volatilidade e sharpe do HGRU11
Facts (resumo):
{"ticker":"HGRU11","medidas":[{"nome":"volatilidade","valor": 0.176,"unidade":"ratio"},{"nome":"sharpe","valor":0.62,"unidade":"ratio"}]}
Resposta (modelo):
Para o **HGRU11**, a volatilidade no período analisado foi **17,6%**, com Sharpe **0,62**. Fonte: SIRIOS.

[EXEMPLO 2]
Pergunta: beta do HGLG11
Facts (resumo):
{"ticker":"HGLG11","medidas":[{"nome":"beta","valor":0.81,"unidade":"ratio"}]}
Resposta (modelo):
O **beta** do **HGLG11** no período avaliado foi **0,81**. Fonte: SIRIOS.
"""


def _fewshot_metricas_financials_revenue() -> str:
    return """
[EXEMPLO 1]
Pergunta: receita com vencimento em 0–3 meses do HGLG11
Facts (resumo):
{"ticker":"HGLG11","faixas":[{"nome":"0_3","valor":0.28,"unidade":"ratio"}]}
Resposta (modelo):
Para o **HGLG11**, a parcela de receita com vencimento em **0–3 meses** é **28%**. Fonte: SIRIOS.

[EXEMPLO 2]
Pergunta: quanto vence em 12 meses do XPML11
Facts (resumo):
{"ticker":"XPML11","faixas":[{"nome":"0_12","valor":0.63,"unidade":"ratio"}]}
Resposta (modelo):
No **XPML11**, cerca de **63%** das receitas vencem em até **12 meses**. Fonte: SIRIOS.
"""


FEW_SHOTS = {
    ("metricas", "fiis_financials_risk"): _fewshot_metricas_financials_risk,
    (
        "metricas",
        "fiis_financials_revenue_schedule",
    ): _fewshot_metricas_financials_revenue,
}


def build_prompt(
    question: str, facts: dict, meta: dict, style: str = "executivo"
) -> str:
    """Compose the final prompt string for the LLM."""
    intent = (meta or {}).get("intent", "")
    entity = (meta or {}).get("entity", "")
    key = (intent, entity)
    few = FEW_SHOTS.get(key)
    fewblock = few() if callable(few) else ""
    facts_json = json.dumps(facts or {}, ensure_ascii=False, indent=2)

    if len(facts_json) > 50000:
        facts_json = facts_json[:49000] + "\n... (truncado)\n"

    return f"""{SYSTEM_PROMPT}

[ESTILO]: {style}
[INTENT]: {intent}
[ENTITY]: {entity}

[PERGUNTA]: {question}

[FACTS]:
{facts_json}

[FEW-SHOTS]
{fewblock}

Tarefa: produza uma resposta **concisa e clara** em Markdown usando EXCLUSIVAMENTE os facts acima.
Caso algum campo essencial não esteja presente, informe a limitação de modo elegante e não invente números.
"""
