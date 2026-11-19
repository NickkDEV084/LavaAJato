"""A checagem de "data e hora futuras" usa o fuso TIMEZONE, não o relógio da máquina.

O "agora" é congelado com monkeypatch em regras.agora_utc, então o resultado não
depende do relógio nem do fuso configurado no computador que roda os testes.
"""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from src.agenda_fila import regras
from src.compartilhado.config import Settings, settings

USUARIO = {"X-Usuario-Id": "usuario-fuso"}

# 02:00 em UTC = 23:00 do dia anterior em America/Recife (UTC-3, sem horário de verão).
AGORA_FIXO_UTC = datetime(2030, 1, 1, 2, 0, tzinfo=UTC)


@pytest.fixture
def relogio_congelado(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(regras, "agora_utc", lambda: AGORA_FIXO_UTC)


@pytest.fixture
def api_com_perfil(api: TestClient, relogio_congelado: None) -> TestClient:
    resposta = api.put("/cliente/perfil", json={"nome": "Cliente Fuso"}, headers=USUARIO)
    assert resposta.status_code == 200
    return api


def _agendar(api: TestClient, data: str, horario: str):
    return api.post(
        "/cliente/agendamentos",
        json={"servico_id": 1, "data": data, "horario": horario},
        headers=USUARIO,
    )


def test_fuso_padrao_e_america_recife() -> None:
    assert Settings.model_fields["TIMEZONE"].default == "America/Recife"


def test_fuso_invalido_e_rejeitado_na_configuracao() -> None:
    with pytest.raises(ValueError, match="Fuso horário inválido"):
        Settings(DATABASE_URL="sqlite://", SECRET_KEY="x", TIMEZONE="Lugar/Inexistente")


def test_horario_futuro_em_recife_e_aceito_mesmo_ja_passado_em_utc(
    api_com_perfil: TestClient,
) -> None:
    # Em Recife são 23:00 de 31/12/2029, então 23:30 ainda é futuro.
    # Se a data fosse lida como UTC (já 01/01/2030), seria rejeitada.
    resposta = _agendar(api_com_perfil, "2029-12-31", "23:30")
    assert resposta.status_code == 201, resposta.json()


def test_horario_ja_passado_em_recife_e_rejeitado(api_com_perfil: TestClient) -> None:
    resposta = _agendar(api_com_perfil, "2029-12-31", "22:59")
    assert resposta.status_code == 422
    assert resposta.json()["erro"]["mensagem"] == "Escolha uma data e um horário futuros"


def test_exatamente_agora_em_recife_e_rejeitado(api_com_perfil: TestClient) -> None:
    assert _agendar(api_com_perfil, "2029-12-31", "23:00").status_code == 422
    assert _agendar(api_com_perfil, "2029-12-31", "23:01").status_code == 201


def test_remarcacao_tambem_usa_o_fuso(api_com_perfil: TestClient) -> None:
    criado = _agendar(api_com_perfil, "2030-01-05", "10:00").json()
    rota = f"/cliente/agendamentos/{criado['id']}"

    passado = {"data": "2029-12-31", "horario": "22:00"}
    futuro = {"data": "2029-12-31", "horario": "23:45"}
    assert api_com_perfil.patch(rota, json=passado, headers=USUARIO).status_code == 422
    assert api_com_perfil.patch(rota, json=futuro, headers=USUARIO).status_code == 200


def test_fuso_configuravel_muda_o_resultado(
    api_com_perfil: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Mesmo instante, em Tóquio (UTC+9) já são 11:00 de 01/01/2030.
    monkeypatch.setattr(settings, "TIMEZONE", "Asia/Tokyo")

    assert _agendar(api_com_perfil, "2029-12-31", "23:30").status_code == 422
    assert _agendar(api_com_perfil, "2030-01-01", "11:30").status_code == 201
