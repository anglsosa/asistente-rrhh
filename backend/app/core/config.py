from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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


@lru_cache
def get_settings() -> Settings:
    """
    Una sola instancia para toda la app
    """
    return Settings()
