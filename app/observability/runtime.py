# app/observability/runtime.py
import os, yaml, re, hashlib
from prometheus_client import Counter, Histogram
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

def load_config():
    cfg_path = os.environ.get("OBSERVABILITY_CONFIG", "data/ops/observability.yaml")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def init_tracing(service_name: str, cfg: dict):
    if not cfg["services"]["gateway"]["tracing"]["enabled"] and service_name == "api":
        return
    # Prefer env var; fallback para YAML. Sempre com esquema http:// para gRPC.
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", cfg["global"]["exporters"]["otlp_endpoint"])
    if not str(otlp_endpoint).startswith("http://") and not str(otlp_endpoint).startswith("https://"):
        otlp_endpoint = f"http://{otlp_endpoint}"
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)))
    trace.set_tracer_provider(provider)

def sql_sanitize(sql: str, max_len: int = 512):
    # elide literals rudimentar: números e strings → '?'
    sql = re.sub(r"\'[^']*\'", "?", sql)
    sql = re.sub(r"\b\d+(\.\d+)?\b", "?", sql)
    return sql[:max_len]

def hash_key(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def init_metrics(cfg: dict, registry=None):
    # exemplo mínimo: buckets do gateway
    gw = cfg["services"]["gateway"]["metrics"]
    http_hist = None
    if gw["http_request_duration_seconds"]["enabled"]:
        buckets = gw["http_request_duration_seconds"]["buckets"]
        http_hist = Histogram(
            "sirios_http_request_duration_seconds",
            "Duração das requisições HTTP",
            ["route","method"],
            buckets=buckets,
            registry=registry,
        )
    http_counter = None
    if gw["http_requests_total"]["enabled"]:
        http_counter = Counter(
            "sirios_http_requests_total",
            "Total de requisições HTTP",
            ["route","method","code"],
            registry=registry,
        )
    return {"http_hist": http_hist, "http_counter": http_counter}


def init_planner_metrics(cfg: dict, registry=None):
    """
    Métricas do Planner/Orchestrator via YAML (services.orchestrator.metrics).
    Retorna dict com handlers já registrados no 'registry' informado.
    """
    ocfg = cfg["services"]["orchestrator"]["metrics"]
    decisions = duration = None
    if ocfg.get("planner_route_decisions_total", {}).get("enabled", True):
        decisions = Counter(
            "sirios_planner_route_decisions_total",
            "Decisões de roteamento do planner",
            ["intent", "entity", "outcome"],
            registry=registry,
        )
    if ocfg.get("planner_duration_seconds", {}).get("enabled", True):
        buckets = ocfg["planner_duration_seconds"]["buckets"]
        duration = Histogram(
            "sirios_planner_duration_seconds",
            "Duração por estágio do planner",
            ["stage"],
            buckets=buckets,
            registry=registry,
        )
    return {"decisions": decisions, "duration": duration}

def init_sql_metrics(cfg: dict, registry=None):
    """
    Métricas do Executor SQL via YAML (services.executor.metrics).
    Retorna dict com handlers já registrados no 'registry' informado.
    """
    ecfg = cfg["services"]["executor"]["metrics"]
    qhist = rows = errors = None
    if ecfg.get("sql_query_duration_seconds", {}).get("enabled", True):
        buckets = ecfg["sql_query_duration_seconds"]["buckets"]
        qhist = Histogram(
            "sirios_sql_query_duration_seconds",
            "Duração de queries SQL por entidade",
            ["entity", "db_name"],
            buckets=buckets,
            registry=registry,
        )
    if ecfg.get("sql_rows_returned_total", {}).get("enabled", True):
        rows = Counter(
            "sirios_sql_rows_returned_total",
            "Linhas retornadas por entidade",
            ["entity"],
            registry=registry,
        )
    if ecfg.get("sql_errors_total", {}).get("enabled", True):
        errors = Counter(
            "sirios_sql_errors_total",
            "Erros SQL por entidade e código",
            ["entity", "error_code"],
            registry=registry,
        )
    return {"qhist": qhist, "rows": rows, "errors": errors}
