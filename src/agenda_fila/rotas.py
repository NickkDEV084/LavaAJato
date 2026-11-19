"""Rotas da área do cliente (/cliente/*), sobre o SQLite lavaajato.db.

O cliente é identificado pelo header X-Usuario-Id.
"""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Header, status

from src.agenda_fila import regras
from src.agenda_fila.conexao import get_conexao
from src.agenda_fila.esquemas import (
    AgendamentoEntrada,
    AgendamentoSaida,
    PerfilEntrada,
    PerfilSaida,
    RemarcacaoEntrada,
    ServicoSaida,
)
from src.compartilhado.erros import ErroApp


def usuario_atual(
    x_usuario_id: Annotated[str | None, Header(alias="X-Usuario-Id")] = None,
) -> str:
    """Lê o header X-Usuario-Id; ausente ou vazio responde 401."""
    usuario_id = (x_usuario_id or "").strip()
    if not usuario_id:
        raise ErroApp(
            "Header X-Usuario-Id é obrigatório",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return usuario_id


Conexao = Annotated[sqlite3.Connection, Depends(get_conexao)]
UsuarioId = Annotated[str, Depends(usuario_atual)]

router = APIRouter(
    prefix="/cliente",
    tags=["área do cliente"],
    dependencies=[Depends(usuario_atual)],
)


@router.get("/servicos")
def listar_servicos(conexao: Conexao) -> list[ServicoSaida]:
    return regras.listar_servicos(conexao)


@router.get("/perfil")
def obter_perfil(conexao: Conexao, usuario_id: UsuarioId) -> PerfilSaida:
    return regras.obter_perfil(conexao, usuario_id)


@router.put("/perfil")
def salvar_perfil(conexao: Conexao, usuario_id: UsuarioId, dados: PerfilEntrada) -> PerfilSaida:
    return regras.salvar_perfil(conexao, usuario_id, dados)


@router.get("/agendamentos")
def listar_agendamentos(conexao: Conexao, usuario_id: UsuarioId) -> list[AgendamentoSaida]:
    return regras.listar_agendamentos(conexao, usuario_id)


@router.get("/agendamentos/{agendamento_id}")
def obter_agendamento(
    conexao: Conexao, usuario_id: UsuarioId, agendamento_id: int
) -> AgendamentoSaida:
    return regras.obter_agendamento(conexao, usuario_id, agendamento_id)


@router.post("/agendamentos", status_code=status.HTTP_201_CREATED)
def criar_agendamento(
    conexao: Conexao, usuario_id: UsuarioId, dados: AgendamentoEntrada
) -> AgendamentoSaida:
    return regras.criar_agendamento(conexao, usuario_id, dados)


@router.patch("/agendamentos/{agendamento_id}")
def remarcar_agendamento(
    conexao: Conexao, usuario_id: UsuarioId, agendamento_id: int, dados: RemarcacaoEntrada
) -> AgendamentoSaida:
    return regras.remarcar_agendamento(conexao, usuario_id, agendamento_id, dados)


@router.post("/agendamentos/{agendamento_id}/cancelar")
def cancelar_agendamento(
    conexao: Conexao, usuario_id: UsuarioId, agendamento_id: int
) -> AgendamentoSaida:
    return regras.cancelar_agendamento(conexao, usuario_id, agendamento_id)


@router.post("/agendamentos/{agendamento_id}/pagar")
def pagar_agendamento(
    conexao: Conexao, usuario_id: UsuarioId, agendamento_id: int
) -> AgendamentoSaida:
    return regras.pagar_agendamento(conexao, usuario_id, agendamento_id)
