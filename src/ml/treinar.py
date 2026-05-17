import mlflow
import mlflow.sklearn
import pandas as pd
from loguru import logger
from src.config import settings
from src.ml.features import carregar_features, preparar_xy
from src.ml.modelo import walk_forward_validation
from src.ingestion.infodengue import MUNICIPIOS, DOENCAS

MLFLOW_EXPERIMENT = "arboviroses-forecast"


def treinar_modelo(municipio: str, doenca: str) -> dict | None:
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(MLFLOW_EXPERIMENT)

    try:
        df = carregar_features(municipio, doenca)
        if len(df) < 104:
            logger.warning(f"{municipio}/{doenca}: dados insuficientes ({len(df)} semanas)")
            return None

        X, y = preparar_xy(df)
        resultado = walk_forward_validation(X, y)

        with mlflow.start_run(run_name=f"{municipio}_{doenca}"):
            mlflow.log_param("municipio", municipio)
            mlflow.log_param("doenca",    doenca)
            mlflow.log_param("n_train",   resultado["n_train"])
            mlflow.log_param("n_test",    resultado["n_test"])

            mlflow.log_metric("r2",   resultado["r2"])
            mlflow.log_metric("mae",  resultado["mae"])
            mlflow.log_metric("rmse", resultado["rmse"])

            mlflow.sklearn.log_model(
                resultado["model"],
                artifact_path="model",
                registered_model_name=f"arboviroses_{municipio}_{doenca}".replace(" ", "_"),
            )

            logger.success(f"{municipio}/{doenca} → R²={resultado['r2']:.3f} MAE={resultado['mae']:.1f}")

        return resultado

    except Exception as e:
        logger.error(f"Erro em {municipio}/{doenca}: {e}")
        return None


def treinar_todos() -> pd.DataFrame:
    resultados = []
    for municipio in MUNICIPIOS:
        for doenca in DOENCAS:
            res = treinar_modelo(municipio, doenca)
            if res:
                resultados.append({
                    "municipio": municipio,
                    "doenca":    doenca,
                    "r2":        round(res["r2"],  3),
                    "mae":       round(res["mae"], 1),
                    "rmse":      round(res["rmse"], 1),
                })

    df = pd.DataFrame(resultados)
    logger.info(f"\n{df.to_string()}")
    return df


if __name__ == "__main__":
    treinar_todos()