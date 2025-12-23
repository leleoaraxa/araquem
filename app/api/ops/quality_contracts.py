from typing import Any, Dict, List, Optional, Tuple


class RoutingPayloadValidationError(ValueError):
    """Erro de contrato para payloads de roteamento (Suite v2)."""


def validate_routing_payload_contract(
    payload: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], Optional[str], str]:
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

    Retorna: (payloads_normalizados, suite_name, description)
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

    return normalized_payloads, suite_name, description
