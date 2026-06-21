"""
Similar Event Retrieval Engine.
Builds feature embeddings for events and uses NearestNeighbors for retrieval.
"""

import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from scipy.sparse import hstack, csr_matrix
import joblib
from pathlib import Path

from app.ml.model_registry import ModelRegistry


class SimilarityModel:
    """
    Builds multi-modal embeddings (categorical + text + geospatial)
    and retrieves nearest neighbors for incident similarity.
    """

    def __init__(self):
        self.nn_model: NearestNeighbors = None
        self.tfidf: TfidfVectorizer = None
        self.ohe: OneHotEncoder = None
        self.scaler: StandardScaler = None
        self.event_ids: list[str] = []
        self.event_metadata: pd.DataFrame = None
        self.is_fitted = False

        # Feature columns for one-hot encoding
        self.cat_columns = ["event_type", "event_cause", "zone", "junction", "corridor"]

    def train(self, df: pd.DataFrame, registry: ModelRegistry) -> dict:
        """Build embeddings for all events and fit NearestNeighbors."""
        print("\n[SIMILARITY] Building event embeddings...")
        df = df.copy()

        # Store event IDs and metadata for retrieval
        self.event_ids = df["id"].tolist()
        self.event_metadata = df[[
            "id", "event_type", "event_cause", "zone", "junction",
            "corridor", "description", "status", "priority",
            "requires_road_closure", "resolution_minutes",
            "latitude", "longitude",
        ]].copy()

        # ── Categorical features (one-hot) ────────────────────
        for col in self.cat_columns:
            if col not in df.columns:
                df[col] = "unknown"
            df[col] = df[col].fillna("unknown").astype(str)

        self.ohe = OneHotEncoder(sparse_output=True, handle_unknown="ignore")
        cat_matrix = self.ohe.fit_transform(df[self.cat_columns])
        print(f"[SIMILARITY] Categorical features: {cat_matrix.shape[1]}")

        # ── Text features (TF-IDF on description) ─────────────
        descriptions = df["description"].fillna("").astype(str)
        self.tfidf = TfidfVectorizer(max_features=100, stop_words="english")
        text_matrix = self.tfidf.fit_transform(descriptions)
        print(f"[SIMILARITY] Text features: {text_matrix.shape[1]}")

        # ── Binary features ───────────────────────────────────
        binary_feats = pd.DataFrame({
            "road_closure": df["requires_road_closure"].astype(int),
        })
        binary_matrix = csr_matrix(binary_feats.values)

        # ── Geospatial features (scaled) ──────────────────────
        geo_feats = df[["latitude", "longitude"]].fillna(0).values
        self.scaler = StandardScaler()
        geo_scaled = self.scaler.fit_transform(geo_feats)
        geo_matrix = csr_matrix(geo_scaled)

        # ── Combine all features ──────────────────────────────
        combined = hstack([cat_matrix, text_matrix, binary_matrix, geo_matrix])
        print(f"[SIMILARITY] Combined embedding: {combined.shape}")

        # ── Fit NearestNeighbors ──────────────────────────────
        self.nn_model = NearestNeighbors(n_neighbors=6, metric="cosine", algorithm="brute")
        self.nn_model.fit(combined)
        self.is_fitted = True

        # Save model
        model_data = {
            "nn_model": self.nn_model,
            "tfidf": self.tfidf,
            "ohe": self.ohe,
            "scaler": self.scaler,
            "event_ids": self.event_ids,
            "event_metadata": self.event_metadata,
            "combined_matrix": combined,
        }
        registry.save_model(model_data, "similarity", "knn",
                          {"n_events": len(self.event_ids), "embedding_dim": combined.shape[1]},
                          is_best=True)

        print(f"[SIMILARITY] [OK] Built index for {len(self.event_ids)} events")

        return {
            "total_events_indexed": len(self.event_ids),
            "embedding_dimensions": combined.shape[1],
        }

    def find_similar(self, event_data: dict, k: int = 5) -> dict:
        """
        Find k most similar events to the query event.
        Returns similar events with metadata and aggregated insights.
        """
        if not self.is_fitted:
            return {
                "similar_events": [],
                "average_resolution_time": None,
                "historical_success_patterns": ["No model trained yet"],
                "recommended_action": "Train the similarity model first",
            }

        # Build query embedding
        query_embedding = self._build_query_embedding(event_data)

        # Find neighbors (k+1 to potentially exclude self-match)
        distances, indices = self.nn_model.kneighbors(query_embedding, n_neighbors=min(k + 1, len(self.event_ids)))

        # Build results
        similar_events = []
        resolution_times = []

        for dist, idx in zip(distances[0], indices[0]):
            if idx >= len(self.event_ids):
                continue

            meta = self.event_metadata.iloc[idx]
            similarity_score = round(1.0 - float(dist), 4)  # cosine distance → similarity

            event_item = {
                "id": str(meta["id"]),
                "event_cause": str(meta["event_cause"]),
                "zone": str(meta.get("zone", "Unknown")),
                "junction": str(meta.get("junction", "Unknown")),
                "resolution_minutes": float(meta["resolution_minutes"]) if pd.notna(meta.get("resolution_minutes")) else None,
                "similarity_score": similarity_score,
                "description": str(meta.get("description", ""))[:200] if pd.notna(meta.get("description")) else None,
            }
            similar_events.append(event_item)

            if pd.notna(meta.get("resolution_minutes")):
                resolution_times.append(float(meta["resolution_minutes"]))

        # Limit to k results
        similar_events = similar_events[:k]

        # Aggregate insights
        avg_resolution = round(np.mean(resolution_times), 1) if resolution_times else None

        # Generate success patterns
        patterns = self._extract_patterns(similar_events, event_data)

        # Generate recommendation
        recommendation = self._generate_recommendation(event_data, similar_events, avg_resolution)

        return {
            "similar_events": similar_events,
            "average_resolution_time": avg_resolution,
            "historical_success_patterns": patterns,
            "recommended_action": recommendation,
        }

    def _build_query_embedding(self, event_data: dict):
        """Build an embedding vector for a single query event."""
        query_df = pd.DataFrame([{
            col: event_data.get(col) if event_data.get(col) is not None else "unknown"
            for col in self.cat_columns
        }])
        for col in self.cat_columns:
            query_df[col] = query_df[col].fillna("unknown").astype(str)

        cat_vec = self.ohe.transform(query_df)
        
        description = event_data.get("description") or ""
        text_vec = self.tfidf.transform([description])
        
        requires_road_closure = event_data.get("requires_road_closure") or False
        binary_vec = csr_matrix([[int(requires_road_closure)]])

        latitude = event_data.get("latitude") if event_data.get("latitude") is not None else 12.97
        longitude = event_data.get("longitude") if event_data.get("longitude") is not None else 77.59
        geo = np.array([[latitude, longitude]])
        geo_vec = csr_matrix(self.scaler.transform(geo))

        return hstack([cat_vec, text_vec, binary_vec, geo_vec])

    def _extract_patterns(self, similar_events: list, query: dict) -> list[str]:
        """Extract historical success patterns from similar events."""
        patterns = []

        causes = [e["event_cause"] for e in similar_events]
        most_common_cause = max(set(causes), key=causes.count) if causes else None
        if most_common_cause:
            patterns.append(f"Most similar incidents were '{most_common_cause}' type")

        resolutions = [e["resolution_minutes"] for e in similar_events if e.get("resolution_minutes")]
        if resolutions:
            patterns.append(f"Similar events resolved in {np.median(resolutions):.0f} min (median)")

        zones = [e["zone"] for e in similar_events if e.get("zone") != "Unknown"]
        if zones:
            patterns.append(f"Similar events commonly occurred in zone: {max(set(zones), key=zones.count)}")

        if not patterns:
            patterns.append("Insufficient historical data for pattern extraction")

        return patterns

    def _generate_recommendation(self, query: dict, similar: list, avg_res: float | None) -> str:
        """Generate an action recommendation based on similar events."""
        cause = query.get("event_cause", "unknown")
        closure = query.get("requires_road_closure", False)

        if cause == "accident" and closure:
            action = "Deploy emergency response team immediately. Set up diversions. Estimated resolution: "
        elif cause == "vehicle_breakdown":
            action = "Dispatch tow vehicle and traffic officer for lane management. Estimated resolution: "
        elif cause == "tree_fall":
            action = "Alert BBMP tree-clearing crew. Deploy barricades for safety. Estimated resolution: "
        elif cause in ("water_logging", "pot_holes", "road_conditions"):
            action = "Deploy warning signage and barricades. Alert municipal authority. Estimated resolution: "
        elif cause in ("protest", "procession", "vip_movement", "public_event"):
            action = "Coordinate with police for crowd/traffic management. Pre-plan diversions. Estimated resolution: "
        else:
            action = "Assess situation and deploy standard response. Estimated resolution: "

        if avg_res:
            action += f"{avg_res:.0f} minutes based on historical data."
        else:
            action += "unknown (no resolution data from similar events)."

        return action

    def load(self, registry: ModelRegistry):
        """Load previously trained model."""
        try:
            data = registry.load_model("similarity", "best")
            self.nn_model = data["nn_model"]
            self.tfidf = data["tfidf"]
            self.ohe = data["ohe"]
            self.scaler = data["scaler"]
            self.event_ids = data["event_ids"]
            self.event_metadata = data["event_metadata"]
            self.is_fitted = True
            print(f"[SIMILARITY] Loaded index with {len(self.event_ids)} events")
        except FileNotFoundError:
            print("[SIMILARITY] No trained model found")
