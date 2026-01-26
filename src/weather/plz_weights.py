# src/weather/plz_registry.py
import pandas as pd

def get_active_plz(
    df_gen_raw: pd.DataFrame,
    reference_time: pd.Timestamp,
    lookback_days: int = 42,
    min_generation: float = 1.0,
) -> pd.Series:
    """
    Returns:
        pd.Series index=PLZ, values=weight (normalized)
    """
    df = df_gen_raw.copy()
    df["DateTimeUtc"] = pd.to_datetime(df["DateTimeUtc"], utc=True)

    start = reference_time - pd.Timedelta(days=lookback_days)

    weights = (
        df.loc[
            (df["DateTimeUtc"] >= start)
            & (df["DateTimeUtc"] < reference_time)
        ]
        .groupby("PostalCode")["Generation"]
        .sum()
    )

    weights = weights[weights >= min_generation]

    if weights.empty:
        raise ValueError("Keine aktiven PLZ im Lookback-Fenster")

    return weights / weights.sum()
