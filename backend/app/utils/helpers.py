"""
Shared utility functions for the TRINETRA AI application.
"""

from datetime import datetime
from typing import Optional
import numpy as np


def parse_datetime_safe(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse a datetime string safely, returning None on failure."""
    if not dt_str:
        return None
    try:
        # Handle various formats
        for fmt in [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S.%f%z",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
        ]:
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        return None
    except Exception:
        return None


def get_hour_of_day(dt: Optional[datetime]) -> int:
    """Extract hour from datetime, default to 12 (noon) if None."""
    if dt is None:
        return 12
    return dt.hour


def is_peak_hour(hour: int) -> bool:
    """Check if the hour falls within Bengaluru peak traffic hours."""
    return (7 <= hour <= 10) or (17 <= hour <= 20)


def compute_impact_level(score: float) -> str:
    """Convert numeric impact score (0-100) to categorical level."""
    if score >= 75:
        return "Critical"
    elif score >= 50:
        return "High"
    elif score >= 25:
        return "Medium"
    else:
        return "Low"


def compute_risk_level(minutes: float) -> str:
    """Convert resolution time to risk level."""
    if minutes > 240:
        return "High"
    elif minutes > 60:
        return "Medium"
    else:
        return "Low"


# Severity mapping for event causes (domain knowledge based)
EVENT_CAUSE_SEVERITY = {
    "accident": 5,
    "tree_fall": 4,
    "water_logging": 4,
    "protest": 4,
    "procession": 3,
    "vip_movement": 3,
    "congestion": 3,
    "construction": 3,
    "public_event": 3,
    "Debris": 3,
    "debris": 3,
    "Fog / Low Visibility": 3,
    "road_conditions": 2,
    "pot_holes": 2,
    "vehicle_breakdown": 2,
    "others": 1,
    "test_demo": 0,
}

# Corridor importance mapping
CORRIDOR_IMPORTANCE = {
    "ORR East 1": 9, "ORR East 2": 9, "ORR West 1": 9, "ORR West 2": 9,
    "ORR North 1": 9, "ORR North 2": 9,
    "CBD 1": 8, "CBD 2": 8,
    "Bellary Road 1": 7, "Bellary Road 2": 7,
    "Hosur Road": 7, "Bannerghata Road": 7,
    "Tumkur Road": 7, "Mysore Road": 7,
    "Old Madras Road": 6, "Magadi Road": 6,
    "West of Chord Road": 6,
    "IRR(Thanisandra road)": 5,
    "Kanakapura Road": 5, "Sarjapura Road": 5,
    "Non-corridor": 2,
}


def safe_float(val, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    try:
        result = float(val)
        return result if not np.isnan(result) else default
    except (ValueError, TypeError):
        return default
