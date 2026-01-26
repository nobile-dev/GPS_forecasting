import pandas as pd


from pathlib import Path
import plotly.graph_objects as go


# 1) Netzbetreiber -> Bundesland
netzbetreiber_map = {
    "001000": ("Wiener Netze GmbH", "Wien"),
    "002000": ("EVN Netz GmbH", "Niederösterreich"),
    "003000": ("Netz Oberösterreich GmbH", "Oberösterreich"),
    "004000": ("Energie AG Oberösterreich Netz GmbH", "Oberösterreich"),
    "005000": ("Linz Strom Netz GmbH", "Oberösterreich"),
    "006000": ("Salzburg Netz GmbH", "Salzburg"),
    "007000": ("Kärnten Netz GmbH", "Kärnten"),
    "008000": ("Vorarlberger Energienetze GmbH", "Vorarlberg"),
    "009000": ("TIWAG Netz AG", "Tirol"),
    "010000": ("Netz Burgenland Strom GmbH", "Burgenland"),
    "011000": ("Energie Steiermark Netz GmbH", "Steiermark"),
}

def get_federal_state_from_number(number):
    if not isinstance(number, str) or len(number) < 8:
        return None
    code = number[2:8]
    info = netzbetreiber_map.get(code)
    return info[1] if info else None

def add_state_columns(df_gen_raw: pd.DataFrame, df_con_raw: pd.DataFrame):
    df_gen_raw = df_gen_raw.copy()
    df_con_raw = df_con_raw.copy()

    df_gen_raw["FederalStateFromMeteringPoint"] = df_gen_raw["Number"].apply(get_federal_state_from_number)
    df_con_raw["FederalStateFromMeteringPoint"] = df_con_raw["Number"].apply(get_federal_state_from_number)

    return df_gen_raw, df_con_raw

def aggregate_consumption_1h(df_con_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_con_raw.copy()
    df["DateTimeUtc"] = pd.to_datetime(df["DateTimeUtc"], utc=True)

    sum_cols = ["Consumption", "ConsumptionCommunity"]
    df_agg = (
        df.set_index("DateTimeUtc")[sum_cols]
        .resample("1h")
        .sum(min_count=1)
        .reset_index()
        .set_index("DateTimeUtc")
    )
    return df_agg

def resample_generation_1h(df_gen_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_gen_raw.copy()
    df["DateTimeUtc"] = pd.to_datetime(df["DateTimeUtc"], utc=True)

    # alles numeric summen (Generation, GenerationCommunity), andere first
    # pragmatisch: wir nehmen nur die beiden relevanten Summen
    df_agg = (
        df.set_index("DateTimeUtc")[["Generation", "GenerationCommunity"]]
        .resample("1h")
        .sum(min_count=1)
        .reset_index()
        .set_index("DateTimeUtc")
    )
    return df_agg

def prepare_generation_by_source_1h(df_gen_raw: pd.DataFrame) -> dict:
    energy_source_map = {
        '1': 'pv_sued',
        '2': 'pv_ostwest',
        '3': 'water',
        '4': 'wind',
        '5': 'biomass',
        'G1': 'pv_all'
    }

    df = df_gen_raw.copy()
    df["DateTimeUtc"] = pd.to_datetime(df["DateTimeUtc"], utc=True)

    gen_1h = {}

    for key, name in energy_source_map.items():
        df_part = df[df["EnergySource"].astype(str) == key]
        if len(df_part) == 0:
            continue

        gen_1h[name] = (
            df_part
            .set_index("DateTimeUtc")[["Generation", "GenerationCommunity"]]
            .resample("1h")
            .sum(min_count=1)
        )

    return gen_1h


def run_full_preparation(df_gen_raw: pd.DataFrame,
                          df_con_raw: pd.DataFrame):
    """
    Zentrale Datenaufbereitung:
    - Bundesland
    - 1h Aggregation
    - Generation nach Source
    """

    # 1) Bundesländer
    df_gen_raw, df_con_raw = add_state_columns(df_gen_raw, df_con_raw)

    # 2) Consumption 1h
    con_1h = aggregate_consumption_1h(df_con_raw)

    # 3) Generation gesamt 1h
    gen_1h_total = resample_generation_1h(df_gen_raw)

    # 4) Generation nach Source 1h
    gen_1h_by_source = prepare_generation_by_source_1h(df_gen_raw)

    return {
        "consumption_1h": con_1h,
        "generation_1h_total": gen_1h_total,
        "generation_1h_by_source": gen_1h_by_source,
    }



def plot_consumption_vs_generation(
    consumption_1h,
    generation_by_source: dict,
    out_dir: Path
):
    out_dir.mkdir(parents=True, exist_ok=True)
    
    if "ConsumptionCommunity" not in consumption_1h.columns:
        raise ValueError("ConsumptionCommunity fehlt - Plot nicht möglich")


    fig = go.Figure()

    # Consumption
    fig.add_trace(go.Scatter(
        x=consumption_1h.index,
        y=consumption_1h["ConsumptionCommunity"],
        name="Consumption Community",
        line=dict(color="red", width=2)
    ))

    colors = {
        "pv_sued": "gold",
        "pv_ostwest": "orange",
        "wind": "green",
        "water": "blue",
        "biomass": "brown",
        "pv_all": "purple",
    }

    for src, df in generation_by_source.items():
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["GenerationCommunity"],
            name=f"Generation {src}",
            line=dict(color=colors.get(src, "gray"), width=1)
        ))

    fig.update_layout(
        title="Consumption vs Generation (Community)",
        hovermode="x unified",
        template="plotly_white"
    )

    out_path = out_dir / "consumption_vs_generation.html"
    fig.write_html(out_path)

    print(f" Plot gespeichert: {out_path}")

def plot_consumption_only(
    consumption_1h: pd.DataFrame,
    out_dir: Path
):
    out_dir.mkdir(parents=True, exist_ok=True)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=consumption_1h.index,
        y=consumption_1h["ConsumptionCommunity"],
        mode="lines",
        name="Consumption Community",
        line=dict(color="red", width=2)
    ))

    fig.update_layout(
        title="Community Consumption (1h)",
        xaxis_title="Time (UTC)",
        yaxis_title="Energy [kWh]",
        hovermode="x unified",
        template="plotly_white"
    )

    out_path = out_dir / "consumption_only.html"
    fig.write_html(out_path)

    print(f"📈 Consumption-Plot gespeichert: {out_path}")
