"""Configuração do Alembic.

A URL do banco vem da DATABASE_URL (src/compartilhado/config.py) e o metadata vem
da Base (src/compartilhado/database.py). Comandos (na raiz do projeto):

    uv run alembic revision --autogenerate -m "cria tabela clientes"
    uv run alembic upgrade head
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from src.compartilhado.config import settings
from src.compartilhado.database import Base

# Importe aqui os modelos de cada módulo para o --autogenerate enxergar as tabelas.
# Ex.: import src.clientes_veiculos.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Gera o SQL das migrations sem conectar no banco (alembic upgrade --sql)."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Aplica as migrations conectando no banco."""
    connectable = create_engine(settings.DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
