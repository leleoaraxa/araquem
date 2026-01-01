"""
Lint ontology intents (tokens/phrases) and generate a Markdown report.

This script reads ``data/ontology/entity.yaml`` and inspects only:
- intents[].tokens.include
- intents[].tokens.exclude
- intents[].phrases.include
- intents[].phrases.exclude

It produces a deterministic report at ``out/ontology_lint_report.md``.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping, MutableMapping, Sequence

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
ENTITY_PATH = REPO_ROOT / "data" / "ontology" / "entity.yaml"
CONFIG_PATH = REPO_ROOT / "data" / "ops" / "quality" / "ontology_lint.yaml"
REPORT_PATH = REPO_ROOT / "out" / "ontology_lint_report.md"

ACCENT_PATTERN = re.compile(r"[áéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ]")
COLLISION_SCOPES = {
    "tokens.include": ["tokens", "include"],
    "phrases.include": ["phrases", "include"],
}


class LintError(Exception):
    """Raised when a lint precondition fails."""


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def normalize_value(value: str) -> str:
    return strip_accents(value).lower().strip()


def load_yaml_file(path: Path) -> Mapping:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    except Exception as exc:  # pylint: disable=broad-except
        raise SystemExit(f"Failed to load YAML: {exc}") from exc


def load_lint_config(path: Path) -> Mapping[str, object]:
    if not path.exists():
        return {}
    data = load_yaml_file(path)
    if not isinstance(data, Mapping):
        return {}
    if "ontology_lint" in data and isinstance(data["ontology_lint"], Mapping):
        config: Mapping[str, object] = data["ontology_lint"]
    else:
        config = data
    collision_gate = config.get("collision_gate", {}) if isinstance(config, Mapping) else {}
    collision_gate_config = collision_gate if isinstance(collision_gate, Mapping) else {}
    defaults = {
        "enabled": False,
        "scope": ["tokens.include"],
        "max_intents_per_token": 0,
        "allowlist": [],
        "forbidden_tokens": [],
        "short_token_allowlist": [],
        "forbid_numeric_tokens": True,
        "min_token_len": 3,
    }
    merged_collision_gate = {**defaults, **{k: v for k, v in collision_gate_config.items() if v is not None}}
    return {"collision_gate": merged_collision_gate}


def ensure_list(value: object) -> List[str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def extract_field(intent: Mapping, path: Sequence[str]) -> List[str]:
    current: MutableMapping[str, object] = intent  # type: ignore[assignment]
    for key in path[:-1]:
        next_value = current.get(key, {}) if isinstance(current, Mapping) else {}
        if not isinstance(next_value, Mapping):
            return []
        current = next_value  # type: ignore[assignment]
    return ensure_list(current.get(path[-1], [])) if isinstance(current, Mapping) else []


def collect_accent_violations(intents: Sequence[Mapping]) -> List[Dict[str, str]]:
    violations: List[Dict[str, str]] = []
    field_paths = {
        "tokens.include": ["tokens", "include"],
        "tokens.exclude": ["tokens", "exclude"],
        "phrases.include": ["phrases", "include"],
        "phrases.exclude": ["phrases", "exclude"],
    }
    for intent in intents:
        intent_name = str(intent.get("name", "<unknown>"))
        for field_label, path in field_paths.items():
            for value in extract_field(intent, path):
                if ACCENT_PATTERN.search(value):
                    violations.append({"intent": intent_name, "field": field_label, "value": value})
    return violations


def collect_duplicates(intents: Sequence[Mapping]) -> Dict[str, List[Dict[str, object]]]:
    exact_dups: List[Dict[str, str]] = []
    normalized_dups: List[Dict[str, object]] = []
    field_paths = {
        "tokens.include": ["tokens", "include"],
        "tokens.exclude": ["tokens", "exclude"],
        "phrases.include": ["phrases", "include"],
        "phrases.exclude": ["phrases", "exclude"],
    }
    for intent in intents:
        intent_name = str(intent.get("name", "<unknown>"))
        for field_label, path in field_paths.items():
            values = extract_field(intent, path)
            if not values:
                continue
            counter = Counter(values)
            for value, count in counter.items():
                if count > 1:
                    exact_dups.append({"intent": intent_name, "field": field_label, "value": value})
            normalized_counter: Counter[str] = Counter()
            normalized_examples: Dict[str, List[str]] = defaultdict(list)
            for value in values:
                normalized = normalize_value(value)
                normalized_counter[normalized] += 1
                normalized_examples[normalized].append(value)
            for normalized, count in normalized_counter.items():
                if count > 1:
                    normalized_dups.append(
                        {
                            "intent": intent_name,
                            "field": field_label,
                            "normalized": normalized,
                            "examples": sorted(set(normalized_examples[normalized])),
                        }
                    )
    return {"exact": exact_dups, "normalized": normalized_dups}


def collect_conflicts(intents: Sequence[Mapping]) -> List[Dict[str, str]]:
    conflicts: List[Dict[str, str]] = []
    for intent in intents:
        intent_name = str(intent.get("name", "<unknown>"))
        token_include = set(extract_field(intent, ["tokens", "include"]))
        token_exclude = set(extract_field(intent, ["tokens", "exclude"]))
        phrase_include = set(extract_field(intent, ["phrases", "include"]))
        phrase_exclude = set(extract_field(intent, ["phrases", "exclude"]))

        for value in sorted(token_include.intersection(token_exclude)):
            conflicts.append({"intent": intent_name, "field": "tokens", "value": value})
        for value in sorted(phrase_include.intersection(phrase_exclude)):
            conflicts.append({"intent": intent_name, "field": "phrases", "value": value})
    return conflicts


def collect_collision_data(
    intents: Sequence[Mapping], scope_paths: Mapping[str, Sequence[str]]
) -> Dict[str, Dict[str, set[str]]]:
    collisions: Dict[str, Dict[str, set[str]]] = {scope: defaultdict(set) for scope in scope_paths}
    for intent in intents:
        intent_name = str(intent.get("name", "<unknown>"))
        for scope, path in scope_paths.items():
            for token in extract_field(intent, path):
                normalized = normalize_value(token)
                collisions[scope][normalized].add(intent_name)
    return collisions


def build_token_collision_counts(intents: Sequence[Mapping]) -> Dict[str, int]:
    collisions: Dict[str, set[str]] = defaultdict(set)
    for intent in intents:
        intent_name = str(intent.get("name", "<unknown>"))
        for token in extract_field(intent, ["tokens", "include"]):
            normalized = normalize_value(token)
            collisions[normalized].add(intent_name)
    return {token: len(intent_set) for token, intent_set in collisions.items()}


def collect_collision_gate_violations(
    intents: Sequence[Mapping], config: Mapping[str, object]
) -> List[Dict[str, object]]:
    collision_gate_cfg = config.get("collision_gate", {}) if isinstance(config, Mapping) else {}
    enabled = bool(collision_gate_cfg.get("enabled", False))
    max_intents = int(collision_gate_cfg.get("max_intents_per_token", 0) or 0)
    if not enabled or max_intents <= 0:
        return []

    scope = collision_gate_cfg.get("scope", ["tokens.include"])
    scope_list = scope if isinstance(scope, list) else [scope]
    scope_paths = {key: COLLISION_SCOPES[key] for key in scope_list if key in COLLISION_SCOPES}
    if not scope_paths:
        return []

    collisions = collect_collision_data(intents, scope_paths)
    allowlist = set(
        normalize_value(item) for item in collision_gate_cfg.get("allowlist", []) if isinstance(item, str)
    )
    forbidden_tokens = set(
        normalize_value(item) for item in collision_gate_cfg.get("forbidden_tokens", []) if isinstance(item, str)
    )
    short_token_allowlist = set(
        normalize_value(item) for item in collision_gate_cfg.get("short_token_allowlist", []) if isinstance(item, str)
    )
    forbid_numeric_tokens = bool(collision_gate_cfg.get("forbid_numeric_tokens", True))
    min_token_len = int(collision_gate_cfg.get("min_token_len", 3) or 0)

    violations: List[Dict[str, object]] = []
    for scope_name, token_map in collisions.items():
        for token, intent_set in token_map.items():
            intents_sorted = sorted(intent_set)
            violation_type = None
            if token in forbidden_tokens:
                violation_type = "forbidden_token"
            elif forbid_numeric_tokens and re.fullmatch(r"\d+", token):
                violation_type = "numeric_token"
            elif len(token) < min_token_len and token not in short_token_allowlist:
                violation_type = "short_token"
            elif len(intent_set) > max_intents and token not in allowlist:
                violation_type = "too_many_intents"

            if violation_type:
                violations.append(
                    {
                        "type": violation_type,
                        "field": scope_name,
                        "token": token,
                        "intents": intents_sorted,
                        "count": len(intent_set),
                        "max": max_intents,
                    }
                )
    return violations


def collect_suspicious_tokens(intents: Sequence[Mapping]) -> List[Dict[str, object]]:
    # Deprecated: replaced by collision gate when enabled. Kept for backward compatibility
    return []


def summarize_totals(
    accent_hits: Sequence[object],
    duplicates: Mapping[str, Sequence[object]],
    conflicts: Sequence[object],
    suspicious_tokens: Sequence[object],
    collision_gate_violations: Sequence[object],
) -> Dict[str, int]:
    totals = {
        "A": len(accent_hits),
        "B": len(duplicates.get("exact", [])) + len(duplicates.get("normalized", [])),
        "C": len(conflicts),
        "D": len(suspicious_tokens),
    }
    totals["F"] = len(collision_gate_violations)
    return totals


def format_table(rows: List[Sequence[str]], headers: Sequence[str]) -> str:
    table_lines = [" | ".join(headers), " | ".join(["---"] * len(headers))]
    for row in rows:
        table_lines.append(" | ".join(row))
    return "\n".join(table_lines)


def render_report(
    accent_hits: Sequence[Mapping[str, str]],
    duplicates: Mapping[str, Sequence[Mapping[str, object]]],
    conflicts: Sequence[Mapping[str, str]],
    suspicious_tokens: Sequence[Mapping[str, object]],
    collision_counts: Mapping[str, int],
    collision_gate_violations: Sequence[Mapping[str, object]],
    collision_gate_config: Mapping[str, object],
) -> str:
    totals = summarize_totals(accent_hits, duplicates, conflicts, suspicious_tokens, collision_gate_violations)
    timestamp = datetime.now(timezone.utc).isoformat()

    lines: List[str] = ["# Ontology Lint Report", f"Gerado em: {timestamp}"]

    lines.append("\n## A) Acentuação")
    if accent_hits:
        rows = [
            (item["intent"], item["field"], item["value"])
            for item in sorted(accent_hits, key=lambda x: (x["intent"], x["field"], x["value"]))
        ]
        lines.append(format_table(rows, ("Intent", "Campo", "Valor")))
    else:
        lines.append("Nenhuma ocorrência encontrada.")

    lines.append("\n## B) Duplicidade")
    lines.append("\n### Duplicatas exatas")
    exact_rows = [
        (item["intent"], item["field"], item["value"])
        for item in sorted(duplicates.get("exact", []), key=lambda x: (x["intent"], x["field"], x["value"]))
    ]
    if exact_rows:
        lines.append(format_table(exact_rows, ("Intent", "Campo", "Valor")))
    else:
        lines.append("Nenhuma duplicata exata encontrada.")

    lines.append("\n### Duplicatas normalizadas")
    normalized_rows = [
        (
            item["intent"],
            item["field"],
            item["normalized"],
            ", ".join(item.get("examples", [])),
        )
        for item in sorted(
            duplicates.get("normalized", []),
            key=lambda x: (x["intent"], x["field"], x["normalized"]),
        )
    ]
    if normalized_rows:
        lines.append(format_table(normalized_rows, ("Intent", "Campo", "Normalizado", "Exemplos")))
    else:
        lines.append("Nenhuma duplicata normalizada encontrada.")

    lines.append("\n## C) Conflitos include vs exclude")
    conflict_rows = [
        (item["intent"], item["field"], item["value"])
        for item in sorted(conflicts, key=lambda x: (x["intent"], x["field"], x["value"]))
    ]
    if conflict_rows:
        lines.append(format_table(conflict_rows, ("Intent", "Campo", "Valor")))
    else:
        lines.append("Nenhum conflito encontrado.")

    lines.append("\n## D) Tokens include genéricos / suspeitos")
    if suspicious_tokens:
        rows = [
            (item["intent"], item["token"], "; ".join(item["criteria"]))
            for item in sorted(
                suspicious_tokens, key=lambda x: (x["intent"], x["token"], ",".join(x["criteria"]))
            )
        ]
        lines.append(format_table(rows, ("Intent", "Token", "Critérios")))
    else:
        if collision_gate_config.get("enabled"):
            lines.append("Substituído pelo Collision Gate.")
        else:
            lines.append("Desabilitado por config.")

    lines.append("\n## E) Resumo Executivo")
    lines.append(
        "* Totais: "
        + ", ".join(
            f"{categoria} = {totals[categoria]}" for categoria in ["A", "B", "C", "D", "F"] if categoria in totals
        )
    )

    top_collisions = sorted(
        ((token, count) for token, count in collision_counts.items()),
        key=lambda x: (-x[1], x[0]),
    )[:20]
    if top_collisions:
        rows = [(token, str(count)) for token, count in top_collisions]
        lines.append("\nTop 20 tokens mais colidentes (normalize):")
        lines.append(format_table(rows, ("Token", "# Intents")))
    else:
        lines.append("\nNenhum token colidente encontrado.")

    lines.append("\n## F) Collision Gate")
    enabled = bool(collision_gate_config.get("enabled", False))
    status = "DISABLED"
    if enabled:
        status = "FAIL" if collision_gate_violations else "PASS"
    lines.append(f"Status: {status}")

    if collision_gate_violations:
        violation_rows = [
            (
                item["type"],
                item.get("field", ""),
                item.get("token", ""),
                str(item.get("count", "")),
                str(item.get("max", "")),
                ", ".join(item.get("intents", [])),
            )
            for item in sorted(
                collision_gate_violations,
                key=lambda x: (
                    x.get("type", ""),
                    x.get("field", ""),
                    x.get("token", ""),
                ),
            )
        ]
        lines.append(format_table(violation_rows, ("Tipo", "Campo", "Token", "#Intents", "Max", "Intents")))
    else:
        if enabled:
            lines.append("Nenhuma violação encontrada.")
        else:
            lines.append("Collision Gate desabilitado por config.")

    lines.append("\nTop 20 tokens mais colidentes (informativo):")
    if top_collisions:
        rows = [(token, str(count)) for token, count in top_collisions]
        lines.append(format_table(rows, ("Token", "# Intents")))
    else:
        lines.append("Nenhum token colidente encontrado.")

    return "\n".join(lines) + "\n"


def lint_entity_yaml() -> Dict[str, object]:
    if not ENTITY_PATH.exists():
        raise LintError(f"YAML não encontrado em {ENTITY_PATH}")

    data = load_yaml_file(ENTITY_PATH)
    intents = data.get("intents", []) if isinstance(data, Mapping) else []
    if not isinstance(intents, list):
        raise LintError("Campo 'intents' ausente ou inválido no YAML")

    lint_config = load_lint_config(CONFIG_PATH)

    accent_hits = collect_accent_violations(intents)
    duplicates = collect_duplicates(intents)
    conflicts = collect_conflicts(intents)
    collision_counts = build_token_collision_counts(intents)
    suspicious_tokens = collect_suspicious_tokens(intents)
    collision_gate_violations = collect_collision_gate_violations(intents, lint_config)

    report = render_report(
        accent_hits,
        duplicates,
        conflicts,
        suspicious_tokens,
        collision_counts,
        collision_gate_violations,
        lint_config.get("collision_gate", {}),
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    return {
        "report": report,
        "violations": {
            "accents": accent_hits,
            "duplicates": duplicates,
            "conflicts": conflicts,
            "collision_gate": collision_gate_violations,
        },
    }


def main() -> int:
    try:
        result = lint_entity_yaml()
    except LintError as exc:
        print(f"Lint failed: {exc}")
        return 1
    except SystemExit:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Erro inesperado: {exc}")
        return 1
    else:
        violations = result.get("violations", {}) if isinstance(result, Mapping) else {}
        collision_gate_violations = violations.get("collision_gate", []) if isinstance(violations, Mapping) else []
        other_failures = any(
            [
                violations.get("accents"),
                violations.get("duplicates", {}).get("exact") if isinstance(violations.get("duplicates"), Mapping) else None,
                violations.get("duplicates", {}).get("normalized") if isinstance(violations.get("duplicates"), Mapping) else None,
                violations.get("conflicts"),
            ]
        )
        exit_code = 1 if collision_gate_violations or other_failures else 0
        print(f"Relatório gerado em {REPORT_PATH}")
        return exit_code


if __name__ == "__main__":
    sys.exit(main())
