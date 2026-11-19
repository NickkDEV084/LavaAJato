"""Configuração comum dos testes.

Os testes não usam o PostgreSQL: get_db é sobrescrito para usar SQLite em memória.
As variáveis abaixo são definidas aqui, então os testes não dependem do .env local.
"""

import os

# Precisa vir antes de importar src.*: as Settings são lidas na importação.
# setdefault mantém valores que já existam no ambiente (ex.: CI).
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "chave-de-teste")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5500")

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from src.compartilhado.database import Base, get_db  # noqa: E402
from src.main import app  # noqa: E402

# StaticPool + check_same_thread=False: todas as sessões compartilham a mesma
# conexão, senão cada conexão enxergaria um banco em memória diferente.
engine_teste = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionTeste = sessionmaker(bind=engine_teste, autoflush=False, expire_on_commit=False)


@pytest.fixture
def db() -> Iterator[Session]:
    """Sessão de banco limpa para cada teste (tabelas criadas e apagadas)."""
    Base.metadata.create_all(engine_teste)
    sessao = SessionTeste()
    try:
        yield sessao
    finally:
        sessao.close()
        Base.metadata.drop_all(engine_teste)


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    """Cliente HTTP da API usando o banco SQLite em memória."""

    def _get_db_teste() -> Iterator[Session]:
        yield db

    app.dependency_overrides[get_db] = _get_db_teste
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()
