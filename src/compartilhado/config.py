"""Configurações da aplicação, lidas das variáveis de ambiente e do arquivo .env."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Raiz do projeto (pasta que contém o pyproject.toml e o .env).
RAIZ_PROJETO = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=RAIZ_PROJETO / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Ex.: postgresql+psycopg://lavaajato:lavaajato@localhost:5434/lavaajato
    DATABASE_URL: str

    # Origens liberadas no CORS, separadas por vírgula no .env.
    # Ex.: CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
    CORS_ORIGINS: Annotated[list[str], NoDecode] = []

    # Chave para assinar tokens (autenticação, futuramente).
    SECRET_KEY: str

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _separar_origens(cls, valor: object) -> object:
        if isinstance(valor, str):
            return [origem.strip() for origem in valor.split(",") if origem.strip()]
        return valor


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
