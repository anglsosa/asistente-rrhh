from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ_PROYECTO = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """
    Configuración de la app: aquí vienen variables de entorno desde el .env
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        env_prefix="APP_",
        extra="ignore",
    )

    name: str = "Asistente de politicas de RRHH"
    version: str = "0.1.0"
    environment: str = "development"
    data_dir: Path = RAIZ_PROYECTO / "data" / "politicas"
    chroma_dir: Path = RAIZ_PROYECTO / "data" / "chroma"


@lru_cache
def get_settings() -> Settings:
    """
    Una sola instancia para toda la app
    """
    return Settings()
