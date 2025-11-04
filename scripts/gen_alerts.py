#!/usr/bin/env python3
"""Generate Prometheus recording and alerting rules from observability bindings."""

from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict

import yaml

try:  # pragma: no cover - optional dependency
    from jinja2 import Environment, FileSystemLoader, StrictUndefined

    HAS_JINJA = True
except ModuleNotFoundError:  # pragma: no cover
    Environment = None  # type: ignore
    FileSystemLoader = None  # type: ignore
    StrictUndefined = None  # type: ignore
    HAS_JINJA = False


def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def ensure_sections(cfg: Dict[str, Any]) -> None:
    for sec in ("bindings", "labels", "thresholds", "alerts"):
        if sec not in cfg:
            raise ValueError(f"Missing required section: {sec}")


def to_namespace(value: Any) -> Any:
    if isinstance(value, dict):
        return SimpleNamespace(**{k: to_namespace(v) for k, v in value.items()})
    if isinstance(value, list):
        return [to_namespace(v) for v in value]
    return value


def render_with_jinja(template_path: Path, cfg: Dict[str, Any]) -> str:
    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    tpl = env.get_template(template_path.name)
    rendered = tpl.render(**cfg)
    yaml.safe_load(rendered)
    return rendered


def render_without_jinja(template_path: Path, cfg: Dict[str, Any]) -> str:
    text = template_path.read_text(encoding="utf-8")
    context = vars(to_namespace(cfg))
    result: list[str] = []
    i = 0
    length = len(text)

    while i < length:
        if text.startswith("{{", i):
            j = i + 2
            in_single = False
            in_double = False
            while j < length:
                ch = text[j]
                if ch == "'" and not in_double:
                    in_single = not in_single
                    j += 1
                    continue
                if ch == '"' and not in_single:
                    in_double = not in_double
                    j += 1
                    continue
                if text.startswith("}}", j) and not in_single and not in_double:
                    expr = text[i + 2 : j].strip()
                    try:
                        rendered_expr = str(eval(expr, {}, context))
                    except Exception as exc:  # pragma: no cover - error path
                        raise RuntimeError(
                            f"Failed to render expression '{expr}': {exc}"
                        ) from exc
                    result.append(rendered_expr)
                    i = j + 2
                    break
                j += 1
            else:  # pragma: no cover - defensive
                raise RuntimeError("Unclosed template expression")
        else:
            result.append(text[i])
            i += 1

    rendered = "".join(result)
    yaml.safe_load(rendered)
    return rendered


def render(template_path: Path, cfg: Dict[str, Any]) -> str:
    if HAS_JINJA:
        return render_with_jinja(template_path, cfg)
    return render_without_jinja(template_path, cfg)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--templates-dir", default="prometheus/templates")
    parser.add_argument("--out-recording", default="prometheus/recording_rules.yml")
    parser.add_argument("--out-alerting", default="prometheus/alerting_rules.yml")
    args = parser.parse_args()

    cfg = load_yaml(args.config)
    ensure_sections(cfg)

    templates_dir = Path(args.templates_dir)
    recording_template = templates_dir / "recording_rules.yml.j2"
    alerting_template = templates_dir / "alerting_rules.yml.j2"

    recording = render(recording_template, cfg)
    alerting = render(alerting_template, cfg)

    Path(args.out_recording).write_text(recording + "\n", encoding="utf-8")
    Path(args.out_alerting).write_text(alerting + "\n", encoding="utf-8")
    print("[ok] rules generated:", args.out_recording, args.out_alerting)


if __name__ == "__main__":
    main()
