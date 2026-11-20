"""Conexão sqlite3 com o banco da área do cliente (lavaajato.db).

Este módulo NUNCA cria ou altera tabelas: isso é feito uma vez, na subida do
servidor, por banco.inicializar_banco().
"""

import sqlite3
from collections.abc import Iterator

from src.compartilhado.config import settings


def abrir_conexao(caminho: str | None = None) -> sqlite3.Connection:
    """Abre uma conexão com foreign keys ligadas e linhas acessíveis por nome.

    mode=rw faz a conexão falhar se o arquivo não existir, em vez de criar um
    banco vazio sem as tabelas.
    """
    alvo = caminho or settings.SQLITE_PATH.as_uri()
    conexao = sqlite3.connect(f"{alvo}?mode=rw", uri=True, check_same_thread=False)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def get_conexao() -> Iterator[sqlite3.Connection]:
    """Dependência do FastAPI: uma conexão por requisição, fechada no final."""
    conexao = abrir_conexao()
    try:
        yield conexao
    finally:
        conexao.close()
