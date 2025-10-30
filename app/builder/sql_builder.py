# app/builder/sql_builder.py

from pathlib import Path
from typing import Dict, Tuple, List, Any
import yaml

ENTITIES_DIR = Path("data/entities")

def _load_entity_yaml(entity: str) -> dict:
    ypath = ENTITIES_DIR / f"{entity}.yaml"
    with open(ypass := ypath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def build_select_for_entity(entity: str, identifiers: Dict[str, Any]) -> Tuple[str, Dict[str, Any], str, List[str]]:
    """
    Constrói SELECT baseado no YAML da entidade.
    - view real = nome da entidade (contrato Araquem).
    - return_columns = colunas que vão para a resposta.
    - WHERE opcional por identificadores (p.ex., ticker).
    """
    cfg = _load_entity_yaml(entity)
    result_key: str = cfg["presentation"]["result_key"]
    return_cols: List[str] = cfg["presentation"]["return_columns"]

    view_name = entity  # entidade lógica == view real
    where = []
    params: Dict[str, Any] = {}

    if identifiers and identifiers.get("ticker"):
        where.append("ticker = %(ticker)s")
        params["ticker"] = identifiers["ticker"].upper()

    where_sql = f" WHERE {' AND '.join(where)}" if where else ""
    cols_sql = ", ".join(return_cols)
    sql = f"SELECT {cols_sql} FROM {view_name}{where_sql} LIMIT 100"

    return sql, params, result_key, return_cols
