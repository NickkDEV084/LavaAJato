"""Criação das tabelas na subida do servidor, no Turso ou no arquivo SQLite.

Com o Turso configurado (TURSO_DATABASE_URL e TURSO_AUTH_TOKEN), as tabelas são
criadas no banco do Turso. Sem ele, no arquivo de SQLITE_PATH, que é criado (com a
pasta) se não existir. Nos dois casos as tabelas e índices usam
CREATE ... IF NOT EXISTS: num banco que já existe nada é alterado nem apagado. Os
serviços iniciais só são inseridos quando a tabela servicos está vazia, então não
duplicam.

No Render (plano free) o disco é efêmero: sem o Turso, o arquivo pode sumir a cada
reinício ou deploy. Com o Turso, os dados ficam na nuvem e sobrevivem a isso.
"""

import logging
import sqlite3
from pathlib import Path

from src.agenda_fila.conexao import Conexao, abrir_conexao_turso
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
    """Garante que as tabelas e os serviços iniciais existam.

    Sem `caminho`, usa o Turso se estiver configurado; senão, o arquivo SQLITE_PATH.
    Com `caminho`, usa sempre esse arquivo SQLite local (é o que os testes fazem).
    """
    conexao: Conexao
    if caminho is None and settings.usa_turso:
        logger.info("Banco: Turso (remoto)")
        conexao = abrir_conexao_turso()
    else:
        alvo = caminho or settings.SQLITE_PATH
        logger.info("Banco: SQLite local (%s)", alvo)
        alvo.parent.mkdir(parents=True, exist_ok=True)
        conexao = sqlite3.connect(alvo)
    try:
        _criar_tabelas_e_servicos(conexao)
    finally:
        conexao.close()


def _criar_tabelas_e_servicos(conexao: Conexao) -> None:
    with conexao:
        for comando in DDL:
            conexao.execute(comando)
        (total,) = conexao.execute("SELECT COUNT(*) FROM servicos").fetchone()
        if total == 0:
            conexao.executemany(
                "INSERT INTO servicos (nome, preco, duracao_min, descricao) VALUES (?, ?, ?, ?)",
                SERVICOS_INICIAIS,
            )
            logger.info("Banco novo: %d serviços iniciais inseridos", len(SERVICOS_INICIAIS))
