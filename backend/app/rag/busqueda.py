def fusionar_rrf(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """
    RRF = Reciprocal Rank Fusion: une varias listas ordenadas en una sin normalizar puntajes

    Cada documento suma 1 / (k + posición) por cada lista en la que aparece
    """

    puntajes: dict[str, float] = {}

    for ranking in rankings:
        for posicion, doc_id in enumerate(ranking, start=1):
            puntajes[doc_id] = puntajes.get(doc_id, 0.0) + 1 / (k + posicion)

    return sorted(puntajes.items(), key=lambda par: par[1], reverse=True)
