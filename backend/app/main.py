import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import health, politicas
from app.core.config import get_settings
from app.rag.indice import construir_indice

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # aquí antes del yield se abre todos los modelos que ocupa la app, db, indice, cliente etc
    settings = get_settings()
    app.state.indice = await asyncio.to_thread(
        construir_indice, settings.data_dir, settings.chroma_dir
    )
    logger.info("Indice de politicas listo")
    yield
    # despues del yield se cierra todo y se apaga el servidor


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.name, version=settings.version, lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(politicas.router)
    return app


app = create_app()
