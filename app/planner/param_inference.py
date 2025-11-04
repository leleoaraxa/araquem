# app/planner/param_inference.py

from __future__ import annotations
from typing import Dict, Any, Optional, Tuple, List
import calendar
import datetime as dt
import re, json, unicodedata
from pathlib import Path

from app.utils.filecache import load_yaml_cached

_DEFAULTS_PATH = Path("data/ops/param_inference.yaml")
_WORD_RE = re.compile(r"\w+", flags=re.UNICODE)


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _norm(text: str) -> str:
    lowered = text.lower()
    no_accents = _strip_accents(lowered)
    return " ".join(_WORD_RE.findall(no_accents))


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path or not Path(path).exists():
        return {}
    return load_yaml_cached(str(path))


def _token_set(text: str) -> set[str]:
    return set(_norm(text).split())


def _match_keywords(text: str, kw_list: List[str]) -> bool:
    """Verifica se qualquer palavra ou frase de kw_list aparece isolada em text."""
    if not kw_list:
        return False
    tokens = _token_set(text)
    norm_kws = [_norm(k) for k in kw_list if k]
    for kw in norm_kws:
        # frases de múltiplas palavras
        if " " in kw:
            if re.search(rf"\b{re.escape(kw)}\b", _norm(text)):
                return True
            kw_tokens = set(kw.split())
            if kw_tokens.issubset(tokens):
                return True
        else:
            if kw in tokens:
                return True
    return False


def _entity_agg_defaults(entity_yaml_path: Optional[str]) -> Dict[str, Any]:
    """
    Lê defaults de agregação da entidade (limit/order para list, janelas permitidas, etc).
    Retorna dict com chaves: list (limit/order), avg, sum, windows_allowed
    """
    y = _load_yaml(Path(entity_yaml_path)) if entity_yaml_path else {}
    agg = (y.get("aggregations") or {}) if isinstance(y, dict) else {}
    defaults = (agg.get("defaults") or {}) if isinstance(agg, dict) else {}
    return {
        "list": defaults.get("list") or {},
        "avg": defaults.get("avg") or {},
        "sum": defaults.get("sum") or {},
        "windows_allowed": agg.get("windows_allowed") or [],
    }


def _months_from_window(window: Optional[str], default: int) -> int:
    if not window:
        return default
    try:
        kind, raw = str(window).split(":", 1)
    except ValueError:
        return default
    if kind != "months":
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def _shift_months(base: dt.date, months: int) -> dt.date:
    if months <= 0:
        return base
    year = base.year
    month = base.month - months
    while month <= 0:
        month += 12
        year -= 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(base.day, last_day)
    return dt.date(year, month, day)


def _infer_metricas_params(
    question: str,
    icfg: Dict[str, Any],
    entity_yaml_path: Optional[str],
) -> Dict[str, Any]:
    metric = None
    metric_keywords = icfg.get("metric_keywords") or {}
    for metric_name, spec in metric_keywords.items():
        if _match_keywords(question, spec.get("include", [])):
            metric = metric_name
            break

    if not metric:
        metric = icfg.get("default_metric")

    window = icfg.get("default_window")
    wkw = icfg.get("window_keywords") or {}
    for kind, mapping in wkw.items():
        for num, kws in mapping.items():
            if _match_keywords(question, kws):
                window = f"{kind}:{num}"
                break

    months = _months_from_window(window, default=12)
    today = dt.date.today()
    period_end = icfg.get("period_end") or today
    if isinstance(period_end, str):
        try:
            period_end_dt = dt.date.fromisoformat(period_end)
        except ValueError:
            period_end_dt = today
    else:
        period_end_dt = today
    period_start_dt = _shift_months(period_end_dt, months)

    return {
        "agg": "metrics",
        "metric": metric,
        "window": f"months:{months}",
        "window_months": months,
        "period_start": period_start_dt.isoformat(),
        "period_end": period_end_dt.isoformat(),
    }


def infer_params(
    question: str,
    intent: str,
    entity: Optional[str] = None,
    entity_yaml_path: Optional[str] = None,
    defaults_yaml_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retorna dict {"agg": ..., "window": ..., "limit": ..., "order": ...}
    seguindo data/ops/param_inference.yaml + defaults do YAML da entidade.
    Não usa querystring externa (compute-on-read).
    """
    # Carrega regras declarativas (param_inference.yaml)
    cfg_path = Path(defaults_yaml_path) if defaults_yaml_path else _DEFAULTS_PATH
    cfg = _load_yaml(cfg_path) or {}
    intents = (cfg or {}).get("intents", {})
    icfg = intents.get(intent, {})
    text = _norm(question)

    if intent == "metricas":
        return _infer_metricas_params(question, icfg, entity_yaml_path)

    # defaults
    agg = icfg.get("default_agg")
    window = icfg.get("default_window")
    limit = None
    order = "desc"
    # Defaults da entidade (limit/order e windows_allowed adicionais)
    ent_def = _entity_agg_defaults(entity_yaml_path)
    ent_windows_allowed = set(str(w) for w in (ent_def.get("windows_allowed") or []))

    # defaults da intent (param_inference.yaml)
    agg = icfg.get("default_agg")
    window = icfg.get("default_window")
    limit: Optional[int] = None
    order: Optional[str] = "desc"
    # 1) detectar agg por palavras
    agg_kw = icfg.get("agg_keywords") or {}

    candidates = []
    for agg_name, spec in (agg_kw or {}).items():
        if _match_keywords(text, spec.get("include", [])):
            candidates.append((agg_name, spec))

    if candidates:
        priority = icfg.get("agg_priority", ["avg", "sum", "latest", "list"])
        priority_order = {name: i for i, name in enumerate(priority)}
        agg, spec = sorted(candidates, key=lambda t: priority_order.get(t[0], 1_000))[0]

        if spec.get("window"):
            window = spec["window"]
        elif spec.get("window_defaults"):
            window = spec["window_defaults"][0]

    # 2) detectar janela (months:X ou count:Y)
    wkw = icfg.get("window_keywords") or {}
    window_kind: Optional[str] = None
    for kind, mapping in wkw.items():
        for num, kws in mapping.items():
            if _match_keywords(text, kws):
                if window_kind == "months" and kind != "months":
                    continue
                window = f"{kind}:{num}"
                window_kind = kind

    # 3) list → definir limit/order
    if agg == "list":
        # a) se janela é count:N, usar N como limit
        if (window or "").startswith("count:"):
            try:
                limit = int((window or "").split(":")[1])
            except Exception:
                limit = None
        if limit is None:
            limit = ent_def.get("list", {}).get("limit") or icfg.get(
                "defaults", {}
            ).get("list", {}).get("limit", 10)
        order = ent_def.get("list", {}).get("order") or icfg.get("defaults", {}).get(
            "list", {}
        ).get("order", "desc")
        # b) fallback para defaults da ENTIDADE (preferência) e, na falta, manter None/desc
        if limit is None:
            limit = ent_def.get("list", {}).get("limit")
        order = ent_def.get("list", {}).get("order", "desc")

    # 3.5) Semântica canônica: latest => janela sempre count:1
    if agg == "latest":
        window = "count:1"
    # 4) validar janela contra windows_allowed (intent + entidade)
    intent_allowed = set(str(w) for w in (icfg.get("windows_allowed") or []))
    allowed = (
        intent_allowed.union(ent_windows_allowed)
        if intent_allowed or ent_windows_allowed
        else set()
    )
    # Não invalida 'count:1' quando agg=latest
    if agg != "latest" and allowed and (str(window) not in allowed):
        window = icfg.get("default_window")

    if allowed and (str(window) not in allowed):
        # fallback no default da intent
        window = icfg.get("default_window")

    out = {"agg": agg, "window": window}
    if limit is not None:
        out["limit"] = limit
    if order is not None:
        out["order"] = order
    return out
