import os
import plotly.graph_objects as go
from pathlib import Path

from src.extract import extract_raw
from src.prep import run_full_preparation


PLOT_DIR = Path("plots/prep")
PLOT_DIR.mkdir(parents=True, exist_ok=True)


def plot_consumption_vs_generation():
    # --------------------------------------------------
    # 1) Daten laden & aufbereiten
    # --------------------------------------------------
    df_gen_raw, df_con_raw = extract_raw()
    data = run_full_preparation(df_gen_raw, df_con_raw)

    consumption = data["consumption_1h"]
    generation_by_source = data["generation_1h_by_source"]

    # --------------------------------------------------
    # 2) Plot
    # --------------------------------------------------
    fig = go.Figure()

    # Consumption – Rot
    fig.add_trace(go.Scatter(
        x=consumption.index,
        y=consumption.values,
        mode="lines",
        name="Consumption",
        line=dict(color="red", width=1.8),
    ))

    # Generation je Quelle
    color_map = {
        "pv_sued": "gold",
        "pv_ostwest": "orange",
        "water": "blue",
        "wind": "green",
        "biomass": "brown",
    }

    for source, series in generation_by_source.items():
        fig.add_trace(go.Scatter(
            x=series.index,
            y=series.values,
            mode="lines",
            name=f"Generation {source}",
            line=dict(width=1.2, color=color_map.get(source, "grey")),
        ))
        
    gen_total = sum(generation_by_source.values())

    fig.add_trace(go.Scatter(
        x=gen_total.index,
        y=gen_total.values,
        mode="lines",
        name="Generation Total (Community)",
        line=dict(color="black", width=2.5, dash="dot"),
    ))

    # --------------------------------------------------
    # 3) Layout
    # --------------------------------------------------
    fig.update_layout(
        title="Energy Community – Consumption vs Generation by Source (Community Share)"
,
        xaxis_title="Zeit (UTC)",
        yaxis_title="Energie [kWh] (Community)"
,
        hovermode="x unified",
        template="plotly_white",
        legend=dict(title="Datenreihen"),
    )


    # --------------------------------------------------
    # 4) Speichern
    # --------------------------------------------------
    out_path = PLOT_DIR / "consumption_vs_generation.html"
    fig.write_html(out_path)

    print(f" Plot gespeichert: {out_path}")


if __name__ == "__main__":
    plot_consumption_vs_generation()
