"""API REST de agendamentos (/api/agendamentos), recebendo e devolvendo JSON.

- GET    /api/agendamentos         lista (filtros opcionais ?data=AAAA-MM-DD&status=...)
- GET    /api/agendamentos/{id}    um agendamento
- POST   /api/agendamentos         cria (201)
- PUT    /api/agendamentos/{id}    substitui cliente, serviço, data, horário e status
- DELETE /api/agendamentos/{id}    apaga de verdade e devolve o registro apagado

Leitura aberta. Escrita (POST/PUT/DELETE) exige o header X-Chave-Gestao, a mesma
chave da área de gestão. Erros: 400 (dados inválidos), 401/403 (chave), 404 (id).
"""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.agenda_fila import regras, repositorio
from src.agenda_fila.conexao import get_conexao
from src.agenda_fila.esquemas import (
    AgendamentoApagado,
    AgendamentoApiAtualizacao,
    AgendamentoApiEntrada,
    AgendamentoApiSaida,
    FiltroAgendamentosGestao,
)
from src.agenda_fila.rotas_gestao import exigir_gestor
from src.compartilhado.erros import ErroApp

Conexao = Annotated[sqlite3.Connection, Depends(get_conexao)]
SoGestao = [Depends(exigir_gestor)]

router = APIRouter(prefix="/api/agendamentos", tags=["API REST de agendamentos"])


def _para_dict(linha: sqlite3.Row) -> AgendamentoApiSaida:
    return AgendamentoApiSaida(
        id=linha["id"],
        cliente_id=linha["cliente_id"],
        nome_cliente=linha["cliente_nome"],
        telefone_cliente=linha["cliente_telefone"],
        carro=linha["cliente_carro"],
        marca=linha["cliente_marca"],
        placa=linha["cliente_placa"],
        servico_id=linha["servico_id"],
        servico=linha["servico_nome"],
        data=linha["data"],
        horario=linha["horario"],
        status=linha["status"],
        preco=linha["preco_snapshot"],
        duracao_min=linha["duracao_snapshot_min"],
        criado_em=linha["criado_em"],
        atualizado_em=linha["atualizado_em"],
    )


def _buscar(conexao: sqlite3.Connection, agendamento_id: int) -> sqlite3.Row:
    linha = repositorio.buscar_agendamento(conexao, agendamento_id)
    if linha is None:
        raise ErroApp(regras.MSG_AGENDAMENTO_NAO_ENCONTRADO, status_code=status.HTTP_404_NOT_FOUND)
    return linha


def _exigir_cliente(conexao: sqlite3.Connection, cliente_id: int) -> None:
    if repositorio.buscar_cliente(conexao, cliente_id) is None:
        raise ErroApp(
            f"Cliente {cliente_id} não encontrado", status_code=status.HTTP_400_BAD_REQUEST
        )


def _exigir_servico_ativo(conexao: sqlite3.Connection, servico_id: int) -> sqlite3.Row:
    servico = repositorio.buscar_servico_ativo(conexao, servico_id)
    if servico is None:
        raise ErroApp(
            f"Serviço {servico_id} não encontrado ou indisponível",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return servico


def _exigir_futuro(data: str, horario: str) -> None:
    try:
        regras._exigir_futuro(data, horario)
    except ErroApp as erro:
        raise ErroApp(erro.mensagem, status_code=status.HTTP_400_BAD_REQUEST) from None


@router.get("", summary="Listar agendamentos")
def listar(
    conexao: Conexao, filtro: Annotated[FiltroAgendamentosGestao, Query()]
) -> list[AgendamentoApiSaida]:
    linhas = repositorio.listar_agendamentos(conexao, filtro.data, filtro.status)
    return [_para_dict(linha) for linha in linhas]


@router.get("/{agendamento_id}", summary="Buscar um agendamento")
def obter(conexao: Conexao, agendamento_id: int) -> AgendamentoApiSaida:
    return _para_dict(_buscar(conexao, agendamento_id))


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    dependencies=SoGestao,
    summary="Criar agendamento (status inicial 'agendado')",
)
def criar(conexao: Conexao, dados: AgendamentoApiEntrada) -> AgendamentoApiSaida:
    _exigir_cliente(conexao, dados.cliente_id)
    servico = _exigir_servico_ativo(conexao, dados.servico_id)
    _exigir_futuro(dados.data, dados.horario)
    novo_id = repositorio.inserir_agendamento(
        conexao, dados.cliente_id, servico, dados.data, dados.horario, regras.agora_iso()
    )
    return _para_dict(_buscar(conexao, novo_id))


@router.put("/{agendamento_id}", dependencies=SoGestao, summary="Atualizar agendamento")
def atualizar(
    conexao: Conexao, agendamento_id: int, dados: AgendamentoApiAtualizacao
) -> AgendamentoApiSaida:
    atual = _buscar(conexao, agendamento_id)
    _exigir_cliente(conexao, dados.cliente_id)
    campos: dict[str, object] = {
        "cliente_id": dados.cliente_id,
        "data": dados.data,
        "horario": dados.horario,
        "status": dados.status,
        "atualizado_em": regras.agora_iso(),
    }
    # Só um horário novo precisa ser futuro: dá para mudar o status de um agendamento antigo.
    if (dados.data, dados.horario) != (atual["data"], atual["horario"]):
        _exigir_futuro(dados.data, dados.horario)
    # Trocar de serviço atualiza o preço/duração guardados; manter preserva o snapshot.
    if dados.servico_id != atual["servico_id"]:
        servico = _exigir_servico_ativo(conexao, dados.servico_id)
        campos |= {
            "servico_id": servico["id"],
            "preco_snapshot": servico["preco"],
            "duracao_snapshot_min": servico["duracao_min"],
        }
    repositorio.atualizar_agendamento(conexao, agendamento_id, campos)
    return _para_dict(_buscar(conexao, agendamento_id))


@router.delete("/{agendamento_id}", dependencies=SoGestao, summary="Apagar agendamento")
def apagar(conexao: Conexao, agendamento_id: int) -> AgendamentoApagado:
    agendamento = _para_dict(_buscar(conexao, agendamento_id))
    if not repositorio.apagar_agendamento(conexao, agendamento_id):
        raise ErroApp(regras.MSG_AGENDAMENTO_NAO_ENCONTRADO, status_code=status.HTTP_404_NOT_FOUND)
    return AgendamentoApagado(mensagem="Agendamento apagado", agendamento=agendamento)
