"""Fixtures da área do cliente: SQLite temporário com o schema real do lavaajato.db.

O DDL abaixo foi copiado de sqlite_master do lavaajato.db. Os testes nunca abrem o
arquivo real: cada teste cria seu próprio banco em tmp_path.
"""

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.agenda_fila.conexao import abrir_conexao, get_conexao
from src.main import app

DDL_LAVAAJATO = [
    """CREATE TABLE agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            servico_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            horario TEXT NOT NULL,
            status TEXT DEFAULT 'agendado', preco_snapshot REAL, duracao_snapshot_min INTEGER, criado_em TEXT, atualizado_em TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (servico_id) REFERENCES servicos(id)
        )""",  # noqa: E501
    """CREATE TABLE clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            carro TEXT,
            marca TEXT,
            placa TEXT
        , usuario_id TEXT, criado_em TEXT, atualizado_em TEXT)""",
    """CREATE TABLE servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            duracao_min INTEGER NOT NULL
        , descricao TEXT NOT NULL DEFAULT '', ativo INTEGER NOT NULL DEFAULT 1)""",
    "CREATE INDEX idx_agendamentos_cliente_data ON agendamentos(cliente_id, data, horario)",
    "CREATE UNIQUE INDEX idx_clientes_usuario ON clientes(usuario_id) WHERE usuario_id IS NOT NULL",
]

SERVICOS_INICIAIS = [
    # (id, nome, preco, duracao_min, descricao, ativo)
    (1, "Higienização interna", 40.0, 15, "", 1),
    (2, "Lavagem interna", 60.0, 30, "Aspiração e limpeza", 1),
    (3, "Polimento (desativado)", 200.0, 120, "", 0),
]


@pytest.fixture
def caminho_banco(tmp_path: Path) -> Path:
    caminho = tmp_path / "lavaajato_teste.db"
    conexao = sqlite3.connect(caminho)
    try:
        for comando in DDL_LAVAAJATO:
            conexao.execute(comando)
        conexao.executemany(
            "INSERT INTO servicos (id, nome, preco, duracao_min, descricao, ativo) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            SERVICOS_INICIAIS,
        )
        conexao.commit()
    finally:
        conexao.close()
    return caminho


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
