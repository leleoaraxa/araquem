"""Formatação determinística do Narrador da SIRIOS.

Recebe o payload retornado pelo executor SQL e converte o conteúdo
estritamente em texto Markdown simples conforme especificação.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List


_MAX_ROWS = 10
_EMPTY_MESSAGE = "Não encontrei registros para essa consulta."


def _normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Garante o acesso ao dicionário de fatos dentro do executor_payload."""

    if not isinstance(payload, dict):
        return {}
    # Compat: alguns geradores podem encapsular em "executor_payload"
    if "executor_payload" in payload and isinstance(payload.get("executor_payload"), dict):
        return payload["executor_payload"].get("facts") or {}
    return payload.get("facts") or {}


def _coerce_rows(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = facts.get("rows") or []
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _get_primary(facts: Dict[str, Any]) -> Dict[str, Any]:
    primary = facts.get("primary") or {}
    return primary if isinstance(primary, dict) else {}


def _iter_records(facts: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    rows = _coerce_rows(facts)
    if rows:
        for row in rows[:_MAX_ROWS]:
            yield row
        return

    primary = _get_primary(facts)
    if primary:
        yield primary


def _format_value(value: Any) -> str:
    if value is None:
        return "-"
    return str(value)


def _format_record(record: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key, value in record.items():
        parts.append(f"**{key}**: {_format_value(value)}")
    return "- " + "; ".join(parts)


def build_narrator_text(executor_payload: Dict[str, Any]) -> str:
    """Converte executor_payload em texto determinístico para o Narrador."""

    facts = _normalize_payload(executor_payload)
    records = list(_iter_records(facts))

    if not records:
        return _EMPTY_MESSAGE

    lines = [_format_record(record) for record in records]
    return "\n".join(lines)
