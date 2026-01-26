# src/weather/era5_autofill.py

from pathlib import Path
import pandas as pd

from src.weather.plz_weights import get_active_plz
from src.weather.era5_coverage import check_era5_coverage
from src.weather.era5_downloader import download_era5_for_plz
from src.weather.era5_convert import convert_nc_to_csv


def ensure_era5_coverage(
    df_gen_raw: pd.DataFrame,
    era5_dir: Path,
    reference_day: str | pd.Timestamp,
    lookback_days: int = 42,
) -> None:
    """
    Stellt sicher, dass für alle aktiven PLZ ERA5 CSVs existieren.
    Fehlende PLZ werden automatisch:
      - heruntergeladen (ERA5)
      - von nc → csv konvertiert
    """

    # --------------------------------------------------
    # 1) Coverage prüfen
    # --------------------------------------------------
    report = check_era5_coverage(
        df_gen_raw=df_gen_raw,
        era5_dir=era5_dir,
        reference_day=reference_day,
        lookback_days=lookback_days,
    )

    missing_plz = report["missing_plz"]

    if not missing_plz:
        print("ERA5 Coverage vollständig ✅")
        return

    print(f"ERA5 fehlt für {len(missing_plz)} PLZ → starte Auto-Fill")
    print("Fehlende PLZ:", missing_plz)

    # --------------------------------------------------
    # 2) Fehlende PLZ automatisch nachziehen
    # --------------------------------------------------
    for plz in missing_plz:
        print(f"→ Lade ERA5 für PLZ {plz}")
        download_era5_for_plz(plz)
        convert_nc_to_csv(plz)

    print("ERA5 Auto-Fill abgeschlossen ✅")
