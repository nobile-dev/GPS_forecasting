# src/weather/era5_downloader.py

from pathlib import Path
from typing import Iterable
import cdsapi
import pandas as pd

from src.geo.plz_registry import PLZ_TO_LATLON

ERA5_DIR = Path("era5_plz")
ERA5_DIR.mkdir(exist_ok=True)


def download_era5_for_plz(plz: str, years=("2024", "2025")):
    if plz not in PLZ_TO_LATLON:
        raise KeyError(f"Keine Koordinaten für PLZ {plz}")

    lat, lon = PLZ_TO_LATLON[plz]
    out_path = ERA5_DIR / f"era5_{plz}.nc"

    c = cdsapi.Client()

    c.retrieve(
        "reanalysis-era5-single-levels",
        {
            "product_type": "reanalysis",
            "variable": "2m_temperature",
            "year": list(years),
            "month": [f"{m:02d}" for m in range(1, 13)],
            "day": [f"{d:02d}" for d in range(1, 32)],
            "time": [f"{h:02d}:00" for h in range(24)],
            "area": [
                lat + 0.25, lon - 0.25,  # N, W
                lat - 0.25, lon + 0.25,  # S, E
            ],
            "format": "netcdf",
        },
        str(out_path),
    )

    print(f"ERA5 geladen: {plz}")

#läuft manuell oder als separater Batch
#Nicht Teil von Forecast
# Fehler sind erwünscht nicht unterdrücken