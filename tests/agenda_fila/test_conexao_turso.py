"""Modo Turso da camada de conexão, sem rede: o driver do Turso é trocado por um falso.

O driver falso é um sqlite3 sem row_factory (devolve tuplas, como o turso_serverless)
num arquivo temporário. Assim os testes conferem o adaptador (linhas por nome,
lastrowid, rowcount, commit/rollback, erros) e a API inteira no modo Turso, sem
depender do Turso de verdade.
"""

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
import turso_serverless
from fastapi.testclient import TestClient
from pydantic import SecretStr

from src.agenda_fila import conexao as modulo_conexao
from src.agenda_fila.banco import SERVICOS_INICIAIS, inicializar_banco
from src.agenda_fila.conexao import ConexaoTurso, Linha, abrir_conexao
from src.compartilhado.config import settings
from src.main import app

URL_FALSA = "libsql://banco-falso.turso.io"
TOKEN_FALSO = "token-falso"
USUARIO = {"X-Usuario-Id": "u-turso"}


@pytest.fixture
def arquivo_turso(tmp_path: Path) -> Path:
    return tmp_path / "turso_falso.db"


@pytest.fixture
def chamadas_turso(
    arquivo_turso: Path, monkeypatch: pytest.MonkeyPatch
) -> list[tuple[str, str | None]]:
    """Liga o modo Turso com um driver falso e registra cada connect(url, auth_token)."""
    chamadas: list[tuple[str, str | None]] = []

    def _connect(url: str, *, auth_token: str | None = None, **_: object) -> sqlite3.Connection:
        chamadas.append((url, auth_token))
        return sqlite3.connect(arquivo_turso, check_same_thread=False)

    monkeypatch.setattr(modulo_conexao.turso_serverless, "connect", _connect)
    monkeypatch.setattr(settings, "TURSO_DATABASE_URL", URL_FALSA)
    monkeypatch.setattr(settings, "TURSO_AUTH_TOKEN", SecretStr(TOKEN_FALSO))
    return chamadas


@pytest.fixture
def api_turso(chamadas_turso: list) -> Iterator[TestClient]:
    """API sem nenhum override de conexão: tudo passa por abrir_conexao() no modo Turso."""
    with TestClient(app) as cliente:
        yield cliente


class _DriverQuebrado:
    def __init__(self, erro: Exception) -> None:
        self._erro = erro

    def execute(self, *_: object) -> None:
        raise self._erro

    def close(self) -> None:
        pass


# --- Escolha do modo ---------------------------------------------------------


def test_testes_nunca_usam_o_turso() -> None:
    assert not settings.usa_turso


@pytest.mark.parametrize(
    ("url", "token"),
    [(None, None), ("", ""), (URL_FALSA, None), (URL_FALSA, ""), (None, TOKEN_FALSO)],
)
def test_turso_so_liga_com_as_duas_variaveis(
    monkeypatch: pytest.MonkeyPatch, url: str | None, token: str | None
) -> None:
    monkeypatch.setattr(settings, "TURSO_DATABASE_URL", url)
    monkeypatch.setattr(settings, "TURSO_AUTH_TOKEN", None if token is None else SecretStr(token))
    assert not settings.usa_turso


def test_sem_turso_abre_o_arquivo_sqlite(
    caminho_banco: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "SQLITE_PATH", caminho_banco)
    conexao = abrir_conexao()
    try:
        assert isinstance(conexao, sqlite3.Connection)
    finally:
        conexao.close()


def test_com_turso_abre_o_turso_com_url_token_e_foreign_keys(chamadas_turso: list) -> None:
    conexao = abrir_conexao()
    try:
        assert isinstance(conexao, ConexaoTurso)
        assert chamadas_turso == [(URL_FALSA, TOKEN_FALSO)]
        assert conexao.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        conexao.close()


def test_caminho_explicito_ignora_o_turso(chamadas_turso: list, caminho_banco: Path) -> None:
    conexao = abrir_conexao(caminho_banco.as_uri())
    try:
        assert isinstance(conexao, sqlite3.Connection)
        assert chamadas_turso == []
    finally:
        conexao.close()


# --- Adaptador -----------------------------------------------------------------


def test_linha_tem_o_acesso_do_sqlite3_row(chamadas_turso: list) -> None:
    conexao = abrir_conexao()
    try:
        linha = conexao.execute("SELECT 7 AS id, 'Ana' AS nome").fetchone()
    finally:
        conexao.close()

    assert isinstance(linha, Linha)
    assert linha["id"] == 7
    assert linha["NOME"] == "Ana"  # sem diferenciar maiúsculas, como o sqlite3.Row
    assert linha[1] == "Ana"
    assert linha.keys() == ["id", "nome"]
    assert dict(linha) == {"id": 7, "nome": "Ana"}
    assert len(linha) == 2
    identificador, nome = linha
    assert (identificador, nome) == (7, "Ana")
    with pytest.raises(IndexError):
        linha["nao_existe"]


def test_lastrowid_e_rowcount(chamadas_turso: list) -> None:
    inicializar_banco()
    conexao = abrir_conexao()
    try:
        with conexao:
            cursor = conexao.execute(
                "INSERT INTO servicos (nome, preco, duracao_min) VALUES (?, ?, ?)",
                ("Teste", 10.0, 5),
            )
        novo_id = cursor.lastrowid
        assert novo_id == len(SERVICOS_INICIAIS) + 1

        with conexao:
            cursor = conexao.execute("DELETE FROM servicos WHERE id = ?", (novo_id,))
        assert cursor.rowcount == 1
        with conexao:
            cursor = conexao.execute("DELETE FROM servicos WHERE id = ?", (novo_id,))
        assert cursor.rowcount == 0
    finally:
        conexao.close()


def test_commit_e_rollback_ficam_gravados_no_banco(
    chamadas_turso: list, arquivo_turso: Path
) -> None:
    inicializar_banco()
    conexao = abrir_conexao()
    try:
        with pytest.raises(RuntimeError), conexao:
            conexao.execute("UPDATE servicos SET nome = 'Desfeito' WHERE id = 1")
            raise RuntimeError("falha no meio da transação")
        with conexao:
            conexao.execute("UPDATE servicos SET nome = 'Gravado' WHERE id = 2")
    finally:
        conexao.close()

    direto = sqlite3.connect(arquivo_turso)
    try:
        nomes = dict(direto.execute("SELECT id, nome FROM servicos WHERE id IN (1, 2)"))
    finally:
        direto.close()
    assert nomes == {1: SERVICOS_INICIAIS[0][0], 2: "Gravado"}


@pytest.mark.parametrize(
    ("erro_do_driver", "erro_esperado"),
    [
        (turso_serverless.IntegrityError("UNIQUE constraint failed"), sqlite3.IntegrityError),
        (turso_serverless.ProgrammingError("conexão fechada"), sqlite3.ProgrammingError),
        (turso_serverless.OperationalError("no such table"), sqlite3.OperationalError),
        (RuntimeError("request failed: timed out"), sqlite3.OperationalError),
    ],
)
def test_erros_do_driver_viram_erros_do_sqlite3(
    erro_do_driver: Exception, erro_esperado: type[sqlite3.Error]
) -> None:
    conexao = ConexaoTurso(_DriverQuebrado(erro_do_driver))
    with pytest.raises(erro_esperado):
        conexao.execute("SELECT 1")


# --- API inteira no modo Turso ---------------------------------------------------


def test_subida_cria_tabelas_e_servicos_sem_duplicar(
    api_turso: TestClient, chamadas_turso: list, arquivo_turso: Path
) -> None:
    assert chamadas_turso, "a subida do app deveria ter aberto o Turso"
    inicializar_banco()  # segunda subida: não duplica nem apaga nada

    direto = sqlite3.connect(arquivo_turso)
    try:
        total = direto.execute("SELECT COUNT(*) FROM servicos").fetchone()[0]
    finally:
        direto.close()
    assert total == len(SERVICOS_INICIAIS)
    assert api_turso.get("/health/db").json() == {"status": "ok", "banco": "ok"}


def test_ciclo_completo_da_api_no_modo_turso(api_turso: TestClient) -> None:
    perfil = {"nome": "Ana", "telefone": "81999990000", "carro": "Onix", "placa": "ABC1D23"}
    resposta = api_turso.put("/cliente/perfil", json=perfil, headers=USUARIO)
    assert resposta.status_code == 200, resposta.text
    cliente_id = resposta.json()["id"]

    corpo = {"cliente_id": cliente_id, "servico_id": 2, "data": "2099-05-10", "horario": "09:30"}
    criado = api_turso.post("/api/agendamentos", json=corpo)
    assert criado.status_code == 201, criado.text
    agendamento = criado.json()
    assert agendamento["servico"] == "Lavagem interna"
    assert agendamento["preco"] == 60.0

    assert [item["id"] for item in api_turso.get("/api/agendamentos").json()] == [agendamento["id"]]
    assert api_turso.get("/cliente/agendamentos", headers=USUARIO).status_code == 200

    corpo_editado = {**corpo, "servico_id": 1, "status": "confirmado"}
    editado = api_turso.put(f"/api/agendamentos/{agendamento['id']}", json=corpo_editado)
    assert editado.status_code == 200, editado.text
    assert editado.json()["status"] == "confirmado"

    apagado = api_turso.delete(f"/api/agendamentos/{agendamento['id']}")
    assert apagado.status_code == 200
    assert api_turso.get("/api/agendamentos").json() == []


def test_falha_do_turso_vira_503_no_health_e_500_generico_na_api(
    api_turso: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _connect_quebrado(*_: object, **__: object) -> _DriverQuebrado:
        return _DriverQuebrado(RuntimeError("detalhe-interno-do-turso"))

    monkeypatch.setattr(modulo_conexao.turso_serverless, "connect", _connect_quebrado)

    saude = api_turso.get("/health/db")
    assert saude.status_code == 503
    assert saude.json() == {"status": "erro", "banco": "indisponivel"}

    resposta = api_turso.get("/api/agendamentos")
    assert resposta.status_code == 500
    assert resposta.json()["erro"]["mensagem"] == "Erro ao acessar o banco de dados"
    assert "detalhe-interno-do-turso" not in resposta.text
