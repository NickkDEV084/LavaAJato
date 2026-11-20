"""O front estático é servido pelo FastAPI sem tapar as rotas da API."""

import json
import os
import re
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.compartilhado.config import settings
from src.main import PASTA_FRONTEND, app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as cliente:
        yield cliente


# Páginas do front com URL limpa. /cliente e /gestao têm o mesmo nome dos prefixos da
# API (/cliente/*, /gestao/*): se alguém criar uma rota da API exatamente nesses caminhos,
# ela tapa a página, e estes testes quebram.
PAGINAS_LIMPAS = ["/cliente", "/gestao", "/agenda", "/auth"]


def _e_pagina_html(resposta) -> bool:
    return resposta.headers["content-type"].startswith("text/html") and (
        "<!DOCTYPE html>" in resposta.text
    )


@pytest.mark.parametrize("caminho", PAGINAS_LIMPAS)
def test_paginas_abrem_sem_extensao_html(client: TestClient, caminho: str) -> None:
    resposta = client.get(caminho, follow_redirects=False)

    assert resposta.status_code == 200
    assert _e_pagina_html(resposta)


@pytest.mark.parametrize(
    ("caminho", "arquivo"),
    [("/cliente", "cliente.html"), ("/gestao", "gestao.html"), ("/agenda", "agenda.html")],
)
def test_url_limpa_entrega_o_arquivo_html_correspondente(
    client: TestClient, caminho: str, arquivo: str
) -> None:
    resposta = client.get(caminho, follow_redirects=False)

    assert resposta.content == (PASTA_FRONTEND / arquivo).read_bytes()


@pytest.mark.parametrize("caminho", ["/cliente", "/gestao"])
def test_cliente_e_gestao_sao_paginas_do_front_e_nao_rotas_da_api(
    client: TestClient, caminho: str
) -> None:
    resposta = client.get(caminho, follow_redirects=False)

    assert resposta.status_code == 200
    assert not resposta.headers["content-type"].startswith("application/json")
    assert caminho not in app.openapi()["paths"]


@pytest.mark.parametrize(
    ("antigo", "novo"),
    [
        ("/agenda.html", "/agenda"),
        ("/cliente.html", "/cliente"),
        ("/gestao.html", "/gestao"),
        ("/auth.html", "/auth"),
        ("/index.html", "/"),
    ],
)
def test_pagina_html_redireciona_301_para_url_limpa(
    client: TestClient, antigo: str, novo: str
) -> None:
    resposta = client.get(antigo, follow_redirects=False)

    assert resposta.status_code == 301
    assert resposta.headers["location"] == novo


def test_redirect_301_mantem_a_query_string(client: TestClient) -> None:
    resposta = client.get("/auth.html?next=cliente.html", follow_redirects=False)

    assert resposta.status_code == 301
    assert resposta.headers["location"] == "/auth?next=cliente.html"


def test_link_antigo_com_html_chega_na_pagina_seguindo_o_redirect(client: TestClient) -> None:
    resposta = client.get("/agenda.html")

    assert resposta.status_code == 200
    assert str(resposta.url).endswith("/agenda")
    assert _e_pagina_html(resposta)


def test_raiz_abre_o_index_que_redireciona_para_cliente(client: TestClient) -> None:
    resposta = client.get("/", follow_redirects=False)

    assert resposta.status_code == 200
    assert resposta.content == (PASTA_FRONTEND / "index.html").read_bytes()
    assert 'url=cliente"' in resposta.text


def test_links_internos_do_front_nao_usam_extensao_html() -> None:
    arquivos = [*PASTA_FRONTEND.glob("*.html"), *PASTA_FRONTEND.rglob("*.js")]
    com_html = [
        f"{arquivo.relative_to(PASTA_FRONTEND)}: {linha.strip()}"
        for arquivo in arquivos
        for linha in arquivo.read_text(encoding="utf-8").splitlines()
        if re.search(r'(href=|href:|location\.\w+\(|url=)\s*"?[\w./-]*\.html', linha)
    ]

    assert com_html == []


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


def test_pagina_inexistente_sem_extensao_retorna_404_no_formato_padrao(
    client: TestClient,
) -> None:
    resposta = client.get("/pagina-que-nao-existe", follow_redirects=False)

    assert resposta.status_code == 404
    assert resposta.json()["erro"]["codigo"] == 404


def test_arquivos_com_outra_extensao_nao_ganham_fallback_html(client: TestClient) -> None:
    resposta = client.get("/js/core/config", follow_redirects=False)

    assert resposta.status_code == 404


# --- auth-navigation.js (roda o módulo de verdade no Node) ---------------------------

NODE = shutil.which("node")
AUTH_NAVIGATION = PASTA_FRONTEND / "js" / "features" / "auth" / "auth-navigation.js"
SCRIPT_DESTINO_POS_LOGIN = """
globalThis.window = { location: { search: process.env.BUSCA } };
const modulo = await import(process.env.MODULO);
console.log(JSON.stringify(modulo.getPostAuthDestination()));
"""


def _destino_pos_login(busca: str) -> str:
    resultado = subprocess.run(
        [NODE, "--input-type=module", "-e", SCRIPT_DESTINO_POS_LOGIN],
        env={**os.environ, "BUSCA": busca, "MODULO": AUTH_NAVIGATION.as_uri()},
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    return json.loads(resultado.stdout)


@pytest.mark.skipif(NODE is None, reason="Node.js não está instalado")
@pytest.mark.parametrize(
    ("busca", "destino"),
    [
        ("?next=cliente", "cliente"),
        ("?next=cliente.html", "cliente"),  # link antigo continua funcionando
        ("", "gestao"),
        ("?next=gestao.html", "gestao"),
        ("?next=https://site-externo.example", "gestao"),
    ],
)
def test_destino_pos_login_usa_urls_limpas(busca: str, destino: str) -> None:
    assert _destino_pos_login(busca) == destino
