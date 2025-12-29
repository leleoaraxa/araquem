import json

from scripts.quality import build_coverage_report


def test_build_reports_smoke(tmp_path, monkeypatch):
    """Ensure the coverage report builder runs and produces expected structure."""

    # Redirect outputs to a temp directory to keep workspace clean during tests.
    monkeypatch.setattr(
        build_coverage_report, "MARKDOWN_REPORT_PATH", tmp_path / "COVERAGE.md"
    )
    monkeypatch.setattr(
        build_coverage_report, "JSON_REPORT_PATH", tmp_path / "coverage.json"
    )

    report = build_coverage_report.build_reports()
    build_coverage_report.write_json_report(report)
    build_coverage_report.write_markdown_report(report)

    json_path = tmp_path / "coverage.json"
    md_path = tmp_path / "COVERAGE.md"

    assert json_path.exists()
    assert md_path.exists()

    with json_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    # Minimal structural checks to ensure core sections are present.
    assert set(data.keys()) == {"records", "gaps", "appendix"}
    assert isinstance(data["records"], dict)
    assert isinstance(data["gaps"], dict)
    assert isinstance(data["appendix"], dict)

    # Validate a sample record has expected sub-keys.
    sample_entity = sorted(data["records"].keys())[0]
    sample_record = data["records"][sample_entity]
    assert {"intents", "coverage_flags", "schema", "policies"}.issubset(
        sample_record.keys()
    )

    # Ensure markdown content was written with expected sections.
    content = md_path.read_text(encoding="utf-8")
    for section in [
        "Resumo executivo",
        "Matriz de coverage por entidade",
        "Gaps P0/P1/P2",
        "Apêndice",
    ]:
        assert section in content
