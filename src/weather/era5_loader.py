# src/weather/era5_loader.py
import pandas as pd
from pathlib import Path

def load_era5_plz(
    plz: int | str,
    era5_dir: Path,
) -> pd.Series:
    path = era5_dir / f"era5_{plz}.csv"

    if not path.exists():
        raise FileNotFoundError(f"ERA5 fehlt für PLZ {plz}")

    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"], utc=True)

    s = pd.Series(
        df["temperature_2m"].values,
        index=df["time"],
        name=f"temp_{plz}",
    )

    return s.asfreq("1h")
