from app.planner.ontology_loader import load_ontology
from app.planner.planner import resolve_bucket
from app.planner.ticker_index import extract_tickers_from_text


ONTOLOGY_PATH = "data/ontology/entity.yaml"


def test_extracts_multiple_tickers_preserving_order():
    question = "compare HGLG11 e MXRF11 com HGRE11"

    tickers = extract_tickers_from_text(question)

    assert tickers == ["HGLG11", "MXRF11", "HGRE11"]


def test_macro_token_does_not_block_ticker_detection():
    question = "IPCA do mês e preço do HGLG11"

    tickers = extract_tickers_from_text(question)

    assert tickers == ["HGLG11"]


def test_bucket_rule_enabled_for_ticker_placeholder():
    ontology = load_ontology(ONTOLOGY_PATH)

    bucket = resolve_bucket("preço do AAAA11", {}, ontology)

    assert bucket == "A"
