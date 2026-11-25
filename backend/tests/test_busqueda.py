from app.rag.busqueda import fusionar_rrf, tokenizar


def test_tokenizar_quita_acentos_y_signos() -> None:
    assert tokenizar("¿Cuántos días? Artículo 76") == ["cuantos", "dias", "articulo", "76"]


def test_rrf_premia_lo_que_aparece_arriba_en_ambas_listas() -> None:
    fusion = fusionar_rrf([["a", "b", "c"], ["c", "a", "d"]])

    assert [doc_id for doc_id, _ in fusion] == ["a", "c", "b", "d"]
