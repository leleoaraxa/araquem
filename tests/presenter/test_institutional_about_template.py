from app.presenter.presenter import present


def test_institutional_about_template_includes_concept_item_name():
    plan = {
        "chosen": {
            "intent": "institutional_about",
            "entity": "institutional_about",
            "score": 0.95,
        }
    }
    orchestrator_results = {"institutional_about": [{"content": "ok"}]}
    meta = {
        "result_key": "institutional_about",
        "planner_score": 0.95,
    }

    result = present(
        question="o que a sirios faz",
        plan=plan,
        orchestrator_results=orchestrator_results,
        meta=meta,
        identifiers={},
        aggregates={},
        narrator=None,
    )

    assert result.template_used is True
    assert "SIRIOS como plataforma" in result.rendered_template
    assert "SIRIOS como plataforma" in result.answer
