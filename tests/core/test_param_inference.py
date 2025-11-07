# tests/test_param_inference.py

import json, yaml
from app.planner.param_inference import infer_params


def test_inference_samples():
    with open(
        "data/ops/quality_experimental/param_inference_samples.json",
        "r",
        encoding="utf-8",
    ) as f:
        samples = json.load(f)["samples"]
    for s in samples:
        q = s["question"]
        exp = s["expected"]
        got = infer_params(q, exp["intent"])
        for k, v in exp["aggregates"].items():
            assert got.get(k) == v, (q, k, got)
