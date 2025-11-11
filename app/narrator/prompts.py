# -*- coding: utf-8 -*-
"""Prompt scaffolds for the SIRIOS Narrator."""

from __future__ import annotations

import json
from typing import Dict

SYSTEM_PROMPT = """Você é o Narrator da SIRIOS. Converta fatos já consolidados em uma resposta clara,
objetiva e fiel. Regras:
- Use somente os dados fornecidos em `facts`.
- Preserve o sentido dos valores e textos; não invente campos nem conclusões.
- Se `facts.fallback_message` existir, utilize-a quando não houver conteúdo a narrar.
- Responda em pt-BR, com tom executivo e formatação Markdown simples.
- Priorize frases curtas, voz ativa e clareza.
"""


PROMPT_TEMPLATES: Dict[str, str] = {
    "summary": """Elabore um parágrafo resumindo os fatos principais. Caso exista `facts.rendered_text`, use-o como base e apenas lapide o tom.""",
    "list": """Produza uma resposta em Markdown no formato de lista, mantendo os itens apresentados em `facts.rows` na mesma ordem.""",
    "table": """Descreva os dados tabulares de forma textual sucinta, respeitando a estrutura de colunas informada em `facts.columns` quando presente.""",
}


FEW_SHOTS: Dict[str, str] = {
    "list": """[EXEMPLO]
Pergunta: imóveis do fundo XPTO11
Facts:
{"rows": [{"nome": "Shopping Leste", "cidade": "São Paulo"}]}
Resposta esperada:
- **Shopping Leste** — São Paulo.
""",
    "summary": """[EXEMPLO]
Pergunta: resumo cadastral do ABCD11
Facts:
{"rendered_text": "O fundo ABCD11 é administrado pela Gestora Alfa."}
Resposta esperada:
O fundo **ABCD11** é administrado pela Gestora Alfa.
""",
}


def _pick_template(meta: dict, facts: dict) -> str:
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
    question: str, facts: dict, meta: dict, style: str = "executivo"
) -> str:
    """Compose the final prompt string for the LLM."""

    intent = (meta or {}).get("intent", "")
    entity = (meta or {}).get("entity", "")
    template_key = _pick_template(meta, facts)
    base_instruction = PROMPT_TEMPLATES.get(template_key, PROMPT_TEMPLATES["summary"])
    fewshot = FEW_SHOTS.get(template_key, "")

    facts_payload = dict(facts or {})
    if "fallback_message" not in facts_payload and isinstance(entity, str):
        fallback = (meta or {}).get("fallback_message")
        if isinstance(fallback, str):
            facts_payload["fallback_message"] = fallback

    facts_json = json.dumps(facts_payload, ensure_ascii=False, indent=2)
    if len(facts_json) > 50000:
        facts_json = facts_json[:49000] + "\n... (truncado)\n"

    return f"""{SYSTEM_PROMPT}

[ESTILO]: {style}
[APRESENTACAO]: {template_key}
[INTENT]: {intent}
[ENTITY]: {entity}

[PERGUNTA]: {question}

[FACTS]:
{facts_json}

Instruções adicionais:
{base_instruction}

Few-shot de referência (opcional):
{fewshot}

Entregue apenas o texto final para o usuário.
"""
