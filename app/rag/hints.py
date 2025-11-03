# app/rag/hints.py

from __future__ import annotations
import re
from typing import Dict, List, Tuple

_PREFIX = re.compile(r"^entity-([a-z0-9_\-]+)")


def entity_hints_from_rag(results: List[Dict]) -> Dict[str, float]:
    """
    Consolida scores por entidade com base no prefixo do doc_id do índice RAG.
    Ex.: 'entity-fiis-cadastro:...' -> chave 'fiis_cadastro'
    """
    agg: Dict[str, float] = {}
    for r in results or []:
        doc_id = (r.get("doc_id") or "").lower()
        m = _PREFIX.match(doc_id)
        if not m:
            continue
        key = m.group(1).replace("-", "_")
        agg[key] = max(agg.get(key, 0.0), float(r.get("score") or 0.0))
    return agg
