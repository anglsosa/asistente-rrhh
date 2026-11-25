import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class Ticket(BaseModel):
    """
    Una consulta escalada a RRHH. empleado_id es ficticio: nunca datos personales
    """

    folio: str
    empleado_id: str = Field(pattern=r"^EMP-\d{4}$")
    tema: str = Field(min_length=3, max_length=120)
    resumen: str = Field(min_length=10, max_length=2000)
    prioridad: Literal["baja", "media", "alta"]
    creado_en: datetime


class RegistroTickets:
    """
    API simulada de RRHH: guarda cada ticket como una línea JSON en un archivo
    """

    def __init__(self, ruta: Path) -> None:
        self._ruta = ruta
        self._candado = asyncio.Lock()

    async def crear(self, empleado_id: str, tema: str, resumen: str, prioridad: str) -> Ticket:
        async with self._candado:
            return await asyncio.to_thread(self._crear_sync, empleado_id, tema, resumen, prioridad)

    def _crear_sync(self, empleado_id: str, tema: str, resumen: str, prioridad: str) -> Ticket:
        self._ruta.parent.mkdir(parents=True, exist_ok=True)
        existentes = (
            self._ruta.read_text(encoding="utf-8").splitlines() if self._ruta.exists() else []
        )
        ahora = datetime.now(UTC)
        ticket = Ticket(
            folio=f"RRHH-{ahora:%Y}-{len(existentes) + 1:05d}",
            empleado_id=empleado_id,
            tema=tema,
            resumen=resumen,
            prioridad=prioridad,
            creado_en=ahora,
        )
        with self._ruta.open("a", encoding="utf-8") as archivo:
            archivo.write(ticket.model_dump_json() + "\n")
        return ticket
