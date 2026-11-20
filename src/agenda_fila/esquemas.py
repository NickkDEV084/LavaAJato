"""Esquemas Pydantic de entrada e saída da área do cliente e da gestão."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


def _texto_opcional(valor: object) -> object:
    """Remove espaços nas pontas; texto vazio vira None."""
    if isinstance(valor, str):
        valor = valor.strip()
        return valor or None
    return valor


class ServicoSaida(BaseModel):
    id: int
    nome: str
    descricao: str
    preco: float
    duracao_min: int


class PerfilEntrada(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    telefone: str | None = Field(default=None, max_length=30)
    carro: str | None = Field(default=None, max_length=100)
    marca: str | None = Field(default=None, max_length=100)
    placa: str | None = Field(default=None, max_length=10)

    @field_validator("nome", mode="before")
    @classmethod
    def _limpar_nome(cls, valor: object) -> object:
        if isinstance(valor, str):
            return " ".join(valor.split())
        return valor

    @field_validator("telefone", "carro", "marca", "placa", mode="before")
    @classmethod
    def _limpar_opcionais(cls, valor: object) -> object:
        return _texto_opcional(valor)


class PerfilSaida(BaseModel):
    id: int
    usuario_id: str
    nome: str
    telefone: str | None
    carro: str | None
    marca: str | None
    placa: str | None
    criado_em: str | None
    atualizado_em: str | None


class DataHorarioEntrada(BaseModel):
    """Data (AAAA-MM-DD) e horário (HH:MM), validados no formato exato."""

    data: str = Field(examples=["2026-12-01"])
    horario: str = Field(examples=["14:30"])

    @field_validator("data")
    @classmethod
    def _validar_data(cls, valor: str) -> str:
        # Ida e volta pelo strptime/strftime: só aceita o formato exato. Rejeita data de
        # semana ISO ("2027-W48-1"), espaços e campos sem zero à esquerda.
        try:
            if datetime.strptime(valor, "%Y-%m-%d").strftime("%Y-%m-%d") != valor:
                raise ValueError
        except ValueError:
            raise ValueError("Data deve estar no formato AAAA-MM-DD") from None
        return valor

    @field_validator("horario")
    @classmethod
    def _validar_horario(cls, valor: str) -> str:
        try:
            if datetime.strptime(valor, "%H:%M").strftime("%H:%M") != valor:
                raise ValueError
        except ValueError:
            raise ValueError("Horário deve estar no formato HH:MM") from None
        return valor


class AgendamentoEntrada(DataHorarioEntrada):
    servico_id: int


class RemarcacaoEntrada(DataHorarioEntrada):
    pass


class ClienteResumo(BaseModel):
    id: int
    nome: str
    telefone: str | None
    carro: str | None
    marca: str | None
    placa: str | None


class AgendamentoSaida(BaseModel):
    id: int
    servico_id: int
    servico_nome: str
    data: str
    horario: str
    status: str
    preco_snapshot: float | None
    duracao_snapshot_min: int | None
    criado_em: str | None
    atualizado_em: str | None
    cliente: ClienteResumo


# --- Gestão (/gestao/*) -----------------------------------------------------

StatusAgendamento = Literal["agendado", "confirmado", "pronto-retirada", "concluido", "cancelado"]


class AgendamentoGestaoEntrada(AgendamentoEntrada):
    """Agendamento criado pela gestão para um cliente já cadastrado."""

    cliente_id: int


class FiltroAgendamentosGestao(BaseModel):
    """Filtros opcionais da lista da gestão (?data=AAAA-MM-DD&status=...)."""

    data: str | None = Field(default=None, examples=["2026-12-01"])
    status: StatusAgendamento | None = None

    @field_validator("data")
    @classmethod
    def _validar_data(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        try:
            if datetime.strptime(valor, "%Y-%m-%d").strftime("%Y-%m-%d") != valor:
                raise ValueError
        except ValueError:
            raise ValueError("Data deve estar no formato AAAA-MM-DD") from None
        return valor


# --- API REST pública (/api/agendamentos) -----------------------------------


class AgendamentoApiEntrada(DataHorarioEntrada):
    """Corpo do POST /api/agendamentos."""

    cliente_id: int = Field(gt=0, examples=[1])
    servico_id: int = Field(gt=0, examples=[2])


class AgendamentoApiAtualizacao(AgendamentoApiEntrada):
    """Corpo do PUT /api/agendamentos/{id}: substitui o agendamento inteiro."""

    status: StatusAgendamento = Field(examples=["confirmado"])


class AgendamentoApiSaida(BaseModel):
    """Um agendamento como dicionário simples (sem objetos aninhados)."""

    id: int
    cliente_id: int
    nome_cliente: str
    telefone_cliente: str | None
    carro: str | None
    marca: str | None
    placa: str | None
    servico_id: int
    servico: str
    data: str
    horario: str
    status: str
    preco: float | None
    duracao_min: int | None
    criado_em: str | None
    atualizado_em: str | None


class AgendamentoApagado(BaseModel):
    mensagem: str
    agendamento: AgendamentoApiSaida
