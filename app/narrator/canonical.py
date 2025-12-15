from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional


def _value_to_string(value: Any) -> Optional[str]:
    if value is None:
        return None

    if isinstance(value, (dict, list, tuple, set)):
        return None

    if isinstance(value, Decimal):
        text = str(value)
    elif isinstance(value, bool):
        return None
    elif isinstance(value, (int, float)):
        text = str(value)
    elif isinstance(value, str):
        text = value.strip()
    else:
        return None

    return text if text else None


def extract_canonical_value(
    facts: Dict[str, Any] | None, focus_metric_key: str | None
) -> Optional[str]:
    """Extrai valor canônico determinístico para a métrica foco.

    Segue a ordem:
    1) Mapas explícitos de métricas no facts (metrics, values_by_key, data).
    2) Linhas únicas em facts.rows contendo a coluna da métrica foco.

    Retorna ``None`` quando não houver valor único/seguro.
    """

    if not isinstance(focus_metric_key, str):
        return None

    key = focus_metric_key.strip()
    if not key:
        return None

    if not isinstance(facts, dict):
        return None

    metric_maps = [
        facts.get("metrics"),
        facts.get("values_by_key"),
        facts.get("data"),
    ]

    for metric_map in metric_maps:
        if isinstance(metric_map, dict) and key in metric_map:
            value_str = _value_to_string(metric_map.get(key))
            if value_str is not None:
                return value_str

    rows = facts.get("rows")
    if isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict):
        if key in rows[0]:
            return _value_to_string(rows[0].get(key))

    return None
