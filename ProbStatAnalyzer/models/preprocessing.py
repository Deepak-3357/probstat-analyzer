from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class CleanedSeries:
    series: pd.Series
    summary: dict


def dataset_profile(df: pd.DataFrame) -> dict:
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": df.columns.tolist(),
        "missing_values": {col: int(val) for col, val in df.isna().sum().items()},
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }


def clean_numeric_series(df: pd.DataFrame, column: str) -> CleanedSeries:
    original_rows = len(df)
    before_dedup = len(df)
    df = df.drop_duplicates()
    duplicates_removed = before_dedup - len(df)

    raw = pd.to_numeric(df[column], errors="coerce")
    missing_removed = int(raw.isna().sum())
    series = raw.dropna()

    finite_mask = np.isfinite(series)
    impossible_removed = int((~finite_mask).sum())
    series = series[finite_mask]

    q1 = float(series.quantile(0.25)) if not series.empty else 0.0
    q3 = float(series.quantile(0.75)) if not series.empty else 0.0
    iqr = q3 - q1
    if iqr > 0:
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_mask = (series < lower) | (series > upper)
    else:
        lower = upper = float(series.iloc[0]) if not series.empty else 0.0
        outlier_mask = pd.Series(False, index=series.index)

    outliers_detected = int(outlier_mask.sum())
    cleaned = series[~outlier_mask].astype(float)

    summary = {
        "original_rows": int(original_rows),
        "duplicates_removed": int(duplicates_removed),
        "missing_values_removed": int(missing_removed),
        "impossible_values_removed": int(impossible_removed),
        "outliers_detected": int(outliers_detected),
        "rows_removed": int(original_rows - len(cleaned)),
        "final_rows": int(len(cleaned)),
        "iqr_lower_bound": round(float(lower), 6),
        "iqr_upper_bound": round(float(upper), 6),
    }
    return CleanedSeries(series=cleaned.reset_index(drop=True), summary=summary)
