"""Conexão com o banco: engine, sessões, Base declarativa e dependência get_db."""

from collections.abc import Iterator
from decimal import Decimal

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.compartilhado.config import settings
from src.compartilhado.tipos import TIPO_DINHEIRO, TIPO_TEXTO

# Nomes previsíveis para constraints. Sem isso cada banco gera nomes do seu jeito
# e o Alembic não consegue apagar/alterar constraints de forma confiável depois.
CONVENCAO_DE_NOMES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base de todos os modelos. Importe-a nos módulos para declarar tabelas."""

    metadata = MetaData(naming_convention=CONVENCAO_DE_NOMES)

    # Mapped[str] sem tipo explícito vira VARCHAR(255) e Mapped[Decimal] vira
    # NUMERIC(10, 2). Para outros tamanhos, use os aliases de tipos.py.
    type_annotation_map = {
        str: TIPO_TEXTO,
        Decimal: TIPO_DINHEIRO,
    }


engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Dependência do FastAPI: abre uma sessão por requisição e fecha no final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
