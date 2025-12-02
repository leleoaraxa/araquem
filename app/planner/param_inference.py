# app/planner/param_inference.py
# Contexto não é consultado diretamente pelo Planner.
# O endpoint /ask resolve contexto via ContextManager.resolve_last_reference()
# e injeta identifiers já enriquecidos.
from __future__ import annotations
from typing import Dict, Any, Optional, List
import calendar
import datetime as dt
import re, unicodedata
from pathlib import Path

from app.utils.filecache import load_yaml_cached

_DEFAULTS_PATH = Path("data/ops/param_inference.yaml")
_WORD_RE = re.compile(r"\w+", flags=re.UNICODE)
_ALLOWED_AGGS = {"avg", "sum", "latest", "list"}
_WINDOW_KINDS = {"months", "count"}
# Extração de tickers é responsabilidade do Orchestrator (extract_identifiers).


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _norm(text: str) -> str:
    lowered = text.lower()
    no_accents = _strip_accents(lowered)
    return " ".join(_WORD_RE.findall(no_accents))


def _require_mapping(obj: Any, *, label: str) -> Dict[str, Any]:
    if not isinstance(obj, dict):
        raise ValueError(f"param_inference.yaml inválido: {label} deve ser mapeamento")
    return obj


def _require_list(obj: Any, *, label: str) -> List[Any]:
    if not isinstance(obj, list):
        raise ValueError(f"param_inference.yaml inválido: {label} deve ser lista")
    return obj


def _validate_window(value: Any, *, context: str) -> str:
    if not isinstance(value, str):
        raise ValueError(
            f"param_inference.yaml inválido: {context} deve ter formato kind:value (ex: months:6)"
        )
    try:
        kind, raw = value.split(":", 1)
    except ValueError:
        raise ValueError(
            f"param_inference.yaml inválido: {context} deve ter formato kind:value (ex: months:6)"
        )
    if kind not in _WINDOW_KINDS:
        raise ValueError(
            f"param_inference.yaml inválido: {context} usa kind desconhecido '{kind}'"
        )
    try:
        parsed = int(raw)
    except ValueError:
        raise ValueError(
            f"param_inference.yaml inválido: {context} deve ter valor numérico inteiro"
        )
    if parsed <= 0:
        raise ValueError(
            f"param_inference.yaml inválido: {context} deve ser inteiro positivo"
        )
    return f"{kind}:{parsed}"


def _validate_param_inference(data: Dict[str, Any], *, path: Path) -> Dict[str, Any]:
    _require_mapping(data, label="raiz do YAML")

    intents = data.get("intents", {})
    _require_mapping(intents, label="intents")

    for intent_name, cfg in intents.items():
        _require_mapping(cfg, label=f"intent '{intent_name}'")

        if "default_agg" in cfg:
            default_agg = cfg["default_agg"]
            if default_agg not in _ALLOWED_AGGS:
                raise ValueError(
                    f"param_inference.yaml inválido: default_agg para intent '{intent_name}' é desconhecido"
                )

        if "agg_priority" in cfg:
            agg_priority = cfg["agg_priority"]
            if not isinstance(agg_priority, list) or any(
                not isinstance(a, str) or a not in _ALLOWED_AGGS for a in agg_priority
            ):
                raise ValueError(
                    "param_inference.yaml inválido: agg_priority da intent "
                    f"'{intent_name}' deve ser lista de agregações conhecidas"
                )

        if "default_window" in cfg:
            cfg["default_window"] = _validate_window(
                cfg["default_window"],
                context=f"default_window para intent '{intent_name}'",
            )

        if "windows_allowed" in cfg:
            windows_allowed = _require_list(
                cfg.get("windows_allowed"),
                label=f"windows_allowed da intent '{intent_name}'",
            )
            cfg["windows_allowed"] = [
                _validate_window(
                    w, context=f"windows_allowed da intent '{intent_name}'"
                )
                for w in windows_allowed
            ]

        agg_keywords = cfg.get("agg_keywords", {})
        _require_mapping(agg_keywords, label=f"agg_keywords da intent '{intent_name}'")
        for agg_name, spec in agg_keywords.items():
            if agg_name not in _ALLOWED_AGGS:
                raise ValueError(
                    f"param_inference.yaml inválido: agg '{agg_name}' desconhecido na intent '{intent_name}'"
                )
            _require_mapping(
                spec, label=f"agg_keywords.{agg_name} da intent '{intent_name}'"
            )
            include = spec.get("include", [])
            if include is not None:
                include_list = _require_list(
                    include,
                    label=f"include de agg '{agg_name}' na intent '{intent_name}'",
                )
                for kw in include_list:
                    if not isinstance(kw, str):
                        raise ValueError(
                            f"param_inference.yaml inválido: keywords de agg '{agg_name}' na intent '{intent_name}' devem ser strings"
                        )
            if spec.get("window") is not None:
                spec["window"] = _validate_window(
                    spec["window"],
                    context=f"window de agg '{agg_name}' na intent '{intent_name}'",
                )
            if spec.get("window_defaults") is not None:
                defaults = _require_list(
                    spec.get("window_defaults"),
                    label=f"window_defaults de agg '{agg_name}' na intent '{intent_name}'",
                )
                spec["window_defaults"] = [
                    _validate_window(
                        w,
                        context=f"window_defaults de agg '{agg_name}' na intent '{intent_name}'",
                    )
                    for w in defaults
                ]

        window_keywords = cfg.get("window_keywords")
        if window_keywords is not None:
            _require_mapping(
                window_keywords, label=f"window_keywords da intent '{intent_name}'"
            )
            for kind, mapping in window_keywords.items():
                if kind not in _WINDOW_KINDS:
                    raise ValueError(
                        f"param_inference.yaml inválido: window_keywords usa kind desconhecido '{kind}' na intent '{intent_name}'"
                    )
                _require_mapping(
                    mapping, label=f"window_keywords.{kind} da intent '{intent_name}'"
                )
                for num, kws in mapping.items():
                    try:
                        num_int = int(num)
                    except Exception:
                        raise ValueError(
                            f"param_inference.yaml inválido: chave de janela '{num}' deve ser inteiro em window_keywords da intent '{intent_name}'"
                        )
                    if num_int <= 0:
                        raise ValueError(
                            f"param_inference.yaml inválido: janela '{num}' deve ser > 0 em window_keywords da intent '{intent_name}'"
                        )
                    kws_list = _require_list(
                        kws,
                        label=f"window_keywords.{kind}.{num} da intent '{intent_name}'",
                    )
                    for kw in kws_list:
                        if not isinstance(kw, str):
                            raise ValueError(
                                f"param_inference.yaml inválido: keywords em window_keywords.{kind}.{num} da intent '{intent_name}' devem ser strings"
                            )

        defaults = cfg.get("defaults")
        if defaults is not None:
            _require_mapping(defaults, label=f"defaults da intent '{intent_name}'")
            list_defaults = defaults.get("list")
            if list_defaults is not None:
                _require_mapping(
                    list_defaults, label=f"defaults.list da intent '{intent_name}'"
                )
                if "limit" in list_defaults:
                    limit_value = list_defaults.get("limit")
                    if not isinstance(limit_value, int) or limit_value <= 0:
                        raise ValueError(
                            f"param_inference.yaml inválido: defaults.list.limit da intent '{intent_name}' deve ser inteiro positivo"
                        )
                if "order" in list_defaults:
                    order_value = list_defaults.get("order")
                    if order_value not in {"asc", "desc"}:
                        raise ValueError(
                            f"param_inference.yaml inválido: defaults.list.order da intent '{intent_name}' deve ser 'asc' ou 'desc'"
                        )

        params_cfg = cfg.get("params")
        if params_cfg is not None:
            params_map = _require_mapping(
                params_cfg, label=f"params da intent '{intent_name}'"
            )
            for param_name, spec in params_map.items():
                _require_mapping(
                    spec, label=f"params.{param_name} da intent '{intent_name}'"
                )
                if "source" in spec:
                    source_list = _require_list(
                        spec.get("source"),
                        label=f"params.{param_name}.source da intent '{intent_name}'",
                    )
                    for src in source_list:
                        if not isinstance(src, str):
                            raise ValueError(
                                "param_inference.yaml inválido: source de params deve ser lista de strings"
                            )
                if "context_key" in spec and spec.get("context_key") is not None:
                    if not isinstance(spec.get("context_key"), str):
                        raise ValueError(
                            "param_inference.yaml inválido: context_key em params deve ser string"
                        )

    return data


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path or not Path(path).exists():
        return {}
    data = load_yaml_cached(str(path))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("param_inference.yaml inválido: raiz deve ser mapeamento")
    return _validate_param_inference(data, path=path)


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
    Lê defaults de agregação da ENTIDADE (limit/order para list, janelas permitidas).
    Retorna dict com chaves: list (limit/order), avg, sum, windows_allowed.
    """
    if entity_yaml_path and Path(entity_yaml_path).exists():
        y = load_yaml_cached(str(entity_yaml_path)) or {}
    else:
        y = {}
    agg = (y.get("aggregations") or {}) if isinstance(y, dict) else {}
    defaults = (agg.get("defaults") or {}) if isinstance(agg, dict) else {}
    list_defaults = defaults.get("list") if isinstance(defaults, dict) else {}
    limit = None
    order = None
    if isinstance(list_defaults, dict):
        if (
            isinstance(list_defaults.get("limit"), int)
            and list_defaults.get("limit") > 0
        ):
            limit = list_defaults.get("limit")
        if list_defaults.get("order") in {"asc", "desc"}:
            order = list_defaults.get("order")

    ent_windows_allowed: List[str] = []
    raw_windows = agg.get("windows_allowed") if isinstance(agg, dict) else None
    if isinstance(raw_windows, list):
        for w in raw_windows:
            ent_windows_allowed.append(
                _validate_window(w, context="aggregations.windows_allowed")
            )

    return {
        "list": {"limit": limit, "order": order},
        "avg": defaults.get("avg") or {},
        "sum": defaults.get("sum") or {},
        "windows_allowed": ent_windows_allowed,
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


def _ticker_from_identifiers(
    identifiers: Optional[Dict[str, Any]], question: str
) -> Optional[str]:
    """
    Resolve ticker a partir dos identifiers canônicos extraídos pelo Orchestrator.

    Regras:
        - Se houver 'ticker' string não vazia, usa esse.
        - Se houver 'tickers' lista com exatamente 1 elemento string, usa esse.
        - Em qualquer cenário ambíguo (0 ou >1 tickers), retorna None.
        - NÃO faz regex em cima do texto cru (question).
    """
    if not identifiers or not isinstance(identifiers, dict):
        return None

    ticker = identifiers.get("ticker")
    if isinstance(ticker, str) and ticker:
        return ticker

    tickers = identifiers.get("tickers")
    if isinstance(tickers, list) and len(tickers) == 1:
        first = tickers[0]
        if isinstance(first, str) and first:
            return first
    return None


def infer_params(
    question: str,
    intent: str,
    entity: Optional[str] = None,
    entity_yaml_path: Optional[str] = None,
    defaults_yaml_path: Optional[str] = None,
    identifiers: Optional[Dict[str, Any]] = None,
    client_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retorna dict {"agg": ..., "window": ..., "limit": ..., "order": ...}
    seguindo data/ops/param_inference.yaml + defaults do YAML da entidade.
    Não usa querystring externa.

    Toda semântica de negócio (prioridade de agg, janelas permitidas,
    defaults de limit/order) é carregada dos YAMLs declarativos. O código
    apenas aplica as regras declaradas.
    """
    # Carrega regras declarativas (param_inference.yaml)
    cfg_path = Path(defaults_yaml_path) if defaults_yaml_path else _DEFAULTS_PATH
    cfg = _load_yaml(cfg_path) or {}
    intents = (cfg or {}).get("intents", {})
    icfg = intents.get(intent, {})
    text = _norm(question)

    # defaults
    agg = icfg.get("default_agg")
    window = icfg.get("default_window")
    limit: Optional[int] = None
    order: Optional[str] = None

    # Defaults da ENTIDADE (limit/order e windows_allowed adicionais)
    ent_def = _entity_agg_defaults(entity_yaml_path)
    ent_windows_allowed = set(str(w) for w in (ent_def.get("windows_allowed") or []))

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
        # b) defaults (ENTIDADE > intent)
        if limit is None:
            limit = ent_def.get("list", {}).get("limit") or icfg.get(
                "defaults", {}
            ).get("list", {}).get("limit")
        order = ent_def.get("list", {}).get("order") or icfg.get("defaults", {}).get(
            "list", {}
        ).get("order")
        if limit is None:
            raise ValueError(
                "param_inference: nenhum limit configurado para agg 'list'; defina em defaults.list.limit do YAML"
            )
        if order is None:
            raise ValueError(
                "param_inference: nenhum order configurado para agg 'list'; defina em defaults.list.order do YAML"
            )

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
    # Se há janelas permitidas mas nenhuma janela foi inferida,
    # tenta usar a default_window declarada para a intent.
    if allowed and not window:
        window = icfg.get("default_window")

    if allowed and window:
        if str(window) not in allowed:
            fallback = icfg.get("default_window")
            if fallback and str(fallback) in allowed:
                window = fallback
            elif fallback:
                raise ValueError(
                    f"param_inference: janela '{window}' não permitida e default_window '{fallback}' fora da lista permitida para intent '{intent}'"
                )
            else:
                raise ValueError(
                    f"param_inference: janela '{window}' não permitida para intent '{intent}'"
                )

    out = {"agg": agg, "window": window}
    if limit is not None:
        out["limit"] = limit
    if order is not None:
        out["order"] = order

    params_section = icfg.get("params") if isinstance(icfg, dict) else {}
    if isinstance(params_section, dict):
        ticker_cfg = (
            params_section.get("ticker") if isinstance(params_section, dict) else None
        )
        if isinstance(ticker_cfg, dict):
            sources = ticker_cfg.get("source") or []
            ticker_value: Optional[str] = None
            if "text" in sources:
                ticker_value = _ticker_from_identifiers(identifiers, question)
            if not ticker_value and "context" in sources:
                ticker_value = _ticker_from_identifiers(identifiers, question)
            if ticker_value:
                out["ticker"] = ticker_value
    return out
