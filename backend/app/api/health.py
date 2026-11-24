from app.core.config import Settings, get_settings
from typing import Annotated
from app.schemas.health import HealthResponse
from fastapi import APIRouter, Depends, status 

router = APIRouter(
	tags=["salud"], 
	)


@router.get(
	"/health", 
	response_model=HealthResponse, 
	status_code=status.HTTP_200_OK, 
	summary="Verifica que la API esté viva"
)
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse: 
	return HealthResponse(status="ok", version=settings.version, environment=settings.environment)