# src/weather/temperature.py

from __future__ import annotations

import pandas as pd
from pathlib import Path

from src.weather.plz_weights import get_active_plz
from src.weather.era5_coverage import check_era5_coverage
from src.weather.era5_autofill import ensure_era5_coverage
from src.weather.era5_loader import load_era5_plz


ERA5_DIR = Path("era5_plz")


def build_temperature_series(
    df_gen_raw: pd.DataFrame,
    train_start: pd.Timestamp,
    test_end: pd.Timestamp,
    lookback_days: int = 42,
) -> pd.Series:
    """
    Baut eine stündliche, UTC, gewichtete Community-Temperatur.

    Pipeline:
    1) aktive PLZ bestimmen (nach Gtemperature geseneration)
    2) ERA5-Coverage sicherstellen (auto-download falls nötig)
    3) ERA5 CSVs laden
    4) gewichtete Aggregation
    """

    train_start = pd.Timestamp(train_start)
    test_end = pd.Timestamp(test_end)

    if train_start.tzinfo is None:
        train_start = train_start.tz_localize("UTC")
    else:
        train_start = train_start.tz_convert("UTC")

    if test_end.tzinfo is None:
        test_end = test_end.tz_localize("UTC")
    else:
        test_end = test_end.tz_convert("UTC")


    # --------------------------------------------------
    # 1) Aktive PLZ + Gewichte
    # --------------------------------------------------
    weights = get_active_plz(
        df_gen_raw=df_gen_raw,
        reference_time=train_start,
        lookback_days=lookback_days,
    )

    # --------------------------------------------------
    # 2) ERA5 Coverage sicherstellen (AUTOMATISCH!)
    # --------------------------------------------------
    ensure_era5_coverage(
        df_gen_raw=df_gen_raw,
        era5_dir=ERA5_DIR,
        reference_day=train_start.date(),
        lookback_days=lookback_days,
    )

    # --------------------------------------------------
    # 3) ERA5 laden + gewichten
    # --------------------------------------------------
    temp_weighted = []

    for plz, w in weights.items():
        s = load_era5_plz(plz, ERA5_DIR)
        s = s.loc[train_start:test_end]
        temp_weighted.append(w * s)

    if not temp_weighted:
        raise ValueError("Keine Temperaturdaten verfügbar")

    # --------------------------------------------------
    # 4) Final
    # --------------------------------------------------
    temp = (
        sum(temp_weighted)
        .sort_index()
        .asfreq("1h")
        .ffill()
    )

    return temp.loc[train_start:test_end]
