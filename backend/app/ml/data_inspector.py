"""
Automatic Dataset Quality Inspector.
Analyzes the traffic event dataset and produces a quality report with
actionable recommendations for the ML pipeline.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ColumnReport:
    name: str
    dtype: str
    null_count: int
    null_pct: float
    unique_count: int
    recommendation: str  # "keep", "impute", "drop", "encode"
    notes: str = ""


@dataclass
class DataQualityReport:
    total_rows: int
    total_columns: int
    columns: list[ColumnReport] = field(default_factory=list)
    usable_for_resolution: int = 0
    date_range: str = ""
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class DataInspector:
    """
    Automatically inspects dataset quality, cardinality,
    and provides recommendations for feature engineering.
    """

    # Columns that are never useful as ML features
    DROP_COLUMNS = {
        "map_file", "comment", "meta_data", "route_path",
        "client_id", "created_by_id", "last_modified_by_id",
        "assigned_to_police_id", "citizen_accident_id",
        "closed_by_id", "resolved_by_id",
    }

    # Columns to impute with a default value
    IMPUTE_DEFAULTS = {
        "zone": "Unknown",
        "junction": "Unknown",
        "corridor": "Non-corridor",
        "priority": "Low",
        "veh_type": "none",
        "description": "",
    }

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.report = None

    def inspect(self) -> DataQualityReport:
        """Run full inspection and return a quality report."""
        report = DataQualityReport(
            total_rows=len(self.df),
            total_columns=len(self.df.columns),
        )

        # Analyze each column
        for col in self.df.columns:
            null_count = int(self.df[col].isna().sum())
            null_pct = round(null_count / len(self.df) * 100, 1)
            unique_count = int(self.df[col].nunique())

            # Determine recommendation
            if col in self.DROP_COLUMNS:
                rec = "drop"
                notes = "Administrative/ID field, not useful for ML"
            elif null_pct > 95:
                rec = "drop"
                notes = f"{null_pct}% null - too sparse"
            elif null_pct > 0 and col in self.IMPUTE_DEFAULTS:
                rec = "impute"
                notes = f"Impute with '{self.IMPUTE_DEFAULTS[col]}'"
            elif self.df[col].dtype == "object" and unique_count < 50:
                rec = "encode"
                notes = f"{unique_count} categories - label encode"
            elif self.df[col].dtype == "object" and unique_count >= 50:
                rec = "encode"
                notes = f"{unique_count} categories - consider top-N or embedding"
            else:
                rec = "keep"
                notes = "Numeric or datetime, use directly"

            report.columns.append(ColumnReport(
                name=col, dtype=str(self.df[col].dtype),
                null_count=null_count, null_pct=null_pct,
                unique_count=unique_count,
                recommendation=rec, notes=notes,
            ))

        # Resolution time feasibility
        resolved_count = self.df["resolved_datetime"].notna().sum()
        closed_count = self.df["closed_datetime"].notna().sum() if "closed_datetime" in self.df.columns else 0
        report.usable_for_resolution = int(max(resolved_count, closed_count))

        # Date range
        try:
            starts = pd.to_datetime(self.df["start_datetime"], format="mixed", utc=True)
            report.date_range = f"{starts.min()} to {starts.max()}"
        except Exception:
            report.date_range = "Unable to parse"

        # Warnings
        if report.usable_for_resolution < 100:
            report.warnings.append(
                f"Only {report.usable_for_resolution} records have resolution timestamps. "
                "Resolution time model will have limited training data."
            )

        high_null_cols = [c for c in report.columns if c.null_pct > 50 and c.recommendation != "drop"]
        if high_null_cols:
            report.warnings.append(
                f"High null columns requiring imputation: {[c.name for c in high_null_cols]}"
            )

        # Recommendations
        report.recommendations = [
            "Use closed_datetime - start_datetime as primary resolution target",
            "Impute zone/junction with 'Unknown' category",
            "Derive impact_score as composite of severity, closure, priority, corridor",
            "Use K-Means clustering for resource recommendation (no resource columns in data)",
            "Cap resolution_minutes at 7 days to filter outliers",
        ]

        self.report = report
        return report

    def apply_cleaning(self) -> pd.DataFrame:
        """Apply the inspector's recommendations to clean the DataFrame."""
        df = self.df.copy()

        # Drop columns
        drop_cols = [c for c in self.DROP_COLUMNS if c in df.columns]
        # Also drop cols with >95% null
        for col in df.columns:
            null_pct = df[col].isna().sum() / len(df) * 100
            if null_pct > 95 and col not in self.IMPUTE_DEFAULTS:
                drop_cols.append(col)

        df.drop(columns=[c for c in set(drop_cols) if c in df.columns], inplace=True)

        # Impute defaults
        for col, default in self.IMPUTE_DEFAULTS.items():
            if col in df.columns:
                df[col] = df[col].fillna(default)

        # Normalize event_cause casing
        if "event_cause" in df.columns:
            df["event_cause"] = df["event_cause"].str.lower().str.strip()

        # Replace string "NULL" with NaN
        df.replace("NULL", np.nan, inplace=True)

        return df

    def print_report(self):
        """Pretty-print the quality report."""
        if not self.report:
            self.inspect()

        r = self.report
        print(f"\n{'='*60}")
        print(f"  DATA QUALITY REPORT")
        print(f"{'='*60}")
        print(f"  Rows: {r.total_rows:,}  |  Columns: {r.total_columns}")
        print(f"  Date Range: {r.date_range}")
        print(f"  Usable for Resolution Model: {r.usable_for_resolution:,}")
        print(f"{'='*60}\n")

        print(f"{'Column':<30} {'Type':<10} {'Null%':<8} {'Unique':<8} {'Action':<8}")
        print("-" * 74)
        for c in r.columns:
            print(f"{c.name:<30} {c.dtype:<10} {c.null_pct:<8} {c.unique_count:<8} {c.recommendation:<8}")

        if r.warnings:
            print(f"\n[!] WARNINGS:")
            for w in r.warnings:
                print(f"   - {w}")

        if r.recommendations:
            print(f"\n[*] RECOMMENDATIONS:")
            for rec in r.recommendations:
                print(f"   - {rec}")
        print()
