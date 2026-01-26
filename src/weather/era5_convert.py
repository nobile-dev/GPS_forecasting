# src/weather/era5_convert.py

from pathlib import Path
import xarray as xr
import pandas as pd

ERA5_DIR = Path("era5_plz")


def convert_nc_to_csv(plz: str):
    nc_path = ERA5_DIR / f"era5_{plz}.nc"
    if not nc_path.exists():
        raise FileNotFoundError(nc_path)

    ds = xr.open_dataset(nc_path)

    # ERA5: 2m temperature
    da = ds["t2m"]

    df = da.to_dataframe().reset_index()

    # --- Zeitspalte robust erkennen ---
    time_col = None
    for c in df.columns:
        if "time" in c.lower():
            time_col = c
            break

    if time_col is None:
        raise ValueError(f"Keine Zeitspalte gefunden in {df.columns}")

    # --- Falls mehrere Gitterpunkte: mitteln ---
    group_cols = [time_col]
    df = (
        df
        .groupby(group_cols)["t2m"]
        .mean()
        .reset_index()
    )

    # Kelvin → Celsius
    df["temperature_2m"] = df["t2m"] - 273.15

    out_path = ERA5_DIR / f"era5_{plz}.csv"
    df[[time_col, "temperature_2m"]].rename(
        columns={time_col: "time"}
    ).to_csv(out_path, index=False)

    print(f"CSV geschrieben: {out_path}")
