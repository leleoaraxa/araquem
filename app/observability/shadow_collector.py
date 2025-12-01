# app/observability/shadow_collector.py


def collect_narrator_shadow(payload: NarratorShadowPayload) -> None:  # type: ignore
    """
    Recebe tudo que aconteceu no /ask para essa requisição
    (request, routing, entity, facts, rag, narrator, presenter),
    aplica narrator_shadow.yaml e, se apropriado, grava o registro de shadow
    + atualiza métricas.
    """
