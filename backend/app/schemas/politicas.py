from pydantic import BaseModel, Field


class ResultadoBusqueda(BaseModel):
    """
    Un articulo encontrado, con lo necesario para citarlo
    """

    id: str
    documento: str
    articulo: str
    titulo: str
    texto: str
    puntaje: float = Field(description="Relevancia segun RRF; más alto es más relevante")
