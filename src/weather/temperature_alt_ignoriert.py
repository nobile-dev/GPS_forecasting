# src/weather/temperature.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Optional

import pandas as pd
import requests


@dataclass(frozen=True)
class TemperatureConfig:
    # Wien als Default
    lat: float = 48.2082
    lon: float = 16.3738

    # Pfad zu ERA5 CSV
    era5_csv_path: str = "data/raw/era5_temp.csv"


def load_era5_temperature(csv_path: str) -> pd.Series:
    df = pd.read_csv(csv_path)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    s = pd.Series(df["temperature_2m"].values, index=df["time"])
    return s.asfreq("1h")


def get_temperature_forecast_open_meteo(
    lat: float,
    lon: float,
    start_utc,
    end_utc,
) -> pd.Series:
    """
    Holt stündliche Temperatur-Vorhersage (UTC) von Open-Meteo
    """

    # --- robustes TZ-Handling ---
    start_utc = pd.Timestamp(start_utc)
    end_utc = pd.Timestamp(end_utc)

    if start_utc.tzinfo is None:
        start_utc = start_utc.tz_localize("UTC")
    else:
        start_utc = start_utc.tz_convert("UTC")

    if end_utc.tzinfo is None:
        end_utc = end_utc.tz_localize("UTC")
    else:
        end_utc = end_utc.tz_convert("UTC")

    # --- API Call ---
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m",
        "timezone": "UTC",
        "start_date": start_utc.date().isoformat(),
        "end_date": end_utc.date().isoformat(),
    }

    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    times = pd.to_datetime(data["hourly"]["time"], utc=True)
    temps = pd.Series(data["hourly"]["temperature_2m"], index=times)

    # --- exakt auf das benötigte Fenster ---
    return temps.loc[start_utc:end_utc].asfreq("1h")


def build_temperature_series(
    train_start: pd.Timestamp,
    test_end: pd.Timestamp,
    cfg: Optional[TemperatureConfig] = None,
) -> pd.Series:
    """
    Hourly temperature series in UTC covering [train_start, test_end]

    Rules:
    - Vergangenheit  -> ERA5
    - Zukunft        -> Open-Meteo
    - Kein Forecast-Wetter für historische Zeiträume
    """
    cfg = cfg or TemperatureConfig()

    # --- robustes TZ-Handling ---
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

    today_utc = pd.Timestamp.utcnow().tz_localize("UTC").floor("D")

    parts = []

    # ======================================================
    # 1) HISTORIE → ERA5
    # ======================================================
    era5_path = Path(cfg.era5_csv_path)
    if era5_path.exists():
        temp_era5 = load_era5_temperature(str(era5_path))

        hist_end = min(test_end, today_utc - pd.Timedelta(hours=1))
        if train_start <= hist_end:
            temp_hist = temp_era5.loc[train_start:hist_end]
            parts.append(temp_hist)
    else:
        print(" ERA5 CSV nicht gefunden – keine historische Temperatur verfügbar")

    # ======================================================
    # 2) ZUKUNFT → Open-Meteo
    # ======================================================
    if test_end >= today_utc:
        fc_start = max(train_start, today_utc)

        temp_fc = get_temperature_forecast_open_meteo(
            cfg.lat,
            cfg.lon,
            fc_start,
            test_end,
        )
        parts.append(temp_fc)

    # ======================================================
    # 3) FINAL
    # ======================================================
    if not parts:
        raise ValueError(
            "Keine Temperaturdaten verfügbar "
            "(ERA5 fehlt und Zeitraum liegt vollständig in der Vergangenheit)."
        )

    temp_all = (
        pd.concat(parts)
        .sort_index()
        .asfreq("1h")
        .ffill()
    )

    return temp_all.loc[train_start:test_end]
