import asyncio
import time
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import errors, types

from app.agent.adk.herramientas import crear_herramientas
from app.agent.errores import LimiteDeConsultas, ProveedorNoDisponible
from app.agent.prompt import cargar_prompt
from app.core.config import Settings
from app.rag.indice import IndicePoliticas
from app.schemas.chat import ChatRespuesta, Fuente, PasoTraza
from app.tools.tickets import RegistroTickets

NOMBRE_APP = "asistente-rrhh"
HTTP_TOO_MANY_REQUESTS = 429


class AgenteADK:
    """
    Implementación del contrato Agente con Google ADK y Gemini
    """

    def __init__(self, settings: Settings, indice: IndicePoliticas, registro: RegistroTickets):
        agente = LlmAgent(
            name="asistente_politicas",
            model=settings.gemini_modelo,
            description="Responde dudas de políticas de RRHH citando el reglamento y escala a RRHH",
            instruction=cargar_prompt(settings.prompt_version),
            tools=crear_herramientas(indice, registro),
            generate_content_config=types.GenerateContentConfig(
                temperature=settings.gemini_temperatura,
                max_output_tokens=settings.gemini_max_tokens,
            ),
        )
        self._sesiones = InMemorySessionService()
        self._runner = Runner(app_name=NOMBRE_APP, agent=agente, session_service=self._sesiones)
        self._timeout = settings.timeout_agente_seg

    async def responder(self, *, sesion_id: str, empleado_id: str, mensaje: str) -> ChatRespuesta:
        inicio = time.perf_counter()
        await self._asegurar_sesion(sesion_id, empleado_id)
        contenido = types.Content(role="user", parts=[types.Part(text=mensaje)])
        texto = ""
        traza: list[PasoTraza] = []
        fuentes: dict[tuple[str, str], Fuente] = {}
        folio: str | None = None
        try:
            async with asyncio.timeout(self._timeout):
                async for evento in self._runner.run_async(
                    user_id=empleado_id, session_id=sesion_id, new_message=contenido
                ):
                    for llamada in evento.get_function_calls():
                        args = dict(llamada.args or {})
                        traza.append(PasoTraza(herramienta=llamada.name or "", argumentos=args))
                    for respuesta in evento.get_function_responses():
                        datos = respuesta.response or {}
                        _completar_paso(traza, respuesta.name, datos)
                        for a in datos.get("articulos", []):
                            fuentes[(a["documento"], a["articulo"])] = Fuente(
                                documento=a["documento"], articulo=a["articulo"], titulo=a["titulo"]
                            )
                        folio = datos.get("folio", folio)
                    if evento.is_final_response() and evento.content and evento.content.parts:
                        texto = "".join(p.text for p in evento.content.parts if p.text)
        except errors.APIError as error:
            if error.code == HTTP_TOO_MANY_REQUESTS:
                raise LimiteDeConsultas(str(error)) from error
            raise ProveedorNoDisponible(str(error)) from error
        return ChatRespuesta(
            sesion_id=sesion_id,
            respuesta=texto or "No pude generar una respuesta. Intenta reformular tu pregunta.",
            fuentes=list(fuentes.values()),
            traza=traza,
            folio_escalamiento=folio,
            duracion_ms=int((time.perf_counter() - inicio) * 1000),
        )

    async def _asegurar_sesion(self, sesion_id: str, empleado_id: str) -> None:
        """
        Crea la sesión la primera vez y guarda el empleado en su estado
        """
        sesion = await self._sesiones.get_session(
            app_name=NOMBRE_APP, user_id=empleado_id, session_id=sesion_id
        )
        if sesion is None:
            await self._sesiones.create_session(
                app_name=NOMBRE_APP,
                user_id=empleado_id,
                session_id=sesion_id,
                state={"empleado_id": empleado_id},
            )


def _completar_paso(traza: list[PasoTraza], nombre: str | None, datos: dict[str, Any]) -> None:
    """
    Pone el resumen del resultado en el último paso de esa herramienta
    """
    for paso in reversed(traza):
        if paso.herramienta == nombre and paso.resumen is None:
            paso.resumen = str(datos.get("resumen") or datos.get("mensaje") or datos.get("status"))
            return
