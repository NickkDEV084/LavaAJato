"""Fixtures da área do cliente e da gestão sobre o SQLite temporário.

O banco temporário (fixture caminho_banco, com o schema real do lavaajato.db) fica
em tests/conftest.py. Os testes nunca abrem o arquivo real.
"""

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.agenda_fila.conexao import abrir_conexao, get_conexao
from src.main import app


@pytest.fixture
def banco(caminho_banco: Path) -> Iterator[sqlite3.Connection]:
    """Conexão direta ao banco de teste, para preparar e conferir dados."""
    conexao = abrir_conexao(caminho_banco.as_uri())
    try:
        yield conexao
    finally:
        conexao.close()


@pytest.fixture
def api(caminho_banco: Path) -> Iterator[TestClient]:
    """Cliente HTTP com get_conexao apontando para o banco temporário."""

    def _conexao_teste() -> Iterator[sqlite3.Connection]:
        conexao = abrir_conexao(caminho_banco.as_uri())
        try:
            yield conexao
        finally:
            conexao.close()

    app.dependency_overrides[get_conexao] = _conexao_teste
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()
