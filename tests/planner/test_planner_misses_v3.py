import pytest
from types import SimpleNamespace

from app.planner.planner import Planner
from app.planner.ticker_index import extract_tickers_from_text


ONTOLOGY_PATH = "data/ontology/entity.yaml"


def _route_question(planner: Planner, question: str) -> SimpleNamespace:
    plan = planner.explain(question)
    chosen = plan.get("chosen") or {}
    return SimpleNamespace(
        entity=chosen.get("entity"),
        intent=chosen.get("intent"),
        plan=plan,
    )


@pytest.fixture(scope="module")
def planner():
    base = Planner(ONTOLOGY_PATH)

    def route_question(question: str) -> SimpleNamespace:
        return _route_question(base, question)

    base.route_question = route_question  # type: ignore[attr-defined]
    return base


@pytest.mark.parametrize(
    "question,expected_entity",
    [
        ("dy historico do hglg11", "fiis_yield_history"),
        ("ultimo dividendo do hglg11", "fiis_dividendos"),
        ("dy acumulado do hglg11", "fiis_dividendos"),
        ("dy atual do mxrf11", "fiis_dividendos"),
    ],
)
def test_fiis_yield_history_vs_dividendos(planner: Planner, question: str, expected_entity: str):
    result = planner.route_question(question)

    assert result.entity == expected_entity


@pytest.mark.parametrize(
    "question,expected_entity",
    [
        ("preco do hglg11", "fiis_precos"),
        ("cotacao hoje do mxrf11", "fiis_precos"),
        ("setor do hglg11", "fiis_financials_snapshot"),
        ("vacancia do vino11", "fiis_financials_snapshot"),
    ],
)
def test_fiis_precos_vs_snapshot(planner: Planner, question: str, expected_entity: str):
    result = planner.route_question(question)

    assert result.entity == expected_entity


@pytest.mark.parametrize(
    "question,expected_entity",
    [
        ("processos do hglg11", "fiis_processos"),
        ("noticias do hglg11", "fiis_noticias"),
        ("acao judicial do mxrf11", "fiis_processos"),
        ("comentarios recentes sobre o hgre11", "fiis_noticias"),
    ],
)
def test_processos_vs_noticias(planner: Planner, question: str, expected_entity: str):
    result = planner.route_question(question)

    assert result.entity == expected_entity


@pytest.mark.parametrize(
    "question,expected_entity",
    [
        ("como ipca alto afeta fiis", "macro_consolidada"),
        ("taxa selic e fiis", "macro_consolidada"),
        ("volatilidade do hglg11", "fiis_financials_risk"),
        ("sharpe do hglg11", "fiis_financials_risk"),
    ],
)
def test_macro_consolidada_vs_risco(planner: Planner, question: str, expected_entity: str):
    result = planner.route_question(question)

    assert result.entity == expected_entity


@pytest.mark.parametrize(
    "question,expected_entity",
    [
        ("overview do hglg11", "fii_overview"),
        ("patrimonio liquido do mxrf11", "fiis_financials_snapshot"),
        ("maiores fiis por preco", "fiis_rankings"),
        ("ranking de fiis do ifix", "fiis_rankings"),
    ],
)
def test_overview_snapshot_rankings(planner: Planner, question: str, expected_entity: str):
    result = planner.route_question(question)

    assert result.entity == expected_entity


def test_multi_ticker_compare_keeps_both(planner: Planner):
    question = "compare hglg11 e mxrf11"

    tickers = extract_tickers_from_text(question)
    result = planner.route_question(question)

    assert tickers == ["HGLG11", "MXRF11"]
    assert result.entity is not None


def test_multi_ticker_dividendos(planner: Planner):
    result = planner.route_question("dy medio de hglg11, mxrf11 e kncr11")

    assert result.entity == "fiis_dividendos"


@pytest.mark.parametrize(
    "question,expected_entity",
    [
        ("cnpj do hglg11", "fii_overview"),
        ("noticia sobre vacancia do hglg11", "fiis_noticias"),
        ("processo sobre rendimento do hglg11", "fiis_processos"),
    ],
)
def test_anti_colisao_global(planner: Planner, question: str, expected_entity: str):
    result = planner.route_question(question)

    assert result.entity == expected_entity
