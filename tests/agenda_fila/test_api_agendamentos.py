"""API REST /api/agendamentos: CRUD em JSON, validação (400), 404 e proteção da escrita."""

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from src.agenda_fila.banco import SERVICOS_INICIAIS, inicializar_banco
from src.compartilhado.config import settings

CHAVE = "chave-de-gestao-de-teste"
GESTAO = {"X-Chave-Gestao": CHAVE}
FUTURO = {"data": "2099-05-10", "horario": "09:30"}
CAMPOS_SAIDA = {
    "id", "cliente_id", "nome_cliente", "telefone_cliente", "carro", "marca", "placa",
    "servico_id", "servico", "data", "horario", "status", "preco", "duracao_min",
    "criado_em", "atualizado_em",
}  # fmt: skip


@pytest.fixture(autouse=True)
def chave_configurada(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "GESTAO_CHAVE", SecretStr(CHAVE))


@pytest.fixture
def cliente_id(api: TestClient) -> int:
    corpo = {"nome": "Ana", "telefone": "81999990000", "carro": "Onix", "placa": "ABC1D23"}
    resposta = api.put("/cliente/perfil", json=corpo, headers={"X-Usuario-Id": "u-api"})
    assert resposta.status_code == 200
    return resposta.json()["id"]


def _criar(api: TestClient, cliente_id: int, **extra) -> dict:
    corpo = {"cliente_id": cliente_id, "servico_id": 2, **FUTURO, **extra}
    resposta = api.post("/api/agendamentos", json=corpo, headers=GESTAO)
    assert resposta.status_code == 201, resposta.json()
    return resposta.json()


def _erro(resposta, codigo: int) -> dict:
    assert resposta.status_code == codigo, resposta.text
    assert resposta.headers["content-type"].startswith("application/json")
    return resposta.json()["erro"]


def test_ciclo_completo_criar_listar_editar_apagar(
    api: TestClient, cliente_id: int, banco: sqlite3.Connection
) -> None:
    criado = _criar(api, cliente_id)
    assert set(criado) == CAMPOS_SAIDA
    assert criado["nome_cliente"] == "Ana"
    assert criado["servico"] == "Lavagem interna"
    assert criado["status"] == "agendado"
    assert criado["preco"] == 60.0

    lista = api.get("/api/agendamentos")
    assert lista.status_code == 200
    assert [item["id"] for item in lista.json()] == [criado["id"]]
    assert api.get(f"/api/agendamentos/{criado['id']}").json() == criado

    corpo = {"cliente_id": cliente_id, "servico_id": 1, "data": "2099-06-01",
             "horario": "10:00", "status": "confirmado"}  # fmt: skip
    editado = api.put(f"/api/agendamentos/{criado['id']}", json=corpo, headers=GESTAO)
    assert editado.status_code == 200, editado.json()
    assert editado.json()["status"] == "confirmado"
    assert editado.json()["servico"] == "Higienização interna"
    assert editado.json()["preco"] == 40.0
    assert editado.json()["data"] == "2099-06-01"

    apagado = api.delete(f"/api/agendamentos/{criado['id']}", headers=GESTAO)
    assert apagado.status_code == 200
    assert apagado.json()["agendamento"]["id"] == criado["id"]
    assert banco.execute("SELECT COUNT(*) FROM agendamentos").fetchone()[0] == 0
    assert api.get("/api/agendamentos").json() == []


def test_filtro_por_status(api: TestClient, cliente_id: int) -> None:
    _criar(api, cliente_id)
    assert len(api.get("/api/agendamentos?status=agendado").json()) == 1
    assert api.get("/api/agendamentos?status=cancelado").json() == []
    _erro(api.get("/api/agendamentos?status=invalido"), 400)


@pytest.mark.parametrize(
    ("metodo", "rota"),
    [("get", "/api/agendamentos/999"), ("put", "/api/agendamentos/999"),
     ("delete", "/api/agendamentos/999")],
)  # fmt: skip
def test_inexistente_retorna_404(api: TestClient, cliente_id: int, metodo: str, rota: str) -> None:
    corpo = {"cliente_id": cliente_id, "servico_id": 1, **FUTURO, "status": "agendado"}
    kwargs = {"json": corpo} if metodo == "put" else {}
    erro = _erro(api.request(metodo, rota, headers=GESTAO, **kwargs), 404)
    assert erro["mensagem"] == "Agendamento não encontrado"


@pytest.mark.parametrize(
    "corpo",
    [
        {},
        {"cliente_id": 1, "servico_id": 2, "data": "10/05/2099", "horario": "09:30"},
        {"cliente_id": 1, "servico_id": 2, "data": "2099-05-10", "horario": "9h"},
        {"cliente_id": 1, "servico_id": "abc", **FUTURO},
        {"cliente_id": 0, "servico_id": 2, **FUTURO},
    ],
)
def test_post_invalido_retorna_400(api: TestClient, cliente_id: int, corpo: dict) -> None:
    erro = _erro(api.post("/api/agendamentos", json=corpo, headers=GESTAO), 400)
    assert erro["mensagem"] == "Dados inválidos na requisição"
    assert erro["detalhes"]


def test_json_malformado_retorna_400(api: TestClient) -> None:
    resposta = api.post(
        "/api/agendamentos",
        content="{nao é json",
        headers={**GESTAO, "Content-Type": "application/json"},
    )
    _erro(resposta, 400)


def test_referencias_e_horario_invalidos_retornam_400(api: TestClient, cliente_id: int) -> None:
    rota = "/api/agendamentos"
    assert (
        "Cliente 999"
        in _erro(
            api.post(rota, json={"cliente_id": 999, "servico_id": 2, **FUTURO}, headers=GESTAO), 400
        )["mensagem"]
    )
    assert "Serviço 999" in _erro(
        api.post(rota, json={"cliente_id": cliente_id, "servico_id": 999, **FUTURO},
                 headers=GESTAO), 400,
    )["mensagem"]  # fmt: skip
    passado = {"cliente_id": cliente_id, "servico_id": 2, "data": "2000-01-01", "horario": "09:00"}
    _erro(api.post(rota, json=passado, headers=GESTAO), 400)


def test_put_status_invalido_retorna_400(api: TestClient, cliente_id: int) -> None:
    criado = _criar(api, cliente_id)
    corpo = {"cliente_id": cliente_id, "servico_id": 2, **FUTURO, "status": "voando"}
    _erro(api.put(f"/api/agendamentos/{criado['id']}", json=corpo, headers=GESTAO), 400)


def test_leitura_e_aberta_e_escrita_exige_chave(api: TestClient, cliente_id: int) -> None:
    criado = _criar(api, cliente_id)
    assert api.get("/api/agendamentos").status_code == 200
    assert api.get(f"/api/agendamentos/{criado['id']}").status_code == 200

    corpo = {"cliente_id": cliente_id, "servico_id": 2, **FUTURO}
    _erro(api.post("/api/agendamentos", json=corpo), 401)
    _erro(api.post("/api/agendamentos", json=corpo, headers={"X-Chave-Gestao": "errada"}), 403)
    _erro(api.put(f"/api/agendamentos/{criado['id']}", json={**corpo, "status": "agendado"}), 401)
    _erro(api.delete(f"/api/agendamentos/{criado['id']}"), 401)


def test_indice_api_lista_as_rotas(api: TestClient) -> None:
    resposta = api.get("/api")
    assert resposta.status_code == 200
    rotas = {(rota["metodo"], rota["caminho"]) for rota in resposta.json()["rotas"]}
    for esperada in [
        ("GET", "/api/agendamentos"),
        ("GET", "/api/agendamentos/{agendamento_id}"),
        ("POST", "/api/agendamentos"),
        ("PUT", "/api/agendamentos/{agendamento_id}"),
        ("DELETE", "/api/agendamentos/{agendamento_id}"),
    ]:
        assert esperada in rotas
    assert resposta.json()["documentacao"]["swagger"].endswith("/docs")


def test_inicializar_banco_cria_arquivo_tabelas_e_servicos(tmp_path: Path) -> None:
    caminho = tmp_path / "pasta" / "nova" / "lavaajato.db"
    inicializar_banco(caminho)
    inicializar_banco(caminho)  # idempotente: não duplica nada

    conexao = sqlite3.connect(caminho)
    try:
        consulta = "SELECT name FROM sqlite_master WHERE type = 'table'"
        tabelas = {linha[0] for linha in conexao.execute(consulta)}
        assert {"clientes", "servicos", "agendamentos"} <= tabelas
        assert conexao.execute("SELECT COUNT(*) FROM servicos").fetchone()[0] == len(
            SERVICOS_INICIAIS
        )
    finally:
        conexao.close()


def test_inicializar_banco_nao_mexe_em_banco_existente(caminho_banco: Path) -> None:
    inicializar_banco(caminho_banco)
    conexao = sqlite3.connect(caminho_banco)
    try:
        nomes = [linha[0] for linha in conexao.execute("SELECT nome FROM servicos ORDER BY id")]
    finally:
        conexao.close()
    assert nomes == ["Higienização interna", "Lavagem interna", "Polimento (desativado)"]
