"""Rotas da agenda da gestão (/gestao/*), sobre o SQLite lavaajato.db.

Rotas abertas, sem autenticação: o projeto é demonstrativo.
"""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.agenda_fila import regras, regras_gestao
from src.agenda_fila.conexao import get_conexao
from src.agenda_fila.esquemas import (
    AgendamentoGestaoEntrada,
    AgendamentoSaida,
    ClienteResumo,
    FiltroAgendamentosGestao,
    ServicoSaida,
)

Conexao = Annotated[sqlite3.Connection, Depends(get_conexao)]

router = APIRouter(prefix="/gestao", tags=["gestão"])


@router.get("/servicos")
def listar_servicos(conexao: Conexao) -> list[ServicoSaida]:
    return regras.listar_servicos(conexao)


@router.get("/clientes")
def listar_clientes(conexao: Conexao) -> list[ClienteResumo]:
    return regras_gestao.listar_clientes(conexao)


@router.get("/agendamentos")
def listar_agendamentos(
    conexao: Conexao, filtro: Annotated[FiltroAgendamentosGestao, Query()]
) -> list[AgendamentoSaida]:
    return regras_gestao.listar_agendamentos(conexao, filtro)


@router.post("/agendamentos", status_code=status.HTTP_201_CREATED)
def criar_agendamento(conexao: Conexao, dados: AgendamentoGestaoEntrada) -> AgendamentoSaida:
    return regras_gestao.criar_agendamento(conexao, dados)


@router.post("/agendamentos/{agendamento_id}/confirmar")
def confirmar_agendamento(conexao: Conexao, agendamento_id: int) -> AgendamentoSaida:
    return regras_gestao.confirmar_agendamento(conexao, agendamento_id)


@router.post("/agendamentos/{agendamento_id}/pronto-retirada")
def marcar_pronto_retirada(conexao: Conexao, agendamento_id: int) -> AgendamentoSaida:
    return regras_gestao.marcar_pronto_retirada(conexao, agendamento_id)


@router.post("/agendamentos/{agendamento_id}/cancelar")
def cancelar_agendamento(conexao: Conexao, agendamento_id: int) -> AgendamentoSaida:
    return regras_gestao.cancelar_agendamento(conexao, agendamento_id)
