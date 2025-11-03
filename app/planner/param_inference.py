from __future__ import annotations
from typing import Dict, Any, Tuple
import re, json
from pathlib import Path

import yaml

_PARAM_PATH = Path("data/ops/param_inference.yaml")

_WORD_RE = re.compile(r"\w+", flags=re.UNICODE)


def _norm(text: str) -> str:
    return " ".join(_WORD_RE.findall(text.lower()))


def _load_cfg() -> Dict[str, Any]:
    with _PARAM_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _match_keywords(text: str, kw_list: list[str]) -> bool:
    return any(k in text for k in kw_list)


def infer_params(question: str, intent: str) -> Dict[str, Any]:
    """
    Retorna dict {"agg": ..., "window": ..., "limit": ..., "order": ...}
    seguindo data/ops/param_inference.yaml. Não usa querystring externa.
    """
    cfg = _load_cfg()
    intents = (cfg or {}).get("intents", {})
    icfg = intents.get(intent, {})
    text = _norm(question)

    # defaults
    agg = icfg.get("default_agg")
    window = icfg.get("default_window")
    limit = None
    order = "desc"

    # 1) detectar agg por palavras
    agg_kw = icfg.get("agg_keywords") or {}
    found = False
    for agg_name, spec in agg_kw.items():
        if _match_keywords(text, spec.get("include", [])):
            agg = agg_name
            # janelas default por agg (quando aplicável)
            if spec.get("window"):
                window = spec["window"]
            elif spec.get("window_defaults"):
                # pega a primeira janela default declarada
                window = spec["window_defaults"][0]
            found = True
            break

    # 2) detectar janela (months:X ou count:Y)
    wkw = icfg.get("window_keywords") or {}
    for kind, mapping in wkw.items():
        for num, kws in mapping.items():
            if _match_keywords(text, kws):
                window = f"{kind}:{num}"

    # 3) list → definir limit a partir de "count:Y" quando presente
    if agg == "list":
        if (window or "").startswith("count:"):
            try:
                limit = int((window or "").split(":")[1])
            except Exception:
                limit = icfg.get("defaults", {}).get("list", {}).get("limit", 10)
        else:
            # sem count → usa limit default se existir
            limit = icfg.get("defaults", {}).get("list", {}).get("limit", 10)
        order = icfg.get("defaults", {}).get("list", {}).get("order", "desc")

    # 4) validar janela contra windows_allowed
    allowed = set(icfg.get("windows_allowed", []))
    if allowed and window not in allowed:
        # fallback nos defaults da intent
        window = icfg.get("default_window")

    out = {"agg": agg, "window": window}
    if limit is not None:
        out["limit"] = limit
    if order is not None:
        out["order"] = order
    return out
