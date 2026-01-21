from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.presenter.institutional import compose_institutional_answer, load_institutional_policy
from app.utils.filecache import load_yaml_cached


def main() -> int:
    policy = load_institutional_policy()
    if not isinstance(policy, dict) or not policy:
        print("Policy not found or invalid.")
        return 1

    paths = policy.get("paths") if isinstance(policy, dict) else {}
    response_contract_path = paths.get("response_contract") if isinstance(paths, dict) else None
    intent_map_path = paths.get("intent_map") if isinstance(paths, dict) else None
    concepts_path = paths.get("concepts") if isinstance(paths, dict) else None

    if not all(
        isinstance(path, str) and path.strip()
        for path in (response_contract_path, intent_map_path, concepts_path)
    ):
        print("Policy paths are missing.")
        return 1

    contract = load_yaml_cached(response_contract_path)
    intent_map = load_yaml_cached(intent_map_path)
    concepts = load_yaml_cached(concepts_path)

    if not contract or not intent_map or not concepts:
        print("Failed to load institutional contract sources.")
        return 1

    baseline_answer = "A SIRIOS é uma plataforma institucional de análise e educação sobre FIIs."
    intent = "institutional_what_is_sirios"

    composed = compose_institutional_answer(
        baseline_answer=baseline_answer,
        intent=intent,
    )

    if not composed:
        print("No composed answer produced.")
        return 1

    print(composed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
