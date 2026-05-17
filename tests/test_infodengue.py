from unittest.mock import patch, MagicMock
from src.ingestion.infodengue import (
    fetch_alertas,
    coletar_municipio,
    coletar_todos,
    MUNICIPIOS,
    DOENCAS,
)

MOCK_RESPONSE = [
    {
        "data_iniSE": "2024-01-01",
        "SE": 202401,
        "casos_est": 100,
        "casos": 80,
        "nivel": 2,
    }
]


def make_mock(data=MOCK_RESPONSE):
    mock = MagicMock()
    mock.json.return_value = data
    mock.raise_for_status.return_value = None
    return mock


def test_municipios_definidos():
    assert "Maringá" in MUNICIPIOS
    assert len(MUNICIPIOS) >= 5


def test_doencas_definidas():
    assert "dengue" in DOENCAS
    assert "chikungunya" in DOENCAS
    assert "zika" in DOENCAS


@patch("src.ingestion.infodengue.httpx.Client")
def test_fetch_alertas(mock_client):
    mock_client.return_value.__enter__.return_value.get.return_value = make_mock()
    result = fetch_alertas(4115200, "dengue", 1, 10, 2024, 2024)
    assert isinstance(result, list)
    assert len(result) == 1


@patch("src.ingestion.infodengue.httpx.Client")
def test_coletar_municipio_adiciona_campos(mock_client):
    mock_client.return_value.__enter__.return_value.get.return_value = make_mock()
    result = coletar_municipio("Maringá", 4115200, 2024, 2024)
    assert all("municipio" in r for r in result)
    assert all("doenca" in r for r in result)
    assert all("geocodigo" in r for r in result)


@patch("src.ingestion.infodengue.httpx.Client")
def test_coletar_todos_retorna_lista(mock_client):
    mock_client.return_value.__enter__.return_value.get.return_value = make_mock()
    result = coletar_todos(2024, 2024)
    assert isinstance(result, list)
    assert len(result) > 0