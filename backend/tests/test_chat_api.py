from fastapi import status
from fastapi.testclient import TestClient

from app.agent.errores import LimiteDeConsultas
from app.agent.prompt import cargar_prompt
from app.api.chat import get_agente
from app.main import create_app
from app.schemas.chat import ChatRespuesta, PasoTraza

MENSAJE = {"mensaje": "¿Cuántos días de vacaciones me tocan?", "empleado_id": "EMP-0042"}


class AgenteFalso:
    """Cumple el contrato Agente sin llamar a ningún modelo."""

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.sesiones: list[str] = []

    async def responder(self, *, sesion_id: str, empleado_id: str, mensaje: str) -> ChatRespuesta:
        self.sesiones.append(sesion_id)
        if self.error is not None:
            raise self.error
        paso = PasoTraza(herramienta="calcular_vacaciones", argumentos={"anios_antiguedad": 3})
        return ChatRespuesta(
            sesion_id=sesion_id, respuesta="16 días.", fuentes=[], traza=[paso], duracion_ms=5
        )


def cliente(agente: AgenteFalso) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_agente] = lambda: agente
    return TestClient(app)


def test_chat_crea_sesion_y_regresa_traza() -> None:
    response = cliente(AgenteFalso()).post("/api/v1/chat", json=MENSAJE)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["sesion_id"]) == 32
    assert response.json()["traza"][0]["herramienta"] == "calcular_vacaciones"


def test_chat_continua_la_sesion_del_cliente() -> None:
    agente = AgenteFalso()

    cliente(agente).post("/api/v1/chat", json={**MENSAJE, "sesion_id": "a" * 32})

    assert agente.sesiones == ["a" * 32]


def test_empleado_con_nombre_real_da_422() -> None:
    response = cliente(AgenteFalso()).post("/api/v1/chat", json={**MENSAJE, "empleado_id": "Juan"})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_errores_del_agente_tienen_su_codigo_http() -> None:
    assert (
        cliente(AgenteFalso(TimeoutError())).post("/api/v1/chat", json=MENSAJE).status_code
        == status.HTTP_504_GATEWAY_TIMEOUT
    )
    assert (
        cliente(AgenteFalso(LimiteDeConsultas())).post("/api/v1/chat", json=MENSAJE).status_code
        == status.HTTP_429_TOO_MANY_REQUESTS
    )


def test_el_prompt_nombra_sus_herramientas_y_no_tiene_llaves() -> None:
    prompt = cargar_prompt("v1")

    for herramienta in ("buscar_politicas", "calcular_vacaciones", "escalar_a_rrhh"):
        assert herramienta in prompt
    assert "{" not in prompt
