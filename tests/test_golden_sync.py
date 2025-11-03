from pathlib import Path
import json
import subprocess
import sys


def _run(args):
    return subprocess.run(
        [sys.executable, "scripts/golden_sync.py", *args],
        capture_output=True,
        text=True,
    )


def test_check_fails_when_outdated(tmp_path: Path):
    yin = tmp_path / "m65_quality.yaml"
    yin.write_text(
        "samples:\n  - {question: 'Q1', expected_intent: 'cadastro', expected_entity: 'fiis_cadastro'}\n",
        encoding="utf-8",
    )

    yout = tmp_path / "routing_samples.json"
    yout.write_text('{"type":"routing","samples":[]}\n', encoding="utf-8")

    r = _run(["--in", str(yin), "--out", str(yout), "--check"])
    assert r.returncode == 1


def test_write_and_check_ok(tmp_path: Path):
    yin = tmp_path / "m65_quality.yaml"
    yin.write_text(
        "samples:\n  - {question: 'Q1', expected_intent: 'cadastro', expected_entity: 'fiis_cadastro'}\n",
        encoding="utf-8",
    )

    yout = tmp_path / "routing_samples.json"

    r1 = _run(["--in", str(yin), "--out", str(yout)])
    assert r1.returncode == 0
    assert json.loads(yout.read_text(encoding="utf-8")) == {
        "type": "routing",
        "samples": [
            {
                "question": "Q1",
                "expected_intent": "cadastro",
                "expected_entity": "fiis_cadastro",
            }
        ],
    }

    r2 = _run(["--in", str(yin), "--out", str(yout), "--check"])
    assert r2.returncode == 0
