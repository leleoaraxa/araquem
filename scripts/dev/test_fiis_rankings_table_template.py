#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Teste rápido de terminal para o template:
data/entities/fiis_rankings/responses/table.md.j2

Uso:
    python scripts/dev/test_fiis_rankings_table_template.py
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined


def build_env() -> Environment:
    """
    Cria o Environment do Jinja2 apontando para a pasta de responses
    da entidade fiis_rankings.
    """
    base_dir = (
        Path(__file__).resolve().parent.parent.parent
    )  # raiz do repo (ajuste se sua árvore for diferente)
    template_dir = base_dir / "data" / "entities" / "fiis_rankings" / "responses"

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        undefined=StrictUndefined,  # explode se faltar alguma variável
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Se o template usar filtros customizados (ex.: date_br, currency_br, pct_br etc.),
    # registre-os aqui. Exemplos de stubs:
    # env.filters["pct_br"] = lambda v: f"{v:.2f}%"
    # env.filters["int_br"] = lambda v: f"{int(v):,}".replace(",", ".")
    return env


def build_sample_context() -> dict:
    """
    Cria um contexto de exemplo coerente com a view rankings_fii.
    Ajuste os campos conforme o que o template espera.
    """
    rows = [
        {
            "ticker": "HGLG11",
            "users_rank_position": None,
            "users_rank_net_movement": None,
            "sirios_rank_position": None,
            "sirios_rank_net_movement": None,
            "ifix_rank_position": 4,
            "ifix_rank_net_movement": 0,
            "ifil_rank_position": 4,
            "ifil_rank_net_movement": 0,
            "rank_dy_12m": 264,
            "rank_dy_monthly": 310,
            "rank_dividends_12m": 63,
            "rank_market_cap": 5,
            "rank_equity": 4,
            "rank_sharpe": 171,
            "rank_sortino": 185,
            "rank_low_volatility": 27,
            "rank_low_drawdown": 34,
            "created_at": "2024-05-22 00:00:00",
            "updated_at": "2025-12-09 00:00:00",
        },
        {
            "ticker": "MXRF11",
            "users_rank_position": 0,
            "users_rank_net_movement": 0,
            "sirios_rank_position": 0,
            "sirios_rank_net_movement": 0,
            "ifix_rank_position": 1,
            "ifix_rank_net_movement": 0,
            "ifil_rank_position": 2,
            "ifil_rank_net_movement": 0,
            "rank_dy_12m": 100,
            "rank_dy_monthly": 90,
            "rank_dividends_12m": 10,
            "rank_market_cap": 1,
            "rank_equity": 2,
            "rank_sharpe": 10,
            "rank_sortino": 15,
            "rank_low_volatility": 5,
            "rank_low_drawdown": 7,
            "created_at": "2024-05-22 00:00:00",
            "updated_at": "2025-12-09 00:00:00",
        },
    ]

    # Se o template usar alguma estrutura de "fields" ou "columns" para montar o cabeçalho,
    # você pode simular aqui algo do tipo:
    fields = {
        "columns": [
            {"name": "ticker", "label": "FII"},
            {"name": "ifix_rank_position", "label": "Rank IFIX"},
            {"name": "ifil_rank_position", "label": "Rank IFIL"},
            {"name": "rank_dy_12m", "label": "Rank DY 12m"},
            {"name": "rank_sharpe", "label": "Rank Sharpe"},
        ]
    }

    context = {
        "rows": rows,
        "fields": fields,
        "result_key": "rankings_fii",
        "empty_message": "Nenhum ranking encontrado.",
        # Se o template usar meta ou outros campos,
        # você pode adicionar aqui sem problemas:
        "meta": {
            "entity": "fiis_rankings",
        },
    }

    return context


def main() -> None:
    env = build_env()
    template = env.get_template("table.md.j2")

    context = build_sample_context()
    output = template.render(**context)

    print("\n==== RENDER DO TEMPLATE table.md.j2 ====\n")
    print(output)
    print("\n==== FIM ====\n")


if __name__ == "__main__":
    main()
