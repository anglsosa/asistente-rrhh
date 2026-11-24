from typing import Literal 
from pydantic import BaseModel 


class HealthResponse(BaseModel): 
	"""
	Respuesta del chequeo de salud
	"""

	status: Literal["ok"]
	version: str
	environment: str