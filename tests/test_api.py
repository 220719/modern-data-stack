from fastapi.testclient import TestClient
from unittest.mock import patch
import pandas as pd
from src.api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_municipios():
    response = client.get("/municipios")
    assert response.status_code == 200
    data = response.json()
    assert "municipios" in data
    assert "Maringá" in data["municipios"]
    assert len(data["municipios"]) == 31


def test_doencas():
    response = client.get("/doencas")
    assert response.status_code == 200
    data = response.json()
    assert "dengue" in data["doencas"]
    assert "chikungunya" in data["doencas"]
    assert "zika" in data["doencas"]


@patch("src.api.main.query")
def test_resumo(mock_query):
    mock_query.return_value = pd.DataFrame([
        {"doenca": "dengue", "municipios": 31, "registros": 9703, "media_casos": 527.6, "max_casos": 85389.0},
        {"doenca": "chikungunya", "municipios": 31, "registros": 9703, "media_casos": 24.9, "max_casos": 2340.0},
        {"doenca": "zika", "municipios": 31, "registros": 6665, "media_casos": 2.9, "max_casos": 149.0},
    ])
    response = client.get("/resumo")
    assert response.status_code == 200
    data = response.json()
    assert "resumo" in data
    assert len(data["resumo"]) == 3


@patch("src.api.main.query")
def test_historico_valido(mock_query):
    mock_query.return_value = pd.DataFrame([
        {"ano": 2024, "semana": 1, "semana_epidemiologica": 202401,
         "data_inicio_se": "2024-01-01", "casos_estimados": 100.0,
         "casos_confirmados": 80.0, "nivel_alerta": 2, "media_movel_4s": 90.0},
    ])
    response = client.get("/historico/Maringá/dengue?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["municipio"] == "Maringá"
    assert data["doenca"] == "dengue"
    assert len(data["registros"]) <= 10


def test_historico_municipio_invalido():
    response = client.get("/historico/CidadeInexistente/dengue")
    assert response.status_code == 404


def test_historico_doenca_invalida():
    response = client.get("/historico/Maringá/malaria")
    assert response.status_code == 404


@patch("src.api.main.query")
def test_alertas(mock_query):
    mock_query.return_value = pd.DataFrame([
        {"municipio": "Maringá", "doenca": "dengue", "ano": 2024,
         "semana": 10, "casos_estimados": 500.0, "nivel_alerta": 3},
    ])
    response = client.get("/alertas")
    assert response.status_code == 200
    data = response.json()
    assert "alertas" in data
    assert "total" in data


@patch("src.api.main.query")
def test_ranking(mock_query):
    mock_query.return_value = pd.DataFrame([
        {"municipio": "São Paulo", "media_semanal": 1000.0, "total_casos": 50000.0, "nivel_max": 4},
        {"municipio": "Maringá", "media_semanal": 500.0, "total_casos": 25000.0, "nivel_max": 3},
    ])
    response = client.get("/ranking/dengue?ano=2024")
    assert response.status_code == 200
    data = response.json()
    assert data["doenca"] == "dengue"
    assert len(data["ranking"]) > 0
    assert data["ranking"][0]["total_casos"] >= data["ranking"][-1]["total_casos"]