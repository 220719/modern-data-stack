import pandas as pd
import numpy as np
from loguru import logger
from src.storage.database import query


def carregar_features(municipio: str, doenca: str) -> pd.DataFrame:
    sql = f"""
        SELECT
            ano,
            semana,
            semana_epidemiologica,
            casos_estimados,
            casos_lag1,
            casos_lag2,
            casos_lag4,
            temp_min_lag2,
            precipitacao_lag2,
            umidade_lag4,
            media_movel_4s,
            nivel_alerta
        FROM mart_arboviroses
        WHERE municipio = '{municipio}'
          AND doenca    = '{doenca}'
          AND casos_lag4 IS NOT NULL
        ORDER BY semana_epidemiologica
    """
    df = query(sql)
    logger.info(f"{municipio}/{doenca}: {len(df)} semanas carregadas")
    return df


def preparar_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    features = [
        "casos_lag1",
        "casos_lag2",
        "casos_lag4",
        "temp_min_lag2",
        "precipitacao_lag2",
        "umidade_lag4",
        "media_movel_4s",
    ]
    X = df[features].fillna(0)
    y = df["casos_estimados"]
    return X, y