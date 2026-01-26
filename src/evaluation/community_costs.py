# src/evaluation/community_costs.py

import pandas as pd
from pathlib import Path
from datetime import datetime

from src.extract import extract_raw
from src.prep import run_full_preparation
from src.prices.spot_app import read_spot_price_hourly


FORECAST_DIR = Path("data/forecasts")
EVAL_DIR = Path("data/processed")
EVAL_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# Loader
# --------------------------------------------------

def load_forecast(forecast_date: str, variant: str) -> pd.DataFrame:
    path = FORECAST_DIR / f"community_forecast_{forecast_date}_{variant}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Forecast nicht gefunden: {path}")
    return pd.read_parquet(path)


def load_actual_consumption(forecast_date: str) -> pd.DataFrame:
    df_gen_raw, df_con_raw = extract_raw()
    prep = run_full_preparation(df_gen_raw, df_con_raw)

    consumption = prep["consumption_1h"]["ConsumptionCommunity"]

    start = pd.Timestamp(forecast_date, tz="UTC")
    end = start + pd.Timedelta(hours=23)

    return (
        consumption
        .loc[start:end]
        .rename("actual_consumption")
        .reset_index()
        .rename(columns={"index": "DateTimeUtc"})
    )


# --------------------------------------------------
# Kostenberechnung
# --------------------------------------------------

def compute_costs(
    forecast_df: pd.DataFrame,
    actual_df: pd.DataFrame,
    forecast_date: str,
) -> pd.DataFrame:

    df = forecast_df.merge(actual_df, on="DateTimeUtc", how="left")

    df["error_kwh"] = df["forecast_consumption"] - df["actual_consumption"]
    df["abs_error_kwh"] = df["error_kwh"].abs()

    spot = read_spot_price_hourly(
        datetime.fromisoformat(forecast_date).date()
    )

    df = df.merge(spot, on="DateTimeUtc", how="left")

    df["signed_impact_eur"] = (df["error_kwh"] / 1000) * df["spot_eur_per_mwh"]
    df["exposure_eur"] = (df["abs_error_kwh"] / 1000) * df["spot_eur_per_mwh"]

    return df

#--------------------------------------------------------
import numpy as np

def compute_forecast_metrics(
    df_cost: pd.DataFrame,
    cap_quantile: float = 0.995,
) -> pd.DataFrame:
    """
    Berechnet klassische Metriken pro Modell:
    - MAE, RMSE (kWh)
    - nMAE, nRMSE (%) normalisiert auf Capacity (q=0.995 von actual)
    """
    out = []
    for model, g in df_cost.groupby("model"):
        g = g.dropna(subset=["forecast_consumption", "actual_consumption"])
        if g.empty:
            continue

        err = g["forecast_consumption"] - g["actual_consumption"]

        mae = float(err.abs().mean())
        rmse = float(np.sqrt((err ** 2).mean()))

        # Capacity = robustes "Max-Level" der Ist-Werte
        cap = float(g["actual_consumption"].quantile(cap_quantile))
        if not np.isfinite(cap) or cap <= 0:
            cap = float(g["actual_consumption"].max())

        nmae = mae / cap * 100
        nrmse = rmse / cap * 100

        out.append({
            "model": model,
            "MAE_kWh": mae,
            "RMSE_kWh": rmse,
            "nMAE_%": nmae,
            "nRMSE_%": nrmse,
            "Capacity_kWh": cap,
        })

    return pd.DataFrame(out).set_index("model")



# --------------------------------------------------
#  TEMPERATUR-VERGLEICH (SCHRITT A)
# --------------------------------------------------

def compare_temperature_impact(forecast_date: str):
    print(f"\n Temperatur-Impact für {forecast_date}")
    print("====================================")

    actuals = load_actual_consumption(forecast_date)

    results = {}
    summaries = {}

    for variant in ["no_temp", "with_temp"]:
        forecast = load_forecast(forecast_date, variant)
        df_cost = compute_costs(forecast, actuals, forecast_date)

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
        metrics = compute_forecast_metrics(df_cost)

        summary = summary.join(metrics)
        results[variant] = summary

        summaries[variant] = summary

    # --------------------------------------------------
    # Vergleich
    # --------------------------------------------------
    comparison = summaries["with_temp"] - summaries["no_temp"]
    comparison = comparison.rename(columns={
        "daily_exposure_eur": "Δ_exposure_eur",
        "bias_eur": "Δ_bias_eur",
        "p90_eur": "Δ_p90_eur",
        "p95_eur": "Δ_p95_eur",
    })

    comparison = comparison.reset_index()
    comparison["forecast_date"] = forecast_date

    print("\n Tages-Exposure (€)")
    print(
        summaries["no_temp"][["daily_exposure_eur"]]
        .rename(columns={"daily_exposure_eur": "no_temp"})
        .join(
            summaries["with_temp"][["daily_exposure_eur"]]
            .rename(columns={"daily_exposure_eur": "with_temp"})
        )
        .round(2)
    )
    print("\n Forecast-Metriken (nMAE / nRMSE in %) – no_temp")
    print(
        results["no_temp"][["nMAE_%", "nRMSE_%", "MAE_kWh", "RMSE_kWh"]]
        .round(2)
    )

    print("\n Forecast-Metriken (nMAE / nRMSE in %) – with_temp")
    print(
        results["with_temp"][["nMAE_%", "nRMSE_%", "MAE_kWh", "RMSE_kWh"]]
        .round(2)
    )

    print("\n Δ (with_temp − no_temp)")
    print(comparison.round(2))

    print("\n Interpretation:")
    print(" Δ < 0  → Temperatur verbessert den Forecast ")
    print(" Δ > 0  → Temperatur verschlechtert den Forecast ")

    out_path = EVAL_DIR / f"community_temp_compare_{forecast_date}.parquet"
    comparison.to_parquet(out_path, index=False)
    print(f"\n Vergleich gespeichert: {out_path}")
    
    metrics = compute_forecast_metrics(df_cost)

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

    summary = summary.join(metrics)
    results[variant] = summary

    delta_metrics = (
        results["with_temp"][["nMAE_%", "nRMSE_%", "MAE_kWh", "RMSE_kWh"]]
        - results["no_temp"][["nMAE_%", "nRMSE_%", "MAE_kWh", "RMSE_kWh"]]
    ).rename(columns={
        "nMAE_%": "Δ_nMAE_%",
        "nRMSE_%": "Δ_nRMSE_%",
        "MAE_kWh": "Δ_MAE_kWh",
        "RMSE_kWh": "Δ_RMSE_kWh",
    })

    print("\n Δ Forecast-Metriken (with_temp − no_temp)")
    print(delta_metrics.round(2))


    return comparison
