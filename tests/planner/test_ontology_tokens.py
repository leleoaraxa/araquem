from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_cadastro_scores_positive_for_cnpj_queries():
    """
    Consulta de cadastro típica: deve pontuar positivamente para a intenção 'cadastro'
    e escolher a entidade 'fiis_cadastro'.
    """
    r = client.get("/debug/planner", params={"q": "CNPJ do VINO11"})
    assert r.status_code == 200
    body = r.json()

    # Sanidade básica do payload
    assert "normalized" in body and isinstance(body["normalized"], str)
    assert "tokens" in body and isinstance(body["tokens"], list)
    assert "intent_scores" in body and "cadastro" in body["intent_scores"]
    assert "chosen" in body and isinstance(body["chosen"], dict)

    # Esperado: intenção escolhida 'cadastro' com score > 0
    assert body["chosen"]["intent"] == "cadastro"
    assert body["chosen"]["entity"] == "fiis_cadastro"
    assert body["chosen"]["score"] > 0.0

    # Deve conter o token 'cnpj' após normalização
    assert "cnpj" in body["tokens"]


def test_anti_tokens_apply_penalty_on_price_queries():
    """
    Consulta de preço não-cadastro: anti-tokens ('preco', 'hoje', etc.) devem penalizar a intenção 'cadastro'.
    Como só existe essa intenção definida por enquanto, ela pode continuar sendo a 'chosen',
    mas o score deve ficar reduzido (idealmente <= 0).
    """
    r = client.get("/debug/planner", params={"q": "Preço do HGLG11 hoje"})
    assert r.status_code == 200
    body = r.json()

    # Sanidade
    assert "details" in body and "cadastro" in body["details"]
    dbg = body["explain"]
    scoring = dbg.get("scoring", {})
    intents = scoring.get("intent", [])
    assert intents and intents[0]["name"] == "precos"

    signals = dbg.get("signals", {})
    weights_summary = signals.get("weights_summary") or {}
    phrase_penalty = weights_summary.get("phrase_sum")
    token_penalty = weights_summary.get("token_sum")
    assert (phrase_penalty is not None and phrase_penalty < 0) or (
        token_penalty is not None and token_penalty <= 0
    )

    # Tokens normalizados devem conter 'preco' e 'hoje' (pois strip_accents está ligado)
    assert "preco" in body["tokens"]
    assert "hoje" in body["tokens"]

    # Escolha final deve seguir a intenção de preços
    assert body["chosen"]["intent"] == "precos"
    assert body["chosen"]["entity"] == "fiis_precos"
