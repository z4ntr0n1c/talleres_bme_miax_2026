"""
Data cleaning, missing value management, and multi-exchange calendar alignment routines.
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np


def clean_missing_values(
    df: pd.DataFrame,
    method: str = "ffill",
    columns: Optional[List[str]] = None,
    max_consecutive_nans: Optional[int] = 5,
) -> pd.DataFrame:
    """Cleans missing values (NaNs) in financial time series according to the selected strategy.

    Strategies:
      - 'ffill': Forward-fills missing quotes (appropriate for financial time series where
                 exchange holidays imply no price change), followed by bfill for leading NaNs.
      - 'drop': Removes rows containing any NaN.
      - 'interpolate': Linearly interpolates between valid observations.

    Args:
        df: Input DataFrame with DatetimeIndex.
        method: Cleaning strategy ('ffill', 'drop', 'interpolate').
        columns: Specific columns to clean (defaults to all columns).
        max_consecutive_nans: Maximum tolerable consecutive missing days before warning/dropping.

    Returns:
        Cleaned pd.DataFrame.
    """
    df_clean = df.copy()
    target_cols = columns if columns is not None else list(df.columns)

    if method == "drop":
        df_clean = df_clean.dropna(subset=target_cols)
    elif method == "ffill":
        # Forward-fill prices with limit on consecutive gaps if specified
        df_clean[target_cols] = df_clean[target_cols].ffill(limit=max_consecutive_nans)
        # Backward-fill remaining leading NaNs
        df_clean[target_cols] = df_clean[target_cols].bfill()
        df_clean = df_clean.dropna(subset=target_cols)
    elif method == "interpolate":
        df_clean[target_cols] = df_clean[target_cols].interpolate(method="time")
        df_clean[target_cols] = df_clean[target_cols].bfill()
        df_clean = df_clean.dropna(subset=target_cols)
    else:
        raise ValueError(
            f"Unsupported cleaning method '{method}'. Choose from 'ffill', 'drop', 'interpolate'."
        )

    return df_clean


def align_calendar_series(
    series_map: Dict[str, pd.Series],
    join_method: str = "inner",
) -> pd.DataFrame:
    """Synchronizes and aligns multiple asset time series originating from different exchange calendars.

    For example, US markets (NYSE/NASDAQ) and European markets (BME) observe different
    bank holidays (e.g. Thanksgiving in US, Epiphany in Spain).

    Alignment Modes:
      - 'inner': Strict intersection of trading days (only days when all markets were open).
                 Preferred for econometric regressions and clean covariance estimation.
      - 'outer_ffill': Union of trading days. If an asset's exchange is closed on day t,
                       its price is carried forward from day t-1. Appropriate for continuous
                       portfolio net asset value tracking.

    Args:
        series_map: Mapping of {ticker: pd.Series} with DatetimeIndex.
        join_method: 'inner' or 'outer_ffill'.

    Returns:
        Aligned pd.DataFrame where each column corresponds to an asset ticker.
    """
    if not series_map:
        return pd.DataFrame()

    combined = pd.DataFrame(series_map)

    if join_method == "inner":
        aligned = combined.dropna()
    elif join_method == "outer_ffill":
        aligned = combined.ffill().bfill().dropna()
    else:
        raise ValueError(f"Unknown join method '{join_method}'. Use 'inner' or 'outer_ffill'.")

    aligned.index.name = "date"
    return aligned


def filter_anomalous_returns(
    returns_series: pd.Series,
    max_abs_return: float = 1.0,
) -> Tuple[pd.Series, pd.Series]:
    """Detects and isolates potential data anomalies or unadjusted split spikes.

    Args:
        returns_series: Daily percentage returns.
        max_abs_return: Maximum realistic absolute daily return (default: 1.0 = 100% intraday swing).

    Returns:
        Tuple of (clean_series, anomalies_detected).
    """
    anomalies = returns_series[returns_series.abs() > max_abs_return]
    clean = returns_series[returns_series.abs() <= max_abs_return]
    return clean, anomalies

