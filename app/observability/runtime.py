# app/observability/runtime.py
import os, yaml, re, hashlib
from prometheus_client import Counter, Histogram, Gauge
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
import json, urllib.parse, urllib.request

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


# -------------------------------------------------------------------
# Cache metrics
# -------------------------------------------------------------------
def init_cache_metrics(cfg: dict, registry=None):
    """
    Métricas do cache (Redis) via YAML (services.cache.metrics).
    Gera métricas padronizadas por operação e resultado.
    """
    ccf = cfg["services"]["cache"]["metrics"]
    ops = None
    latency = None

    if ccf.get("cache_ops_total", {}).get("enabled", True):
        ops = Counter(
            "sirios_cache_ops_total",
            "Operações de cache (get/set/bust) por resultado",
            ["op", "outcome"],
            registry=registry,
        )

    if ccf.get("cache_latency_seconds", {}).get("enabled", True):
        buckets = ccf["cache_latency_seconds"]["buckets"]
        latency = Histogram(
            "sirios_cache_latency_seconds",
            "Latência de operações de cache (s)",
            ["op"],
            buckets=buckets,
            registry=registry,
        )

    return {"ops": ops, "latency": latency}


def init_planner_metrics(cfg: dict, registry=None):
    """
    Métricas do Planner/Orchestrator via YAML (services.orchestrator.metrics).
    Retorna dict com handlers já registrados no 'registry' informado.
    """
    ocfg = cfg["services"]["orchestrator"]["metrics"]
    decisions = duration = None
    explain_enabled = explain_latency = explain_nodes = None
    explain_weight_sum = None
    intent_score_hist = None
    entity_score_hist = None
    explain_depth = None
    routed_total = None
    top1_match_total = None
    confusion_total = None
    top2_gap_hist = None
    quality_last_gap = None
    blocked_by_threshold = None
    projection_total = None

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
    # --- M6.3: métricas Explain (todas opcionais conforme YAML) ---
    if ocfg.get("planner_explain_enabled_total", {}).get("enabled", True):
        explain_enabled = Counter(
            "sirios_planner_explain_enabled_total",
            "Número de requisições com explain habilitado",
            [],
            registry=registry,
        )
    if ocfg.get("planner_explain_latency_seconds", {}).get("enabled", True):
        buckets = ocfg.get("planner_explain_latency_seconds", {}).get("buckets", [0.01,0.05,0.1,0.25,0.5,1,2])
        explain_latency = Histogram(
            "sirios_planner_explain_latency_seconds",
            "Latência do cálculo de explain do planner",
            [],
            buckets=buckets,
            registry=registry,
        )
    if ocfg.get("planner_explain_nodes_total", {}).get("enabled", True):
        explain_nodes = Counter(
            "sirios_planner_explain_nodes_total",
            "Nós contados no explain do planner por tipo",
            ["node_kind"],
            registry=registry,
        )
    # --- M6.4: métricas adicionais (todas opcionais via YAML) ---
    if ocfg.get("planner_explain_weight_sum_total", {}).get("enabled", True):
        explain_weight_sum = Counter(
            "sirios_planner_explain_weight_sum_total",
            "Somatório de pesos por tipo de sinal (token|phrase|anti) durante o explain",
            ["type"],
            registry=registry,
        )
    if ocfg.get("planner_intent_score", {}).get("enabled", True):
        buckets_i = ocfg.get("planner_intent_score", {}).get("buckets", [0,1,2,3,5,8,13,21])
        intent_score_hist = Histogram(
            "sirios_planner_intent_score",
            "Distribuição de score por intent vencedora",
            ["intent"],
            buckets=buckets_i,
            registry=registry,
        )
    if ocfg.get("planner_entity_score", {}).get("enabled", True):
        buckets_e = ocfg.get("planner_entity_score", {}).get("buckets", [0,1,2,3,5,8,13,21])
        entity_score_hist = Histogram(
            "sirios_planner_entity_score",
            "Distribuição de score por entidade vencedora",
            ["entity"],
            buckets=buckets_e,
            registry=registry,
        )
    if ocfg.get("planner_explain_decision_depth", {}).get("enabled", True):
        explain_depth = Gauge(
            "sirios_planner_explain_decision_depth",
            "Profundidade (nós) do decision_path do explain mais recente",
            [],
            registry=registry,
        )

    # ---- M6.5: métricas de qualidade/“confusion” ----
    if ocfg.get("planner_routed_total", {}).get("enabled", True):
        routed_total = Counter(
            "sirios_planner_routed_total",
            "Total de requisições roteadas ou não roteadas",
            ["outcome"],  # ok|unroutable
            registry=registry,
        )
    if ocfg.get("planner_top1_match_total", {}).get("enabled", True):
        top1_match_total = Counter(
            "sirios_planner_top1_match_total",
            "Acertos/erros do top1 vs esperado (intent)",
            ["result"],  # hit|miss
            registry=registry,
        )
    if ocfg.get("planner_confusion_total", {}).get("enabled", True):
        confusion_total = Counter(
            "sirios_planner_confusion_total",
            "Matriz de confusão (intent esperada x prevista)",
            ["expected_intent", "predicted_intent"],
            registry=registry,
        )
    if ocfg.get("planner_top2_gap_histogram", {}).get("enabled", True):
        buckets_g = ocfg.get("planner_top2_gap_histogram", {}).get("buckets", [0.0, 0.5, 1, 2, 3, 5])
        top2_gap_hist = Histogram(
            "sirios_planner_top2_gap_histogram",
            "Distribuição do gap entre top1 e top2 intents",
            [],
            buckets=buckets_g,
            registry=registry,
        )
    if ocfg.get("planner_quality_last_gap", {}).get("enabled", True):
        quality_last_gap = Gauge(
            "sirios_planner_quality_last_gap",
            "Último gap top1-top2 observado",
            [],
            registry=registry,
        )
    # ---- M6.6: quality gates (bloqueios) ----
    if ocfg.get("planner_blocked_by_threshold_total", {}).get("enabled", True):
        blocked_by_threshold = Counter(
            "sirios_planner_blocked_by_threshold_total",
            "Bloqueios por threshold (score/gap) no planner",
            ["reason", "intent", "entity"],  # reason: low_score|low_gap
            registry=registry,
        )
    # ---- M6.7: projection gate outcome ----
    if ocfg.get("planner_projection_total", {}).get("enabled", True):
        projection_total = Counter(
            "sirios_planner_projection_total",
            "Resultados do projection gate (colunas exigidas presentes)",
            ["outcome", "entity"],  # ok|fail
            registry=registry,
        )

    return {
        "decisions": decisions,
        "duration": duration,
        "explain_enabled": explain_enabled,
        "explain_latency": explain_latency,
        "explain_nodes": explain_nodes,
        "explain_weight_sum": explain_weight_sum,
        "intent_score_hist": intent_score_hist,
        "entity_score_hist": entity_score_hist,
        "explain_depth": explain_depth,
        "routed_total": routed_total,
        "top1_match_total": top1_match_total,
        "confusion_total": confusion_total,
        "top2_gap_histogram": top2_gap_hist,
        "quality_last_gap": quality_last_gap,
        "blocked_by_threshold": blocked_by_threshold,
        "projection_total": projection_total,
    }

# -------------------------------------------------------------------
# Prometheus instant query helper (sem dependência externa)
# -------------------------------------------------------------------
def prom_query_instant(expr: str):
    """
    Executa uma PromQL instantânea em PROMETHEUS_URL (env) e retorna:
      - float se a resposta for um vetor único com 1 amostra
      - dict bruto (JSON) caso contrário
    """
    base = os.getenv("PROMETHEUS_URL", "http://prometheus:9090").rstrip("/")
    url = f"{base}/api/v1/query?query={urllib.parse.quote_plus(expr)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("status") != "success":
        return data
    result = (data.get("data") or {}).get("result") or []
    if len(result) == 1 and "value" in result[0] and len(result[0]["value"]) == 2:
        # ["ts", "val"]
        try:
            return float(result[0]["value"][1])
        except Exception:
            return data
    return data

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
