#!/usr/bin/env python3
"""Generate Grafana dashboards from Jinja templates and observability bindings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Iterable, List

import yaml

try:  # pragma: no cover - optional dependency
    from jinja2 import Environment, FileSystemLoader, StrictUndefined

    HAS_JINJA = True
except ModuleNotFoundError:  # pragma: no cover
    Environment = None  # type: ignore
    FileSystemLoader = None  # type: ignore
    StrictUndefined = None  # type: ignore
    HAS_JINJA = False

TEMPLATES = {
    "00_sirios_overview.json": "00_sirios_overview.json.j2",
    "10_api_slo_pipeline.json": "10_api_slo_pipeline.json.j2",
    "20_planner_rag_intelligence.json": "20_planner_rag_intelligence.json.j2",
    "30_ops_reliability.json": "30_ops_reliability.json.j2",
}


class SimpleTemplate:  # pragma: no cover - exercised in fallback mode
    def __init__(self, text: str, global_context: Dict[str, object]):
        self.text = text
        self.global_context = global_context

    def render(self, **context: Dict[str, object]) -> str:
        combined = {**self.global_context, **context}
        output: List[str] = []
        cursor = 0
        text = self.text
        while True:
            start = text.find("{{", cursor)
            if start == -1:
                output.append(text[cursor:])
                break
            output.append(text[cursor:start])
            end = text.find("}}", start)
            if end == -1:
                raise RuntimeError("Unmatched '{{' in template")
            expr = text[start + 2 : end].strip()
            try:
                value = eval(expr, {}, combined)
            except Exception as exc:  # pragma: no cover - error path
                raise RuntimeError(
                    f"Failed to render expression '{expr}': {exc}"
                ) from exc
            output.append(str(value))
            cursor = end + 2
        return "".join(output)


class SimpleEnvironment:  # pragma: no cover - exercised in fallback mode
    def __init__(self, template_dir: str, labels: Dict[str, str]):
        self.template_dir = Path(template_dir)
        self.global_context = {
            "promql_filter": lambda keys: promql_filter(keys, labels)
        }

    def get_template(self, template_name: str) -> SimpleTemplate:
        text = (self.template_dir / template_name).read_text(encoding="utf-8")
        return SimpleTemplate(text, self.global_context)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Grafana dashboards from YAML bindings"
    )
    parser.add_argument(
        "--config", required=True, help="Path to observability YAML configuration"
    )
    parser.add_argument(
        "--out", required=True, help="Output directory for rendered dashboards"
    )
    parser.add_argument(
        "--templates",
        default=str(Path("grafana") / "templates"),
        help="Directory containing dashboard templates",
    )
    return parser.parse_args()


def load_config(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def ensure_required_keys(config: Dict) -> None:
    missing_sections = [
        section
        for section in ("bindings", "labels", "thresholds")
        if section not in config
    ]
    if missing_sections:
        raise ValueError(
            f"Missing required sections in config: {', '.join(missing_sections)}"
        )


def promql_filter(keys: Iterable[str], labels: Dict[str, str]) -> str:
    parts: List[str] = []
    for key in keys:
        label_name = labels.get(key)
        if not label_name:
            continue
        parts.append(f"{label_name}=~'${key}'")
    if not parts:
        return ""
    return "{" + ", ".join(parts) + "}"


def to_namespace(value):  # pragma: no cover - exercised indirectly
    if isinstance(value, dict):
        return SimpleNamespace(**{k: to_namespace(v) for k, v in value.items()})
    if isinstance(value, list):
        return [to_namespace(v) for v in value]
    return value


def make_environment(template_dir: str, labels: Dict[str, str]):
    if HAS_JINJA:
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False,
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        env.globals["promql_filter"] = lambda keys: promql_filter(keys, labels)
        return env
    return SimpleEnvironment(template_dir, labels)


def render_dashboards(env: Environment, config: Dict, output_dir: Path) -> None:  # type: ignore
    output_dir.mkdir(parents=True, exist_ok=True)
    render_context = (
        config if HAS_JINJA else {k: to_namespace(v) for k, v in config.items()}
    )
    for filename, template_name in TEMPLATES.items():
        template = env.get_template(template_name)
        rendered = template.render(**render_context)
        json.loads(rendered)  # validate JSON
        (output_dir / filename).write_text(rendered + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    ensure_required_keys(config)
    env = make_environment(args.templates, config.get("labels", {}))
    render_dashboards(env, config, Path(args.out))


if __name__ == "__main__":
    main()
