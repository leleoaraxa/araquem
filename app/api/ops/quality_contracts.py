from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class RoutingBatchMetadata:
    """Metadados de batch para payloads de roteamento."""

    id: str
    index: int
    total: int


class RoutingPayloadValidationError(ValueError):
    """Erro de contrato para payloads de roteamento (Suite v2)."""


def _validate_batch_metadata(payload: Dict[str, Any]) -> Optional[RoutingBatchMetadata]:
    raw_batch = payload.get("batch")
    if raw_batch is None:
        return None
    if not isinstance(raw_batch, dict):
        raise RoutingPayloadValidationError("invalid routing payload: 'batch' must be an object")

    batch_id = raw_batch.get("id")
    if not isinstance(batch_id, str) or not batch_id.strip():
        raise RoutingPayloadValidationError(
            "invalid routing payload: batch.id must be a non-empty string"
        )

    raw_index = raw_batch.get("index")
    if not isinstance(raw_index, int) or raw_index < 1:
        raise RoutingPayloadValidationError(
            "invalid routing payload: batch.index must be an integer >= 1"
        )

    raw_total = raw_batch.get("total")
    if not isinstance(raw_total, int) or raw_total < 1:
        raise RoutingPayloadValidationError(
            "invalid routing payload: batch.total must be an integer >= 1"
        )

    if raw_index > raw_total:
        raise RoutingPayloadValidationError(
            "invalid routing payload: batch.index cannot exceed batch.total"
        )

    return RoutingBatchMetadata(id=batch_id.strip(), index=raw_index, total=raw_total)


def validate_routing_payload_contract(
    payload: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], Optional[str], str, Optional[RoutingBatchMetadata]]:
    """
    Valida o contrato canônico de routing (Suite v2).

    Espera um objeto com:
      - type: "routing" (não é validado aqui, fica a cargo do caller)
      - payloads: lista não vazia de objetos com as chaves:
          question: str não vazia
          expected_intent: Optional[str]
          expected_entity: Optional[str]
      - suite: Optional[str]
      - description: Optional[str]
      - batch: Optional[{"id": str, "index": int >= 1, "total": int >= 1, index <= total}]

    Retorna: (payloads_normalizados, suite_name, description, batch_metadata)
    """
    if "samples" in payload:
        raise RoutingPayloadValidationError(
            "invalid routing payload: use 'payloads' (Suite v2), not 'samples'"
        )

    payloads_raw = payload.get("payloads")
    if not isinstance(payloads_raw, list) or not payloads_raw:
        raise RoutingPayloadValidationError(
            "invalid routing payload: 'payloads' must be a non-empty list"
        )

    suite_name = payload.get("suite")
    if suite_name is not None and not isinstance(suite_name, str):
        raise RoutingPayloadValidationError(
            "invalid routing payload: 'suite' must be a string"
        )

    description = payload.get("description") or ""
    if not isinstance(description, str):
        raise RoutingPayloadValidationError(
            "invalid routing payload: 'description' must be a string"
        )

    batch_meta = _validate_batch_metadata(payload)

    normalized_payloads: List[Dict[str, Any]] = []
    for idx, sample in enumerate(payloads_raw):
        if not isinstance(sample, dict):
            raise RoutingPayloadValidationError(
                f"invalid routing payload: payloads[{idx}] must be an object"
            )
        q = sample.get("question")
        if not isinstance(q, str) or not q.strip():
            raise RoutingPayloadValidationError(
                "invalid routing payload: "
                f"payloads[{idx}].question must be a non-empty string"
            )
        q = q.strip()
        expected_intent = sample.get("expected_intent")
        if expected_intent is not None and not isinstance(expected_intent, str):
            raise RoutingPayloadValidationError(
                "invalid routing payload: "
                f"payloads[{idx}].expected_intent must be a string or null"
            )
        expected_entity = sample.get("expected_entity")
        if expected_entity is not None and not isinstance(expected_entity, str):
            raise RoutingPayloadValidationError(
                "invalid routing payload: "
                f"payloads[{idx}].expected_entity must be a string or null"
            )
        normalized_payloads.append(
            {
                "question": q,
                "expected_intent": expected_intent,
                "expected_entity": expected_entity,
            }
        )

    return normalized_payloads, suite_name, description, batch_meta
