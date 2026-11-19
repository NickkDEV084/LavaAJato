"""Cria e abre o banco SQLite simples da tela do cliente."""

import sqlite3
from pathlib import Path


BANCO = Path(__file__).resolve().parent.parent / "lavaajato.db"


def conectar():
    conexao = sqlite3.connect(BANCO)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def _garantir_catalogo_compativel(conexao):
    colunas = {linha["name"] for linha in conexao.execute("PRAGMA table_info(servicos)")}
    if "descricao" not in colunas:
        conexao.execute("ALTER TABLE servicos ADD COLUMN descricao TEXT DEFAULT ''")
    if "ativo" not in colunas:
        conexao.execute("ALTER TABLE servicos ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1")


def criar_tabelas():
    conexao = conectar()
    try:
        conexao.executescript("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                telefone TEXT,
                carro TEXT,
                marca TEXT,
                placa TEXT
            );

            CREATE TABLE IF NOT EXISTS servicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                descricao TEXT DEFAULT '',
                preco REAL NOT NULL,
                duracao_min INTEGER NOT NULL,
                ativo INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS agendamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                servico_id INTEGER NOT NULL,
                data TEXT NOT NULL,
                horario TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'agendado',
                FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                FOREIGN KEY (servico_id) REFERENCES servicos(id)
            );
        """)
        _garantir_catalogo_compativel(conexao)

        quantidade = conexao.execute("SELECT COUNT(*) FROM servicos").fetchone()[0]
        if quantidade == 0:
            conexao.executemany(
                "INSERT INTO servicos (nome, descricao, preco, duracao_min) VALUES (?, ?, ?, ?)",
                [
                    ("Higienização interna", "Serviço disponível para agendamento.", 40, 15),
                    ("Lavagem interna", "Serviço disponível para agendamento.", 60, 30),
                    ("Shampoo automotivo", "Serviço disponível para agendamento.", 70, 30),
                ],
            )
        conexao.commit()
    finally:
        conexao.close()


if __name__ == "__main__":
    criar_tabelas()
    print(f"Banco criado: {BANCO}")
