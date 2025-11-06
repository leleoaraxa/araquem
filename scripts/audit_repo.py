#!/usr/bin/env python3
import os, re, json, sys
from pathlib import Path

REPO = Path(".").resolve()
OUT = Path("docs/reports/github_structure_audit.md")


def list_files(pat):
    return sorted([str(p) for p in REPO.rglob(pat)])


def has(p):
    return (REPO / p).exists()


def md_header(title, level=2):
    return f"\n{'#'*level} {title}\n"


def detect_entities():
    ent_root = REPO / "data" / "entities"
    quality_root = REPO / "data" / "ops" / "quality"
    ents = []
    if not ent_root.exists():
        return ents
    quality_lookup = quality_root if quality_root.exists() else None
    for d in sorted([p for p in ent_root.iterdir() if p.is_dir()]):
        ent = {
            "name": d.name,
            "schema": (d / "schema.yaml").exists(),
            "responses": (d / "responses.yaml").exists(),
            "projections": (
                sorted(
                    [
                        str(p)
                        for p in quality_lookup.rglob(
                            f"projection*{d.name}*.json"
                        )
                    ]
                )
                if quality_lookup is not None
                else []
            ),
        }
        ents.append(ent)
    # detectar YAMLs "flat" (ex.: fiis_precos.yaml)
    for f in sorted(
        [
            p
            for p in ent_root.iterdir()
            if p.is_file()
            and p.suffix in {".yaml", ".yml"}
            and p.stem.startswith("fiis_")
        ],
        key=lambda p: p.stem,
    ):
        name = f.stem
        projections = []
        if quality_lookup is not None:
            projections = sorted(
                str(p)
                for p in quality_lookup.rglob(f"projection_*{name}*.json")
            )
        ents.append(
            {
                "name": name,
                "schema": True,
                "responses": False,
                "projections": projections,
            }
        )
    return ents


def find_response_leaks_in_ontology():
    out = []
    onto = REPO / "data" / "ontology"
    if not onto.exists():
        return out
    patterns = [
        r"responses?:",
        r"padrao",
        r"padr[aã]o",
        r"template",
        r"formata",
        r"mascara",
        r"mask",
        r"output",
    ]
    rx = re.compile("|".join(patterns), flags=re.IGNORECASE)
    for p in onto.rglob("*.y*ml"):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if rx.search(text):
            out.append(str(p))
    return out


def find_policies_in_entities():
    out = []
    ents = REPO / "data" / "entities"
    if not ents.exists():
        return out
    for p in ents.rglob("*"):
        if p.is_file() and re.search(r"polic(y|ies)", p.name, re.IGNORECASE):
            out.append(str(p))
    return out


def rag_locations():
    candidates = []
    for pat in ["data/policies/rag.yaml", "data/rag/config.yaml", "data/rag.yaml"]:
        if has(pat):
            candidates.append(pat)
    # also scan YAMLs for typical keys
    hits = []
    keys = [r"\\bk:\\s*\\d+", r"min_score", r"weight", r"tie[_-]?break", r"max_context"]
    import re

    rx = re.compile("|".join(keys), re.IGNORECASE)
    for p in REPO.rglob("*.y*ml"):
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if rx.search(t):
            hits.append(str(p))
    return candidates, sorted(set(hits))


def planner_thresholds():
    locs = []
    for pat in ["data/ops/planner_thresholds.yaml"]:
        if has(pat):
            locs.append(pat)
    # duplicates in code/yaml
    dups = []
    rx = re.compile(r"min_(score|gap)", re.IGNORECASE)
    for p in REPO.rglob("*"):
        if p.is_file() and (p.suffix in [".py", ".yaml", ".yml"]):
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if rx.search(t):
                dups.append(str(p))
    return locs, sorted(set(dups))


def dashboards():
    g = REPO / "grafana"
    return sorted([str(p) for p in g.rglob("*.json")]) if g.exists() else []


def projections_tests():
    q = REPO / "data" / "ops" / "quality"
    t = REPO / "tests"
    projs = sorted([str(p) for p in q.rglob("projection_*.json")]) if q.exists() else []
    tests = sorted([str(p) for p in t.rglob("test_*.py")]) if t.exists() else []
    return projs, tests


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    md = []
    md.append("# Audit Araquem — estrutura do repositório\\n")
    md.append("_Gerado por scripts/audit_repo.py_\\n")

    # Ontologia vs Entidades
    md.append(md_header("Ontologia x Entidades"))
    leaks = find_response_leaks_in_ontology()
    md.append(f"- Padrões de resposta indevidos em `data/ontology/`: **{len(leaks)}**")
    for p in leaks:
        md.append(f"  - {p}")

    ents = detect_entities()
    md.append("\\n- Entidades detectadas: **{}**".format(len(ents)))
    for e in ents:
        md.append(
            f"  - {e['name']}: schema={'ok' if e['schema'] else 'faltando'} | responses={'ok' if e['responses'] else 'faltando'} | projections={len(e['projections'])}"
        )

    # Policies
    md.append(md_header("Policies"))
    pol_in_entities = find_policies_in_entities()
    md.append(
        f"- Arquivos de policies dentro de `data/entities/`: **{len(pol_in_entities)}**"
    )
    for p in pol_in_entities:
        md.append(f"  - {p}")
    md.append(
        f"- Existe `data/policies/`: {'sim' if (REPO/'data'/'policies').exists() else 'não'}"
    )

    # RAG/LLM & Planner
    md.append(md_header("RAG/LLM & Planner"))
    candidates, hits = rag_locations()
    md.append(
        f"- Arquivo(s) candidato(s) a config RAG: {', '.join(candidates) if candidates else 'nenhum padrão encontrado'}"
    )
    md.append(f"- YAMLs com chaves típicas de RAG: {len(hits)} (lista reduzida abaixo)")
    for p in hits[:20]:
        md.append(f"  - {p}")
    thr_main, thr_dups = planner_thresholds()
    md.append(
        f"- planner_thresholds esperado: {thr_main if thr_main else 'não encontrado'}"
    )
    md.append(
        f"- Locais com `min_score/min_gap` (para checar duplicatas): {len(thr_dups)}"
    )
    for p in thr_dups[:20]:
        md.append(f"  - {p}")

    # Dashboards
    md.append(md_header("Dashboards Grafana"))
    dbs = dashboards()
    md.append(f"- Painéis (.json) detectados: **{len(dbs)}**")
    for p in dbs:
        md.append(f"  - {p}")

    # Projections & Tests
    md.append(md_header("Projections & Tests"))
    projs, tests = projections_tests()
    md.append(f"- Projections: **{len(projs)}**")
    for p in projs[:30]:
        md.append(f"  - {p}")
    md.append(f"- Tests: **{len(tests)}**")
    for p in tests[:30]:
        md.append(f"  - {p}")

    OUT.write_text("\\n".join(md), encoding="utf-8")
    print(f"OK: wrote {OUT}")


if __name__ == "__main__":
    main()
