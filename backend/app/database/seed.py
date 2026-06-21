"""
Seed the database with the CSV traffic event dataset.
Handles data cleaning, type conversion, and derived field computation.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from app.database.connection import engine, SessionLocal, init_db
from app.models.database import TrafficEvent


def clean_datetime(val):
    """Parse mixed-format datetime strings safely."""
    if pd.isna(val) or val == "NULL":
        return None
    try:
        return pd.to_datetime(val, format="mixed", utc=True)
    except Exception:
        return None


def compute_resolution_minutes(row) -> float | None:
    """Compute resolution time from closed_datetime - start_datetime."""
    start = row.get("start_datetime_parsed")
    closed = row.get("closed_datetime_parsed")
    resolved = row.get("resolved_datetime_parsed")

    end = resolved if resolved is not None else closed
    if start is None or end is None:
        return None

    delta = (end - start).total_seconds() / 60.0
    # Filter out negative or absurdly long resolutions (> 30 days)
    if delta < 0 or delta > 43200:
        return None
    return round(delta, 2)


def seed_database(csv_path: str, drop_existing: bool = True):
    """
    Load the CSV dataset into the PostgreSQL traffic_events table.

    Args:
        csv_path: Path to the anonymized event data CSV.
        drop_existing: If True, drop and recreate the table.
    """
    print(f"[SEED] Loading dataset from {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"[SEED] Loaded {len(df)} rows, {len(df.columns)} columns")

    # Replace string 'NULL' with actual NaN
    df.replace("NULL", np.nan, inplace=True)

    # Parse datetime columns
    dt_cols = ["start_datetime", "end_datetime", "modified_datetime",
               "created_date", "closed_datetime", "resolved_datetime"]
    for col in dt_cols:
        df[f"{col}_parsed"] = df[col].apply(clean_datetime)

    # Compute derived resolution_minutes
    df["resolution_minutes"] = df.apply(compute_resolution_minutes, axis=1)

    # Clean numeric fields
    df["endlatitude"] = pd.to_numeric(df["endlatitude"], errors="coerce")
    df["endlongitude"] = pd.to_numeric(df["endlongitude"], errors="coerce")
    df["age_of_truck"] = pd.to_numeric(df["age_of_truck"], errors="coerce")

    # Replace 0 in endlat/endlong with None
    df.loc[df["endlatitude"] == 0, "endlatitude"] = None
    df.loc[df["endlongitude"] == 0, "endlongitude"] = None

    # Initialize DB
    if drop_existing:
        print("[SEED] Initializing database tables...")
        init_db()

    # Insert in batches
    session = SessionLocal()
    batch_size = 500
    inserted = 0

    try:
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i + batch_size]
            events = []

            for _, row in batch.iterrows():
                event = TrafficEvent(
                    id=str(row["id"]),
                    event_type=row["event_type"],
                    latitude=row["latitude"],
                    longitude=row["longitude"],
                    endlatitude=row.get("endlatitude"),
                    endlongitude=row.get("endlongitude"),
                    address=row.get("address"),
                    end_address=row.get("end_address") if pd.notna(row.get("end_address")) else None,
                    event_cause=row["event_cause"],
                    requires_road_closure=bool(row["requires_road_closure"]),
                    start_datetime=row["start_datetime_parsed"],
                    end_datetime=row.get("end_datetime_parsed"),
                    status=row["status"],
                    authenticated=row.get("authenticated"),
                    modified_datetime=row.get("modified_datetime_parsed"),
                    direction=row.get("direction") if pd.notna(row.get("direction")) else None,
                    description=row.get("description") if pd.notna(row.get("description")) else None,
                    veh_type=row.get("veh_type") if pd.notna(row.get("veh_type")) else None,
                    veh_no=row.get("veh_no") if pd.notna(row.get("veh_no")) else None,
                    corridor=row.get("corridor") if pd.notna(row.get("corridor")) else "Non-corridor",
                    priority=row.get("priority") if pd.notna(row.get("priority")) else "Low",
                    cargo_material=row.get("cargo_material") if pd.notna(row.get("cargo_material")) else None,
                    reason_breakdown=row.get("reason_breakdown") if pd.notna(row.get("reason_breakdown")) else None,
                    age_of_truck=row.get("age_of_truck") if pd.notna(row.get("age_of_truck")) else None,
                    created_date=row.get("created_date_parsed"),
                    client_id=int(row["client_id"]) if pd.notna(row.get("client_id")) else None,
                    created_by_id=row.get("created_by_id") if pd.notna(row.get("created_by_id")) else None,
                    last_modified_by_id=row.get("last_modified_by_id") if pd.notna(row.get("last_modified_by_id")) else None,
                    assigned_to_police_id=row.get("assigned_to_police_id") if pd.notna(row.get("assigned_to_police_id")) else None,
                    citizen_accident_id=row.get("citizen_accident_id") if pd.notna(row.get("citizen_accident_id")) else None,
                    police_station=row.get("police_station") if pd.notna(row.get("police_station")) else None,
                    kgid=row.get("kgid") if pd.notna(row.get("kgid")) else None,
                    resolved_at_address=row.get("resolved_at_address") if pd.notna(row.get("resolved_at_address")) else None,
                    resolved_at_latitude=row.get("resolved_at_latitude") if pd.notna(row.get("resolved_at_latitude")) else None,
                    resolved_at_longitude=row.get("resolved_at_longitude") if pd.notna(row.get("resolved_at_longitude")) else None,
                    closed_by_id=row.get("closed_by_id") if pd.notna(row.get("closed_by_id")) else None,
                    closed_datetime=row.get("closed_datetime_parsed"),
                    resolved_by_id=row.get("resolved_by_id") if pd.notna(row.get("resolved_by_id")) else None,
                    resolved_datetime=row.get("resolved_datetime_parsed"),
                    gba_identifier=row.get("gba_identifier") if pd.notna(row.get("gba_identifier")) else None,
                    zone=row.get("zone") if pd.notna(row.get("zone")) else None,
                    junction=row.get("junction") if pd.notna(row.get("junction")) else None,
                    resolution_minutes=row.get("resolution_minutes"),
                )
                events.append(event)

            session.bulk_save_objects(events)
            session.commit()
            inserted += len(events)
            print(f"[SEED] Inserted {inserted}/{len(df)} events...")

        print(f"[SEED] [OK] Database seeded with {inserted} events")

    except Exception as e:
        session.rollback()
        print(f"[SEED] [FAIL] Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    import sys
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/events.csv"
    seed_database(csv_path)
