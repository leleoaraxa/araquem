import json

from scripts.quality import build_coverage_report as coverage


def test_build_reports_smoke(tmp_path):
    report = coverage.build_reports()

    assert set(report.keys()) == {"records", "gaps", "appendix"}
    assert report["records"]
    sample_entity = sorted(report["records"].keys())[0]
    sample_record = report["records"][sample_entity]
    assert {"bucket", "intents", "coverage_flags", "paths", "schema", "policies", "notes"}.issubset(
        sample_record.keys()
    )

    json_path = tmp_path / "coverage.json"
    md_path = tmp_path / "coverage.md"
    coverage.write_json_report(report, output_path=json_path)
    coverage.write_markdown_report(report, output_path=md_path)

    assert json_path.exists()
    assert md_path.exists()

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert set(data.keys()) == {"records", "gaps", "appendix"}
    assert set(data["gaps"].keys()) == {"P0", "P1", "P2"}

    md_content = md_path.read_text(encoding="utf-8")
    for section in [
        "Resumo executivo",
        "Escopo e fontes de verdade",
        "Metodologia",
        "Matriz de coverage por entidade",
        "Gaps (P0/P1/P2)",
        "Apêndice",
    ]:
        assert section in md_content
