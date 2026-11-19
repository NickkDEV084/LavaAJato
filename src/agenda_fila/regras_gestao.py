"""Regras de negócio da agenda da gestão (/gestao/*).

As regras da área do cliente ficam em regras.py e não mudam: o cliente continua só
remarcando e cancelando em 'agendado' e pagando em 'pronto-retirada'.
"""

import sqlite3

from fastapi import status

from src.agenda_fila import regras, repositorio
from src.agenda_fila.esquemas import (
    AgendamentoGestaoEntrada,
    AgendamentoSaida,
    ClienteResumo,
    FiltroAgendamentosGestao,
)
from src.compartilhado.erros import ErroApp

STATUS_CONFIRMADO = "confirmado"

# Mudanças de status que a gestão pode fazer. Qualquer outra responde 409.
TRANSICOES: dict[str, frozenset[str]] = {
    regras.STATUS_AGENDADO: frozenset({STATUS_CONFIRMADO, regras.STATUS_CANCELADO}),
    STATUS_CONFIRMADO: frozenset({regras.STATUS_PRONTO_RETIRADA, regras.STATUS_CANCELADO}),
}


def _buscar(conexao: sqlite3.Connection, agendamento_id: int) -> sqlite3.Row:
    linha = repositorio.buscar_agendamento(conexao, agendamento_id)
    if linha is None:
        raise ErroApp(regras.MSG_AGENDAMENTO_NAO_ENCONTRADO, status_code=status.HTTP_404_NOT_FOUND)
    return linha


# --- Consultas --------------------------------------------------------------


def listar_clientes(conexao: sqlite3.Connection) -> list[ClienteResumo]:
    return [ClienteResumo(**dict(linha)) for linha in repositorio.listar_clientes(conexao)]


def listar_agendamentos(
    conexao: sqlite3.Connection, filtro: FiltroAgendamentosGestao
) -> list[AgendamentoSaida]:
    return [
        regras._para_agendamento(linha)
        for linha in repositorio.listar_agendamentos(conexao, filtro.data, filtro.status)
    ]


def obter_agendamento(conexao: sqlite3.Connection, agendamento_id: int) -> AgendamentoSaida:
    return regras._para_agendamento(_buscar(conexao, agendamento_id))


# --- Criação ----------------------------------------------------------------


def criar_agendamento(
    conexao: sqlite3.Connection, dados: AgendamentoGestaoEntrada
) -> AgendamentoSaida:
    if repositorio.buscar_cliente(conexao, dados.cliente_id) is None:
        raise ErroApp("Cliente não encontrado", status_code=status.HTTP_404_NOT_FOUND)
    regras._exigir_futuro(dados.data, dados.horario)
    servico = repositorio.buscar_servico_ativo(conexao, dados.servico_id)
    if servico is None:
        raise ErroApp(
            "Serviço não encontrado ou indisponível",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    novo_id = repositorio.inserir_agendamento(
        conexao, dados.cliente_id, servico, dados.data, dados.horario, regras.agora_iso()
    )
    return obter_agendamento(conexao, novo_id)


# --- Mudanças de status -----------------------------------------------------


def _mudar_status(
    conexao: sqlite3.Connection, agendamento_id: int, novo_status: str
) -> AgendamentoSaida:
    linha = _buscar(conexao, agendamento_id)
    status_atual = linha["status"]
    if novo_status not in TRANSICOES.get(status_atual, frozenset()):
        raise ErroApp(
            f"Não é possível mudar o status de '{status_atual}' para '{novo_status}'",
            status_code=status.HTTP_409_CONFLICT,
        )
    # O UPDATE só acontece se o status ainda for o lido acima. Se o cliente cancelou
    # (ou outra aba da gestão mudou) entre a leitura e a escrita, nada é gravado.
    if not repositorio.atualizar_status_se(
        conexao, agendamento_id, status_atual, novo_status, regras.agora_iso()
    ):
        raise ErroApp(
            "O status deste agendamento mudou durante a operação. Atualize a lista e tente de novo",
            status_code=status.HTTP_409_CONFLICT,
        )
    return obter_agendamento(conexao, agendamento_id)


def confirmar_agendamento(conexao: sqlite3.Connection, agendamento_id: int) -> AgendamentoSaida:
    return _mudar_status(conexao, agendamento_id, STATUS_CONFIRMADO)


def marcar_pronto_retirada(conexao: sqlite3.Connection, agendamento_id: int) -> AgendamentoSaida:
    return _mudar_status(conexao, agendamento_id, regras.STATUS_PRONTO_RETIRADA)


def cancelar_agendamento(conexao: sqlite3.Connection, agendamento_id: int) -> AgendamentoSaida:
    return _mudar_status(conexao, agendamento_id, regras.STATUS_CANCELADO)
