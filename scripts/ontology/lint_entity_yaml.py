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
REPORT_PATH = REPO_ROOT / "out" / "ontology_lint_report.md"

ACCENT_PATTERN = re.compile(r"[áéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ]")
TEMPORAL_STOPLIST = {
    "hoje",
    "ontem",
    "agora",
    "atual",
    "ultima",
    "ultimo",
    "mes",
    "meses",
    "ano",
    "anual",
    "mensal",
    "dias",
    "semana",
    "data",
}
LENGTH_WHITELIST = {"dy", "pm", "vs", "x", "r2"}


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


def build_token_collision_counts(intents: Sequence[Mapping]) -> Dict[str, int]:
    collisions: Dict[str, set[str]] = defaultdict(set)
    for intent in intents:
        intent_name = str(intent.get("name", "<unknown>"))
        for token in extract_field(intent, ["tokens", "include"]):
            normalized = normalize_value(token)
            collisions[normalized].add(intent_name)
    return {token: len(intent_set) for token, intent_set in collisions.items()}


def collect_suspicious_tokens(
    intents: Sequence[Mapping], collision_counts: Mapping[str, int]
) -> List[Dict[str, object]]:
    suspicious: List[Dict[str, object]] = []
    for intent in intents:
        intent_name = str(intent.get("name", "<unknown>"))
        for token in extract_field(intent, ["tokens", "include"]):
            normalized = normalize_value(token)
            criteria: List[str] = []
            stripped = token.strip()
            if re.fullmatch(r"\d+", stripped):
                criteria.append("numérico puro")
            if len(stripped) <= 2 and normalized not in LENGTH_WHITELIST:
                criteria.append("comprimento <= 2")
            count = collision_counts.get(normalized, 0)
            if count >= 6:
                criteria.append(f"alta colisão ({count} intents)")
            if normalized in TEMPORAL_STOPLIST:
                criteria.append("stoplist temporal")
            if criteria:
                suspicious.append({"intent": intent_name, "token": token, "criteria": criteria})
    return suspicious


def summarize_totals(
    accent_hits: Sequence[object],
    duplicates: Mapping[str, Sequence[object]],
    conflicts: Sequence[object],
    suspicious_tokens: Sequence[object],
) -> Dict[str, int]:
    return {
        "A": len(accent_hits),
        "B": len(duplicates.get("exact", [])) + len(duplicates.get("normalized", [])),
        "C": len(conflicts),
        "D": len(suspicious_tokens),
    }


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
) -> str:
    totals = summarize_totals(accent_hits, duplicates, conflicts, suspicious_tokens)
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
        lines.append("Nenhum token suspeito encontrado.")

    lines.append("\n## E) Resumo Executivo")
    lines.append(
        "* Totais: "
        + ", ".join(f"{categoria} = {totals[categoria]}" for categoria in ["A", "B", "C", "D"])
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

    return "\n".join(lines) + "\n"


def lint_entity_yaml() -> str:
    if not ENTITY_PATH.exists():
        raise LintError(f"YAML não encontrado em {ENTITY_PATH}")

    data = load_yaml_file(ENTITY_PATH)
    intents = data.get("intents", []) if isinstance(data, Mapping) else []
    if not isinstance(intents, list):
        raise LintError("Campo 'intents' ausente ou inválido no YAML")

    accent_hits = collect_accent_violations(intents)
    duplicates = collect_duplicates(intents)
    conflicts = collect_conflicts(intents)
    collision_counts = build_token_collision_counts(intents)
    suspicious_tokens = collect_suspicious_tokens(intents, collision_counts)

    report = render_report(accent_hits, duplicates, conflicts, suspicious_tokens, collision_counts)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    return report


def main() -> int:
    try:
        lint_entity_yaml()
    except LintError as exc:
        print(f"Lint failed: {exc}")
        return 1
    except SystemExit:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Erro inesperado: {exc}")
        return 1
    else:
        print(f"Relatório gerado em {REPORT_PATH}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
