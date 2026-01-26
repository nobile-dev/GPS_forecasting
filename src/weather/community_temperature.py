# src/weather/community_temperature.py
import pandas as pd
from pathlib import Path

from src.weather.plz_registry import get_active_plz
from src.weather.era5_loader import load_era5_plz


def build_weighted_community_temperature(
    df_gen_raw: pd.DataFrame,
    era5_dir: Path,
    day: str,
    lookback_days: int = 42,
):
    """
    Returns:
        temp_series (pd.Series, hourly, UTC)
        report (dict)
    """
    day = pd.Timestamp(day, tz="UTC")

    weights = get_active_plz(
        df_gen_raw,
        reference_time=day,
        lookback_days=lookback_days,
    )

    temps = []
    missing = []

    for plz, w in weights.items():
        try:
            s = load_era5_plz(plz, era5_dir)
            temps.append(w * s)
        except FileNotFoundError:
            missing.append(plz)

    coverage = 1 - weights.loc[missing].sum() if missing else 1.0

    if not temps:
        raise RuntimeError("Keine ERA5-Daten verfügbar")

    temp_comm = sum(temps)

    report = {
        "date": day.date().isoformat(),
        "coverage": round(coverage * 100, 2),
        "missing_plz": missing,
        "n_active_plz": len(weights),
    }

    return temp_comm, report
