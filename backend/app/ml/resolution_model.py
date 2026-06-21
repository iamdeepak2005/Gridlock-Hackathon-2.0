"""
Resolution Time Prediction Model.
Predicts how long an event will take to resolve (in minutes).
Uses closed_datetime - start_datetime as training target.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor

from app.ml.feature_engineering import FeatureEngineer
from app.ml.model_registry import ModelRegistry


MAX_RESOLUTION_MINUTES = 10080  # 7 days cap


def prepare_resolution_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter dataset to records with computable resolution time.
    Computes resolution_minutes from closed_datetime - start_datetime.
    """
    df = df.copy()

    # Parse datetime columns
    df["start_dt"] = pd.to_datetime(df["start_datetime"], format="mixed", utc=True, errors="coerce")

    # Try resolved_datetime first, then closed_datetime
    df["end_dt"] = pd.to_datetime(df["resolved_datetime"], format="mixed", utc=True, errors="coerce")
    mask_no_resolved = df["end_dt"].isna()
    df.loc[mask_no_resolved, "end_dt"] = pd.to_datetime(
        df.loc[mask_no_resolved, "closed_datetime"], format="mixed", utc=True, errors="coerce"
    )

    # Compute resolution minutes
    df["resolution_minutes"] = (df["end_dt"] - df["start_dt"]).dt.total_seconds() / 60.0

    # Filter valid rows
    valid = df[
        (df["resolution_minutes"].notna()) &
        (df["resolution_minutes"] > 0) &
        (df["resolution_minutes"] <= MAX_RESOLUTION_MINUTES)
    ].copy()

    print(f"[RESOLUTION] Valid resolution records: {len(valid)} / {len(df)}")
    print(f"[RESOLUTION] Resolution stats: mean={valid['resolution_minutes'].mean():.1f}min, "
          f"median={valid['resolution_minutes'].median():.1f}min, "
          f"max={valid['resolution_minutes'].max():.1f}min")

    return valid


def train_resolution_models(
    df: pd.DataFrame,
    feature_engineer: FeatureEngineer,
    registry: ModelRegistry,
) -> dict:
    """
    Train 4 regression models for resolution time prediction.
    Returns metrics dict and saves best model.
    """
    print("\n[RESOLUTION] Preparing data...")
    valid_df = prepare_resolution_data(df)

    if len(valid_df) < 50:
        print("[RESOLUTION] [WARN] Too few samples for training. Skipping.")
        return {"error": "Insufficient data", "valid_samples": len(valid_df)}

    # Feature engineering
    print("[RESOLUTION] Engineering features...")
    X = feature_engineer.fit_transform(valid_df)
    y = valid_df["resolution_minutes"].values

    # Log-transform target for better distribution
    y_log = np.log1p(y)

    print(f"[RESOLUTION] Feature matrix: {X.shape}")

    models = {
        "xgboost": {
            "model": XGBRegressor(random_state=42, verbosity=0),
            "params": {
                "n_estimators": [100, 200],
                "max_depth": [4, 6, 8],
                "learning_rate": [0.05, 0.1],
            }
        },
        "lightgbm": {
            "model": LGBMRegressor(random_state=42, verbose=-1),
            "params": {
                "n_estimators": [100, 200],
                "max_depth": [4, 6, 8],
                "learning_rate": [0.05, 0.1],
            }
        },
        "catboost": {
            "model": CatBoostRegressor(random_state=42, verbose=0),
            "params": {
                "iterations": [100, 200],
                "depth": [4, 6],
                "learning_rate": [0.05, 0.1],
            }
        },
        "random_forest": {
            "model": RandomForestRegressor(random_state=42),
            "params": {
                "n_estimators": [100, 200],
                "max_depth": [6, 10, 15],
            }
        },
    }

    results = {}
    best_score = -np.inf
    best_model_name = None
    best_model = None

    for name, config in models.items():
        print(f"\n[RESOLUTION] Training {name}...")

        try:
            grid = GridSearchCV(
                config["model"], config["params"],
                cv=3, scoring="neg_mean_absolute_error",
                n_jobs=-1, verbose=0,
            )
            grid.fit(X, y_log)

            model = grid.best_estimator_
            y_pred_log = model.predict(X)
            y_pred = np.expm1(y_pred_log)

            mae = mean_absolute_error(y, y_pred)
            rmse = np.sqrt(mean_squared_error(y, y_pred))
            r2 = r2_score(y, y_pred)

            cv_scores = cross_val_score(model, X, y_log, cv=3, scoring="neg_mean_absolute_error")
            cv_mae = -cv_scores.mean()

            metrics = {
                "mae": round(mae, 4),
                "rmse": round(rmse, 4),
                "r2": round(r2, 4),
                "cv_mae_log": round(cv_mae, 4),
                "best_params": grid.best_params_,
                "training_samples": len(y),
                "uses_log_transform": True,
            }

            if hasattr(model, "feature_importances_"):
                importance = dict(zip(X.columns, model.feature_importances_))
                top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]
                metrics["top_features"] = [{"feature": f, "importance": round(float(i), 4)} for f, i in top_features]

            results[name] = metrics
            print(f"[RESOLUTION] {name}: MAE={mae:.1f}min, RMSE={rmse:.1f}min, R2={r2:.4f}")

            if r2 > best_score:
                best_score = r2
                best_model_name = name
                best_model = model

            registry.save_model(model, "resolution", name, metrics, is_best=False)

        except Exception as e:
            print(f"[RESOLUTION] [FAIL] {name} failed: {e}")
            results[name] = {"error": str(e)}

    if best_model is not None:
        registry.save_model(best_model, "resolution", "best", results[best_model_name], is_best=True)
        print(f"\n[RESOLUTION] [BEST] Best model: {best_model_name} (R2={best_score:.4f})")

    return results
