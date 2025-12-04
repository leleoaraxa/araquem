import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.planner.ontology_loader import load_ontology
from app.planner.planner import Planner
from app.planner.param_inference import infer_params
from app.planner.ticker_index import extract_tickers_from_text

ONTOLOGY_PATH = os.getenv("ONTOLOGY_PATH", "data/ontology/entity.yaml")
CATALOG_PATH = Path("docs/catalog/tests_catalog.json")
REPORT_PATH = Path("reports/planner/regression_audit.json")
MANIFEST_PATH = Path("data/ontology/ontology_manifest.yaml")


def _is_ascii(text: Any) -> bool:
    if not isinstance(text, str):
        return False
    try:
        text.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


def _load_manifest_entities() -> List[str]:
    if not MANIFEST_PATH.exists():
        return []
    try:
        import yaml

        raw = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
        entities = raw.get("entities") if isinstance(raw, dict) else None
        if isinstance(entities, list):
            collected: List[str] = []
            for item in entities:
                if isinstance(item, dict):
                    ent_id = item.get("id")
                    if isinstance(ent_id, str):
                        collected.append(ent_id)
            return collected
    except Exception:
        return []
    return []


def _collect_ascii_issues(ontology: Any) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    for intent in getattr(ontology, "intents", []) or []:
        for token in (getattr(intent, "tokens_include", []) or []):
            if not _is_ascii(token):
                issues.append(
                    {"intent": intent.name, "issue": "token_ascii_invalid", "token": token}
                )
        for token in (getattr(intent, "tokens_exclude", []) or []):
            if not _is_ascii(token):
                issues.append(
                    {
                        "intent": intent.name,
                        "issue": "token_ascii_invalid",
                        "token": token,
                    }
                )
        for phrase in (getattr(intent, "phrases_include", []) or []):
            if not _is_ascii(phrase):
                issues.append(
                    {
                        "intent": intent.name,
                        "issue": "phrase_ascii_invalid",
                        "token": phrase,
                    }
                )
        for phrase in (getattr(intent, "phrases_exclude", []) or []):
            if not _is_ascii(phrase):
                issues.append(
                    {
                        "intent": intent.name,
                        "issue": "phrase_ascii_invalid",
                        "token": phrase,
                    }
                )
    for group, tokens in (getattr(ontology, "anti_tokens", {}) or {}).items():
        for token in tokens or []:
            if not _is_ascii(token):
                issues.append(
                    {"intent": group, "issue": "anti_token_ascii_invalid", "token": token}
                )
    return issues


def _validate_entities(ontology: Any, valid_entities: List[str]) -> List[Dict[str, Any]]:
    if not valid_entities:
        return []
    issues: List[Dict[str, Any]] = []
    valid_set = set(valid_entities)
    for intent in getattr(ontology, "intents", []) or []:
        for entity in getattr(intent, "entities", []) or []:
            if entity not in valid_set:
                issues.append(
                    {
                        "intent": intent.name,
                        "issue": "entity_invalid",
                        "token": entity,
                    }
                )
    return issues


def _detect_collisions(ontology: Any) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    token_map: Dict[str, set] = {}
    phrase_map: Dict[str, set] = {}
    anti_tokens = set()
    for toks in (getattr(ontology, "anti_tokens", {}) or {}).values():
        for tok in toks or []:
            anti_tokens.add(tok)

    for intent in getattr(ontology, "intents", []) or []:
        for token in (getattr(intent, "tokens_include", []) or []):
            token_map.setdefault(token, set()).add(intent.name)
        for phrase in (getattr(intent, "phrases_include", []) or []):
            phrase_map.setdefault(phrase, set()).add(intent.name)

    for token, intents in token_map.items():
        intents_list = sorted(intents)
        if len(intents_list) > 1 and token not in anti_tokens:
            issues.append(
                {
                    "intent": intents_list[0],
                    "issue": "token_collision",
                    "token": token,
                    "conflicts": intents_list,
                }
            )
    for phrase, intents in phrase_map.items():
        intents_list = sorted(intents)
        if len(intents_list) > 1 and phrase not in anti_tokens:
            issues.append(
                {
                    "intent": intents_list[0],
                    "issue": "phrase_collision",
                    "token": phrase,
                    "conflicts": intents_list,
                }
            )
    return issues


def lint_ontology() -> List[Dict[str, Any]]:
    ontology = load_ontology(ONTOLOGY_PATH)
    manifest_entities = _load_manifest_entities()
    issues: List[Dict[str, Any]] = []
    issues.extend(_collect_ascii_issues(ontology))
    issues.extend(_validate_entities(ontology, manifest_entities))
    issues.extend(_detect_collisions(ontology))
    return issues


def _load_catalog() -> List[Dict[str, Any]]:
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(f"Catálogo não encontrado em {CATALOG_PATH}")
    with CATALOG_PATH.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("Catálogo deve ser uma lista de casos de teste")
    return data


def _prepare_identifiers(question: str) -> Dict[str, Any]:
    tickers = extract_tickers_from_text(question) or []
    identifiers: Dict[str, Any] = {}
    if tickers:
        identifiers["tickers"] = tickers
        identifiers["ticker"] = tickers[0]
    return identifiers


def _compare_expected(
    expected_entities: Optional[List[str]],
    got_entity: Optional[str],
    expected_params: Optional[Dict[str, Any]],
    got_params: Optional[Dict[str, Any]],
) -> Optional[str]:
    if expected_entities is not None:
        exp_list = expected_entities
        if isinstance(exp_list, list):
            exp_normalized = [str(e) for e in exp_list]
        else:
            exp_normalized = [str(exp_list)]
        if got_entity not in exp_normalized:
            return "entity_mismatch"
    if expected_params is not None:
        if not isinstance(got_params, dict):
            return "params_missing"
        for key, value in expected_params.items():
            if key not in got_params or got_params.get(key) != value:
                return "params_mismatch"
    return None


def run_catalog(planner: Planner) -> Dict[str, Any]:
    failures: List[Dict[str, Any]] = []
    try:
        catalog = _load_catalog()
    except Exception as exc:
        return {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "failures": [
                {
                    "idx": -1,
                    "question": None,
                    "expected": None,
                    "got": None,
                    "reason": f"catalog_error:{exc}",
                }
            ],
        }

    total = len(catalog)
    passed = 0
    for idx, item in enumerate(catalog):
        question = item.get("question") if isinstance(item, dict) else None
        expected_entities = item.get("expected_entities") if isinstance(item, dict) else None
        expected_params = item.get("expected_params") if isinstance(item, dict) else None
        plan = planner.explain(question or "")
        chosen = plan.get("chosen") or {}
        got_entity = chosen.get("entity")
        identifiers = _prepare_identifiers(question or "")

        agg_params = None
        try:
            agg_params = infer_params(
                question=question or "",
                intent=chosen.get("intent"),
                entity=got_entity,
                entity_yaml_path=f"data/entities/{got_entity}/entity.yaml" if got_entity else "",
                defaults_yaml_path="data/ops/param_inference.yaml",
                identifiers=identifiers,
                client_id=None,
                conversation_id=None,
            )
        except Exception as exc:
            agg_params = {"error": str(exc)}

        reason = _compare_expected(
            expected_entities if isinstance(expected_entities, list) else (expected_entities and [expected_entities]),
            got_entity,
            expected_params,
            agg_params,
        )

        if reason is None:
            passed += 1
            continue

        failures.append(
            {
                "idx": idx,
                "question": question,
                "expected": expected_entities,
                "got": [got_entity] if got_entity is not None else [],
                "reason": reason,
                "params": agg_params if isinstance(agg_params, dict) else None,
            }
        )

    failed = len(failures)
    return {
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "failures": failures,
    }


def write_report(report: Dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)


def main() -> int:
    ontology_issues = lint_ontology()
    planner = Planner(ONTOLOGY_PATH)
    catalog_result = run_catalog(planner)

    timestamp = datetime.utcnow().isoformat()
    report = {
        "timestamp": timestamp,
        "total_tests": catalog_result.get("total_tests", 0),
        "passed": catalog_result.get("passed", 0),
        "failed": catalog_result.get("failed", 0),
        "failures": catalog_result.get("failures", []),
        "ontology_issues": ontology_issues,
    }
    write_report(report)

    exit_code = 0
    if ontology_issues or report.get("failed"):
        exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
