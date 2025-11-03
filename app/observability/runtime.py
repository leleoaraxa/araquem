# app/observability/runtime.py
# Backend Prometheus + (no-op) spans e bootstrap. Registro centralizado de métricas.
import os, yaml, re, hashlib, json, urllib.parse, urllib.request
from typing import Dict, Any, Tuple, Optional

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter as PromCounter,
    Gauge as PromGauge,
    Histogram as PromHistogram,
    generate_latest,
)
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from app.observability import instrumentation as obs

# ---------------- Config -----------------------------------------------------


def load_config():
    cfg_path = os.environ.get("OBSERVABILITY_CONFIG", "data/ops/observability.yaml")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------- Tracing (opcional) ----------------------------------------


def init_tracing(service_name: str, cfg: dict):
    # keep behavior; só inicializa para a API conforme config
    if service_name == "api" and not cfg["services"]["gateway"]["tracing"]["enabled"]:
        return
    otlp_endpoint = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT", cfg["global"]["exporters"]["otlp_endpoint"]
    )
    if not str(otlp_endpoint).startswith(("http://", "https://")):
        otlp_endpoint = f"http://{otlp_endpoint}"
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
    )
    trace.set_tracer_provider(provider)


# ---------------- Utils ------------------------------------------------------


def sql_sanitize(sql: str, max_len: int = 512):
    sql = re.sub(r"\'[^']*\'", "?", sql)
    sql = re.sub(r"\b\d+(\.\d+)?\b", "?", sql)
    return sql[:max_len]


def hash_key(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ---------------- Prom Instant Query helper ---------------------------------


def prom_query_instant(expr: str):
    base = os.getenv("PROMETHEUS_URL", "http://prometheus:9090").rstrip("/")
    url = f"{base}/api/v1/query?query={urllib.parse.quote_plus(expr)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("status") != "success":
        return data
    result = (data.get("data") or {}).get("result") or []
    if len(result) == 1 and "value" in result[0] and len(result[0]["value"]) == 2:
        try:
            return float(result[0]["value"][1])
        except Exception:
            return data
    return data


# ---------------- Backend Prometheus (injeção) -------------------------------

_COUNTERS: Dict[Tuple[str, Tuple[str, ...]], PromCounter] = {}
_HISTOS: Dict[Tuple[str, Tuple[str, ...]], PromHistogram] = {}
_GAUGES: Dict[Tuple[str, Tuple[str, ...]], PromGauge] = {}

_DEFAULT_BUCKETS_MS = (0.5, 1, 2, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000)

# Esquemas CANÔNICOS de métricas → força labelnames e tipo, evita cardinalidade acidental
_METRIC_SCHEMAS = {
    # Explain (M6.6)
    "planner_explain_total": ("counter", ("intent", "entity", "route_id")),
    "planner_explain_errors_total": ("counter", ("stage",)),
    "planner_explain_match_total": (
        "counter",
        ("intent", "entity", "route_id", "match"),
    ),
    "planner_explain_gold_total": ("counter", ("intent", "entity")),
    "planner_explain_gold_agree_total": ("counter", ("intent", "entity")),
    "planner_explain_latency_ms_bucket": (
        "histogram",
        ("intent", "entity", "route_id"),
    ),
    # Decorator padrão de operações
    "app_op_total": ("counter", ("component", "operation", "status")),
    # Exemplos existentes (gateway/cache/planner/executor) — mantidos
    "sirios_http_request_duration_seconds": ("histogram", ("route", "method")),
    "sirios_http_requests_total": ("counter", ("route", "method", "code")),
    "sirios_cache_ops_total": ("counter", ("op", "outcome")),
    "sirios_cache_latency_seconds": ("histogram", ("op",)),
    "sirios_planner_route_decisions_total": (
        "counter",
        ("intent", "entity", "outcome"),
    ),
    "sirios_planner_duration_seconds": ("histogram", ("stage",)),
    "sirios_planner_explain_enabled_total": ("counter", ()),
    "sirios_planner_explain_latency_seconds": ("histogram", ()),
    "sirios_planner_explain_nodes_total": ("counter", ("node_kind",)),
    "sirios_planner_explain_weight_sum_total": ("counter", ("type",)),
    "sirios_planner_intent_score": ("histogram", ("intent",)),
    "sirios_planner_entity_score": ("histogram", ("entity",)),
    "sirios_planner_explain_decision_depth": ("gauge", ()),
    "sirios_planner_routed_total": ("counter", ("outcome",)),
    "sirios_planner_top1_match_total": ("counter", ("result",)),
    "sirios_planner_confusion_total": (
        "counter",
        ("expected_intent", "predicted_intent"),
    ),
    "sirios_planner_top2_gap_histogram": ("histogram", ()),
    "sirios_planner_quality_last_gap": ("gauge", ()),
    "sirios_planner_blocked_by_threshold_total": (
        "counter",
        ("reason", "intent", "entity"),
    ),
    "sirios_planner_projection_total": ("counter", ("outcome", "entity")),
    "sirios_sql_query_duration_seconds": ("histogram", ("entity", "db_name")),
    "sirios_sql_rows_returned_total": ("counter", ("entity",)),
    "sirios_sql_errors_total": ("counter", ("entity", "error_code")),
    "sirios_rag_search_total": ("counter", ("outcome",)),
    "sirios_rag_topscore": ("histogram", ()),
}


def _get_counter(name: str, labelnames: Tuple[str, ...]) -> PromCounter:
    key = (name, labelnames)
    if key not in _COUNTERS:
        _COUNTERS[key] = PromCounter(
            name, name.replace("_", " "), labelnames=labelnames
        )
    return _COUNTERS[key]


def _get_histogram(
    name: str, labelnames: Tuple[str, ...], buckets=None
) -> PromHistogram:
    key = (name, labelnames)
    if key not in _HISTOS:
        _HISTOS[key] = PromHistogram(
            name,
            name.replace("_", " "),
            labelnames=labelnames,
            buckets=(buckets or _DEFAULT_BUCKETS_MS),
        )
    return _HISTOS[key]


def _get_gauge(name: str, labelnames: Tuple[str, ...]) -> PromGauge:
    key = (name, labelnames)
    if key not in _GAUGES:
        _GAUGES[key] = PromGauge(name, name.replace("_", " "), labelnames=labelnames)
    return _GAUGES[key]


def _ensure_metric(name: str, labels: Dict[str, str]):
    """
    Garante tipo e labels conforme schema canônico.
    """
    if name not in _METRIC_SCHEMAS:
        raise ValueError(f"Métrica '{name}' não declarada no schema canônico.")
    kind, labelnames = _METRIC_SCHEMAS[name]
    # valida labels
    lbls_tuple = tuple(sorted((labels or {}).keys()))
    if tuple(sorted(labelnames)) != lbls_tuple:
        raise ValueError(
            f"Labels inválidos para '{name}'. Esperado {labelnames}, recebido {lbls_tuple}."
        )
    return kind, labelnames


class _SpanHandle:
    __slots__ = ("span", "_cm")

    def __init__(self, span, cm=None):
        self.span = span
        self._cm = cm


class _PromBackend(obs._Backend):
    def __init__(self) -> None:
        self._tracer = trace.get_tracer("app")

    def inc(self, name: str, labels: Dict[str, str], value: float = 1.0) -> None:
        kind, labelnames = _ensure_metric(name, labels)
        if kind != "counter":
            raise ValueError(f"'{name}' não é counter.")
        ctr = _get_counter(name, labelnames)
        if labelnames:
            ctr.labels(**labels).inc(float(value))
        else:
            ctr.inc(float(value))

    def observe(self, name: str, value: float, labels: Dict[str, str]) -> None:
        kind, labelnames = _ensure_metric(name, labels)
        if kind != "histogram":
            raise ValueError(f"'{name}' não é histogram.")
        h = _get_histogram(name, labelnames)
        if labelnames:
            h.labels(**labels).observe(float(value))
        else:
            h.observe(float(value))

    def start_span(self, name: str, attributes: Dict[str, Any]):
        cm = self._tracer.start_as_current_span(name)
        span = cm.__enter__()
        handle = _SpanHandle(span, cm)
        for key, value in attributes.items():
            if value is not None:
                self.set_span_attr(handle, key, value)
        return handle

    def end_span(
        self,
        span,
        exc_type: Optional[type] = None,
        exc_value: Optional[BaseException] = None,
        exc_tb: Any = None,
    ) -> None:
        cm = getattr(span, "_cm", None)
        if cm is not None:
            cm.__exit__(exc_type, exc_value, exc_tb)

    def set_span_attr(self, span, key: str, value: Any) -> None:
        raw = getattr(span, "span", span)
        if raw is None:
            return
        setter = getattr(raw, "set_attribute", None)
        if callable(setter):
            setter(key, value)
        else:
            raw.setdefault("attrs", {})[key] = value

    def span_trace_id(self, span) -> Optional[str]:
        raw = getattr(span, "span", span)
        if raw is None:
            return None
        ctx = getattr(raw, "get_span_context", lambda: None)()
        trace_id = getattr(ctx, "trace_id", 0) if ctx else 0
        if trace_id:
            return f"{trace_id:032x}"
        return None

    def current_trace_id(self) -> Optional[str]:
        current = trace.get_current_span()
        ctx = current.get_span_context() if current else None
        trace_id = getattr(ctx, "trace_id", 0) if ctx else 0
        if trace_id:
            return f"{trace_id:032x}"
        return None


def render_prometheus_latest():
    return generate_latest(), CONTENT_TYPE_LATEST


def bootstrap(service_name: str = "api", cfg: dict = None) -> None:
    """
    Chamar no app.main: inicializa tracing (opcional) e injeta backend Prometheus.
    """
    if cfg is None:
        cfg = load_config()
    # Tracing opcional conforme config
    init_tracing(service_name, cfg)
    # Injeção do backend Prometheus na facade
    obs.set_backend(_PromBackend())


# ----------------- Inicializadores compat (caso queira manter) --------------


def init_metrics(cfg: dict, registry=None):
    # Mantido por compatibilidade com seu código atual de gateway
    gw = cfg["services"]["gateway"]["metrics"]
    http_hist = http_counter = None
    if gw.get("http_request_duration_seconds", {}).get("enabled", False):
        buckets = gw["http_request_duration_seconds"]["buckets"]
        _get_histogram(
            "sirios_http_request_duration_seconds", ("route", "method"), buckets=buckets
        )
        http_hist = True
    if gw.get("http_requests_total", {}).get("enabled", False):
        _get_counter("sirios_http_requests_total", ("route", "method", "code"))
        http_counter = True
    return {"http_hist": http_hist, "http_counter": http_counter}


def init_cache_metrics(cfg: dict, registry=None):
    ccf = cfg["services"]["cache"]["metrics"]
    if ccf.get("cache_ops_total", {}).get("enabled", True):
        _get_counter("sirios_cache_ops_total", ("op", "outcome"))
    if ccf.get("cache_latency_seconds", {}).get("enabled", True):
        buckets = ccf["cache_latency_seconds"]["buckets"]
        _get_histogram("sirios_cache_latency_seconds", ("op",), buckets=buckets)
    return {"ops": True, "latency": True}


def init_planner_metrics(cfg: dict, registry=None):
    ocfg = cfg["services"]["orchestrator"]["metrics"]

    def on(flag, name, kind, labels, *, buckets=None):
        if ocfg.get(flag, {}).get("enabled", False):
            if kind == "counter":
                _get_counter(name, labels)
            elif kind == "gauge":
                _get_gauge(name, labels)
            elif kind == "histogram":
                _get_histogram(name, labels, buckets=buckets)

    on(
        "planner_route_decisions_total",
        "sirios_planner_route_decisions_total",
        "counter",
        ("intent", "entity", "outcome"),
    )
    on(
        "planner_duration_seconds",
        "sirios_planner_duration_seconds",
        "histogram",
        ("stage",),
        buckets=ocfg.get("planner_duration_seconds", {}).get("buckets"),
    )
    on(
        "planner_explain_enabled_total",
        "sirios_planner_explain_enabled_total",
        "counter",
        (),
    )
    on(
        "planner_explain_latency_seconds",
        "sirios_planner_explain_latency_seconds",
        "histogram",
        (),
        buckets=ocfg.get("planner_explain_latency_seconds", {}).get(
            "buckets", [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2]
        ),
    )
    on(
        "planner_explain_nodes_total",
        "sirios_planner_explain_nodes_total",
        "counter",
        ("node_kind",),
    )
    on(
        "planner_explain_weight_sum_total",
        "sirios_planner_explain_weight_sum_total",
        "counter",
        ("type",),
    )
    on(
        "planner_intent_score",
        "sirios_planner_intent_score",
        "histogram",
        ("intent",),
        buckets=ocfg.get("planner_intent_score", {}).get(
            "buckets", [0, 1, 2, 3, 5, 8, 13, 21]
        ),
    )
    on(
        "planner_entity_score",
        "sirios_planner_entity_score",
        "histogram",
        ("entity",),
        buckets=ocfg.get("planner_entity_score", {}).get(
            "buckets", [0, 1, 2, 3, 5, 8, 13, 21]
        ),
    )
    on(
        "planner_explain_decision_depth",
        "sirios_planner_explain_decision_depth",
        "gauge",
        (),
    )
    on("planner_routed_total", "sirios_planner_routed_total", "counter", ("outcome",))
    on(
        "planner_top1_match_total",
        "sirios_planner_top1_match_total",
        "counter",
        ("result",),
    )
    on(
        "planner_confusion_total",
        "sirios_planner_confusion_total",
        "counter",
        ("expected_intent", "predicted_intent"),
    )
    on(
        "planner_top2_gap_histogram",
        "sirios_planner_top2_gap_histogram",
        "histogram",
        (),
        buckets=ocfg.get("planner_top2_gap_histogram", {}).get(
            "buckets", [0.0, 0.5, 1, 2, 3, 5]
        ),
    )
    on("planner_quality_last_gap", "sirios_planner_quality_last_gap", "gauge", ())
    on(
        "planner_blocked_by_threshold_total",
        "sirios_planner_blocked_by_threshold_total",
        "counter",
        ("reason", "intent", "entity"),
    )
    on(
        "planner_projection_total",
        "sirios_planner_projection_total",
        "counter",
        ("outcome", "entity"),
    )
    return {"ok": True}


def init_sql_metrics(cfg: dict, registry=None):
    ecfg = cfg["services"]["executor"]["metrics"]
    if ecfg.get("sql_query_duration_seconds", {}).get("enabled", True):
        buckets = ecfg["sql_query_duration_seconds"]["buckets"]
        _get_histogram(
            "sirios_sql_query_duration_seconds", ("entity", "db_name"), buckets=buckets
        )
    if ecfg.get("sql_rows_returned_total", {}).get("enabled", True):
        _get_counter("sirios_sql_rows_returned_total", ("entity",))
    if ecfg.get("sql_errors_total", {}).get("enabled", True):
        _get_counter("sirios_sql_errors_total", ("entity", "error_code"))
    return {"ok": True}
