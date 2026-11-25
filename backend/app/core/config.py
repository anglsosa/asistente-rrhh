from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
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
    tickets_path: Path = RAIZ_PROYECTO / "data" / "tickets.jsonl"
    google_api_key: SecretStr | None = Field(default=None, validation_alias="GOOGLE_API_KEY")
    gemini_modelo: str = "gemini-2.5-flash"
    gemini_temperatura: float = Field(default=0.2, ge=0, le=2)
    gemini_max_tokens: int = Field(default=1024, ge=128, le=8192)
    prompt_version: str = "v1"
    timeout_agente_seg: float = Field(default=45, gt=0)


@lru_cache
def get_settings() -> Settings:
    """
    Una sola instancia para toda la app
    """
    return Settings()
