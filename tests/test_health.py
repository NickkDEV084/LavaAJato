import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.agenda_fila.conexao import get_conexao
from src.compartilhado.config import settings
from src.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()


def test_health_retorna_ok(client: TestClient) -> None:
    resposta = client.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_health_db_retorna_ok_com_banco_valido(
    client: TestClient, caminho_banco: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "SQLITE_PATH", caminho_banco)

    resposta = client.get("/health/db")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "banco": "ok"}


def test_health_db_retorna_503_com_arquivo_inexistente(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inexistente = tmp_path / "nao_existe.db"
    monkeypatch.setattr(settings, "SQLITE_PATH", inexistente)

    resposta = client.get("/health/db")

    assert resposta.status_code == 503
    assert resposta.json() == {"status": "erro", "banco": "indisponivel"}
    # mode=rw: a checagem não pode criar um banco vazio no lugar.
    assert not inexistente.exists()


def test_health_db_retorna_503_sem_as_tabelas(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vazio = tmp_path / "vazio.db"
    sqlite3.connect(vazio).close()
    monkeypatch.setattr(settings, "SQLITE_PATH", vazio)

    resposta = client.get("/health/db")

    assert resposta.status_code == 503
    assert resposta.json() == {"status": "erro", "banco": "indisponivel"}


def test_erro_do_sqlite_vira_500_sem_vazar_o_detalhe(client: TestClient) -> None:
    def _conexao_quebrada() -> Iterator[sqlite3.Connection]:
        raise sqlite3.OperationalError("detalhe-interno-do-banco")
        yield  # pragma: no cover

    app.dependency_overrides[get_conexao] = _conexao_quebrada

    resposta = client.get("/cliente/servicos", headers={"X-Usuario-Id": "usuario-teste"})

    assert resposta.status_code == 500
    assert resposta.json()["erro"]["mensagem"] == "Erro ao acessar o banco de dados"
    assert "detalhe-interno-do-banco" not in resposta.text


def test_rota_inexistente_retorna_erro_no_formato_padrao(client: TestClient) -> None:
    resposta = client.get("/rota-que-nao-existe")

    assert resposta.status_code == 404
    assert resposta.json()["erro"]["codigo"] == 404
