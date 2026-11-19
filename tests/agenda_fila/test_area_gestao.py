"""Agenda da gestão (/gestao/*): proteção por chave, listagens, criação e status.

Usa as mesmas fixtures da área do cliente (SQLite temporário com o schema real).
A GESTAO_CHAVE é definida por monkeypatch, então os testes não dependem do .env.
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from src.agenda_fila import regras_gestao, repositorio
from src.compartilhado.config import settings

CHAVE = "chave-de-gestao-de-teste"
GESTAO = {"X-Chave-Gestao": CHAVE}
CLIENTE = {"X-Usuario-Id": "usuario-gestao"}
FUTURO = {"data": "2099-05-10", "horario": "09:30"}

ROTAS_GESTAO = [
    ("get", "/gestao/servicos"),
    ("get", "/gestao/clientes"),
    ("get", "/gestao/agendamentos"),
    ("post", "/gestao/agendamentos"),
    ("post", "/gestao/agendamentos/1/confirmar"),
    ("post", "/gestao/agendamentos/1/pronto-retirada"),
    ("post", "/gestao/agendamentos/1/cancelar"),
]


@pytest.fixture(autouse=True)
def chave_configurada(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "GESTAO_CHAVE", SecretStr(CHAVE))


def _assert_erro(resposta, codigo: int) -> dict:
    assert resposta.status_code == codigo, resposta.json()
    erro = resposta.json()["erro"]
    assert erro["codigo"] == codigo
    return erro


def _criar_cliente(api: TestClient, headers: dict[str, str] = CLIENTE, nome: str = "Ana") -> int:
    corpo = {"nome": nome, "telefone": "81999990000", "carro": "Onix", "placa": "ABC1D23"}
    resposta = api.put("/cliente/perfil", json=corpo, headers=headers)
    assert resposta.status_code == 200
    return resposta.json()["id"]


def _agendar_pela_gestao(api: TestClient, cliente_id: int, **extra) -> dict:
    corpo = {"cliente_id": cliente_id, "servico_id": 2, **FUTURO, **extra}
    resposta = api.post("/gestao/agendamentos", json=corpo, headers=GESTAO)
    assert resposta.status_code == 201, resposta.json()
    return resposta.json()


def _agendar_pelo_cliente(api: TestClient, **extra) -> dict:
    corpo = {"servico_id": 2, **FUTURO, **extra}
    resposta = api.post("/cliente/agendamentos", json=corpo, headers=CLIENTE)
    assert resposta.status_code == 201, resposta.json()
    return resposta.json()


def _definir_status(banco: sqlite3.Connection, agendamento_id: int, status: str) -> None:
    with banco:
        banco.execute("UPDATE agendamentos SET status = ? WHERE id = ?", (status, agendamento_id))


def _status_no_banco(banco: sqlite3.Connection, agendamento_id: int) -> str:
    linha = banco.execute("SELECT status FROM agendamentos WHERE id = ?", (agendamento_id,))
    return linha.fetchone()["status"]


# --- Proteção (401 / 403 / 503) ---------------------------------------------


@pytest.mark.parametrize(("metodo", "rota"), ROTAS_GESTAO)
@pytest.mark.parametrize("headers", [{}, {"X-Chave-Gestao": ""}, {"X-Chave-Gestao": "   "}])
def test_sem_chave_retorna_401(api: TestClient, metodo: str, rota: str, headers) -> None:
    _assert_erro(api.request(metodo, rota, headers=headers, json={}), 401)


@pytest.mark.parametrize(("metodo", "rota"), ROTAS_GESTAO)
# Bytes não-ASCII (latin-1) cobrem um header que compare_digest com str recusaria (500).
@pytest.mark.parametrize(
    "chave", ["errada", CHAVE + "x", CHAVE.upper(), "çhave-não-ascii".encode("latin-1")]
)
def test_chave_errada_retorna_403(
    api: TestClient, metodo: str, rota: str, chave: str | bytes
) -> None:
    erro = _assert_erro(api.request(metodo, rota, headers={"X-Chave-Gestao": chave}, json={}), 403)
    assert CHAVE not in erro["mensagem"]


def test_header_do_cliente_nao_libera_a_gestao(api: TestClient) -> None:
    _assert_erro(api.get("/gestao/agendamentos", headers=CLIENTE), 401)


@pytest.mark.parametrize("valor", [None, SecretStr(""), SecretStr("   ")])
@pytest.mark.parametrize(("metodo", "rota"), ROTAS_GESTAO)
def test_sem_gestao_chave_configurada_retorna_503(
    api: TestClient, monkeypatch: pytest.MonkeyPatch, metodo: str, rota: str, valor
) -> None:
    monkeypatch.setattr(settings, "GESTAO_CHAVE", valor)
    # Recusa mesmo com header: sem chave no servidor, nada da gestão funciona.
    erro = _assert_erro(api.request(metodo, rota, headers=GESTAO, json={}), 503)
    assert "GESTAO_CHAVE" in erro["mensagem"]
    assert CHAVE not in erro["mensagem"]


def test_chave_nao_aparece_na_configuracao_impressa() -> None:
    assert CHAVE not in repr(settings)
    assert CHAVE not in str(settings.GESTAO_CHAVE)


# --- Serviços e clientes ----------------------------------------------------


def test_lista_apenas_servicos_ativos(api: TestClient) -> None:
    resposta = api.get("/gestao/servicos", headers=GESTAO)

    assert resposta.status_code == 200
    assert {s["id"] for s in resposta.json()} == {1, 2}


def test_lista_clientes_ordenados_por_nome(api: TestClient) -> None:
    id_bruno = _criar_cliente(api, {"X-Usuario-Id": "u-bruno"}, nome="Bruno")
    id_ana = _criar_cliente(api, {"X-Usuario-Id": "u-ana"}, nome="Ana")

    resposta = api.get("/gestao/clientes", headers=GESTAO)

    assert resposta.status_code == 200
    clientes = resposta.json()
    assert [c["id"] for c in clientes] == [id_ana, id_bruno]
    assert clientes[0] == {
        "id": id_ana,
        "nome": "Ana",
        "telefone": "81999990000",
        "carro": "Onix",
        "marca": None,
        "placa": "ABC1D23",
    }


def test_lista_clientes_vazia(api: TestClient) -> None:
    resposta = api.get("/gestao/clientes", headers=GESTAO)

    assert resposta.status_code == 200
    assert resposta.json() == []


# --- Listagem de agendamentos -----------------------------------------------


def test_agendamento_do_cliente_aparece_para_a_gestao(api: TestClient) -> None:
    _criar_cliente(api)
    criado = _agendar_pelo_cliente(api)

    resposta = api.get("/gestao/agendamentos", headers=GESTAO)

    assert resposta.status_code == 200
    assert resposta.json() == [criado]
    assert criado["cliente"]["nome"] == "Ana"
    assert criado["servico_nome"] == "Lavagem interna"


def test_lista_de_todos_os_clientes_ordenada_por_data_e_horario(api: TestClient) -> None:
    id_ana = _criar_cliente(api)
    id_bruno = _criar_cliente(api, {"X-Usuario-Id": "u-bruno"}, nome="Bruno")
    tarde = _agendar_pela_gestao(api, id_ana, data="2099-05-10", horario="15:00")
    outro_dia = _agendar_pela_gestao(api, id_bruno, data="2099-05-09", horario="18:00")
    manha = _agendar_pela_gestao(api, id_bruno, data="2099-05-10", horario="08:00")

    resposta = api.get("/gestao/agendamentos", headers=GESTAO)

    assert [a["id"] for a in resposta.json()] == [outro_dia["id"], manha["id"], tarde["id"]]


def test_filtra_por_data_e_status(api: TestClient, banco: sqlite3.Connection) -> None:
    cliente_id = _criar_cliente(api)
    dia_10 = _agendar_pela_gestao(api, cliente_id, data="2099-05-10")
    dia_11 = _agendar_pela_gestao(api, cliente_id, data="2099-05-11")
    _definir_status(banco, dia_11["id"], "confirmado")

    def ids(params: dict[str, str]) -> list[int]:
        resposta = api.get("/gestao/agendamentos", params=params, headers=GESTAO)
        assert resposta.status_code == 200
        return [a["id"] for a in resposta.json()]

    assert ids({"data": "2099-05-10"}) == [dia_10["id"]]
    assert ids({"status": "confirmado"}) == [dia_11["id"]]
    assert ids({"data": "2099-05-11", "status": "confirmado"}) == [dia_11["id"]]
    assert ids({"data": "2099-05-10", "status": "confirmado"}) == []
    assert ids({"status": "cancelado"}) == []


@pytest.mark.parametrize(
    "params",
    [{"data": "10/05/2099"}, {"data": "2099-5-10"}, {"data": "2099-02-30"}, {"status": "pago"}],
)
def test_filtro_invalido_retorna_422(api: TestClient, params: dict[str, str]) -> None:
    _assert_erro(api.get("/gestao/agendamentos", params=params, headers=GESTAO), 422)


# --- Criação pela gestão ----------------------------------------------------


def test_cria_agendamento_para_cliente(api: TestClient, banco: sqlite3.Connection) -> None:
    cliente_id = _criar_cliente(api)

    criado = _agendar_pela_gestao(api, cliente_id)

    assert criado["status"] == "agendado"
    assert criado["servico_id"] == 2
    assert criado["preco_snapshot"] == 60.0
    assert criado["duracao_snapshot_min"] == 30
    assert criado["data"] == FUTURO["data"]
    assert criado["horario"] == FUTURO["horario"]
    assert criado["cliente"]["id"] == cliente_id
    assert criado["criado_em"] == criado["atualizado_em"]

    linha = banco.execute(
        "SELECT cliente_id, status, preco_snapshot FROM agendamentos WHERE id = ?",
        (criado["id"],),
    ).fetchone()
    assert dict(linha) == {"cliente_id": cliente_id, "status": "agendado", "preco_snapshot": 60.0}

    # O cliente enxerga o agendamento criado pela gestão.
    do_cliente = api.get("/cliente/agendamentos", headers=CLIENTE).json()
    assert [a["id"] for a in do_cliente] == [criado["id"]]


def test_criar_com_cliente_inexistente_retorna_404(api: TestClient) -> None:
    corpo = {"cliente_id": 999, "servico_id": 2, **FUTURO}
    _assert_erro(api.post("/gestao/agendamentos", json=corpo, headers=GESTAO), 404)


@pytest.mark.parametrize("servico_id", [3, 999])
def test_criar_com_servico_inativo_ou_inexistente_retorna_422(
    api: TestClient, servico_id: int
) -> None:
    cliente_id = _criar_cliente(api)
    corpo = {"cliente_id": cliente_id, "servico_id": servico_id, **FUTURO}
    _assert_erro(api.post("/gestao/agendamentos", json=corpo, headers=GESTAO), 422)


def test_criar_no_passado_retorna_422(api: TestClient) -> None:
    cliente_id = _criar_cliente(api)
    corpo = {"cliente_id": cliente_id, "servico_id": 2, "data": "2000-01-01", "horario": "10:00"}
    erro = _assert_erro(api.post("/gestao/agendamentos", json=corpo, headers=GESTAO), 422)
    assert erro["mensagem"] == "Escolha uma data e um horário futuros"


@pytest.mark.parametrize(
    "corpo",
    [
        {"servico_id": 2, **FUTURO},
        {"cliente_id": 1, **FUTURO},
        {"cliente_id": 1, "servico_id": 2, "data": "2099-5-10", "horario": "09:30"},
        {"cliente_id": 1, "servico_id": 2, "data": "2099-05-10", "horario": "9:30"},
    ],
)
def test_criar_com_corpo_invalido_retorna_422(api: TestClient, corpo: dict) -> None:
    _criar_cliente(api)
    _assert_erro(api.post("/gestao/agendamentos", json=corpo, headers=GESTAO), 422)


# --- Mudanças de status -----------------------------------------------------

ACOES = {
    "confirmar": "confirmado",
    "pronto-retirada": "pronto-retirada",
    "cancelar": "cancelado",
}

TRANSICOES_VALIDAS = [
    ("agendado", "confirmar"),
    ("agendado", "cancelar"),
    ("confirmado", "pronto-retirada"),
    ("confirmado", "cancelar"),
]

TODOS_OS_STATUS = ["agendado", "confirmado", "pronto-retirada", "concluido", "cancelado"]
TRANSICOES_INVALIDAS = [
    (status, acao)
    for status in TODOS_OS_STATUS
    for acao in ACOES
    if (status, acao) not in TRANSICOES_VALIDAS
]


def test_tabela_de_transicoes_e_a_combinada() -> None:
    assert regras_gestao.TRANSICOES == {
        "agendado": {"confirmado", "cancelado"},
        "confirmado": {"pronto-retirada", "cancelado"},
    }


@pytest.mark.parametrize(("status_inicial", "acao"), TRANSICOES_VALIDAS)
def test_transicoes_validas(
    api: TestClient, banco: sqlite3.Connection, status_inicial: str, acao: str
) -> None:
    agendamento = _agendar_pela_gestao(api, _criar_cliente(api))
    _definir_status(banco, agendamento["id"], status_inicial)

    resposta = api.post(f"/gestao/agendamentos/{agendamento['id']}/{acao}", headers=GESTAO)

    assert resposta.status_code == 200, resposta.json()
    assert resposta.json()["status"] == ACOES[acao]
    assert _status_no_banco(banco, agendamento["id"]) == ACOES[acao]


@pytest.mark.parametrize(("status_inicial", "acao"), TRANSICOES_INVALIDAS)
def test_transicoes_invalidas_retornam_409(
    api: TestClient, banco: sqlite3.Connection, status_inicial: str, acao: str
) -> None:
    agendamento = _agendar_pela_gestao(api, _criar_cliente(api))
    _definir_status(banco, agendamento["id"], status_inicial)

    resposta = api.post(f"/gestao/agendamentos/{agendamento['id']}/{acao}", headers=GESTAO)

    _assert_erro(resposta, 409)
    assert _status_no_banco(banco, agendamento["id"]) == status_inicial


@pytest.mark.parametrize("acao", list(ACOES))
def test_mudar_status_de_agendamento_inexistente_retorna_404(api: TestClient, acao: str) -> None:
    _assert_erro(api.post(f"/gestao/agendamentos/999/{acao}", headers=GESTAO), 404)


def test_status_mudou_no_meio_retorna_409(
    api: TestClient, banco: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Corrida: o cliente cancela entre a leitura e o UPDATE da gestão."""
    agendamento = _agendar_pela_gestao(api, _criar_cliente(api))
    buscar_original = repositorio.buscar_agendamento

    def buscar_e_cliente_cancela(conexao, agendamento_id):
        linha = buscar_original(conexao, agendamento_id)  # ainda 'agendado'
        _definir_status(banco, agendamento_id, "cancelado")
        return linha

    monkeypatch.setattr(repositorio, "buscar_agendamento", buscar_e_cliente_cancela)

    resposta = api.post(f"/gestao/agendamentos/{agendamento['id']}/confirmar", headers=GESTAO)

    erro = _assert_erro(resposta, 409)
    assert "mudou durante a operação" in erro["mensagem"]
    assert _status_no_banco(banco, agendamento["id"]) == "cancelado"


def test_atualizar_status_se_so_grava_com_o_status_esperado(
    api: TestClient, banco: sqlite3.Connection
) -> None:
    agendamento = _agendar_pela_gestao(api, _criar_cliente(api))

    assert not repositorio.atualizar_status_se(
        banco, agendamento["id"], "confirmado", "pronto-retirada", "2099-01-01T00:00:00+00:00"
    )
    assert _status_no_banco(banco, agendamento["id"]) == "agendado"
    assert repositorio.atualizar_status_se(
        banco, agendamento["id"], "agendado", "confirmado", "2099-01-01T00:00:00+00:00"
    )
    assert _status_no_banco(banco, agendamento["id"]) == "confirmado"


# --- Regras do cliente continuam as mesmas ----------------------------------


def test_cliente_nao_cancela_nem_remarca_depois_de_confirmado(api: TestClient) -> None:
    _criar_cliente(api)
    agendamento = _agendar_pelo_cliente(api)
    api.post(f"/gestao/agendamentos/{agendamento['id']}/confirmar", headers=GESTAO)

    cancelar = api.post(f"/cliente/agendamentos/{agendamento['id']}/cancelar", headers=CLIENTE)
    remarcar = api.patch(
        f"/cliente/agendamentos/{agendamento['id']}",
        json={"data": "2099-06-01", "horario": "10:00"},
        headers=CLIENTE,
    )

    _assert_erro(cancelar, 409)
    _assert_erro(remarcar, 409)


# --- Fluxo completo ---------------------------------------------------------


def test_fluxo_cliente_agenda_gestao_confirma_e_pronto_cliente_paga(api: TestClient) -> None:
    _criar_cliente(api)
    agendamento = _agendar_pelo_cliente(api)
    caminho = f"/gestao/agendamentos/{agendamento['id']}"

    listados = api.get("/gestao/agendamentos", headers=GESTAO).json()
    assert [(a["id"], a["status"]) for a in listados] == [(agendamento["id"], "agendado")]

    # Antes de ficar pronto, o cliente não consegue pagar.
    pagar_cedo = api.post(f"/cliente/agendamentos/{agendamento['id']}/pagar", headers=CLIENTE)
    _assert_erro(pagar_cedo, 409)

    confirmado = api.post(f"{caminho}/confirmar", headers=GESTAO)
    assert confirmado.status_code == 200
    assert confirmado.json()["status"] == "confirmado"

    pronto = api.post(f"{caminho}/pronto-retirada", headers=GESTAO)
    assert pronto.status_code == 200
    assert pronto.json()["status"] == "pronto-retirada"

    visto_pelo_cliente = api.get(f"/cliente/agendamentos/{agendamento['id']}", headers=CLIENTE)
    assert visto_pelo_cliente.json()["status"] == "pronto-retirada"

    pago = api.post(f"/cliente/agendamentos/{agendamento['id']}/pagar", headers=CLIENTE)
    assert pago.status_code == 200
    assert pago.json()["status"] == "concluido"

    final = api.get("/gestao/agendamentos", params={"status": "concluido"}, headers=GESTAO)
    assert [a["id"] for a in final.json()] == [agendamento["id"]]

    # Concluído é final: a gestão não muda mais nada.
    _assert_erro(api.post(f"{caminho}/cancelar", headers=GESTAO), 409)
