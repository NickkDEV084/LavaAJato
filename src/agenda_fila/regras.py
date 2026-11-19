"""Regras de negócio da área do cliente: perfil e agendamentos."""

import sqlite3
from datetime import UTC, datetime

from fastapi import status

from src.agenda_fila import repositorio
from src.agenda_fila.esquemas import (
    AgendamentoEntrada,
    AgendamentoSaida,
    ClienteResumo,
    PerfilEntrada,
    PerfilSaida,
    RemarcacaoEntrada,
    ServicoSaida,
)
from src.compartilhado.config import settings
from src.compartilhado.erros import ErroApp

STATUS_AGENDADO = "agendado"
STATUS_PRONTO_RETIRADA = "pronto-retirada"
STATUS_CANCELADO = "cancelado"
STATUS_CONCLUIDO = "concluido"

MSG_AGENDAMENTO_NAO_ENCONTRADO = "Agendamento não encontrado"


def agora_utc() -> datetime:
    """Único ponto de leitura do relógio (com fuso), para os testes poderem congelá-lo."""
    return datetime.now(UTC)


def agora_iso() -> str:
    """Momento atual em ISO 8601 (UTC), usado em criado_em/atualizado_em."""
    return agora_utc().isoformat(timespec="seconds")


def _exigir_futuro(data: str, horario: str) -> None:
    """Data/horário são interpretados no fuso TIMEZONE, não no fuso do servidor."""
    fuso = settings.fuso
    momento = datetime.strptime(f"{data} {horario}", "%Y-%m-%d %H:%M").replace(tzinfo=fuso)
    if momento <= agora_utc().astimezone(fuso):
        raise ErroApp(
            "Escolha uma data e um horário futuros",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )


def _para_agendamento(linha: sqlite3.Row) -> AgendamentoSaida:
    return AgendamentoSaida(
        id=linha["id"],
        servico_id=linha["servico_id"],
        servico_nome=linha["servico_nome"],
        data=linha["data"],
        horario=linha["horario"],
        status=linha["status"],
        preco_snapshot=linha["preco_snapshot"],
        duracao_snapshot_min=linha["duracao_snapshot_min"],
        criado_em=linha["criado_em"],
        atualizado_em=linha["atualizado_em"],
        cliente=ClienteResumo(
            id=linha["cliente_id"],
            nome=linha["cliente_nome"],
            telefone=linha["cliente_telefone"],
            carro=linha["cliente_carro"],
            marca=linha["cliente_marca"],
            placa=linha["cliente_placa"],
        ),
    )


# --- Serviços ---------------------------------------------------------------


def listar_servicos(conexao: sqlite3.Connection) -> list[ServicoSaida]:
    return [ServicoSaida(**dict(linha)) for linha in repositorio.listar_servicos_ativos(conexao)]


# --- Perfil -----------------------------------------------------------------


def obter_perfil(conexao: sqlite3.Connection, usuario_id: str) -> PerfilSaida:
    cliente = repositorio.buscar_cliente_por_usuario(conexao, usuario_id)
    if cliente is None:
        raise ErroApp("Perfil não encontrado", status_code=status.HTTP_404_NOT_FOUND)
    return PerfilSaida(**dict(cliente))


def salvar_perfil(
    conexao: sqlite3.Connection, usuario_id: str, dados: PerfilEntrada
) -> PerfilSaida:
    repositorio.salvar_cliente(conexao, usuario_id, dados.model_dump(), agora_iso())
    return obter_perfil(conexao, usuario_id)


# --- Agendamentos -----------------------------------------------------------


def _id_do_cliente(conexao: sqlite3.Connection, usuario_id: str) -> int | None:
    cliente = repositorio.buscar_cliente_por_usuario(conexao, usuario_id)
    return None if cliente is None else int(cliente["id"])


def _buscar_do_cliente(
    conexao: sqlite3.Connection, usuario_id: str, agendamento_id: int
) -> sqlite3.Row:
    """Agendamento do próprio cliente; de outro cliente (ou inexistente) vira 404."""
    cliente_id = _id_do_cliente(conexao, usuario_id)
    linha = (
        None
        if cliente_id is None
        else repositorio.buscar_agendamento_do_cliente(conexao, agendamento_id, cliente_id)
    )
    if linha is None:
        raise ErroApp(MSG_AGENDAMENTO_NAO_ENCONTRADO, status_code=status.HTTP_404_NOT_FOUND)
    return linha


def listar_agendamentos(conexao: sqlite3.Connection, usuario_id: str) -> list[AgendamentoSaida]:
    cliente_id = _id_do_cliente(conexao, usuario_id)
    if cliente_id is None:
        return []
    return [
        _para_agendamento(linha)
        for linha in repositorio.listar_agendamentos_do_cliente(conexao, cliente_id)
    ]


def obter_agendamento(
    conexao: sqlite3.Connection, usuario_id: str, agendamento_id: int
) -> AgendamentoSaida:
    return _para_agendamento(_buscar_do_cliente(conexao, usuario_id, agendamento_id))


def criar_agendamento(
    conexao: sqlite3.Connection, usuario_id: str, dados: AgendamentoEntrada
) -> AgendamentoSaida:
    cliente_id = _id_do_cliente(conexao, usuario_id)
    if cliente_id is None:
        raise ErroApp(
            "Complete seu perfil antes de agendar",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    _exigir_futuro(dados.data, dados.horario)
    servico = repositorio.buscar_servico_ativo(conexao, dados.servico_id)
    if servico is None:
        raise ErroApp(
            "Serviço não encontrado ou indisponível",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    novo_id = repositorio.inserir_agendamento(
        conexao, cliente_id, servico, dados.data, dados.horario, agora_iso()
    )
    return obter_agendamento(conexao, usuario_id, novo_id)


def remarcar_agendamento(
    conexao: sqlite3.Connection,
    usuario_id: str,
    agendamento_id: int,
    dados: RemarcacaoEntrada,
) -> AgendamentoSaida:
    linha = _buscar_do_cliente(conexao, usuario_id, agendamento_id)
    if linha["status"] != STATUS_AGENDADO:
        raise ErroApp(
            "Somente agendamentos com status 'agendado' podem ser remarcados",
            status_code=status.HTTP_409_CONFLICT,
        )
    _exigir_futuro(dados.data, dados.horario)
    repositorio.atualizar_data_horario(
        conexao, agendamento_id, dados.data, dados.horario, agora_iso()
    )
    return obter_agendamento(conexao, usuario_id, agendamento_id)


def cancelar_agendamento(
    conexao: sqlite3.Connection, usuario_id: str, agendamento_id: int
) -> AgendamentoSaida:
    linha = _buscar_do_cliente(conexao, usuario_id, agendamento_id)
    if linha["status"] != STATUS_AGENDADO:
        raise ErroApp(
            "Somente agendamentos com status 'agendado' podem ser cancelados",
            status_code=status.HTTP_409_CONFLICT,
        )
    repositorio.atualizar_status(conexao, agendamento_id, STATUS_CANCELADO, agora_iso())
    return obter_agendamento(conexao, usuario_id, agendamento_id)


def pagar_agendamento(
    conexao: sqlite3.Connection, usuario_id: str, agendamento_id: int
) -> AgendamentoSaida:
    linha = _buscar_do_cliente(conexao, usuario_id, agendamento_id)
    if linha["status"] != STATUS_PRONTO_RETIRADA:
        raise ErroApp(
            "Este agendamento ainda não está pronto para pagamento",
            status_code=status.HTTP_409_CONFLICT,
        )
    repositorio.atualizar_status(conexao, agendamento_id, STATUS_CONCLUIDO, agora_iso())
    return obter_agendamento(conexao, usuario_id, agendamento_id)
