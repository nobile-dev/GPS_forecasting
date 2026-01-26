from datetime import date, timedelta
from io import BytesIO
import pandas as pd
import requests


def read_spot_price_hourly(day: date) -> pd.DataFrame:
    """
    Returns:
        DateTimeUtc | spot_eur_per_mwh
        (24 rows)
    """
    if day > date.today() + timedelta(days=1):
        raise ValueError("Date cannot be after tomorrow")

    day_str = (
        day.strftime("%Y-%m-%dT000000")
        + "/"
        + (day + timedelta(days=1)).strftime("%Y-%m-%dT000000")
    )

    url = (
        "https://transparency.apg.at/api/v1/EXAAD1P/Download/English/PT15M/"
        + day_str
        + "?p_exaaMode=EXAA_Full&resolution=PT15M"
    )

    r = requests.get(url, timeout=30)
    r.raise_for_status()

    df = pd.read_csv(BytesIO(r.content), sep=",")
    if df.empty:
        raise ValueError(f"No spot price data for {day}")

    df.columns = df.columns.str.replace("\ufeff", "").str.strip()

    df = df.drop(
        columns=[
            "Time from [CET/CEST]",
            "MC Reference price [EUR/MWh]",
        ]
    )

    df["Time to [CET/CEST]"] = pd.to_datetime(df["Time to [CET/CEST]"])
    df = df.set_index("Time to [CET/CEST]")

    df.index = (
        df.index
        .tz_localize("Europe/Vienna")
        .tz_convert("UTC")
    )

    df = df.rename(
     columns={"Price MC Auction [EUR/MWh]": "spot_eur_per_mwh"}
    )
    

    df_hourly = (
        df
        .resample("h")
        .mean()
        .reset_index()
        .rename(columns={"index": "DateTimeUtc"})
    )
    
    # ---------WICHTIG: exakt auf Forecast Tag in UTC beschreiben, sonst gibt es immer 25h im winter
    
      # 15min → hourly (Index bleibt DateTimeIndex!)
    df_hourly = df.resample("h").mean()

    # exakt Forecast-Tag in UTC
    start_utc = pd.Timestamp(day, tz="UTC")
    end_utc = start_utc + pd.Timedelta(hours=23)

    # JETZT slicen (Index ist DateTimeIndex → funktioniert)
    df_hourly = df_hourly.loc[(df_hourly.index >= start_utc) & 
                              (df_hourly.index <= end_utc)]

    # erst ganz am Ende reset_index
    df_hourly = (
        df_hourly
        .reset_index()
        .rename(columns={"Time to [CET/CEST]": "DateTimeUtc"})
    )

    
    
    return df_hourly
