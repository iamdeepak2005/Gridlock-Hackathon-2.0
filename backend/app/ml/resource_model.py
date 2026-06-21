"""
Resource Recommendation Model.
Uses K-Means clustering + rule-based inference since no resource columns exist.
Groups similar incidents and derives resource profiles per cluster.
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path

from app.ml.feature_engineering import FeatureEngineer
from app.ml.model_registry import ModelRegistry
from app.utils.helpers import EVENT_CAUSE_SEVERITY


# Rule-based resource estimation per event cause
RESOURCE_RULES = {
    "accident": {"officers": 3, "barricades": 4, "tow": 1},
    "tree_fall": {"officers": 2, "barricades": 3, "tow": 0},
    "water_logging": {"officers": 2, "barricades": 4, "tow": 0},
    "vehicle_breakdown": {"officers": 1, "barricades": 2, "tow": 1},
    "congestion": {"officers": 2, "barricades": 2, "tow": 0},
    "construction": {"officers": 1, "barricades": 3, "tow": 0},
    "pot_holes": {"officers": 1, "barricades": 2, "tow": 0},
    "road_conditions": {"officers": 1, "barricades": 2, "tow": 0},
    "protest": {"officers": 4, "barricades": 6, "tow": 0},
    "procession": {"officers": 3, "barricades": 5, "tow": 0},
    "vip_movement": {"officers": 4, "barricades": 6, "tow": 0},
    "public_event": {"officers": 3, "barricades": 4, "tow": 0},
    "debris": {"officers": 1, "barricades": 2, "tow": 0},
    "fog / low visibility": {"officers": 2, "barricades": 3, "tow": 0},
    "others": {"officers": 1, "barricades": 1, "tow": 0},
    "test_demo": {"officers": 0, "barricades": 0, "tow": 0},
}


class ResourceModel:
    """
    Clusters similar incidents and derives resource recommendations.
    Combines K-Means clustering with domain-specific rules.
    """

    def __init__(self):
        self.kmeans = None
        self.scaler = StandardScaler()
        self.cluster_profiles: dict[int, dict] = {}
        self.n_clusters = 6
        self.feature_engineer = None
        self.is_fitted = False

    def train(
        self,
        df: pd.DataFrame,
        feature_engineer: FeatureEngineer,
        registry: ModelRegistry,
    ) -> dict:
        """
        Train clustering model for resource recommendation.
        """
        print("\n[RESOURCE] Training resource recommendation model...")
        self.feature_engineer = feature_engineer

        # Use only resolved/closed events
        valid_df = df[df["status"].isin(["closed", "resolved"])].copy()
        print(f"[RESOURCE] Using {len(valid_df)} closed/resolved events")

        # Engineer features
        X = feature_engineer.fit_transform(valid_df)

        # Scale features for clustering
        X_scaled = self.scaler.fit_transform(X)

        # Find optimal k using silhouette score
        best_k = self.n_clusters
        best_silhouette = -1

        for k in range(4, 10):
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = km.fit_predict(X_scaled)
            score = silhouette_score(X_scaled, labels)
            print(f"[RESOURCE] k={k}, silhouette={score:.3f}")
            if score > best_silhouette:
                best_silhouette = score
                best_k = k

        print(f"[RESOURCE] Optimal clusters: {best_k} (silhouette={best_silhouette:.3f})")

        # Fit final model
        self.n_clusters = best_k
        self.kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        valid_df["cluster"] = self.kmeans.fit_predict(X_scaled)

        # Build cluster profiles with resource estimates
        for cluster_id in range(best_k):
            cluster_df = valid_df[valid_df["cluster"] == cluster_id]
            profile = self._build_cluster_profile(cluster_df)
            self.cluster_profiles[cluster_id] = profile
            print(f"[RESOURCE] Cluster {cluster_id}: {len(cluster_df)} events, "
                  f"officers={profile['officers']}, barricades={profile['barricades']}, "
                  f"tow={profile['tow']}, avg_resolution={profile['avg_resolution_min']:.0f}min")

        self.is_fitted = True

        # Save model
        model_data = {
            "kmeans": self.kmeans,
            "scaler": self.scaler,
            "cluster_profiles": self.cluster_profiles,
            "n_clusters": self.n_clusters,
        }
        registry.save_model(model_data, "resource", "kmeans",
                          {"n_clusters": best_k, "silhouette": round(best_silhouette, 4)},
                          is_best=True)

        return {
            "n_clusters": best_k,
            "silhouette": round(best_silhouette, 4),
            "cluster_sizes": {int(k): int(v) for k, v in
                            valid_df["cluster"].value_counts().to_dict().items()},
        }

    def _build_cluster_profile(self, cluster_df: pd.DataFrame) -> dict:
        """Build a resource profile for a cluster based on incident characteristics."""
        # Get dominant event cause for this cluster
        cause_counts = cluster_df["event_cause"].value_counts()
        dominant_cause = cause_counts.index[0] if len(cause_counts) > 0 else "others"

        # Base from rules
        base = RESOURCE_RULES.get(dominant_cause, RESOURCE_RULES["others"])

        # Adjust based on cluster characteristics
        has_closure_rate = cluster_df["requires_road_closure"].mean()
        has_high_priority_rate = (cluster_df["priority"] == "High").mean()

        # More closures = more resources
        closure_mult = 1.0 + has_closure_rate * 0.5
        priority_mult = 1.0 + has_high_priority_rate * 0.3

        officers = max(1, round(base["officers"] * closure_mult * priority_mult))
        barricades = max(0, round(base["barricades"] * closure_mult))
        tow = base["tow"]

        # Has vehicle info = more likely to need tow
        if "veh_type" in cluster_df.columns:
            veh_rate = cluster_df["veh_type"].notna().mean()
            if veh_rate > 0.5:
                tow = max(tow, 1)

        # Average resolution time
        if "resolution_minutes" in cluster_df.columns:
            avg_res = cluster_df["resolution_minutes"].dropna().median()
        else:
            avg_res = 120.0

        return {
            "officers": int(officers),
            "barricades": int(barricades),
            "tow": int(tow),
            "avg_resolution_min": float(avg_res) if pd.notna(avg_res) else 120.0,
            "dominant_cause": dominant_cause,
            "closure_rate": round(float(has_closure_rate), 2),
            "size": len(cluster_df),
        }

    def predict(self, event_data: dict, feature_engineer: FeatureEngineer) -> dict:
        """
        Predict resource requirements for a new event.
        Falls back to rules if clustering unavailable.
        """
        cause = event_data.get("event_cause", "others").lower()

        if self.is_fitted and self.kmeans is not None:
            try:
                X = feature_engineer.transform_single(event_data)
                X_scaled = self.scaler.transform(X)
                cluster = int(self.kmeans.predict(X_scaled)[0])
                profile = self.cluster_profiles.get(cluster, {})

                # Blend cluster profile with rule-based for the specific cause
                rule = RESOURCE_RULES.get(cause, RESOURCE_RULES["others"])

                return {
                    "officers_required": max(profile.get("officers", rule["officers"]),
                                           rule["officers"]),
                    "barricades_required": max(profile.get("barricades", rule["barricades"]),
                                             rule["barricades"]),
                    "tow_vehicles_required": rule["tow"],
                    "estimated_resolution_time": round(profile.get("avg_resolution_min", 120.0), 1),
                    "confidence": 0.75,
                    "cluster_id": cluster,
                }
            except Exception:
                pass

        # Fallback to pure rules
        rule = RESOURCE_RULES.get(cause, RESOURCE_RULES["others"])

        # Adjust for road closure and priority
        closure_mult = 1.5 if event_data.get("requires_road_closure") else 1.0
        priority_mult = 1.3 if event_data.get("priority") == "High" else 1.0

        return {
            "officers_required": max(1, round(rule["officers"] * closure_mult * priority_mult)),
            "barricades_required": max(0, round(rule["barricades"] * closure_mult)),
            "tow_vehicles_required": rule["tow"],
            "estimated_resolution_time": 120.0,
            "confidence": 0.5,
            "cluster_id": -1,
        }

    def load(self, registry: ModelRegistry):
        """Load a previously trained model."""
        try:
            data = registry.load_model("resource", "best")
            self.kmeans = data["kmeans"]
            self.scaler = data["scaler"]
            self.cluster_profiles = data["cluster_profiles"]
            self.n_clusters = data["n_clusters"]
            self.is_fitted = True
            print("[RESOURCE] Model loaded successfully")
        except FileNotFoundError:
            print("[RESOURCE] No trained model found, using rules-only fallback")
