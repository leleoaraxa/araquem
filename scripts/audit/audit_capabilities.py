import json
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class EntityAudit:
    name: str
    has_contract: bool
    has_entity_yaml: bool
    supports_multi_ticker: Optional[bool]
    multi_ticker_template: bool
    response_kinds: Set[str]
    has_hints_md: bool
    in_quality_suite: bool
    template_paths: List[Path] = field(default_factory=list)


@dataclass
class OntologyCollision:
    intent_a: str
    intent_b: str
    overlap_literals: Set[str]


@dataclass
class LiteralOverlap:
    literal: str
    intents: Set[str]
    entities: Set[str]


MD_HEADER = """# Audit – Capabilities (Static & Live)

Relatório gerado automaticamente por `scripts/audit/audit_capabilities.py`.
"""


TICKER_PATTERN = re.compile(r"[A-Za-z]{4}11")
GROUPBY_TICKER_PATTERN = re.compile(r"groupby\(['\"]ticker['\"]\)")
TICKER_LOOP_PATTERN = re.compile(r"{%\s*for[^%]*ticker", re.IGNORECASE)
TICKER_HEADER_PATTERN = re.compile(r"^###\s*{{\s*ticker", re.MULTILINE)


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def detect_response_kinds(response_dir: Path) -> Set[str]:
    kinds = set()
    template_paths: List[Path] = []
    if response_dir.exists():
        for path in sorted(response_dir.glob("*.md.j2")):
            template_paths.append(path)
            kinds.add(path.name.split(".")[0])
    return kinds, template_paths


def detect_multi_ticker_template(template_paths: List[Path]) -> bool:
    for path in template_paths:
        content = path.read_text(encoding="utf-8")
        if (
            GROUPBY_TICKER_PATTERN.search(content)
            or TICKER_LOOP_PATTERN.search(content)
            or TICKER_HEADER_PATTERN.search(content)
        ):
            return True
    return False


def audit_entities() -> List[EntityAudit]:
    catalog = load_yaml(REPO_ROOT / "data/entities/catalog.yaml")
    entities = catalog.get("entities", {})

    quality_suites = {
        path.name.replace("_suite.json", "")
        for path in (REPO_ROOT / "data/ops/quality/payloads").glob("*_suite.json")
    }

    audits: List[EntityAudit] = []
    for entity in sorted(entities.keys()):
        entity_dir = REPO_ROOT / "data/entities" / entity
        entity_yaml_path = entity_dir / "entity.yaml"
        has_entity_yaml = entity_yaml_path.exists()
        supports_multi_ticker: Optional[bool] = None

        if has_entity_yaml:
            data = load_yaml(entity_yaml_path) or {}
            options = data.get("options") or {}
            supports_multi_ticker = options.get("supports_multi_ticker")

        response_kinds, template_paths = detect_response_kinds(entity_dir / "responses")
        multi_ticker_template = detect_multi_ticker_template(template_paths)
        has_hints_md = (entity_dir / "templates.md").exists()

        contract_root = REPO_ROOT / "data/contracts/entities"
        has_contract = any(contract_root.glob(f"{entity}.*"))

        audits.append(
            EntityAudit(
                name=entity,
                has_contract=has_contract,
                has_entity_yaml=has_entity_yaml,
                supports_multi_ticker=supports_multi_ticker,
                multi_ticker_template=multi_ticker_template,
                response_kinds=response_kinds,
                has_hints_md=has_hints_md,
                in_quality_suite=entity in quality_suites,
                template_paths=template_paths,
            )
        )
    return audits


def collect_literals(intent: dict) -> Set[str]:
    literals: Set[str] = set()
    tokens = intent.get("tokens") or {}
    phrases = intent.get("phrases") or {}
    for group in (tokens, phrases):
        for key in ("include", "exclude"):
            values = group.get(key) or []
            for val in values:
                literals.add(str(val))
    return literals


def audit_ontology():
    data = load_yaml(REPO_ROOT / "data/ontology/entity.yaml")
    intents = data.get("intents", [])

    intents_by_entity: Dict[str, List[str]] = defaultdict(list)
    literals_by_intent: Dict[str, Set[str]] = {}
    entities_by_intent: Dict[str, Set[str]] = {}

    for intent in intents:
        name = intent.get("name")
        if not name:
            continue
        literals = collect_literals(intent)
        literals_by_intent[name] = literals
        entities = set(intent.get("entities") or [])
        entities_by_intent[name] = entities
        for entity in entities:
            intents_by_entity[entity].append(name)

    collisions: List[OntologyCollision] = []
    for i, (name_a, literals_a) in enumerate(literals_by_intent.items()):
        for name_b, literals_b in list(literals_by_intent.items())[i + 1 :]:
            overlap = literals_a & literals_b
            if overlap:
                collisions.append(
                    OntologyCollision(name_a, name_b, overlap_literals=overlap)
                )

    collisions.sort(key=lambda c: len(c.overlap_literals), reverse=True)

    literals_overlap: List[LiteralOverlap] = []
    literal_to_intents: Dict[str, Set[str]] = defaultdict(set)
    literal_to_entities: Dict[str, Set[str]] = defaultdict(set)
    for intent_name, literals in literals_by_intent.items():
        ents = entities_by_intent.get(intent_name, set())
        for literal in literals:
            literal_to_intents[literal].add(intent_name)
            literal_to_entities[literal].update(ents)

    for literal, intents_set in literal_to_intents.items():
        entities_set = literal_to_entities.get(literal, set())
        if len(entities_set) >= 3:
            literals_overlap.append(
                LiteralOverlap(literal=literal, intents=intents_set, entities=entities_set)
            )

    return {
        "intents_by_entity": intents_by_entity,
        "collisions": collisions,
        "literals_overlap": literals_overlap,
    }


def audit_policies():
    narrator_yaml = REPO_ROOT / "data/policies/narrator.yaml"
    narrator_prompts = REPO_ROOT / "app/narrator/prompts.py"
    narrator_py = REPO_ROOT / "app/narrator/narrator.py"
    presenter_py = REPO_ROOT / "app/presenter/presenter.py"

    conceptual_supported = False
    fallback_rows = False

    search_terms = ["conceitual", "conceptual", "concept"]
    if narrator_yaml.exists():
        content = narrator_yaml.read_text(encoding="utf-8").lower()
        conceptual_supported = any(term in content for term in search_terms)
    if narrator_prompts.exists():
        content = narrator_prompts.read_text(encoding="utf-8").lower()
        conceptual_supported = conceptual_supported or any(
            term in content for term in search_terms
        )

    def has_empty_branch(path: Path) -> bool:
        if not path.exists():
            return False
        content = path.read_text(encoding="utf-8")
        return bool(re.search(r"if\s+not\s+rows|len\(rows\)\s*==\s*0", content))

    fallback_rows = has_empty_branch(narrator_py) or has_empty_branch(presenter_py)

    return {
        "conceptual_supported": conceptual_supported,
        "fallback_rows": fallback_rows,
    }


def audit_quality_samples():
    routing_path = REPO_ROOT / "data/ops/quality/routing_samples.json"
    rag_overview_path = REPO_ROOT / "data/ops/quality/payloads/rag_overview_risk_macro.json"

    def load_samples(path: Path):
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("samples", [])

    def classify_samples(samples):
        multi_ticker = 0
        multi_intent = 0
        for sample in samples:
            question = sample.get("question", "")
            tickers = TICKER_PATTERN.findall(question)
            if len(tickers) >= 2:
                multi_ticker += 1
            if isinstance(sample.get("expected_intent"), list):
                multi_intent += 1
        return multi_ticker, multi_intent

    routing_samples = load_samples(routing_path)
    rag_samples = load_samples(rag_overview_path)

    routing_multi_ticker, routing_multi_intent = classify_samples(routing_samples)
    rag_multi_ticker, rag_multi_intent = classify_samples(rag_samples)

    return {
        "routing_samples_count": len(routing_samples),
        "routing_multi_ticker": routing_multi_ticker,
        "routing_multi_intent": routing_multi_intent,
        "rag_samples_count": len(rag_samples),
        "rag_multi_ticker": rag_multi_ticker,
        "rag_multi_intent": rag_multi_intent,
    }


def run_live_audit():
    try:
        import requests
    except ImportError:
        return None

    try:
        resp = requests.get("http://localhost:8000/healthz", timeout=2)
        if resp.status_code != 200:
            return None
    except Exception:
        return None

    audit_script = REPO_ROOT / "scripts/audit/audit_multiticker.py"
    if audit_script.exists():
        try:
            proc = subprocess.run(
                ["python", str(audit_script)],
                capture_output=True,
                text=True,
                check=False,
            )
            stdout = proc.stdout.strip()
            lines = [json.loads(line) for line in stdout.splitlines() if line.strip()]
        except Exception:
            return None
    else:
        lines = []

    categories = defaultdict(lambda: defaultdict(int))
    for entry in lines:
        status = entry.get("status", {})
        meta = entry.get("meta", {})
        reason = status.get("reason") or meta.get("gate", {}).get("reason") or "unknown"
        category = meta.get("intent") or meta.get("entity") or "unknown"
        categories[category][reason] += 1

    summary = {}
    for category, reasons in categories.items():
        total = sum(reasons.values())
        summary[category] = {
            reason: count / total for reason, count in reasons.items()
        }

    return {"raw": lines, "summary": summary}


def build_ready_sections(audits: List[EntityAudit]):
    ready = []
    unused = []
    missing = []

    for audit in audits:
        if audit.supports_multi_ticker is True and not audit.multi_ticker_template:
            unused.append(
                f"{audit.name}: supports_multi_ticker no YAML mas template não agrupa por ticker"
            )
        if audit.supports_multi_ticker is False and audit.multi_ticker_template:
            missing.append(
                f"{audit.name}: template multi-ticker sem sinal correspondente no entity.yaml"
            )
        if audit.has_entity_yaml and audit.response_kinds and (audit.supports_multi_ticker == audit.multi_ticker_template):
            ready.append(audit.name)
        if not audit.response_kinds:
            missing.append(f"{audit.name}: nenhum template em responses/")
        if not audit.has_contract:
            missing.append(f"{audit.name}: contrato ausente em data/contracts/entities")
        if audit.supports_multi_ticker and not audit.multi_ticker_template:
            missing.append(f"{audit.name}: render multi-ticker ausente no template")
    return ready, unused, missing


def render_table(audits: List[EntityAudit]) -> str:
    headers = [
        "entity",
        "has_contract",
        "has_entity_yaml",
        "supports_multi_ticker",
        "multi_ticker_template",
        "response_kinds",
        "has_hints_md",
        "in_quality_suite",
    ]
    lines = ["| " + " | ".join(headers) + " |", "|" + " --- |" * len(headers)]
    for audit in audits:
        line = [
            audit.name,
            "yes" if audit.has_contract else "no",
            "yes" if audit.has_entity_yaml else "no",
            "yes" if audit.supports_multi_ticker else "no" if audit.supports_multi_ticker is not None else "-",
            "yes" if audit.multi_ticker_template else "no",
            ",".join(sorted(audit.response_kinds)) if audit.response_kinds else "-",
            "yes" if audit.has_hints_md else "no",
            "yes" if audit.in_quality_suite else "no",
        ]
        lines.append("| " + " | ".join(line) + " |")
    return "\n".join(lines)


def generate_report():
    audits = audit_entities()
    ontology = audit_ontology()
    policies = audit_policies()
    quality = audit_quality_samples()
    live = run_live_audit()

    ready, unused, missing = build_ready_sections(audits)

    report_lines = [MD_HEADER]
    report_lines.append("## Tabela por entidade")
    report_lines.append(render_table(audits))

    report_lines.append("\n## Ready")
    if ready:
        report_lines.append("- " + "\n- ".join(sorted(ready)))
    else:
        report_lines.append("- (nenhuma entidade plenamente consistente)")

    report_lines.append("\n## Ready but unused")
    if unused:
        report_lines.append("- " + "\n- ".join(unused))
    else:
        report_lines.append("- (nenhum sinal de capacidade não utilizada)")

    report_lines.append("\n## Missing / Gaps")
    if missing:
        report_lines.append("- " + "\n- ".join(missing))
    else:
        report_lines.append("- (nenhum gap detectado pelo auditor estático)")

    report_lines.append("\n## Ontologia – intents por entidade")
    for entity, intents in sorted(ontology["intents_by_entity"].items()):
        report_lines.append(f"- {entity}: {', '.join(sorted(intents)) if intents else '(sem intents)'}")

    report_lines.append("\n### Overlaps literais (top 10)")
    if ontology["collisions"]:
        for collision in ontology["collisions"][:10]:
            report_lines.append(
                f"- {collision.intent_a} x {collision.intent_b}: {', '.join(sorted(collision.overlap_literals))}"
            )
    else:
        report_lines.append("- (nenhum overlap literal)")

    report_lines.append("\n### Literais presentes em intents de 3+ entidades")
    if ontology["literals_overlap"]:
        for overlap in ontology["literals_overlap"]:
            report_lines.append(
                f"- `{overlap.literal}` em intents {', '.join(sorted(overlap.intents))} cobrindo entidades {', '.join(sorted(overlap.entities))}"
            )
    else:
        report_lines.append("- (nenhum literal compartilhado por 3+ entidades)")

    report_lines.append("\n## Policies / Narrator")
    report_lines.append(f"- Modo conceitual suportado: {'sim' if policies['conceptual_supported'] else 'não'}")
    report_lines.append(f"- Fallback quando rows == 0: {'sim' if policies['fallback_rows'] else 'não'}")

    report_lines.append("\n## Quality assets")
    report_lines.append(
        f"- Suites encontradas: {quality['routing_samples_count']} amostras de roteamento; {quality['rag_samples_count']} amostras RAG"
    )
    report_lines.append(
        f"- Amostras multi-ticker: routing={quality['routing_multi_ticker']}, rag={quality['rag_multi_ticker']}"
    )
    report_lines.append(
        f"- Amostras multi-intent: routing={quality['routing_multi_intent']}, rag={quality['rag_multi_intent']}"
    )

    if live:
        report_lines.append("\n## Live results")
        if live.get("summary"):
            for category, ratios in live["summary"].items():
                pretty = ", ".join(f"{reason}: {ratio:.0%}" for reason, ratio in ratios.items())
                report_lines.append(f"- {category}: {pretty}")
        else:
            report_lines.append("- (sem linhas na execução live)")
    else:
        report_lines.append("\n## Live results")
        report_lines.append("- (API indisponível ou requests não instalado)")

    output_path = REPO_ROOT / "docs/dev/audits/AUDIT_CAPABILITIES.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    generate_report()
