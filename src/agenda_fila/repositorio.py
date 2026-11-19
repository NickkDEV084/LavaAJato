"""Acesso ao SQLite da área do cliente. Só SQL parametrizado (?), sem regra de negócio."""

import sqlite3
from typing import Any

_SELECT_AGENDAMENTO = """
    SELECT
        a.id, a.servico_id, a.data, a.horario, a.status,
        a.preco_snapshot, a.duracao_snapshot_min, a.criado_em, a.atualizado_em,
        s.nome AS servico_nome,
        c.id AS cliente_id, c.nome AS cliente_nome, c.telefone AS cliente_telefone,
        c.carro AS cliente_carro, c.marca AS cliente_marca, c.placa AS cliente_placa
    FROM agendamentos a
    JOIN servicos s ON s.id = a.servico_id
    JOIN clientes c ON c.id = a.cliente_id
"""


def listar_servicos_ativos(conexao: sqlite3.Connection) -> list[sqlite3.Row]:
    return conexao.execute(
        "SELECT id, nome, descricao, preco, duracao_min FROM servicos WHERE ativo = 1 ORDER BY nome"
    ).fetchall()


def buscar_servico_ativo(conexao: sqlite3.Connection, servico_id: int) -> sqlite3.Row | None:
    return conexao.execute(
        "SELECT id, nome, preco, duracao_min FROM servicos WHERE id = ? AND ativo = 1",
        (servico_id,),
    ).fetchone()


def buscar_cliente_por_usuario(conexao: sqlite3.Connection, usuario_id: str) -> sqlite3.Row | None:
    return conexao.execute(
        "SELECT id, usuario_id, nome, telefone, carro, marca, placa, criado_em, atualizado_em "
        "FROM clientes WHERE usuario_id = ?",
        (usuario_id,),
    ).fetchone()


def salvar_cliente(
    conexao: sqlite3.Connection, usuario_id: str, dados: dict[str, Any], agora: str
) -> None:
    """Cria o cliente do usuário ou atualiza o existente (criado_em é preservado)."""
    with conexao:
        conexao.execute(
            """
            INSERT INTO clientes
                (usuario_id, nome, telefone, carro, marca, placa, criado_em, atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (usuario_id) WHERE usuario_id IS NOT NULL DO UPDATE SET
                nome = excluded.nome,
                telefone = excluded.telefone,
                carro = excluded.carro,
                marca = excluded.marca,
                placa = excluded.placa,
                atualizado_em = excluded.atualizado_em
            """,
            (
                usuario_id,
                dados["nome"],
                dados["telefone"],
                dados["carro"],
                dados["marca"],
                dados["placa"],
                agora,
                agora,
            ),
        )


def listar_agendamentos_do_cliente(
    conexao: sqlite3.Connection, cliente_id: int
) -> list[sqlite3.Row]:
    return conexao.execute(
        _SELECT_AGENDAMENTO + " WHERE a.cliente_id = ? ORDER BY a.data, a.horario, a.id",
        (cliente_id,),
    ).fetchall()


def buscar_agendamento_do_cliente(
    conexao: sqlite3.Connection, agendamento_id: int, cliente_id: int
) -> sqlite3.Row | None:
    return conexao.execute(
        _SELECT_AGENDAMENTO + " WHERE a.id = ? AND a.cliente_id = ?",
        (agendamento_id, cliente_id),
    ).fetchone()


def inserir_agendamento(
    conexao: sqlite3.Connection,
    cliente_id: int,
    servico: sqlite3.Row,
    data: str,
    horario: str,
    agora: str,
) -> int:
    with conexao:
        cursor = conexao.execute(
            """
            INSERT INTO agendamentos
                (cliente_id, servico_id, data, horario, status,
                 preco_snapshot, duracao_snapshot_min, criado_em, atualizado_em)
            VALUES (?, ?, ?, ?, 'agendado', ?, ?, ?, ?)
            """,
            (
                cliente_id,
                servico["id"],
                data,
                horario,
                servico["preco"],
                servico["duracao_min"],
                agora,
                agora,
            ),
        )
    return int(cursor.lastrowid)


def atualizar_data_horario(
    conexao: sqlite3.Connection, agendamento_id: int, data: str, horario: str, agora: str
) -> None:
    with conexao:
        conexao.execute(
            "UPDATE agendamentos SET data = ?, horario = ?, atualizado_em = ? WHERE id = ?",
            (data, horario, agora, agendamento_id),
        )


def atualizar_status(
    conexao: sqlite3.Connection, agendamento_id: int, status: str, agora: str
) -> None:
    with conexao:
        conexao.execute(
            "UPDATE agendamentos SET status = ?, atualizado_em = ? WHERE id = ?",
            (status, agora, agendamento_id),
        )
