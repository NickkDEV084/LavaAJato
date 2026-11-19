"""Ponto de entrada da API do LavaAjato.

Rodar em desenvolvimento:  uv run uvicorn src.main:app --reload
"""

import logging
from typing import Annotated

from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.agenda_fila.rotas import router as rotas_area_cliente
from src.agenda_fila.rotas_gestao import router as rotas_gestao
from src.compartilhado.config import settings
from src.compartilhado.database import get_db
from src.compartilhado.erros import registrar_tratadores_de_erro

logger = logging.getLogger(__name__)

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
def health_db(db: Annotated[Session, Depends(get_db)]) -> JSONResponse:
    """Verifica se a API consegue falar com o banco (executa SELECT 1)."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("Falha ao conectar no banco de dados")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "erro", "banco": "indisponivel"},
        )
    return JSONResponse(content={"status": "ok", "banco": "ok"})
