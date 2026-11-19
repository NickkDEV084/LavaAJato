"""Configuração comum dos testes.

Os testes nunca abrem o lavaajato.db real: cada teste cria seu próprio SQLite em
tmp_path (fixture caminho_banco). As variáveis abaixo são definidas aqui, então os
testes não dependem do .env local.
"""

import os

# Precisa vir antes de importar src.*: as Settings são lidas na importação.
# setdefault mantém valores que já existam no ambiente (ex.: CI).
os.environ.setdefault("SECRET_KEY", "chave-de-teste")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5500")

import sqlite3  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402

# O DDL abaixo foi copiado de sqlite_master do lavaajato.db.
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
