# src/weather/era5_to_csv.py

import xarray as xr
import pandas as pd
from pathlib import Path


def convert_nc_to_csv(nc_path: Path, csv_path: Path):
    ds = xr.open_dataset(nc_path)

    df = (
        ds["t2m"]
        .to_dataframe()
        .reset_index()
        .rename(columns={"time": "time", "t2m": "temperature_2m"})
    )

    df["temperature_2m"] = df["temperature_2m"] - 273.15  # Kelvin → °C

    df[["time", "temperature_2m"]].to_csv(csv_path, index=False)
