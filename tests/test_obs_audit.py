import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "obs_audit.py"
YAML_PATH = ROOT / "data" / "ops" / "observability.yaml"
DASHBOARD_PATHS = [
    ROOT / "grafana" / "dashboards" / name
    for name in [
        "00_sirios_overview.json",
        "10_api_slo_pipeline.json",
        "20_planner_rag_intelligence.json",
        "30_ops_reliability.json",
    ]
]


def run_audit() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(AUDIT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_obs_audit_runs_ok():
    proc = run_audit()
    assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"


def test_dashboards_not_older_than_yaml():
    assert AUDIT.exists()
    yaml_stat = YAML_PATH.stat()
    dashboards_stats = {path: path.stat().st_mtime for path in DASHBOARD_PATHS}
    min_dash_mtime = min(dashboards_stats.values())

    desired_yaml_mtime = min_dash_mtime - 60
    original_yaml_times = (yaml_stat.st_atime, yaml_stat.st_mtime)

    os.utime(YAML_PATH, (desired_yaml_mtime, desired_yaml_mtime))

    try:
        proc = run_audit()
        assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    finally:
        os.utime(YAML_PATH, original_yaml_times)
        for path, mtime in dashboards_stats.items():
            os.utime(path, (mtime, mtime))
