# src/evaluation/community_backtest.py

import pandas as pd
from datetime import timedelta

from src.evaluation.community_costs import compute_costs, load_actual_consumption
from pathlib import Path

FORECAST_DIR = Path("data/forecasts")
OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(exist_ok=True)

def run_temperature_backtest(
    end_date: str,
    n_days: int = 7,
) -> pd.DataFrame:

    end = pd.Timestamp(end_date)
    days = [end - timedelta(days=i) for i in range(n_days)]

    rows = []

    for day in days:
        day_str = day.date().isoformat()
        print(f"\n Backtest {day_str}")

        actuals = load_actual_consumption(day_str)

        results = {}

        for variant in ["no_temp", "with_temp"]:
            path = FORECAST_DIR / f"community_forecast_{day_str}_{variant}.parquet"
            if not path.exists():
                print(f"  ⚠️ fehlt: {path}")
                continue

            df_fc = pd.read_parquet(path)
            df_cost = compute_costs(df_fc, actuals, day_str)

            summary = (
                df_cost
                .groupby("model")
                .agg(
                    daily_exposure_eur=("exposure_eur", "sum"),
                    bias_eur=("signed_impact_eur", "sum"),
                    p90_eur=("exposure_eur", lambda x: x.quantile(0.9)),
                    p95_eur=("exposure_eur", lambda x: x.quantile(0.95)),
                )
            )

            results[variant] = summary

        # ------------------------------
        # Vergleich no_temp vs with_temp
        # ------------------------------
# Vergleich nur wenn beide Varianten existieren
# ------------------------------
        if not {"no_temp", "with_temp"}.issubset(results):
            print(f"  ⏭️ Überspringe {day_str} (Forecasts unvollständig)")
            continue

        for model in results["no_temp"].index:
            no_t = results["no_temp"].loc[model]
            with_t = results["with_temp"].loc[model]


            delta = with_t["daily_exposure_eur"] - no_t["daily_exposure_eur"]

            rows.append({
                "date": day_str,
                "model": model,
                "no_temp_eur": round(no_t["daily_exposure_eur"], 2),
                "with_temp_eur": round(with_t["daily_exposure_eur"], 2),
                "delta_eur": round(delta, 2),
                "verdict": "better" if delta < 0 else "worse",
            })

    df = pd.DataFrame(rows).sort_values(["date", "model"])

    out = OUT_DIR / f"temperature_backtest_{end_date}_{n_days}d.parquet"
    df.to_parquet(out, index=False)
    df.to_csv(out.with_suffix(".csv"), index=False)

    print(f"\n Backtest gespeichert: {out}")
    return df
