#!/usr/bin/env python3
"""Validate concepts YAML schema and generate a deterministic markdown report."""

from __future__ import annotations

import argparse
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml


ALLOWED_TOP_LEVEL_KEYS = {"version", "domain", "owner", "sections"}
ALLOWED_SECTION_KEYS = {"id", "title", "items"}
ALLOWED_ITEM_KEYS = {
    "name",
    "description",
    "aliases",
    "related_entities",
    "related_intents",
    "typical_questions",
    "typical_uses",
    "interpretation",
    "definition",
    "usage",
    "cautions",
    "notes",
    "subitems",
    "id",
}
ALLOWED_SUBITEM_KEYS = {"name", "description"}

TEXT_FIELDS = {
    "name",
    "description",
    "aliases",
    "related_entities",
    "related_intents",
    "typical_questions",
    "typical_uses",
    "interpretation",
    "definition",
    "usage",
    "cautions",
    "notes",
}

KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass
class Issue:
    gate: str
    severity: str
    file: str
    message: str
    line: int | None = None
    snippet: str | None = None
    suggestion: str | None = None


def load_yaml(path: Path) -> tuple[Any | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, f"File not found: {path}"
    try:
        return yaml.safe_load(text), None
    except yaml.YAMLError as exc:
        return None, f"YAML parse error: {exc}"


def find_line(lines: list[str], pattern: str) -> tuple[int | None, str | None]:
    for idx, line in enumerate(lines, start=1):
        if re.search(pattern, line):
            return idx, line.rstrip("\n")
    return None, None


def add_issue(
    issues: list[Issue],
    gate: str,
    severity: str,
    path: Path,
    message: str,
    lines: list[str] | None = None,
    pattern: str | None = None,
    suggestion: str | None = None,
) -> None:
    line_no = None
    snippet = None
    if lines is not None and pattern:
        line_no, snippet = find_line(lines, pattern)
    issues.append(
        Issue(
            gate=gate,
            severity=severity,
            file=str(path),
            message=message,
            line=line_no,
            snippet=snippet,
            suggestion=suggestion,
        )
    )


def is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def sum_text(value: Any) -> int:
    if isinstance(value, str):
        return len(value)
    if isinstance(value, list):
        return sum(len(item) for item in value if isinstance(item, str))
    return 0


def collect_text_chars(sections: list[dict[str, Any]]) -> int:
    total = 0
    for section in sections:
        if isinstance(section, dict):
            total += sum_text(section.get("title"))
            items = section.get("items")
            if isinstance(items, list):
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    for field in TEXT_FIELDS:
                        total += sum_text(item.get(field))
                    subitems = item.get("subitems")
                    if isinstance(subitems, list):
                        for subitem in subitems:
                            if not isinstance(subitem, dict):
                                continue
                            total += sum_text(subitem.get("name"))
                            total += sum_text(subitem.get("description"))
    return total


def load_git_file(path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "show", f"HEAD^:{path.as_posix()}"] ,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return None
    return result.stdout


def calculate_metrics(data: dict[str, Any]) -> dict[str, int]:
    sections = data.get("sections") if isinstance(data, dict) else None
    if not isinstance(sections, list):
        return {"sections": 0, "items": 0, "text_chars": 0}
    items_count = sum(
        len(section.get("items"))
        for section in sections
        if isinstance(section, dict) and isinstance(section.get("items"), list)
    )
    text_chars = collect_text_chars(sections)
    return {"sections": len(sections), "items": items_count, "text_chars": text_chars}


def format_delta(current: int, previous: int) -> float:
    if previous == 0:
        return 0.0
    return (current - previous) / previous


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate concepts YAML schema and emit a markdown report.")
    parser.add_argument(
        "--report",
        default="CONCEPTS_VALIDATION_REPORT.md",
        help="Path to write the markdown report.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root path.",
    )
    args = parser.parse_args()

    root = Path(args.root)
    concepts_dir = root / "data" / "concepts"
    index_path = root / "data" / "embeddings" / "index.yaml"
    catalog_path = concepts_dir / "catalog.yaml"
    report_path = root / args.report

    issues: list[Issue] = []
    metrics: dict[str, dict[str, int]] = {}
    metrics_prev: dict[str, dict[str, int]] = {}
    per_file_status: dict[str, str] = {}
    per_file_notes: dict[str, list[str]] = defaultdict(list)
    item_id_global: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))

    # Gate 1: YAML parse validation for all concepts YAMLs (including catalog)
    yaml_paths = sorted(concepts_dir.glob("*.yaml"))
    for path in yaml_paths:
        data, error = load_yaml(path)
        if error:
            add_issue(
                issues,
                gate="Gate 1",
                severity="fail",
                path=path,
                message=error,
                suggestion="Corrigir o YAML para parsear corretamente.",
            )
        else:
            metrics[str(path)] = calculate_metrics(data)

    # Gate 1: catalog references
    catalog_data, catalog_error = load_yaml(catalog_path)
    if catalog_error:
        add_issue(
            issues,
            gate="Gate 1",
            severity="fail",
            path=catalog_path,
            message=catalog_error,
            suggestion="Corrigir o YAML para parsear corretamente.",
        )
    elif isinstance(catalog_data, dict):
        concepts = catalog_data.get("concepts", [])
        if isinstance(concepts, list):
            for entry in concepts:
                if not isinstance(entry, dict):
                    continue
                file_path = entry.get("file")
                if isinstance(file_path, str):
                    target = root / file_path
                    if not target.exists():
                        lines = catalog_path.read_text(encoding="utf-8").splitlines()
                        add_issue(
                            issues,
                            gate="Gate 1",
                            severity="fail",
                            path=catalog_path,
                            message=f"Catalog reference missing: {file_path}",
                            lines=lines,
                            pattern=re.escape(file_path),
                            suggestion="Corrigir o path ou adicionar o arquivo faltante.",
                        )

    # Gate 1: index references + duplicates
    index_data, index_error = load_yaml(index_path)
    if index_error:
        add_issue(
            issues,
            gate="Gate 1",
            severity="fail",
            path=index_path,
            message=index_error,
            suggestion="Corrigir o YAML para parsear corretamente.",
        )
    elif isinstance(index_data, dict):
        include = index_data.get("include", [])
        seen_paths: dict[str, list[int]] = defaultdict(list)
        if isinstance(include, list):
            lines = index_path.read_text(encoding="utf-8").splitlines()
            for idx, entry in enumerate(include, start=1):
                if not isinstance(entry, dict):
                    continue
                path_value = entry.get("path")
                if isinstance(path_value, str):
                    seen_paths[path_value].append(idx)
                    target = root / path_value
                    if not target.exists():
                        add_issue(
                            issues,
                            gate="Gate 1",
                            severity="fail",
                            path=index_path,
                            message=f"Index reference missing: {path_value}",
                            lines=lines,
                            pattern=re.escape(path_value),
                            suggestion="Corrigir o path ou adicionar o arquivo faltante.",
                        )
            for path_value, indices in seen_paths.items():
                if len(indices) > 1:
                    add_issue(
                        issues,
                        gate="Gate 1",
                        severity="fail",
                        path=index_path,
                        message=f"Duplicate path in index include: {path_value}",
                        suggestion="Remover duplicatas para manter o index determinístico.",
                    )

    # Gate 2: schema validation
    for path in sorted(concepts_dir.glob("concepts-*.yaml")):
        lines = path.read_text(encoding="utf-8").splitlines()
        data, error = load_yaml(path)
        if error or not isinstance(data, dict):
            add_issue(
                issues,
                gate="Gate 2",
                severity="fail",
                path=path,
                message=error or "Top-level YAML is not a mapping.",
                suggestion="Garantir que o arquivo siga o schema canônico.",
            )
            continue

        missing_top = [key for key in ALLOWED_TOP_LEVEL_KEYS if key not in data]
        if missing_top:
            add_issue(
                issues,
                gate="Gate 2",
                severity="fail",
                path=path,
                message=f"Missing top-level keys: {', '.join(missing_top)}",
                suggestion="Adicionar as chaves obrigatórias no topo do documento.",
            )

        extra_top = [key for key in data.keys() if key not in ALLOWED_TOP_LEVEL_KEYS]
        if extra_top:
            add_issue(
                issues,
                gate="Gate 2",
                severity="fail",
                path=path,
                message=f"Unexpected top-level keys: {', '.join(extra_top)}",
                suggestion="Remover chaves fora do schema canônico.",
            )

        domain = data.get("domain")
        if isinstance(domain, str) and not KEBAB_RE.match(domain):
            add_issue(
                issues,
                gate="Gate 2",
                severity="fail",
                path=path,
                message=f"Domain is not kebab-case: {domain}",
                suggestion="Normalizar o domínio para kebab-case.",
            )

        sections = data.get("sections")
        if not isinstance(sections, list):
            add_issue(
                issues,
                gate="Gate 2",
                severity="fail",
                path=path,
                message="Sections must be a list.",
                suggestion="Garantir que 'sections' seja uma lista de seções.",
            )
            continue

        section_ids: list[str] = []
        item_ids: list[str] = []

        for section in sections:
            if not isinstance(section, dict):
                add_issue(
                    issues,
                    gate="Gate 2",
                    severity="fail",
                    path=path,
                    message="Section entry is not a mapping.",
                    suggestion="Garantir que cada seção seja um mapa com id/title/items.",
                )
                continue

            missing_section = [key for key in ALLOWED_SECTION_KEYS if key not in section]
            if missing_section:
                section_id = section.get("id", "")
                add_issue(
                    issues,
                    gate="Gate 2",
                    severity="fail",
                    path=path,
                    message=f"Missing section keys: {', '.join(missing_section)}",
                    lines=lines,
                    pattern=re.escape(str(section_id)),
                    suggestion="Adicionar campos obrigatórios na seção.",
                )

            extra_section = [key for key in section if key not in ALLOWED_SECTION_KEYS]
            if extra_section:
                section_id = section.get("id", "")
                add_issue(
                    issues,
                    gate="Gate 2",
                    severity="fail",
                    path=path,
                    message=f"Unexpected section keys: {', '.join(extra_section)}",
                    lines=lines,
                    pattern=re.escape(str(section_id)),
                    suggestion="Remover chaves fora do schema canônico.",
                )

            section_id = section.get("id")
            if isinstance(section_id, str):
                section_ids.append(section_id)
                if not KEBAB_RE.match(section_id):
                    add_issue(
                        issues,
                        gate="Gate 2",
                        severity="fail",
                        path=path,
                        message=f"Section id not kebab-case: {section_id}",
                        lines=lines,
                        pattern=re.escape(section_id),
                        suggestion="Normalizar id da seção para kebab-case.",
                    )

            items = section.get("items")
            if not isinstance(items, list):
                add_issue(
                    issues,
                    gate="Gate 2",
                    severity="fail",
                    path=path,
                    message="Section items must be a list.",
                    lines=lines,
                    pattern=re.escape(str(section_id)),
                    suggestion="Garantir que items seja uma lista.",
                )
                continue

            for item in items:
                if not isinstance(item, dict):
                    add_issue(
                        issues,
                        gate="Gate 2",
                        severity="fail",
                        path=path,
                        message="Item entry is not a mapping.",
                        lines=lines,
                        pattern=re.escape(str(section_id)),
                        suggestion="Garantir que cada item seja um mapa.",
                    )
                    continue

                if "name" not in item:
                    add_issue(
                        issues,
                        gate="Gate 2",
                        severity="fail",
                        path=path,
                        message="Item missing required field: name",
                        lines=lines,
                        pattern=re.escape(str(section_id)),
                        suggestion="Adicionar o campo 'name' em cada item.",
                    )
                else:
                    name = item.get("name")
                    if isinstance(name, str):
                        pattern = re.escape(name)
                    else:
                        pattern = re.escape(str(section_id))
                    for key in item:
                        if key not in ALLOWED_ITEM_KEYS:
                            add_issue(
                                issues,
                                gate="Gate 2",
                                severity="fail",
                                path=path,
                                message=f"Unexpected item key: {key}",
                                lines=lines,
                                pattern=pattern,
                                suggestion="Remover chaves fora do schema canônico.",
                            )

                    for list_key in (
                        "aliases",
                        "related_entities",
                        "related_intents",
                        "typical_questions",
                        "typical_uses",
                        "interpretation",
                        "notes",
                    ):
                        if list_key in item and not is_string_list(item.get(list_key)):
                            add_issue(
                                issues,
                                gate="Gate 2",
                                severity="fail",
                                path=path,
                                message=f"Field '{list_key}' must be a list of strings.",
                                lines=lines,
                                pattern=pattern,
                                suggestion="Ajustar o campo para lista de strings.",
                            )

                    for str_key in ("description", "definition", "usage", "cautions"):
                        if str_key in item and not isinstance(item.get(str_key), str):
                            add_issue(
                                issues,
                                gate="Gate 2",
                                severity="fail",
                                path=path,
                                message=f"Field '{str_key}' must be a string.",
                                lines=lines,
                                pattern=pattern,
                                suggestion="Ajustar o campo para string.",
                            )

                    subitems = item.get("subitems")
                    if subitems is not None:
                        if not isinstance(subitems, list):
                            add_issue(
                                issues,
                                gate="Gate 2",
                                severity="fail",
                                path=path,
                                message="Subitems must be a list.",
                                lines=lines,
                                pattern=pattern,
                                suggestion="Garantir que subitems seja uma lista.",
                            )
                        else:
                            for subitem in subitems:
                                if not isinstance(subitem, dict):
                                    add_issue(
                                        issues,
                                        gate="Gate 2",
                                        severity="fail",
                                        path=path,
                                        message="Subitem entry is not a mapping.",
                                        lines=lines,
                                        pattern=pattern,
                                        suggestion="Garantir que cada subitem seja um mapa.",
                                    )
                                    continue
                                if "name" not in subitem:
                                    add_issue(
                                        issues,
                                        gate="Gate 2",
                                        severity="fail",
                                        path=path,
                                        message="Subitem missing required field: name",
                                        lines=lines,
                                        pattern=pattern,
                                        suggestion="Adicionar 'name' nos subitems.",
                                    )
                                extra_subitem = [
                                    key for key in subitem if key not in ALLOWED_SUBITEM_KEYS
                                ]
                                if extra_subitem:
                                    add_issue(
                                        issues,
                                        gate="Gate 2",
                                        severity="fail",
                                        path=path,
                                        message=(
                                            "Unexpected subitem keys: "
                                            + ", ".join(extra_subitem)
                                        ),
                                        lines=lines,
                                        pattern=pattern,
                                        suggestion="Remover chaves fora do schema canônico.",
                                    )

                item_id = item.get("id") if isinstance(item, dict) else None
                if isinstance(item_id, str):
                    item_ids.append(item_id)
                    item_id_global[domain][item_id].append(str(path))

        duplicate_sections = {
            section_id for section_id in section_ids if section_ids.count(section_id) > 1
        }
        for section_id in sorted(duplicate_sections):
            add_issue(
                issues,
                gate="Gate 2",
                severity="fail",
                path=path,
                message=f"Duplicate section id: {section_id}",
                lines=lines,
                pattern=re.escape(section_id),
                suggestion="Garantir ids únicos por seção.",
            )

        duplicate_items = {item_id for item_id in item_ids if item_ids.count(item_id) > 1}
        for item_id in sorted(duplicate_items):
            add_issue(
                issues,
                gate="Gate 2",
                severity="fail",
                path=path,
                message=f"Duplicate item id: {item_id}",
                lines=lines,
                pattern=re.escape(item_id),
                suggestion="Garantir ids únicos por item.",
            )

        if not item_ids:
            per_file_notes[str(path)].append("items.id não presente (checagem de unicidade N/A)")

    # Optional global id collision report per domain
    for domain, ids in item_id_global.items():
        for item_id, files in ids.items():
            if len(set(files)) > 1:
                add_issue(
                    issues,
                    gate="Gate 2",
                    severity="warn",
                    path=Path(files[0]),
                    message=(
                        f"Global item id collision in domain '{domain}': {item_id}"
                    ),
                    suggestion="Unificar ou renomear ids duplicados no domínio.",
                )

    # Gate 3: regression metrics
    for path in sorted(concepts_dir.glob("concepts-*.yaml")):
        current_metrics = metrics.get(str(path))
        if current_metrics is None:
            continue
        prev_text = load_git_file(path)
        if prev_text:
            try:
                prev_data = yaml.safe_load(prev_text)
            except yaml.YAMLError:
                prev_data = None
            if isinstance(prev_data, dict):
                metrics_prev[str(path)] = calculate_metrics(prev_data)

        lines = path.read_text(encoding="utf-8").splitlines()
        data, _ = load_yaml(path)
        if not isinstance(data, dict):
            continue
        sections = data.get("sections") if isinstance(data, dict) else None
        if not isinstance(sections, list):
            continue
        for section in sections:
            if not isinstance(section, dict):
                continue
            items = section.get("items")
            section_id = section.get("id", "")
            if isinstance(items, list) and len(items) == 0:
                add_issue(
                    issues,
                    gate="Gate 3",
                    severity="fail",
                    path=path,
                    message=f"Section has empty items list: {section_id}",
                    lines=lines,
                    pattern=re.escape(str(section_id)),
                    suggestion="Adicionar itens ou remover a seção vazia.",
                )
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                pattern = re.escape(str(name)) if name else re.escape(str(section_id))
                body_fields = [
                    item.get("description"),
                    item.get("definition"),
                    item.get("usage"),
                    item.get("cautions"),
                ]
                list_body_fields = [
                    item.get("typical_questions"),
                    item.get("typical_uses"),
                    item.get("interpretation"),
                    item.get("notes"),
                ]
                body_has_text = any(
                    isinstance(value, str) and value.strip() for value in body_fields
                ) or any(
                    isinstance(value, list) and any(
                        isinstance(entry, str) and entry.strip() for entry in value
                    )
                    for value in list_body_fields
                )
                if not body_has_text:
                    add_issue(
                        issues,
                        gate="Gate 3",
                        severity="fail",
                        path=path,
                        message="Item missing body/definition content.",
                        lines=lines,
                        pattern=pattern,
                        suggestion="Adicionar description/definition/usage ou notas úteis.",
                    )

    # Gate 3: compare deltas
    for path_str, current in metrics.items():
        prev = metrics_prev.get(path_str)
        if not prev:
            continue
        for metric in ("sections", "items", "text_chars"):
            delta = format_delta(current[metric], prev[metric])
            if delta < -0.3:
                add_issue(
                    issues,
                    gate="Gate 3",
                    severity="fail",
                    path=Path(path_str),
                    message=(
                        f"{metric} decreased by {abs(delta) * 100:.1f}% ("
                        f"{prev[metric]} -> {current[metric]})"
                    ),
                    suggestion="Rever remoções ou justificar redução.",
                )

    # Prepare per-file status
    issues_by_file: dict[str, list[Issue]] = defaultdict(list)
    for issue in issues:
        issues_by_file[issue.file].append(issue)

    for path in sorted(concepts_dir.glob("concepts-*.yaml")):
        file_issues = issues_by_file.get(str(path), [])
        if any(issue.severity == "fail" for issue in file_issues):
            per_file_status[str(path)] = "FAIL"
        elif any(issue.severity == "warn" for issue in file_issues):
            per_file_status[str(path)] = "WARN"
        else:
            per_file_status[str(path)] = "OK"

    gate1_fail = any(issue.gate == "Gate 1" and issue.severity == "fail" for issue in issues)
    gate2_fail = any(issue.gate == "Gate 2" and issue.severity == "fail" for issue in issues)
    gate3_fail = any(issue.gate == "Gate 3" and issue.severity == "fail" for issue in issues)

    gate_status = {
        "Gate 1": "FAIL" if gate1_fail else "OK",
        "Gate 2": "FAIL" if gate2_fail else "OK",
        "Gate 3": "FAIL" if gate3_fail else "OK",
    }

    output_lines = [
        "validate_concepts_schema.py summary:",
        f"Gate 1: {gate_status['Gate 1']}",
        f"Gate 2: {gate_status['Gate 2']}",
        f"Gate 3: {gate_status['Gate 3']}",
        f"Issues: {len(issues)}",
    ]
    for line in output_lines:
        print(line)

    report_lines: list[str] = []
    report_lines.append("# Concepts Validation Report")
    report_lines.append("")
    report_lines.append("## Resumo")
    report_lines.append("")
    report_lines.append(f"- Gate 1 (integridade estrutural): **{gate_status['Gate 1']}**")
    report_lines.append(f"- Gate 2 (schema): **{gate_status['Gate 2']}**")
    report_lines.append(f"- Gate 3 (regressão semântica): **{gate_status['Gate 3']}**")
    report_lines.append("")
    report_lines.append("## Tabela por arquivo")
    report_lines.append("")
    report_lines.append("| arquivo | sections | items | text_chars | delta_items | delta_text_chars | status | notas |")
    report_lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")

    for path in sorted(concepts_dir.glob("concepts-*.yaml")):
        path_str = str(path)
        current = metrics.get(path_str, {"sections": 0, "items": 0, "text_chars": 0})
        prev = metrics_prev.get(path_str)
        delta_items = "n/a"
        delta_text = "n/a"
        if prev:
            delta_items_val = format_delta(current["items"], prev["items"])
            delta_text_val = format_delta(current["text_chars"], prev["text_chars"])
            delta_items = f"{delta_items_val * 100:.1f}%"
            delta_text = f"{delta_text_val * 100:.1f}%"
        status = per_file_status.get(path_str, "OK")
        notes = "; ".join(per_file_notes.get(path_str, []))
        report_lines.append(
            f"| {path_str} | {current['sections']} | {current['items']} | "
            f"{current['text_chars']} | {delta_items} | {delta_text} | {status} | {notes} |"
        )

    report_lines.append("")
    report_lines.append("## Problemas encontrados")
    report_lines.append("")
    if not issues:
        report_lines.append("Nenhum problema encontrado.")
    else:
        for issue in issues:
            location = ""
            if issue.line:
                location = f" (linha {issue.line})"
            snippet = f" — `{issue.snippet.strip()}`" if issue.snippet else ""
            suggestion = f" Sugestão: {issue.suggestion}" if issue.suggestion else ""
            report_lines.append(
                f"- **{issue.gate}** [{issue.severity.upper()}] {issue.file}{location}: "
                f"{issue.message}{snippet}.{suggestion}"
            )

    report_lines.append("")
    report_lines.append("## Saída do script")
    report_lines.append("")
    report_lines.append("```text")
    report_lines.extend(output_lines)
    report_lines.append("```")

    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return 1 if any(status == "FAIL" for status in gate_status.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
