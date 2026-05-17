import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from loguru import logger


def walk_forward_validation(
    X: pd.DataFrame,
    y: pd.Series,
    n_test: int = 52,
    n_estimators: int = 200,
    random_state: int = 42,
) -> dict:
    n = len(X)
    n_train = n - n_test

    if n_train < 52:
        raise ValueError(f"Dados insuficientes: {n} semanas (mínimo 104)")

    X_train = X.iloc[:n_train]
    y_train = y.iloc[:n_train]
    X_test  = X.iloc[n_train:]
    y_test  = y.iloc[n_train:]

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mae  = mean_absolute_error(y_test, y_pred)
    rmse = root_mean_squared_error(y_test, y_pred)
    r2   = r2_score(y_test, y_pred)

    importances = pd.Series(
        model.feature_importances_,
        index=X.columns,
    ).sort_values(ascending=False)

    logger.info(f"R²={r2:.3f} | MAE={mae:.1f} | RMSE={rmse:.1f}")

    return {
        "model":       model,
        "mae":         mae,
        "rmse":        rmse,
        "r2":          r2,
        "y_test":      y_test,
        "y_pred":      y_pred,
        "importances": importances,
        "n_train":     n_train,
        "n_test":      n_test,
    }