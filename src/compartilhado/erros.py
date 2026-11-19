"""Tratamento padrão de erros da API.

Todas as respostas de erro saem no mesmo formato JSON:

    {"erro": {"codigo": 404, "mensagem": "Cliente não encontrado", "detalhes": null}}

Nos módulos, para erros de regra de negócio, levante ErroApp (ou HTTPException):

    raise ErroApp("Horário já ocupado", status_code=409)
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ErroApp(Exception):
    """Erro de regra de negócio, convertido em resposta JSON com o status indicado."""

    def __init__(
        self,
        mensagem: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detalhes: Any = None,
    ) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status_code = status_code
        self.detalhes = detalhes


def resposta_erro(status_code: int, mensagem: str, detalhes: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"erro": {"codigo": status_code, "mensagem": mensagem, "detalhes": detalhes}},
    )


async def _erro_app(request: Request, exc: ErroApp) -> JSONResponse:
    return resposta_erro(exc.status_code, exc.mensagem, exc.detalhes)


async def _erro_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    response = resposta_erro(exc.status_code, str(exc.detail))
    if exc.headers:
        response.headers.update(exc.headers)
    return response


async def _erro_validacao(request: Request, exc: RequestValidationError) -> JSONResponse:
    detalhes = [
        {"campo": ".".join(str(parte) for parte in erro["loc"]), "mensagem": erro["msg"]}
        for erro in exc.errors()
    ]
    return resposta_erro(
        status.HTTP_422_UNPROCESSABLE_CONTENT, "Dados inválidos na requisição", detalhes
    )


async def _erro_banco(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.exception("Erro de banco de dados em %s %s", request.method, request.url.path)
    return resposta_erro(status.HTTP_500_INTERNAL_SERVER_ERROR, "Erro ao acessar o banco de dados")


async def _erro_inesperado(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Erro inesperado em %s %s", request.method, request.url.path)
    return resposta_erro(status.HTTP_500_INTERNAL_SERVER_ERROR, "Erro interno no servidor")


def registrar_tratadores_de_erro(app: FastAPI) -> None:
    app.add_exception_handler(ErroApp, _erro_app)
    app.add_exception_handler(StarletteHTTPException, _erro_http)
    app.add_exception_handler(RequestValidationError, _erro_validacao)
    app.add_exception_handler(SQLAlchemyError, _erro_banco)
    app.add_exception_handler(Exception, _erro_inesperado)
