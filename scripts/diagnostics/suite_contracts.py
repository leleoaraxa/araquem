#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contrato único para suites de qualidade (Suite v2).

Shape esperado:
{
  "suite": "<nome>",
  "description": "...",
  "payloads": [
    { "question": "...", "expected_intent": "...", "expected_entity": "..." },
    ...
  ]
}
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class SuiteValidationError(ValueError):
    """Erro de contrato para arquivos *_suite.json (Suite v2)."""


def expected_suite_from_filename(path: str) -> str:
    stem = Path(path).stem
    if stem.endswith("_suite"):
        return stem[: -len("_suite")]
    return stem


def load_suite_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise SuiteValidationError(f"Formato inválido em {path}: esperado objeto com {{suite, payloads}}")
    if "samples" in data:
        raise SuiteValidationError(
            f"Formato inválido em {path}: esperado contrato Suite v2 com 'payloads' (remova 'samples')"
        )

    suite_name = data.get("suite")
    if not isinstance(suite_name, str) or not suite_name.strip():
        raise SuiteValidationError(f"Formato inválido em {path}: campo obrigatório 'suite' ausente ou vazio")
    suite_name = suite_name.strip()

    expected_suite = expected_suite_from_filename(path)
    if suite_name != expected_suite:
        raise SuiteValidationError(
            f"Formato inválido: suite='{suite_name}' não bate com filename (esperado '{expected_suite}') em {path}"
        )

    description = data.get("description") or ""
    if not isinstance(description, str):
        raise SuiteValidationError(f"Formato inválido: description deve ser string em {path}")

    if "payloads" not in data:
        raise SuiteValidationError(
            f"Formato inválido em {path}: campo obrigatório 'payloads' ausente (Suite v2)"
        )
    payloads = data.get("payloads")
    if not isinstance(payloads, list):
        raise SuiteValidationError(f"Suite inválida em {path}: 'payloads' deve ser uma lista")

    normalized_payloads: List[Dict[str, Any]] = []
    for idx, payload in enumerate(payloads, start=1):
        if not isinstance(payload, dict):
            raise SuiteValidationError(
                f"Payload #{idx} inválido em {path}: esperado objeto com question/expected_*"
            )
        q = payload.get("question")
        if not isinstance(q, str) or not q.strip():
            raise SuiteValidationError(f"Payload #{idx} inválido em {path}: campo 'question' vazio")

        expected_intent = payload.get("expected_intent")
        if expected_intent is not None and not isinstance(expected_intent, str):
            raise SuiteValidationError(
                f"Payload #{idx} inválido (expected_intent deve ser string ou null) em {path}"
            )

        expected_entity = payload.get("expected_entity")
        if expected_entity is not None and not isinstance(expected_entity, str):
            raise SuiteValidationError(
                f"Payload #{idx} inválido (expected_entity deve ser string ou null) em {path}"
            )

        normalized_payloads.append(
            {
                "question": q,
                "expected_intent": expected_intent,
                "expected_entity": expected_entity,
            }
        )

    return {"suite": suite_name, "description": description, "payloads": normalized_payloads}
