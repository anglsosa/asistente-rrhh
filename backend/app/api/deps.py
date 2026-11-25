from fastapi import Request

from app.rag.indice import IndicePoliticas


def get_indice(request: Request) -> IndicePoliticas:
    """
    El infice se construye al arrancar y vive en el app.state
    """

    return request.app.state.indice
