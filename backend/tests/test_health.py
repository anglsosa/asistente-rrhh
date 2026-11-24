from fastapi import status
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import create_app


def test_health_responde_ok() -> None:
    client = TestClient(create_app())
    response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "ok"


def test_health_usa_la_configuracion_inyectada() -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(environment="pruebas")
    client = TestClient(app)
    response = client.get("/health")
    assert response.json()["environment"] == "pruebas"
