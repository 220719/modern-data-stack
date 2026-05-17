import duckdb
import pandas as pd
from pathlib import Path
from loguru import logger
from src.config import settings


def get_connection() -> duckdb.DuckDBPyConnection:
    path = settings.duckdb_path
    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path))


def inicializar_banco() -> None:
    logger.info(f"Inicializando banco em {settings.duckdb_path}")
    con = get_connection()

    con.execute("""
        CREATE TABLE IF NOT EXISTS casos_raw (
            municipio        VARCHAR,
            geocodigo        INTEGER,
            doenca           VARCHAR,
            data_iniSE       VARCHAR,
            SE               INTEGER,
            casos_est        DOUBLE,
            casos            DOUBLE,
            nivel            INTEGER,
            inserted_at      TIMESTAMP DEFAULT current_timestamp
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS clima_raw (
            municipio              VARCHAR,
            data                   VARCHAR,
            temperature_2m_max     DOUBLE,
            temperature_2m_min     DOUBLE,
            temperature_2m_mean    DOUBLE,
            precipitation_sum      DOUBLE,
            relative_humidity_2m_max DOUBLE,
            relative_humidity_2m_min DOUBLE,
            inserted_at            TIMESTAMP DEFAULT current_timestamp
        )
    """)

    logger.success("Banco inicializado com sucesso")
    con.close()


def inserir_casos(registros: list[dict]) -> int:
    if not registros:
        logger.warning("Nenhum registro de casos para inserir")
        return 0

    df = pd.DataFrame(registros)

    colunas = [
        "municipio", "geocodigo", "doenca",
        "data_iniSE", "SE", "casos_est", "casos", "nivel"
    ]
    for col in colunas:
        if col not in df.columns:
            df[col] = None

    df = df[colunas]

    con = get_connection()
    con.execute("""
        INSERT INTO casos_raw
            (municipio, geocodigo, doenca, data_iniSE, SE, casos_est, casos, nivel)
        SELECT * FROM df
    """)
    total = con.execute("SELECT COUNT(*) FROM casos_raw").fetchone()[0]
    con.close()

    logger.success(f"{len(df)} registros de casos inseridos — total na tabela: {total}")
    return len(df)


def inserir_clima(registros: list[dict]) -> int:
    if not registros:
        logger.warning("Nenhum registro de clima para inserir")
        return 0

    df = pd.DataFrame(registros)

    colunas = [
        "municipio", "data",
        "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
        "precipitation_sum",
        "relative_humidity_2m_max", "relative_humidity_2m_min",
    ]
    for col in colunas:
        if col not in df.columns:
            df[col] = None

    df = df[colunas]

    con = get_connection()
    con.execute("""
        INSERT INTO clima_raw
            (municipio, data, temperature_2m_max, temperature_2m_min,
             temperature_2m_mean, precipitation_sum,
             relative_humidity_2m_max, relative_humidity_2m_min)
        SELECT * FROM df
    """)
    total = con.execute("SELECT COUNT(*) FROM clima_raw").fetchone()[0]
    con.close()

    logger.success(f"{len(df)} registros de clima inseridos — total na tabela: {total}")
    return len(df)


def query(sql: str) -> pd.DataFrame:
    con = get_connection()
    result = con.execute(sql).df()
    con.close()
    return result