from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import health
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # aquí antes del yield se abre todos los modelos que ocupa la app, db, indice, cliente etc
    yield
    # despues del yield se cierra todo y se apaga el servidor


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.name, version=settings.version, lifespan=lifespan)
    app.include_router(health.router)
    return app


app = create_app()
