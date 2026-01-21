# Institutional contract runtime

## Policy

The institutional contract is controlled by `data/policies/institutional.yaml`.
The policy declares whether the contract is enabled, the intent prefix gating, and
paths for the contract, intent map, and concept files.

## Contract sources

* Response contract: `data/contracts/responses/institutional_response_contract.yaml`
* Intent map: `data/contracts/responses/institutional_intent_map.yaml`
* Concepts: `data/concepts/concepts-institutional.yaml`

## Validation

Run the existing intent-map validator:

```bash
python scripts/quality/validate_institutional_intent_map.py
```
