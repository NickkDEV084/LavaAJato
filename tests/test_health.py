from fastapi.testclient import TestClient


def test_health_retorna_ok(client: TestClient) -> None:
    resposta = client.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_health_db_retorna_ok_com_banco_de_teste(client: TestClient) -> None:
    resposta = client.get("/health/db")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "banco": "ok"}


def test_rota_inexistente_retorna_erro_no_formato_padrao(client: TestClient) -> None:
    resposta = client.get("/rota-que-nao-existe")

    assert resposta.status_code == 404
    assert resposta.json()["erro"]["codigo"] == 404
