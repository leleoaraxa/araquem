#!/usr/bin/env python3
"""Audit observability usage to enforce facade compliance."""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import List, NamedTuple

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
OBS_DIR = APP_DIR / "observability"
PROHIBITED_IMPORT_PREFIXES = ("prometheus_client", "opentelemetry")
METRIC_CTORS = {"Counter", "Histogram", "Gauge", "Summary"}


class Issue(NamedTuple):
    path: str
    lineno: int
    message: str
    snippet: str


def _is_in_observability(path: Path) -> bool:
    try:
        path.relative_to(OBS_DIR)
        return True
    except ValueError:
        return False


def _gather_python_files(base: Path) -> List[Path]:
    files: List[Path] = []
    for path in base.rglob("*.py"):
        if _is_in_observability(path):
            continue
        files.append(path)
    return files


def _check_file(path: Path) -> List[Issue]:
    rel = path.relative_to(ROOT)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    try:
        tree = ast.parse(text, filename=str(rel))
    except SyntaxError as exc:
        return [Issue(str(rel), exc.lineno or 0, "syntax_error", exc.msg)]

    issues: List[Issue] = []

    class Visitor(ast.NodeVisitor):
        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                name = alias.name
                if name.startswith(PROHIBITED_IMPORT_PREFIXES):
                    msg = f"prohibited import '{name}'"
                    issues.append(
                        Issue(
                            str(rel),
                            node.lineno,
                            msg,
                            lines[node.lineno - 1].strip(),
                        )
                    )
            self.generic_visit(node)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            module = node.module or ""
            if module.startswith(PROHIBITED_IMPORT_PREFIXES):
                msg = f"prohibited import from '{module}'"
                issues.append(
                    Issue(
                        str(rel),
                        node.lineno,
                        msg,
                        lines[node.lineno - 1].strip(),
                    )
                )
            self.generic_visit(node)

        def visit_Attribute(self, node: ast.Attribute) -> None:
            if isinstance(node.value, ast.Name) and node.value.id in {
                "prometheus_client",
                "opentelemetry",
            }:
                msg = f"direct access to '{node.value.id}'"
                issues.append(
                    Issue(
                        str(rel),
                        node.lineno,
                        msg,
                        lines[node.lineno - 1].strip(),
                    )
                )
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            name = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute) and isinstance(func.attr, str):
                name = func.attr
            if name in METRIC_CTORS:
                msg = f"direct metric constructor '{name}()'"
                issues.append(
                    Issue(
                        str(rel),
                        node.lineno,
                        msg,
                        lines[node.lineno - 1].strip(),
                    )
                )
            self.generic_visit(node)

    Visitor().visit(tree)
    return issues


def main() -> int:
    all_issues: List[Issue] = []
    for file_path in _gather_python_files(APP_DIR):
        all_issues.extend(_check_file(file_path))

    if all_issues:
        all_issues.sort(key=lambda issue: (issue[0], issue[1]))
        for rel, lineno, message, snippet in all_issues:
            print(f"{rel}:{lineno}: {message}")
            if snippet:
                print(f"    {snippet}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
