import logging
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.agent.contrato import Agente
from app.agent.errores import LimiteDeConsultas, ProveedorNoDisponible
from app.schemas.chat import ChatPeticion, ChatRespuesta

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


def get_agente(request: Request) -> Agente:
    """
    El agente se construye una vez al arrancar y vive en app.state
    """
    return request.app.state.agente


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
    except TimeoutError as error:
        raise HTTPException(
            status.HTTP_504_GATEWAY_TIMEOUT, "El asistente tardó demasiado."
        ) from error
    except LimiteDeConsultas as error:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Límite de consultas del modelo. Espera un minuto."
        ) from error
    except ProveedorNoDisponible as error:
        logger.error("Falla del proveedor del modelo: %s", error)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "El modelo no respondió bien.") from error
