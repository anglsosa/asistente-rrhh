import asyncio
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.agent.adk.agente import AgenteADK
from app.api import chat, health, politicas
from app.core.config import get_settings
from app.rag.indice import construir_indice
from app.tools.tickets import RegistroTickets

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # aquí antes del yield se abre todos los modelos que ocupa la app, db, indice, cliente etc
    settings = get_settings()
    if settings.google_api_key is None:
        raise RuntimeError("Falta GOOGLE_API_KEY, cópiala en el archivo .env")
    os.environ["GOOGLE_API_KEY"] = settings.google_api_key.get_secret_value()
    indice = await asyncio.to_thread(construir_indice, settings.data_dir, settings.chroma_dir)
    app.state.indice = indice
    app.state.agente = AgenteADK(settings, indice, RegistroTickets(settings.tickets_path))
    logger.info("Índice y agente listos (modelo %s)", settings.gemini_modelo)
    yield
    # despues del yield se cierra todo y se apaga el servidor


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.name, version=settings.version, lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(politicas.router)
    app.include_router(chat.router)
    return app


app = create_app()
