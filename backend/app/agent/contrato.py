from typing import Protocol

from app.schemas.chat import ChatRespuesta


class Agente(Protocol):
    """
    Lo único que la API sabe del agente: cualquier framework que cumpla esto sirve
    """

    async def responder(self, *, sesion_id: str, empleado_id: str, mensaje: str) -> ChatRespuesta:
        """
        Procesa un mensaje dentro de una sesión y regresa la respuesta con su traza
        """
        ...
