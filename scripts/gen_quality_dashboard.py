#!/usr/bin/env python3
import json, os, sys, yaml
from pathlib import Path
from datetime import datetime, UTC
import argparse

QUALITY_POLICY_PATH = os.getenv("QUALITY_POLICY_PATH", "data/policies/quality.yaml")
FALLBACK_THR_PATH = os.getenv("PLANNER_THRESHOLDS_PATH", "data/ops/planner_thresholds.yaml")
OUT_PATH = Path("grafana/dashboards/quality_dashboard.json")

# Painel base
def base_dashboard():
    return {
        "title": "Araquem — Quality Gates (YAML-driven)",
        "uid": "araquem-quality-gates",
        "timezone": "browser",
        "schemaVersion": 39,
        "version": 1,
        "refresh": "30s",
        "tags": ["Araquem", "Planner", "Quality", "YAML"],
        "time": {"from": "now-6h", "to": "now"},
        "panels": [],
    }

def gauge_panel(title, expr, min_val, max_val, thresholds, x, y):
    """
    thresholds: lista de (value, color, label_opcional)
    """
    return {
        "type": "gauge",
        "title": title,
        "gridPos": {"x": x, "y": y, "w": 8, "h": 6},
        "targets": [{"expr": expr, "legendFormat": ""}],
        "options": {
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "orientation": "auto",
            "showThresholdLabels": True,
            "showThresholdMarkers": True,
            "min": min_val,
            "max": max_val,
            "thresholds": {
                "mode": "absolute",
                "steps": [
                    # Grafana espera steps ordenados crescente
                    {"value": None, "color": thresholds[0][1]},  # cor inicial
                    *[
                        {"value": v, "color": c}
                        for (v, c, *_) in thresholds[1:]
                    ],
                ],
            },
        },
        "fieldConfig": {"defaults": {"unit": "percentunit"},"overrides": []},
    }

def singlestat_panel(title, expr, unit, x, y):
    return {
        "type": "stat",
        "title": title,
        "gridPos": {"x": x, "y": y, "w": 8, "h": 4},
        "targets": [{"expr": expr}],
        "options": {
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "orientation": "auto",
            "colorMode": "value",
        },
        "fieldConfig": {"defaults": {"unit": unit},"overrides": []},
    }

def table_panel(title, expr, x, y):
    return {
        "type": "table",
        "title": title,
        "gridPos": {"x": x, "y": y, "w": 24, "h": 7},
        "targets": [{"expr": expr}],
        "options": {
            "showHeader": True
        },
        "fieldConfig": {"defaults": {},"overrides": []},
    }

def heatmap_panel(title, expr, x, y, h=10):
    return {
        "type": "heatmap",
        "title": title,
        "gridPos": {"x": x, "y": y, "w": 24, "h": h},
        "targets": [{"expr": expr}],
        "options": {"yAxis": {"format": "short"}}
    }

def main():
    parser = argparse.ArgumentParser(description="Generate Grafana dashboard from YAML thresholds")
    parser.add_argument("--pretty", action="store_true", help="Emit pretty-printed JSON (indent=2)")
    args = parser.parse_args()

    policy_path = Path(QUALITY_POLICY_PATH)
    source_path = policy_path if policy_path.exists() else Path(FALLBACK_THR_PATH)
    if not source_path.exists():
        print(
            f"error: quality policy not found (tried {policy_path} and {FALLBACK_THR_PATH})",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(source_path, "r", encoding="utf-8") as f:
        policy = yaml.safe_load(f) or {}

    targets = (policy.get("targets") or {})
    if not targets:
        targets = ((policy.get("quality_gates") or {}).get("thresholds") or {})

    min_top1_accuracy = float(targets.get("min_top1_accuracy", 0.95))
    min_routed_rate   = float(targets.get("min_routed_rate", 0.98))
    min_top2_gap      = float(targets.get("min_top2_gap", 0.25))
    # misses_* não entram em gauge; exibiremos em stat/table

    db = base_dashboard()

    # PromQL (mesmos usados no /ops/quality/report)
    q_top1_acc  = 'sum(sirios_planner_top1_match_total{result="hit"}) / clamp_min(sum(sirios_planner_top1_match_total), 1)'
    q_routed_rt = 'sum(sirios_planner_routed_total{outcome!="unroutable"}) / clamp_min(sum(sirios_planner_routed_total), 1)'
    q_gap_p50   = 'histogram_quantile(0.50, sum(rate(sirios_planner_top2_gap_histogram_bucket[5m])) by (le))'
    q_miss_abs  = 'sum(sirios_planner_top1_match_total{result="miss"})'
    q_miss_ratio= f'({q_miss_abs}) / clamp_min(sum(sirios_planner_top1_match_total), 1)'
    q_conf_heat = 'sum by (expected_intent, predicted_intent) (sirios_planner_confusion_total)'

    # Gauges com thresholds vindos do YAML
    # Cores: vermelho (#E02F44), amarelo (#EAB839), verde (#299C46)
    # Top1 Accuracy
    db["panels"].append(
        gauge_panel(
            "Top-1 Accuracy",
            q_top1_acc,
            0, 1,
            thresholds=[
                (None, "#E02F44"),                         # default
                (min_top1_accuracy, "#299C46", "pass"),    # >= min => verde
            ],
            x=0, y=0
        )
    )
    # Routed Rate
    db["panels"].append(
        gauge_panel(
            "Routed Rate",
            q_routed_rt,
            0, 1,
            thresholds=[
                (None, "#E02F44"),
                (min_routed_rate, "#299C46", "pass"),
            ],
            x=8, y=0
        )
    )
    # Top-2 Gap (p50) — tratamos como [0..1] no gauge; gap pode ser >1 em alguns modelos, mas manteremos 1 para leitura
    db["panels"].append(
        gauge_panel(
            "Top-2 Gap (p50)",
            q_gap_p50,
            0, 1,
            thresholds=[
                (None, "#E02F44"),
                (min_top2_gap, "#299C46", "pass"),
            ],
            x=16, y=0
        )
    )

    # Misses (stat)
    db["panels"].append(
        singlestat_panel("Misses (abs)", q_miss_abs, "none", x=0, y=6)
    )
    db["panels"].append(
        singlestat_panel("Misses (ratio)", q_miss_ratio, "percentunit", x=8, y=6)
    )

    # Confusion Matrix (heatmap)
    db["panels"].append(
        heatmap_panel("Confusion Matrix — expected × predicted", q_conf_heat, x=0, y=10, h=10)
    )

    # Metadata (read-only, título com versão/janela)
    version = str(thr.get("version", "unknown"))
    window  = str(thr.get("window", "rolling"))
    db["title"] = f"Araquem — Quality Gates (v{version}, window={window})"
    db["annotations"] = {
        "list": [{
            "builtIn": 1, "datasource": "-- Grafana --",
            "enable": True, "hide": True, "iconColor": "rgba(0, 211, 255, 1)",
            "name": "Annotations & Alerts", "type": "dashboard"
        }]
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # pretty opcional para facilitar diff/leitura. Por padrão mantemos minificado.
    if args.pretty or os.getenv("DASH_PRETTY_JSON", "").lower() in ("1","true","yes"):
        with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as f:
            json.dump(db, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write("\n")
    else:
        with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as f:
            json.dump(db, f, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
            f.write("\n")

    now_utc = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    print(f"[ok] dashboard gerado: {OUT_PATH} @ {now_utc}")

if __name__ == "__main__":
    main()
