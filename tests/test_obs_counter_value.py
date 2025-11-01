# tests/test_obs_counter_value.py
from app.observability import instrumentation as obs
from app.observability.runtime import _METRIC_SCHEMAS


def test_counter_value_not_label(monkeypatch):
    captured = {}

    class Dummy(obs._Backend):
        def inc(self, name, labels, value=1.0):
            captured["name"] = name
            captured["labels"] = labels
            captured["value"] = value

        def observe(self, *a, **k): ...
        def start_span(self, *a, **k):
            return {}

        def end_span(self, *a, **k): ...
        def set_span_attr(self, *a, **k): ...

    obs.set_backend(Dummy())
    obs.counter("sirios_sql_rows_returned_total", entity="fiis_cadastro", _value=7)
    assert captured["name"] == "sirios_sql_rows_returned_total"
    assert captured["labels"] == {"entity": "fiis_cadastro"}
    assert captured["value"] == 7.0
