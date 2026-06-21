"""
End-to-end training pipeline for all TRINETRA AI models.
Run: python -m app.training.train_all [csv_path]
"""

import sys
import time
import pandas as pd
from pathlib import Path

from app.ml.data_inspector import DataInspector
from app.ml.feature_engineering import FeatureEngineer
from app.ml.model_registry import ModelRegistry
from app.ml.impact_model import train_impact_models
from app.ml.resolution_model import train_resolution_models
from app.ml.resource_model import ResourceModel
from app.ml.similarity_model import SimilarityModel
from app.config import settings


def train_all(csv_path: str = None):
    """
    Run the complete training pipeline:
    1. Load & inspect data
    2. Feature engineering
    3. Train Impact model
    4. Train Resolution model
    5. Train Resource clustering model
    6. Build Similarity index
    """
    start_time = time.time()
    csv_path = csv_path or str(settings.data_path_resolved)

    print("=" * 70)
    print("  TRINETRA AI - Model Training Pipeline")
    print("=" * 70)

    # ── Step 1: Load data ─────────────────────────────────
    print(f"\n[LOAD] Loading dataset from: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"   Loaded {len(df)} rows x {len(df.columns)} columns")

    # ── Step 2: Inspect data quality ──────────────────────
    print("\n[INSPECT] Running data quality inspection...")
    inspector = DataInspector(df)
    report = inspector.inspect()
    inspector.print_report()

    # Apply cleaning
    df_clean = inspector.apply_cleaning()
    print(f"   Cleaned dataset: {len(df_clean)} rows x {len(df_clean.columns)} columns")

    # ── Step 3: Initialize registry ───────────────────────
    registry = ModelRegistry()

    # ── Step 4: Train Impact Scoring Model ────────────────
    print("\n" + "=" * 70)
    print("  FEATURE 1: Impact Scoring Engine")
    print("=" * 70)

    impact_fe = FeatureEngineer()
    impact_results = train_impact_models(df_clean, impact_fe, registry)
    impact_fe.save(settings.model_dir_path / "impact")

    # ── Step 5: Train Resolution Time Model ───────────────
    print("\n" + "=" * 70)
    print("  FEATURE 4: Resolution Time Prediction")
    print("=" * 70)

    resolution_fe = FeatureEngineer()
    resolution_results = train_resolution_models(df, resolution_fe, registry)
    resolution_fe.save(settings.model_dir_path / "resolution")

    # ── Step 6: Train Resource Recommendation Model ───────
    print("\n" + "=" * 70)
    print("  FEATURE 2: Resource Recommendation Engine")
    print("=" * 70)

    resource_fe = FeatureEngineer()
    resource_model = ResourceModel()
    resource_results = resource_model.train(df_clean, resource_fe, registry)
    resource_fe.save(settings.model_dir_path / "resource")

    # ── Step 7: Build Similarity Index ────────────────────
    print("\n" + "=" * 70)
    print("  FEATURE 3: Similar Event Retrieval Engine")
    print("=" * 70)

    # Compute resolution_minutes for similarity metadata
    df_sim = df.copy()
    df_sim["start_dt"] = pd.to_datetime(df_sim["start_datetime"], format="mixed", utc=True, errors="coerce")
    df_sim["end_dt"] = pd.to_datetime(df_sim["closed_datetime"], format="mixed", utc=True, errors="coerce")
    df_sim["resolution_minutes"] = (df_sim["end_dt"] - df_sim["start_dt"]).dt.total_seconds() / 60.0
    df_sim.loc[df_sim["resolution_minutes"] < 0, "resolution_minutes"] = None
    df_sim.loc[df_sim["resolution_minutes"] > 10080, "resolution_minutes"] = None

    # Fill nulls for similarity features
    for col in ["zone", "junction", "corridor", "description"]:
        if col in df_sim.columns:
            df_sim[col] = df_sim[col].fillna("unknown" if col != "description" else "")

    similarity_model = SimilarityModel()
    similarity_results = similarity_model.train(df_sim, registry)

    # ── Summary ───────────────────────────────────────────
    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print("  TRAINING COMPLETE")
    print("=" * 70)
    print(f"  [TIME] Total time: {elapsed:.1f}s")
    print(f"  [SAVE] Models saved to: {settings.model_dir_path}")
    print(f"  [LIST] Available models: {registry.list_available_models()}")
    print()

    print("  Impact Scoring:")
    for name, metrics in impact_results.items():
        if "error" not in metrics:
            print(f"    {name}: MAE={metrics['mae']}, R2={metrics['r2']}")

    print(f"\n  Resolution Time:")
    if isinstance(resolution_results, dict) and "error" not in resolution_results:
        for name, metrics in resolution_results.items():
            if "error" not in metrics:
                print(f"    {name}: MAE={metrics['mae']}min, R2={metrics['r2']}")

    print(f"\n  Resource Clustering: {resource_results}")
    print(f"  Similarity Index: {similarity_results}")
    print()

    return {
        "impact": impact_results,
        "resolution": resolution_results,
        "resource": resource_results,
        "similarity": similarity_results,
        "training_time_seconds": round(elapsed, 1),
    }


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else None
    train_all(csv_path)
