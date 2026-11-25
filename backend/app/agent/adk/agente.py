import asyncio
import time
from collections.abc import AsyncIterator
from typing import Any

from google.adk.agents import LlmAgent, RunConfig
from google.adk.agents.run_config import StreamingMode
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import errors, types

from app.agent.adk.herramientas import crear_herramientas
from app.agent.errores import LimiteDeConsultas, ProveedorNoDisponible
from app.agent.prompt import cargar_prompt
from app.core.config import Settings
from app.rag.indice import IndicePoliticas
from app.schemas.chat import ChatRespuesta, EventoAgente, FragmentoTexto, Fuente, PasoTraza
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
                thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW),
            ),
        )
        self._sesiones = InMemorySessionService()
        self._runner = Runner(app_name=NOMBRE_APP, agent=agente, session_service=self._sesiones)
        self._timeout = settings.timeout_agente_seg

    async def responder(self, *, sesion_id: str, empleado_id: str, mensaje: str) -> ChatRespuesta:
        """
        Usa el mismo flujo que el stream y se queda solo con la respuesta completa
        """
        async for evento in self.responder_stream(
            sesion_id=sesion_id, empleado_id=empleado_id, mensaje=mensaje
        ):
            if isinstance(evento, ChatRespuesta):
                return evento
        raise ProveedorNoDisponible("El agente terminó sin respuesta")

    async def responder_stream(
        self, *, sesion_id: str, empleado_id: str, mensaje: str
    ) -> AsyncIterator[EventoAgente]:
        inicio = time.perf_counter()
        await self._asegurar_sesion(sesion_id, empleado_id)
        contenido = types.Content(role="user", parts=[types.Part(text=mensaje)])
        eventos = self._runner.run_async(
            user_id=empleado_id,
            session_id=sesion_id,
            new_message=contenido,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
        # El timeout es para todo el turno, se revisa en cada evento y nunca envuelve un yield
        limite = asyncio.get_running_loop().time() + self._timeout
        texto = ""
        texto_parcial = ""
        traza: list[PasoTraza] = []
        fuentes: dict[tuple[str, str], Fuente] = {}
        folio: str | None = None
        try:
            while True:
                async with asyncio.timeout_at(limite):
                    evento = await anext(eventos, None)
                if evento is None:
                    break
                if evento.partial:
                    # Un fragmento solo sirve para mostrarlo, al final llega el evento completo
                    if trozo := _texto_de(evento):
                        texto_parcial += trozo
                        yield FragmentoTexto(texto=trozo)
                    continue
                for llamada in evento.get_function_calls():
                    paso = PasoTraza(
                        herramienta=llamada.name or "", argumentos=dict(llamada.args or {})
                    )
                    traza.append(paso)
                    yield paso
                for respuesta in evento.get_function_responses():
                    datos = respuesta.response or {}
                    _completar_paso(traza, respuesta.name, datos)
                    for a in datos.get("articulos", []):
                        fuentes[(a["documento"], a["articulo"])] = Fuente(
                            documento=a["documento"], articulo=a["articulo"], titulo=a["titulo"]
                        )
                    folio = datos.get("folio", folio)
                if evento.is_final_response():
                    texto = _texto_de(evento) or texto
        except errors.APIError as error:
            if error.code == HTTP_TOO_MANY_REQUESTS:
                raise LimiteDeConsultas(str(error)) from error
            raise ProveedorNoDisponible(str(error)) from error
        finally:
            await eventos.aclose()
        yield ChatRespuesta(
            sesion_id=sesion_id,
            respuesta=texto
            or texto_parcial
            or "No pude generar una respuesta. Intenta reformular tu pregunta.",
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


def _texto_de(evento: Event) -> str:
    """
    Junta el texto visible de un evento, sin los pensamientos del modelo
    """
    if not evento.content or not evento.content.parts:
        return ""
    return "".join(p.text for p in evento.content.parts if p.text and not p.thought)


def _completar_paso(traza: list[PasoTraza], nombre: str | None, datos: dict[str, Any]) -> None:
    """
    Pone el resumen del resultado en el último paso de esa herramienta
    """
    for paso in reversed(traza):
        if paso.herramienta == nombre and paso.resumen is None:
            paso.resumen = str(datos.get("resumen") or datos.get("mensaje") or datos.get("status"))
            return
