"""Ponto de entrada da API do LavaAjato.

Rodar em desenvolvimento:  uv run uvicorn src.main:app --reload
"""

import logging
import sqlite3

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.agenda_fila.conexao import abrir_conexao
from src.agenda_fila.rotas import router as rotas_area_cliente
from src.agenda_fila.rotas_gestao import router as rotas_gestao
from src.compartilhado.config import settings
from src.compartilhado.erros import registrar_tratadores_de_erro

logger = logging.getLogger(__name__)

# Tabelas que precisam existir no lavaajato.db para a API funcionar.
TABELAS_OBRIGATORIAS = frozenset({"servicos", "clientes", "agendamentos"})

app = FastAPI(
    title="LavaAjato API",
    description="API do sistema de gestão de lava-jato.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

registrar_tratadores_de_erro(app)

app.include_router(rotas_area_cliente)
app.include_router(rotas_gestao)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Verifica se a API está no ar."""
    return {"status": "ok"}


@app.get("/health/db", tags=["health"])
def health_db() -> JSONResponse:
    """Verifica se o lavaajato.db abre e tem as tabelas servicos, clientes e agendamentos.

    Só lê o sqlite_master: nunca cria nem altera nada no banco.
    """
    indisponivel = JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "erro", "banco": "indisponivel"},
    )
    conexao: sqlite3.Connection | None = None
    try:
        # Aberta aqui (e não via Depends) para que a falha ao abrir também vire 503.
        conexao = abrir_conexao()
        linhas = conexao.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    except sqlite3.Error:
        logger.exception("Falha ao acessar o banco SQLite")
        return indisponivel
    finally:
        if conexao is not None:
            conexao.close()

    faltando = TABELAS_OBRIGATORIAS - {linha["name"] for linha in linhas}
    if faltando:
        logger.error("Banco SQLite sem as tabelas obrigatórias: %s", sorted(faltando))
        return indisponivel
    return JSONResponse(content={"status": "ok", "banco": "ok"})
