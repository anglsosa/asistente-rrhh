import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_indice
from app.rag.indice import IndicePoliticas
from app.schemas.politicas import ResultadoBusqueda

router = APIRouter(prefix="/api/v1/politicas", tags=["políticas"])


@router.get(
    "/buscar",
    response_model=list[ResultadoBusqueda],
    status_code=status.HTTP_200_OK,
    summary="Busca los artículos más relevantes para una pregunta",
)
async def buscar(
    indice: Annotated[IndicePoliticas, Depends(get_indice)],
    q: Annotated[str, Query(min_length=3, max_length=300, description="Pregunta del empleado")],
    k: Annotated[int, Query(ge=1, le=10, description="Cuántos artículos regresar")] = 3,
) -> list[ResultadoBusqueda]:
    return await asyncio.to_thread(indice.buscar, q, k)
