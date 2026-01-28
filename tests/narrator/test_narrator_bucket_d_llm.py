# tests/narrator/test_narrator_bucket_d_llm.py
from app.narrator.narrator import Narrator


class DummyClient:
    def __init__(self):
        self.calls = []

    def generate(self, prompt, model=None, stream=False, **kwargs):
        self.calls.append({"prompt": prompt, "model": model, "kwargs": kwargs})
        return "Narrativa macro gerada"


def test_valid_bucket_triggers_llm(monkeypatch):
    narrator = Narrator()
    narrator.client = DummyClient()

    counters = []
    histograms = []

    monkeypatch.setattr(
        "app.narrator.narrator.counter",
        lambda name, **labels: counters.append((name, labels)),
    )
    monkeypatch.setattr(
        "app.narrator.narrator.histogram",
        lambda name, value, **labels: histograms.append((name, value, labels)),
    )

    results = {
        "rows": [
            {"indicador": "IPCA", "valor": 3.1},
            {"indicador": "SELIC", "valor": 10.5},
        ]
    }
    meta = {"window": "12m"}

    enriched_meta = narrator.render_global_post_sql(
        question="Como estão os indicadores macro?",
        entity="consolidated_macroeconomic",
        bucket="A",
        results=results,
        meta=meta,
    )

    assert enriched_meta.get("narrative") == "Narrativa macro gerada"
    assert narrator.client.calls, "LLM client should have been invoked"
    assert results["rows"][0]["indicador"] == "IPCA", "results must stay intact"

    assert any(
        name == "services_narrator_llm_requests_total" and labels.get("outcome") == "ok"
        for name, labels in counters
    )
    assert any(
        name == "services_narrator_llm_latency_seconds" for name, *_ in histograms
    )


def test_invalid_bucket_does_not_abort_flow(monkeypatch):
    narrator = Narrator()
    dummy_client = DummyClient()
    narrator.client = dummy_client
    monkeypatch.setattr("app.narrator.narrator.counter", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "app.narrator.narrator.histogram", lambda *args, **kwargs: None
    )

    enriched_meta = narrator.render_global_post_sql(
        question="Pergunta genérica",
        entity="consolidated_macroeconomic",
        bucket="Z",
        results={"rows": [{"x": 1}]},
        meta={},
    )

    assert enriched_meta.get("narrative") == "Narrativa macro gerada"
    assert dummy_client.calls
