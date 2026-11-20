"""Criação do banco SQLite na subida do servidor.

Se o arquivo de SQLITE_PATH (ou a pasta dele) não existir, é criado. As tabelas e
índices usam CREATE ... IF NOT EXISTS: num banco que já existe nada é alterado.
Os serviços iniciais só são inseridos quando a tabela servicos está vazia.

Necessário no Render (plano free): o disco é efêmero e o banco pode sumir a cada
reinício ou deploy.
"""

import logging
import sqlite3
from pathlib import Path

from src.compartilhado.config import settings

logger = logging.getLogger(__name__)

# Mesmo schema do lavaajato.db original (ver sqlite_master), com IF NOT EXISTS.
DDL = [
    """CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            carro TEXT,
            marca TEXT,
            placa TEXT,
            usuario_id TEXT,
            criado_em TEXT,
            atualizado_em TEXT
        )""",
    """CREATE TABLE IF NOT EXISTS servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            duracao_min INTEGER NOT NULL,
            descricao TEXT NOT NULL DEFAULT '',
            ativo INTEGER NOT NULL DEFAULT 1
        )""",
    """CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            servico_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            horario TEXT NOT NULL,
            status TEXT DEFAULT 'agendado',
            preco_snapshot REAL,
            duracao_snapshot_min INTEGER,
            criado_em TEXT,
            atualizado_em TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (servico_id) REFERENCES servicos(id)
        )""",
    "CREATE INDEX IF NOT EXISTS idx_agendamentos_cliente_data "
    "ON agendamentos(cliente_id, data, horario)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_clientes_usuario "
    "ON clientes(usuario_id) WHERE usuario_id IS NOT NULL",
]

# (nome, preco, duracao_min, descricao): os mesmos do lavaajato.db versionado.
SERVICOS_INICIAIS = [
    ("Higienização interna", 40.0, 15, ""),
    ("Lavagem interna", 60.0, 30, ""),
    ("Shampoo automotivo", 70.0, 30, ""),
]


def inicializar_banco(caminho: Path | None = None) -> None:
    """Garante que o arquivo, as tabelas e os serviços iniciais existam."""
    alvo = caminho or settings.SQLITE_PATH
    alvo.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(alvo)
    try:
        with conexao:
            for comando in DDL:
                conexao.execute(comando)
            (total,) = conexao.execute("SELECT COUNT(*) FROM servicos").fetchone()
            if total == 0:
                conexao.executemany(
                    "INSERT INTO servicos (nome, preco, duracao_min, descricao) "
                    "VALUES (?, ?, ?, ?)",
                    SERVICOS_INICIAIS,
                )
                logger.info("Banco novo: %d serviços iniciais inseridos", len(SERVICOS_INICIAIS))
    finally:
        conexao.close()
