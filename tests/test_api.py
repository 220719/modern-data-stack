from fastapi.testclient import TestClient
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


def test_resumo():
    response = client.get("/resumo")
    assert response.status_code == 200
    data = response.json()
    assert "resumo" in data
    assert len(data["resumo"]) == 3


def test_historico_valido():
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


def test_alertas():
    response = client.get("/alertas")
    assert response.status_code == 200
    data = response.json()
    assert "alertas" in data
    assert "total" in data


def test_ranking():
    response = client.get("/ranking/dengue?ano=2024")
    assert response.status_code == 200
    data = response.json()
    assert data["doenca"] == "dengue"
    assert len(data["ranking"]) > 0
    assert data["ranking"][0]["total_casos"] >= data["ranking"][-1]["total_casos"]