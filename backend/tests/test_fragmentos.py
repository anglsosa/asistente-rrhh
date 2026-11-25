from app.rag.fragmentos import partir_por_articulo

REGLAMENTO = """# Reglamento

### Artículo 1. Objeto
Aplica a todo el personal.

### Artículo 2. Horario
De 9:00 a 18:00 horas.
"""


def test_parte_un_fragmento_por_articulo() -> None:
    fragmentos = partir_por_articulo(REGLAMENTO, "reglamento")

    assert [f.articulo for f in fragmentos] == ["Artículo 1", "Artículo 2"]
    assert fragmentos[1].id == "reglamento#art-2"
    assert "9:00 a 18:00" in fragmentos[1].texto
    assert "Aplica a todo" not in fragmentos[1].texto


def test_documento_sin_articulos_es_un_solo_fragmento() -> None:
    fragmentos = partir_por_articulo("# Comunicado\nTexto libre.", "comunicado")

    assert len(fragmentos) == 1
    assert fragmentos[0].articulo == "Documento completo"
    assert fragmentos[0].id == "comunicado#completo"


def test_reconoce_articulos_con_sufijo() -> None:
    texto = "### Artículo 170 Bis. Licencia\nTexto.\n\n### Artículo 330-E. Teletrabajo\nTexto."

    fragmentos = partir_por_articulo(texto, "lft")

    assert [f.id for f in fragmentos] == ["lft#art-170-bis", "lft#art-330-e"]


def test_el_encabezado_de_capitulo_no_se_pega_al_articulo_anterior() -> None:
    texto = (
        "### Artículo 1. Uno\nTexto uno.\n\n"
        "## Capítulo II · Otro\n\n"
        "### Artículo 2. Dos\nTexto dos."
    )

    fragmentos = partir_por_articulo(texto, "doc")

    assert "Capítulo II" not in fragmentos[0].texto
    assert fragmentos[0].texto.endswith("Texto uno.")
