import logging
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.agenda_fila.banco import inicializar_banco
from src.agenda_fila.conexao import abrir_conexao
from src.agenda_fila.rotas import router as rotas_area_cliente
from src.agenda_fila.rotas_api import router as rotas_api_agendamentos
from src.agenda_fila.rotas_gestao import router as rotas_gestao
from src.compartilhado.config import RAIZ_PROJETO, settings
from src.compartilhado.erros import registrar_tratadores_de_erro
from src.compartilhado.estaticos import FrontendSemExtensao

logger = logging.getLogger(__name__)

# Front estático (HTML/CSS/JS sem build), servido pela própria API.
PASTA_FRONTEND = RAIZ_PROJETO / "frontend"

# Tabelas que precisam existir no lavaajato.db para a API funcionar.
TABELAS_OBRIGATORIAS = frozenset({"servicos", "clientes", "agendamentos"})


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Cria o arquivo, as tabelas e os serviços iniciais se ainda não existirem.
    inicializar_banco()
    yield


app = FastAPI(
    title="LavaAjato API",
    description="API do sistema de gestão de lava-jato. Índice das rotas em JSON: GET /api.",
    version="0.1.0",
    lifespan=lifespan,
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
app.include_router(rotas_api_agendamentos)


@app.get("/api", tags=["API REST de agendamentos"], summary="Índice das rotas da API")
def indice_api() -> dict[str, object]:
    """Lista em JSON todas as rotas da API (a mesma fonte do /docs: o schema OpenAPI)."""
    rotas = [
        {
            "metodo": metodo.upper(),
            "caminho": caminho,
            "descricao": operacao.get("summary", ""),
            "headers": [
                param["name"]
                for param in operacao.get("parameters", [])
                if param.get("in") == "header"
            ],
        }
        for caminho, operacoes in app.openapi()["paths"].items()
        for metodo, operacao in operacoes.items()
    ]
    return {
        "nome": app.title,
        "versao": app.version,
        "documentacao": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        },
        "rotas": rotas,
    }


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


# Front estático: TEM que ser montado por último. O mount em "/" casa com qualquer
# caminho, então as rotas da API (/cliente, /gestao, /health, /docs, /openapi.json)
# precisam estar registradas antes para terem prioridade. html=True faz "/" servir
# o index.html (que redireciona para /cliente). FrontendSemExtensao entrega /agenda
# como agenda.html e redireciona (301) /agenda.html para /agenda.
# Atenção: /cliente e /gestao são páginas do front; não crie rotas da API exatamente
# nesses caminhos (os testes de tests/test_frontend.py protegem isso).
app.mount("/", FrontendSemExtensao(directory=PASTA_FRONTEND, html=True), name="frontend")
