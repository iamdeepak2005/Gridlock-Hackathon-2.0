"""
Event Impact Scoring Model.
Derives a 0-100 impact score and trains multiple models to predict it.
Auto-selects the best performing model.
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
from app.utils.helpers import EVENT_CAUSE_SEVERITY, CORRIDOR_IMPORTANCE


def derive_impact_score(df: pd.DataFrame) -> pd.Series:
    """
    Derive a composite impact score (0-100) from multiple event signals.
    This becomes the training target since no explicit impact column exists.
    """
    scores = pd.Series(0.0, index=df.index)

    # 1. Event cause severity (0-25 points)
    cause_weight = df["event_cause"].map(EVENT_CAUSE_SEVERITY).fillna(1)
    scores += (cause_weight / 5.0) * 25  # Normalize 0-5 → 0-25

    # 2. Road closure (0-20 points)
    if "requires_road_closure" in df.columns:
        scores += df["requires_road_closure"].astype(int) * 20

    # 3. Priority (0-15 points)
    if "priority" in df.columns:
        scores += df["priority"].map({"High": 15, "Low": 5}).fillna(5)

    # 4. Resolution time percentile (0-15 points)
    if "resolution_minutes" in df.columns:
        res_min = df["resolution_minutes"].fillna(df["resolution_minutes"].median())
        res_pct = res_min.rank(pct=True).fillna(0.5)
        scores += res_pct * 15

    # 5. Corridor importance (0-10 points)
    if "corridor" in df.columns:
        corr_imp = df["corridor"].map(CORRIDOR_IMPORTANCE).fillna(2)
        scores += (corr_imp / 9.0) * 10  # Normalize 0-9 → 0-10

    # 6. Peak hour bonus (0-10 points)
    if "start_datetime" in df.columns:
        dt = pd.to_datetime(df["start_datetime"], format="mixed", utc=True, errors="coerce")
        hour = dt.dt.hour.fillna(12)
        is_peak = ((hour >= 7) & (hour <= 10)) | ((hour >= 17) & (hour <= 20))
        scores += is_peak.astype(int) * 10

    # 7. Vehicle involvement (0-5 points)
    if "veh_type" in df.columns:
        scores += df["veh_type"].notna().astype(int) * 5

    # Clip to 0-100 and add small noise for variance
    np.random.seed(42)
    noise = np.random.normal(0, 2, len(scores))
    scores = (scores + noise).clip(0, 100).round(2)

    return scores


def train_impact_models(
    df: pd.DataFrame,
    feature_engineer: FeatureEngineer,
    registry: ModelRegistry,
) -> dict:
    """
    Train 4 regression models for impact scoring.
    Returns metrics dict and saves best model.
    """
    print("\n[IMPACT] Deriving impact scores...")
    df = df.copy()
    df["impact_score"] = derive_impact_score(df)

    print(f"[IMPACT] Score stats: mean={df['impact_score'].mean():.1f}, "
          f"std={df['impact_score'].std():.1f}, "
          f"min={df['impact_score'].min():.1f}, max={df['impact_score'].max():.1f}")

    # Feature engineering
    print("[IMPACT] Engineering features...")
    X = feature_engineer.fit_transform(df)
    y = df["impact_score"].values

    print(f"[IMPACT] Feature matrix: {X.shape}")

    # Define models with hyperparameter grids
    models = {
        "xgboost": {
            "model": XGBRegressor(random_state=42, verbosity=0),
            "params": {
                "n_estimators": [100, 200],
                "max_depth": [4, 6],
                "learning_rate": [0.05, 0.1],
            }
        },
        "lightgbm": {
            "model": LGBMRegressor(random_state=42, verbose=-1),
            "params": {
                "n_estimators": [100, 200],
                "max_depth": [4, 6],
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
                "max_depth": [6, 10],
            }
        },
    }

    results = {}
    best_score = -np.inf
    best_model_name = None
    best_model = None

    for name, config in models.items():
        print(f"\n[IMPACT] Training {name}...")

        try:
            grid = GridSearchCV(
                config["model"], config["params"],
                cv=3, scoring="neg_mean_absolute_error",
                n_jobs=-1, verbose=0,
            )
            grid.fit(X, y)

            model = grid.best_estimator_
            y_pred = model.predict(X)

            mae = mean_absolute_error(y, y_pred)
            rmse = np.sqrt(mean_squared_error(y, y_pred))
            r2 = r2_score(y, y_pred)

            # Cross-val score
            cv_scores = cross_val_score(model, X, y, cv=3, scoring="neg_mean_absolute_error")
            cv_mae = -cv_scores.mean()

            metrics = {
                "mae": round(mae, 4),
                "rmse": round(rmse, 4),
                "r2": round(r2, 4),
                "cv_mae": round(cv_mae, 4),
                "best_params": grid.best_params_,
            }

            # Feature importance
            if hasattr(model, "feature_importances_"):
                importance = dict(zip(X.columns, model.feature_importances_))
                top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]
                metrics["top_features"] = [{"feature": f, "importance": round(float(i), 4)} for f, i in top_features]

            results[name] = metrics
            print(f"[IMPACT] {name}: MAE={mae:.2f}, RMSE={rmse:.2f}, R2={r2:.4f}, CV-MAE={cv_mae:.2f}")

            # Track best
            if r2 > best_score:
                best_score = r2
                best_model_name = name
                best_model = model

            # Save model
            registry.save_model(model, "impact", name, metrics, is_best=False)

        except Exception as e:
            print(f"[IMPACT] [FAIL] {name} failed: {e}")
            results[name] = {"error": str(e)}

    # Save best model
    if best_model is not None:
        registry.save_model(best_model, "impact", "best", results[best_model_name], is_best=True)
        print(f"\n[IMPACT] [BEST] Best model: {best_model_name} (R2={best_score:.4f})")

    return results
