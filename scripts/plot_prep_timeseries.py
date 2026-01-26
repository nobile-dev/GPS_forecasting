# scripts/plot_prep_timeseries.py

import os
import plotly.graph_objects as go

from src.extract import extract_raw
from src.prep import run_full_preparation

PLOT_DIR = "plots/prep"
os.makedirs(PLOT_DIR, exist_ok=True)


def plot_consumption_vs_generation():
    # -----------------------------
    # Daten laden & vorbereiten
    # -----------------------------
    df_gen_raw, df_con_raw = extract_raw()
    prep = run_full_preparation(df_gen_raw, df_con_raw)

    pv = prep["generation_1h"]["PV"]
    water = prep["generation_1h"]["Water"]
    consumption = prep["consumption_1h"]["ConsumptionCommunity"]

    # -----------------------------
    # Plot
    # -----------------------------
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=pv.index,
        y=pv.values,
        mode="lines",
        name="PV Generation",
        line=dict(color="gold", width=1.5),
    ))

    fig.add_trace(go.Scatter(
        x=water.index,
        y=water.values,
        mode="lines",
        name="Water Generation",
        line=dict(color="blue", width=1.5),
    ))

    fig.add_trace(go.Scatter(
        x=consumption.index,
        y=consumption.values,
        mode="lines",
        name="Consumption",
        line=dict(color="red", width=1.5),
    ))

    fig.update_layout(
        title="Consumption vs PV and Water Generation",
        xaxis_title="Zeit (UTC)",
        yaxis_title="Energie [kWh]",
        hovermode="x unified",
        template="plotly_white",
    )

    out_path = os.path.join(PLOT_DIR, "consumption_vs_generation.html")
    fig.write_html(out_path)
    print(f" Plot gespeichert: {out_path}")


if __name__ == "__main__":
    plot_consumption_vs_generation()
