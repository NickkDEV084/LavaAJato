"""Configurações da aplicação, lidas das variáveis de ambiente e do arquivo .env."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import SecretStr, field_validator
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

    # Chave da área de gestão (/gestao/*), enviada pelo front no header X-Chave-Gestao.
    # Sem ela configurada, a API recusa todas as rotas de gestão (503).
    # SecretStr esconde o valor em repr/logs (aparece como '**********').
    GESTAO_CHAVE: SecretStr | None = None

    # Banco SQLite da área do cliente (agenda_fila). Caminho relativo é resolvido
    # a partir da raiz do projeto. Ex.: SQLITE_PATH=lavaajato.db
    SQLITE_PATH: Path = Path("lavaajato.db")

    @field_validator("SQLITE_PATH", mode="after")
    @classmethod
    def _resolver_caminho_sqlite(cls, valor: Path) -> Path:
        return valor if valor.is_absolute() else RAIZ_PROJETO / valor

    # Fuso usado nas regras de horário (ex.: "data e hora futuras"), independente
    # do relógio/fuso do servidor. Nome IANA, ex.: America/Recife.
    TIMEZONE: str = "America/Recife"

    @field_validator("TIMEZONE", mode="after")
    @classmethod
    def _validar_fuso(cls, valor: str) -> str:
        try:
            ZoneInfo(valor)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError(f"Fuso horário inválido: {valor!r}") from None
        return valor

    @property
    def fuso(self) -> ZoneInfo:
        return ZoneInfo(self.TIMEZONE)

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
