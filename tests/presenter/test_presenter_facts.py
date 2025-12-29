import pytest

from app.presenter.presenter import build_facts


def test_build_facts_tabular_contract():
    plan = {
        "chosen": {"intent": "fiis_cadastro", "entity": "fiis_cadastro", "score": 0.91}
    }
    orchestrator_results = {
        "cadastro_fii": [
            {
                "ticker": "ABCD11",
                "fund": "FII ABC",
                "display_name": "Fundo ABC",
                "sector": "Logístico",
            }
        ]
    }
    meta = {
        "result_key": "cadastro_fii",
        "planner_score": 0.91,
        "requested_metrics": ["ticker", "fund"],
    }
    identifiers = {"ticker": "ABCD11"}
    aggregates = {"limit": 1}

    facts, result_key, rows, mismatch_reason = build_facts(
        question="qual o cadastro do abcd11?",
        plan=plan,
        orchestrator_results=orchestrator_results,
        meta=meta,
        identifiers=identifiers,
        aggregates=aggregates,
    )

    assert facts.intent == plan["chosen"]["intent"]
    assert facts.entity == plan["chosen"]["entity"]
    assert facts.result_key == "cadastro_fii"
    assert result_key == facts.result_key
    assert facts.rows == orchestrator_results["cadastro_fii"]
    assert rows == facts.rows
    assert facts.primary == orchestrator_results["cadastro_fii"][0]
    assert facts.score == meta["planner_score"]
    assert facts.aggregates == aggregates
    assert facts.identifiers == identifiers
    assert facts.requested_metrics == meta["requested_metrics"]
    assert mismatch_reason is None  # build_facts agora retorna o motivo de ajuste da result_key


def test_build_facts_risk_contract():
    plan = {
        "chosen": {
            "intent": "fiis_financials_risk",
            "entity": "fiis_financials_risk",
            "score": 0.73,
        }
    }
    orchestrator_results = {
        "financials_risk": [
            {
                "ticker": "XPTO11",
                "volatility_ratio": 0.2,
                "sharpe_ratio": 0.35,
                "beta_index": 1.1,
                "max_drawdown": 0.15,
            }
        ]
    }
    meta = {
        "result_key": "financials_risk",
        "planner_score": 0.73,
        "requested_metrics": ["sharpe_ratio", "beta_index"],
    }
    identifiers = {"ticker": "XPTO11"}
    aggregates = {"limit": 5, "order": "desc"}

    facts, result_key, rows, mismatch_reason = build_facts(
        question="qual o sharpe e beta do xpto11?",
        plan=plan,
        orchestrator_results=orchestrator_results,
        meta=meta,
        identifiers=identifiers,
        aggregates=aggregates,
    )

    assert facts.intent == "fiis_financials_risk"
    assert facts.entity == "fiis_financials_risk"
    assert facts.result_key == "financials_risk"
    assert facts.rows == orchestrator_results["financials_risk"]
    assert facts.primary == orchestrator_results["financials_risk"][0]
    assert facts.score == meta["planner_score"]
    assert facts.identifiers == identifiers
    assert facts.requested_metrics == meta["requested_metrics"]
    assert result_key == "financials_risk"
    assert rows == orchestrator_results["financials_risk"]
    assert "sharpe_ratio" in facts.primary
    assert "beta_index" in facts.primary
    assert mismatch_reason is None  # build_facts agora retorna o motivo de ajuste da result_key
