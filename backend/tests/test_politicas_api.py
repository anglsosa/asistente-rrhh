from fastapi import status
from fastapi.testclient import TestClient

from app.api.deps import get_indice
from app.main import create_app
from app.schemas.politicas import ResultadoBusqueda


class IndiceFalso:
    """Imita a IndicePoliticas: responde siempre lo mismo y recuerda qué le pidieron."""

    def __init__(self) -> None:
        self.ultima_pregunta: str | None = None

    def buscar(self, pregunta: str, k: int = 3) -> list[ResultadoBusqueda]:
        self.ultima_pregunta = pregunta
        resultado = ResultadoBusqueda(
            id="reglamento-interior#art-5",
            documento="reglamento-interior",
            articulo="Artículo 5",
            titulo="Vacaciones",
            texto="Artículo 5. Vacaciones\n12 días al cumplir el primer año.",
            puntaje=0.0328,
        )
        return [resultado][:k]


def crear_cliente(indice: IndiceFalso) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_indice] = lambda: indice
    return TestClient(app)


def test_buscar_regresa_articulos_citables() -> None:
    indice = IndiceFalso()
    client = crear_cliente(indice)

    response = client.get("/api/v1/politicas/buscar", params={"q": "vacaciones"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["articulo"] == "Artículo 5"
    assert indice.ultima_pregunta == "vacaciones"


def test_pregunta_demasiado_corta_da_422() -> None:
    client = crear_cliente(IndiceFalso())

    response = client.get("/api/v1/politicas/buscar", params={"q": "a"})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_k_fuera_de_rango_da_422() -> None:
    client = crear_cliente(IndiceFalso())

    response = client.get("/api/v1/politicas/buscar", params={"q": "vacaciones", "k": 50})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
