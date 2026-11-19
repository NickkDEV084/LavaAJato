"""O front estático é servido pelo FastAPI sem tapar as rotas da API."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.compartilhado.config import settings
from src.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as cliente:
        yield cliente


@pytest.mark.parametrize("caminho", ["/", "/cliente.html", "/agenda.html", "/gestao.html"])
def test_paginas_do_front_sao_servidas_como_html(client: TestClient, caminho: str) -> None:
    resposta = client.get(caminho)

    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("text/html")
    assert "<!DOCTYPE html>" in resposta.text


def test_raiz_serve_o_index_que_redireciona_para_cliente(client: TestClient) -> None:
    resposta = client.get("/")

    assert "url=cliente.html" in resposta.text


def test_config_js_e_servido_como_javascript(client: TestClient) -> None:
    resposta = client.get("/js/core/config.js")

    assert resposta.status_code == 200
    assert "javascript" in resposta.headers["content-type"]
    assert "API_BASE_URL" in resposta.text


def test_health_db_continua_respondendo_json(
    client: TestClient, caminho_banco: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "SQLITE_PATH", caminho_banco)

    resposta = client.get("/health/db")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "banco": "ok"}


def test_docs_e_openapi_continuam_funcionando(client: TestClient) -> None:
    docs = client.get("/docs")
    openapi = client.get("/openapi.json")

    assert docs.status_code == 200
    assert "swagger" in docs.text.lower()
    assert openapi.status_code == 200
    assert "/cliente/servicos" in openapi.json()["paths"]


def test_rotas_da_api_nao_sao_tapadas_pelo_front(
    client: TestClient, caminho_banco: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "SQLITE_PATH", caminho_banco)

    resposta = client.get("/cliente/servicos", headers={"X-Usuario-Id": "usuario-teste"})

    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("application/json")


def test_arquivo_inexistente_retorna_404_no_formato_padrao(client: TestClient) -> None:
    resposta = client.get("/pagina-que-nao-existe.html")

    assert resposta.status_code == 404
    assert resposta.json()["erro"]["codigo"] == 404
