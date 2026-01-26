# src/weather/era5_updater.py

from pathlib import Path
from datetime import date

from src.geo.plz_registry import PLZ_TO_LATLON
from src.weather.era5_downloader import download_era5_for_plz
from src.weather.era5_to_csv import convert_nc_to_csv


ERA5_DIR = Path("era5_plz")
TMP_DIR = Path("era5_tmp")


def update_all_plz(start_year=2024, end_year=None):
    end_year = end_year or date.today().year

    for plz, (lat, lon) in PLZ_TO_LATLON.items():
        print(f"Updating ERA5 for PLZ {plz}")

        download_era5_for_plz(
            plz, lat, lon,
            start_year=start_year,
            end_year=end_year,
            out_dir=TMP_DIR,
        )

        convert_nc_to_csv(
            TMP_DIR / f"era5_{plz}.nc",
            ERA5_DIR / f"era5_{plz}.csv",
        )
