"""Rotas da agenda da gestão (/gestao/*), sobre o SQLite lavaajato.db.

Proteção mínima (ainda não há autenticação real): toda rota exige o header
X-Chave-Gestao igual à configuração GESTAO_CHAVE. A chave nunca é registrada em
log nem devolvida em mensagens de erro.
"""

import secrets
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, status

from src.agenda_fila import regras, regras_gestao
from src.agenda_fila.conexao import get_conexao
from src.agenda_fila.esquemas import (
    AgendamentoGestaoEntrada,
    AgendamentoSaida,
    ClienteResumo,
    FiltroAgendamentosGestao,
    ServicoSaida,
)
from src.compartilhado.config import settings
from src.compartilhado.erros import ErroApp


def exigir_gestor(
    x_chave_gestao: Annotated[str | None, Header(alias="X-Chave-Gestao")] = None,
) -> None:
    """503 sem GESTAO_CHAVE configurada; 401 sem o header; 403 com a chave errada."""
    configurada = settings.GESTAO_CHAVE.get_secret_value() if settings.GESTAO_CHAVE else ""
    if not configurada.strip():
        raise ErroApp(
            "Área de gestão indisponível: GESTAO_CHAVE não está configurada no servidor",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    enviada = (x_chave_gestao or "").strip()
    if not enviada:
        raise ErroApp(
            "Header X-Chave-Gestao é obrigatório",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    # Compara bytes (aceita qualquer caractere) em tempo constante.
    if not secrets.compare_digest(enviada.encode("utf-8"), configurada.encode("utf-8")):
        raise ErroApp("Chave de gestão inválida", status_code=status.HTTP_403_FORBIDDEN)


Conexao = Annotated[sqlite3.Connection, Depends(get_conexao)]

router = APIRouter(
    prefix="/gestao",
    tags=["gestão"],
    dependencies=[Depends(exigir_gestor)],
)


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
