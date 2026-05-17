import pytest
import duckdb
from unittest.mock import patch
from pathlib import Path
from src.storage.database import (
    get_connection,
    inicializar_banco,
    inserir_casos,
    inserir_clima,
    query,
)

CASOS_MOCK = [
    {
        "municipio": "Maringá",
        "geocodigo": 4115200,
        "doenca": "dengue",
        "data_iniSE": "2024-01-01",
        "SE": 202401,
        "casos_est": 100.0,
        "casos": 80.0,
        "nivel": 2,
    }
]

CLIMA_MOCK = [
    {
        "municipio": "Maringá",
        "data": "2024-01-01",
        "temperature_2m_max": 32.1,
        "temperature_2m_min": 22.0,
        "temperature_2m_mean": 27.0,
        "precipitation_sum": 0.0,
        "relative_humidity_2m_max": 85.0,
        "relative_humidity_2m_min": 60.0,
    }
]


@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    db_path = tmp_path / "test.duckdb"
    monkeypatch.setattr("src.storage.database.settings.duckdb_path", db_path)
    inicializar_banco()
    yield
    if db_path.exists():
        db_path.unlink()


def test_inicializar_banco_cria_tabelas():
    df = query("SELECT table_name FROM information_schema.tables WHERE table_schema='main'")
    tabelas = df["table_name"].tolist()
    assert "casos_raw" in tabelas
    assert "clima_raw" in tabelas


def test_inserir_casos():
    n = inserir_casos(CASOS_MOCK)
    assert n == 1
    df = query("SELECT * FROM casos_raw")
    assert len(df) == 1
    assert df["municipio"][0] == "Maringá"


def test_inserir_clima():
    n = inserir_clima(CLIMA_MOCK)
    assert n == 1
    df = query("SELECT * FROM clima_raw")
    assert len(df) == 1
    assert df["municipio"][0] == "Maringá"


def test_inserir_casos_vazio():
    n = inserir_casos([])
    assert n == 0


def test_inserir_clima_vazio():
    n = inserir_clima([])
    assert n == 0


def test_query_retorna_dataframe():
    inserir_casos(CASOS_MOCK)
    df = query("SELECT municipio, doenca FROM casos_raw")
    assert "municipio" in df.columns
    assert "doenca" in df.columns