import logging
from collections.abc import AsyncIterator
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.sse import EventSourceResponse, ServerSentEvent

from app.agent.contrato import Agente
from app.agent.errores import LimiteDeConsultas, ProveedorNoDisponible
from app.schemas.chat import ChatPeticion, ChatRespuesta, FragmentoTexto, PasoTraza

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# Un solo lugar para traducir los errores del agente a HTTP, lo usan las dos rutas
ERRORES: dict[type[Exception], tuple[int, str]] = {
    TimeoutError: (status.HTTP_504_GATEWAY_TIMEOUT, "El asistente tardó demasiado."),
    LimiteDeConsultas: (
        status.HTTP_429_TOO_MANY_REQUESTS,
        "Límite de consultas del modelo. Espera un minuto.",
    ),
    ProveedorNoDisponible: (status.HTTP_502_BAD_GATEWAY, "El modelo no respondió bien."),
}
NOMBRE_EVENTO = {FragmentoTexto: "texto", PasoTraza: "paso", ChatRespuesta: "fin"}


def get_agente(request: Request) -> Agente:
    """
    El agente se construye una vez al arrancar y vive en app.state
    """
    return request.app.state.agente


def _traducir(error: Exception) -> tuple[int, str]:
    if isinstance(error, ProveedorNoDisponible):
        logger.error("Falla del proveedor del modelo: %s", error)
    return ERRORES[type(error)]


@router.post(
    "",
    response_model=ChatRespuesta,
    status_code=status.HTTP_200_OK,
    summary="Envía un mensaje al asistente de políticas de RRHH",
    responses={
        status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Límite de consultas del modelo"},
        status.HTTP_502_BAD_GATEWAY: {"description": "El proveedor del modelo falló"},
        status.HTTP_504_GATEWAY_TIMEOUT: {"description": "El asistente tardó demasiado"},
    },
)
async def chat(
    peticion: ChatPeticion, agente: Annotated[Agente, Depends(get_agente)]
) -> ChatRespuesta:
    sesion_id = peticion.sesion_id or uuid4().hex
    try:
        return await agente.responder(
            sesion_id=sesion_id, empleado_id=peticion.empleado_id, mensaje=peticion.mensaje
        )
    except tuple(ERRORES) as error:
        codigo, detalle = _traducir(error)
        raise HTTPException(codigo, detalle) from error


@router.post(
    "/stream",
    response_class=EventSourceResponse,
    summary="Envía un mensaje y recibe la respuesta en partes con SSE",
)
async def chat_stream(
    peticion: ChatPeticion, agente: Annotated[Agente, Depends(get_agente)]
) -> AsyncIterator[ServerSentEvent]:
    """
    Eventos: texto (pedazo de respuesta), paso (herramienta usada), fin (ChatRespuesta completa)
    y error, que va como evento porque el status 200 ya se mandó cuando empieza el stream
    """
    sesion_id = peticion.sesion_id or uuid4().hex
    try:
        async for evento in agente.responder_stream(
            sesion_id=sesion_id, empleado_id=peticion.empleado_id, mensaje=peticion.mensaje
        ):
            yield ServerSentEvent(event=NOMBRE_EVENTO[type(evento)], data=evento)
    except tuple(ERRORES) as error:
        codigo, detalle = _traducir(error)
        yield ServerSentEvent(event="error", data={"status": codigo, "detail": detalle})
