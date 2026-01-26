# src/forecast/community_one_day.py

import pandas as pd
from pathlib import Path
from typing import Optional

from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
import plotly.graph_objects as go

# Projekt-interne Imports
from src.extract import extract_raw
from src.prep import run_full_preparation
from src.features import build_dataset_leakage_free
from src.weather.temperature import build_temperature_series




# ============================================================
# Output-Verzeichnis
# ============================================================
FORECAST_DIR = Path("data/forecasts")
FORECAST_DIR.mkdir(parents=True, exist_ok=True)


def run_one_day_forecast(
    forecast_date: Optional[str] = None,
    train_days: int = 45,
    use_temperature: bool = False,
):

    """
    Erstellt einen 24h-Community-Forecast (Consumption)

    - forecast_date=None            → PRODUKTION (morgen)
    - forecast_date="YYYY-MM-DD"    → SIMULATION
    """

    # ========================================================
    # 0) Zeitdefinition
    # ========================================================
    if forecast_date is None:
        forecast_start = (
            pd.Timestamp.today(tz="UTC").floor("D")
            + pd.Timedelta(days=1)
        )
        mode = "PRODUCTION"
    else:
        forecast_start = pd.Timestamp(forecast_date, tz="UTC")
        mode = "SIMULATION"

    forecast_end = forecast_start + pd.Timedelta(hours=23)
    train_start = forecast_start - pd.Timedelta(days=train_days)

    print(f"Running one-day forecast for {forecast_start.date()} ({mode})")

    # ========================================================
    # 1) Rohdaten laden
    # ========================================================
    df_gen_raw, df_con_raw = extract_raw()

    prep = run_full_preparation(df_gen_raw, df_con_raw)
    consumption_1h = prep["consumption_1h"]["ConsumptionCommunity"]

    if use_temperature:
        temp_series = build_temperature_series(
            df_gen_raw=df_gen_raw,
            train_start=train_start,
            test_end=forecast_end,
        )
        print(" Temperatur aktiv:", temp_series.shape)
    else:
        temp_series = None



    # ========================================================
    # 2) Feature-Dataset (leakage-frei)
    # ========================================================
    X_train, y_train, X_test, _ = build_dataset_leakage_free(
        series=consumption_1h,
        train_start=train_start,
        test_start=forecast_start,
        test_end=forecast_end,
        temp_series=temp_series,
    )

    # --- sauberer Abbruch ---
    if X_test.empty:
        print(" Keine validen Feature-Zeilen für Forecast-Zeitraum.")
        print(" Wahrscheinlich fehlen noch aktuelle Consumption-Daten im SQL.")
        return None

    if len(X_train) < 100:
        raise ValueError(" Zu wenig Trainingsdaten für Forecast")

    # ========================================================
    # 3) Modelle
    # ========================================================
    models = {
        "RF": RandomForestRegressor(
            n_estimators=400,
            max_depth=15,
            n_jobs=-1,
            random_state=42,
        ),
        "XGB": XGBRegressor(
            n_estimators=400,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
            n_jobs=-1,
            random_state=42,
        ),
    }

    forecasts = []

    # ========================================================
    # 4) Trainieren & Vorhersagen
    # ========================================================
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_hat = model.predict(X_test)

        df_out = pd.DataFrame(
            {
                "DateTimeUtc": X_test.index,
                "forecast_consumption": y_hat,
                "model": name,
                "use_temperature": use_temperature,
                "forecast_day": forecast_start.date().isoformat(),
            }
        )

        forecasts.append(df_out)

    result = pd.concat(forecasts).sort_values("DateTimeUtc")

    # ========================================================
    # 5) Speichern (ZUERST!)
    # ========================================================
    suffix = "with_temp" if use_temperature else "no_temp"
    out_path = FORECAST_DIR / f"community_forecast_{forecast_start.date()}_{suffix}.parquet"

    result.to_parquet(out_path, index=False)
    print(f" Forecast gespeichert: {out_path}")

    # ========================================================
    # 6) Plot (erst NACH dem Speichern!)
    # ========================================================
    fig = go.Figure()

    for model in result["model"].unique():
        df_m = result[result["model"] == model]
        fig.add_trace(
            go.Scatter(
                x=df_m["DateTimeUtc"],
                y=df_m["forecast_consumption"],
                name=f"Forecast {model}",
            )
        )

    fig.update_layout(
        title=f"Community Forecast {forecast_start.date()} ({mode})",
        xaxis_title="Zeit (UTC)",
        yaxis_title="Consumption",
        template="plotly_white",
    )

    plot_path = out_path.with_suffix(".html")
    fig.write_html(plot_path)

    print(f" Plot gespeichert: {plot_path}")

    return result
