from typing import Any

from pydantic import BaseModel, Field


class ChatPeticion(BaseModel):
    """
    Un mensaje del empleado al asistente
    """

    mensaje: str = Field(min_length=1, max_length=2000)
    empleado_id: str = Field(pattern=r"^EMP-\d{4}$", examples=["EMP-0042"])
    sesion_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")


class Fuente(BaseModel):
    documento: str
    articulo: str
    titulo: str


class PasoTraza(BaseModel):
    herramienta: str
    argumentos: dict[str, Any]
    resumen: str | None = None


class ChatRespuesta(BaseModel):
    """
    Respuesta con todo lo necesario para auditarla
    """

    sesion_id: str
    respuesta: str
    fuentes: list[Fuente]
    traza: list[PasoTraza]
    folio_escalamiento: str | None = None
    duracion_ms: int
