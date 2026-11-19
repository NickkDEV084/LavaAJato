import sqlite3
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

USUARIO = {"X-Usuario-Id": "usuario-a"}
OUTRO_USUARIO = {"X-Usuario-Id": "usuario-b"}

PERFIL = {
    "nome": "  Maria   da Silva ",
    "telefone": "11999990000",
    "carro": "Onix",
    "marca": "Chevrolet",
    "placa": "ABC1D23",
}
FUTURO = {"data": "2099-05-10", "horario": "09:30"}


def _criar_perfil(api: TestClient, headers: dict[str, str] = USUARIO) -> dict:
    resposta = api.put("/cliente/perfil", json=PERFIL, headers=headers)
    assert resposta.status_code == 200
    return resposta.json()


def _criar_agendamento(api: TestClient, headers: dict[str, str] = USUARIO, **extra) -> dict:
    corpo = {"servico_id": 2, **FUTURO, **extra}
    resposta = api.post("/cliente/agendamentos", json=corpo, headers=headers)
    assert resposta.status_code == 201, resposta.json()
    return resposta.json()


def _definir_status(banco: sqlite3.Connection, agendamento_id: int, status: str) -> None:
    with banco:
        banco.execute("UPDATE agendamentos SET status = ? WHERE id = ?", (status, agendamento_id))


def _assert_erro(resposta, codigo: int) -> dict:
    assert resposta.status_code == codigo
    erro = resposta.json()["erro"]
    assert erro["codigo"] == codigo
    return erro


# --- Autenticação (401) -----------------------------------------------------


@pytest.mark.parametrize(
    ("metodo", "rota"),
    [
        ("get", "/cliente/servicos"),
        ("get", "/cliente/perfil"),
        ("put", "/cliente/perfil"),
        ("get", "/cliente/agendamentos"),
        ("get", "/cliente/agendamentos/1"),
        ("post", "/cliente/agendamentos"),
        ("patch", "/cliente/agendamentos/1"),
        ("post", "/cliente/agendamentos/1/cancelar"),
        ("post", "/cliente/agendamentos/1/pagar"),
    ],
)
@pytest.mark.parametrize("headers", [{}, {"X-Usuario-Id": ""}, {"X-Usuario-Id": "   "}])
def test_sem_usuario_retorna_401(api: TestClient, metodo: str, rota: str, headers) -> None:
    resposta = api.request(metodo, rota, headers=headers, json={})
    _assert_erro(resposta, 401)


# --- Serviços ---------------------------------------------------------------


def test_lista_apenas_servicos_ativos(api: TestClient) -> None:
    resposta = api.get("/cliente/servicos", headers=USUARIO)

    assert resposta.status_code == 200
    servicos = resposta.json()
    assert {s["id"] for s in servicos} == {1, 2}
    lavagem = next(s for s in servicos if s["id"] == 2)
    assert lavagem == {
        "id": 2,
        "nome": "Lavagem interna",
        "descricao": "Aspiração e limpeza",
        "preco": 60.0,
        "duracao_min": 30,
    }


# --- Perfil -----------------------------------------------------------------


def test_perfil_inexistente_retorna_404(api: TestClient) -> None:
    _assert_erro(api.get("/cliente/perfil", headers=USUARIO), 404)


def test_put_perfil_cria_e_depois_atualiza(api: TestClient) -> None:
    criado = _criar_perfil(api)
    assert criado["nome"] == "Maria da Silva"
    assert criado["usuario_id"] == "usuario-a"
    assert criado["placa"] == "ABC1D23"
    datetime.fromisoformat(criado["criado_em"])
    assert criado["criado_em"] == criado["atualizado_em"]

    resposta = api.put(
        "/cliente/perfil", json={"nome": "Maria S.", "telefone": ""}, headers=USUARIO
    )
    assert resposta.status_code == 200
    atualizado = resposta.json()
    assert atualizado["id"] == criado["id"]
    assert atualizado["nome"] == "Maria S."
    assert atualizado["telefone"] is None
    assert atualizado["carro"] is None
    assert atualizado["criado_em"] == criado["criado_em"]
    datetime.fromisoformat(atualizado["atualizado_em"])

    assert api.get("/cliente/perfil", headers=USUARIO).json() == atualizado


@pytest.mark.parametrize("corpo", [{}, {"nome": ""}, {"nome": "   "}, {"telefone": "1"}])
def test_put_perfil_sem_nome_retorna_422(api: TestClient, corpo: dict) -> None:
    _assert_erro(api.put("/cliente/perfil", json=corpo, headers=USUARIO), 422)


# --- Criar agendamento ------------------------------------------------------


def test_cria_agendamento_com_snapshot(api: TestClient, banco: sqlite3.Connection) -> None:
    perfil = _criar_perfil(api)
    agendamento = _criar_agendamento(api)

    assert agendamento["status"] == "agendado"
    assert agendamento["servico_id"] == 2
    assert agendamento["servico_nome"] == "Lavagem interna"
    assert agendamento["data"] == "2099-05-10"
    assert agendamento["horario"] == "09:30"
    assert agendamento["preco_snapshot"] == 60.0
    assert agendamento["duracao_snapshot_min"] == 30
    assert agendamento["cliente"]["id"] == perfil["id"]
    assert agendamento["cliente"]["placa"] == "ABC1D23"
    datetime.fromisoformat(agendamento["criado_em"])
    datetime.fromisoformat(agendamento["atualizado_em"])

    # Mudar o preço do serviço depois não altera o snapshot.
    with banco:
        banco.execute("UPDATE servicos SET preco = 99, duracao_min = 45 WHERE id = 2")
    lido = api.get(f"/cliente/agendamentos/{agendamento['id']}", headers=USUARIO).json()
    assert lido["preco_snapshot"] == 60.0
    assert lido["duracao_snapshot_min"] == 30


def test_agendar_sem_perfil_retorna_422(api: TestClient) -> None:
    resposta = api.post("/cliente/agendamentos", json={"servico_id": 2, **FUTURO}, headers=USUARIO)
    erro = _assert_erro(resposta, 422)
    assert erro["mensagem"] == "Complete seu perfil antes de agendar"


@pytest.mark.parametrize(
    "corpo",
    [
        {"servico_id": 3, **FUTURO},  # inativo
        {"servico_id": 999, **FUTURO},  # inexistente
        {"servico_id": 2, "data": "2000-01-01", "horario": "10:00"},  # passado
        {"servico_id": 2, "data": "10/05/2099", "horario": "10:00"},  # formato de data
        {"servico_id": 2, "data": "2099-02-30", "horario": "10:00"},  # data inválida
        {"servico_id": 2, "data": "2099-05-10", "horario": "9:30"},  # formato de hora
        {"servico_id": 2, "data": "2099-05-10", "horario": "25:00"},  # hora inválida
        {"data": "2099-05-10", "horario": "10:00"},  # sem serviço
    ],
)
def test_criar_agendamento_invalido_retorna_422(api: TestClient, corpo: dict) -> None:
    _criar_perfil(api)
    _assert_erro(api.post("/cliente/agendamentos", json=corpo, headers=USUARIO), 422)


# --- Listar / buscar --------------------------------------------------------


def test_lista_so_do_proprio_cliente_ordenada(api: TestClient) -> None:
    _criar_perfil(api)
    _criar_perfil(api, OUTRO_USUARIO)
    tarde = _criar_agendamento(api, data="2099-05-10", horario="15:00")
    outro_dia = _criar_agendamento(api, data="2099-04-01", horario="18:00")
    manha = _criar_agendamento(api, data="2099-05-10", horario="08:00")
    _criar_agendamento(api, OUTRO_USUARIO)

    resposta = api.get("/cliente/agendamentos", headers=USUARIO)

    assert resposta.status_code == 200
    assert [a["id"] for a in resposta.json()] == [outro_dia["id"], manha["id"], tarde["id"]]


def test_lista_vazia_sem_perfil(api: TestClient) -> None:
    resposta = api.get("/cliente/agendamentos", headers=USUARIO)
    assert resposta.status_code == 200
    assert resposta.json() == []


def test_agendamento_de_outro_cliente_retorna_404(api: TestClient) -> None:
    _criar_perfil(api)
    _criar_perfil(api, OUTRO_USUARIO)
    alheio = _criar_agendamento(api, OUTRO_USUARIO)
    base = f"/cliente/agendamentos/{alheio['id']}"

    _assert_erro(api.get(base, headers=USUARIO), 404)
    _assert_erro(api.patch(base, json=FUTURO, headers=USUARIO), 404)
    _assert_erro(api.post(f"{base}/cancelar", headers=USUARIO), 404)
    _assert_erro(api.post(f"{base}/pagar", headers=USUARIO), 404)
    # Usuário sem perfil também não enxerga.
    _assert_erro(api.get(base, headers={"X-Usuario-Id": "sem-perfil"}), 404)


def test_agendamento_inexistente_retorna_404(api: TestClient) -> None:
    _criar_perfil(api)
    erro = _assert_erro(api.get("/cliente/agendamentos/12345", headers=USUARIO), 404)
    assert erro["mensagem"] == "Agendamento não encontrado"


# --- Remarcar ---------------------------------------------------------------


def test_remarca_agendamento(api: TestClient) -> None:
    _criar_perfil(api)
    agendamento = _criar_agendamento(api)

    resposta = api.patch(
        f"/cliente/agendamentos/{agendamento['id']}",
        json={"data": "2099-06-01", "horario": "11:15"},
        headers=USUARIO,
    )

    assert resposta.status_code == 200
    remarcado = resposta.json()
    assert (remarcado["data"], remarcado["horario"]) == ("2099-06-01", "11:15")
    assert remarcado["status"] == "agendado"
    assert remarcado["criado_em"] == agendamento["criado_em"]


@pytest.mark.parametrize("status", ["confirmado", "pronto-retirada", "cancelado", "concluido"])
def test_remarcar_fora_de_agendado_retorna_409(
    api: TestClient, banco: sqlite3.Connection, status: str
) -> None:
    _criar_perfil(api)
    agendamento = _criar_agendamento(api)
    _definir_status(banco, agendamento["id"], status)

    resposta = api.patch(f"/cliente/agendamentos/{agendamento['id']}", json=FUTURO, headers=USUARIO)
    _assert_erro(resposta, 409)


def test_remarcar_para_o_passado_retorna_422(api: TestClient) -> None:
    _criar_perfil(api)
    agendamento = _criar_agendamento(api)

    resposta = api.patch(
        f"/cliente/agendamentos/{agendamento['id']}",
        json={"data": "2001-01-01", "horario": "10:00"},
        headers=USUARIO,
    )
    _assert_erro(resposta, 422)


# --- Cancelar ---------------------------------------------------------------


def test_cancela_agendado_sem_apagar(api: TestClient, banco: sqlite3.Connection) -> None:
    _criar_perfil(api)
    agendamento = _criar_agendamento(api)

    resposta = api.post(f"/cliente/agendamentos/{agendamento['id']}/cancelar", headers=USUARIO)

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "cancelado"
    linha = banco.execute(
        "SELECT status FROM agendamentos WHERE id = ?", (agendamento["id"],)
    ).fetchone()
    assert linha["status"] == "cancelado"


@pytest.mark.parametrize("status", ["confirmado", "pronto-retirada", "cancelado", "concluido"])
def test_cancelar_fora_de_agendado_retorna_409(
    api: TestClient, banco: sqlite3.Connection, status: str
) -> None:
    _criar_perfil(api)
    agendamento = _criar_agendamento(api)
    _definir_status(banco, agendamento["id"], status)

    resposta = api.post(f"/cliente/agendamentos/{agendamento['id']}/cancelar", headers=USUARIO)
    _assert_erro(resposta, 409)


# --- Pagar ------------------------------------------------------------------


def test_paga_agendamento_pronto(api: TestClient, banco: sqlite3.Connection) -> None:
    _criar_perfil(api)
    agendamento = _criar_agendamento(api)
    _definir_status(banco, agendamento["id"], "pronto-retirada")

    resposta = api.post(f"/cliente/agendamentos/{agendamento['id']}/pagar", headers=USUARIO)

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "concluido"


@pytest.mark.parametrize("status", ["agendado", "confirmado", "cancelado", "concluido"])
def test_pagar_fora_de_pronto_retorna_409(
    api: TestClient, banco: sqlite3.Connection, status: str
) -> None:
    _criar_perfil(api)
    agendamento = _criar_agendamento(api)
    _definir_status(banco, agendamento["id"], status)

    resposta = api.post(f"/cliente/agendamentos/{agendamento['id']}/pagar", headers=USUARIO)
    _assert_erro(resposta, 409)
