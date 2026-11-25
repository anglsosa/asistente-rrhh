from collections.abc import AsyncIterator
from typing import Protocol

from app.schemas.chat import ChatRespuesta, EventoAgente


class Agente(Protocol):
    """
    Lo único que la API sabe del agente: cualquier framework que cumpla esto sirve
    """

    async def responder(self, *, sesion_id: str, empleado_id: str, mensaje: str) -> ChatRespuesta:
        """
        Procesa un mensaje dentro de una sesión y regresa la respuesta con su traza
        """
        ...

    def responder_stream(
        self, *, sesion_id: str, empleado_id: str, mensaje: str
    ) -> AsyncIterator[EventoAgente]:
        """
        Igual que responder pero va regresando el texto y los pasos conforme pasan,
        el último evento siempre es la ChatRespuesta completa
        """
        ...
