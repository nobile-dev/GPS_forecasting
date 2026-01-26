# src/weather/era5_coverage.py

from pathlib import Path
import pandas as pd

from src.weather.plz_weights import get_active_plz


def check_era5_coverage(
    df_gen_raw: pd.DataFrame,
    era5_dir: Path,
    reference_day: str,
    lookback_days: int = 42,
):
    """
    Prüft, für welche aktiven PLZ ERA5-Daten vorhanden sind.

    Returns:
        dict mit Coverage-Infos
    """
    reference_time = pd.Timestamp(reference_day, tz="UTC")

    # 1) Aktive PLZ + Gewichte bestimmen
    weights = get_active_plz(
        df_gen_raw=df_gen_raw,
        reference_time=reference_time,
        lookback_days=lookback_days,
    )

    active_plz = set(weights.index.astype(str))

    # 2) Vorhandene ERA5-CSVs
    existing_plz = {
        p.stem.replace("era5_", "")
        for p in era5_dir.glob("era5_*.csv")
    }

    # 3) Vergleich
    missing_plz = sorted(active_plz - existing_plz)
    covered_plz = sorted(active_plz & existing_plz)

    coverage = weights.loc[covered_plz].sum() if covered_plz else 0.0

    report = {
        "reference_day": reference_day,
        "n_active_plz": len(active_plz),
        "n_with_era5": len(covered_plz),
        "n_missing": len(missing_plz),
        "coverage_pct": round(float(coverage * 100), 2),
        "missing_plz": missing_plz,
    }

    return report
