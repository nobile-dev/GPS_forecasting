import numpy as np
import pandas as pd
import requests
from io import BytesIO
from datetime import date, timedelta
import matplotlib.pyplot as plt


def aggregate_string(day: date) -> str: 
    # create the day string for request
    return day.strftime("%Y-%m-%dT000000") + "/" + (day + timedelta(days=1)).strftime("%Y-%m-%dT000000")

def read_spot_price(date: date) -> pd.DataFrame:
    if date > date.today() + timedelta(days=1):
        raise ValueError("Date cannot be after tommorow")
    day_str = aggregate_string(date)
    URL = "https://transparency.apg.at/api/v1/EXAAD1P/Download/English/PT15M/" + day_str + "?p_exaaMode=EXAA_Full&resolution=PT15M"

    r = requests.get(URL, timeout=30)
    r.raise_for_status()

    df = pd.read_csv(BytesIO(r.content), sep=",")
    if df.empty:
        raise ValueError(f"No data available for date: {date}")

    # delet BOM 
    df.columns = df.columns.str.replace("\ufeff", "").str.strip()
    df.drop(columns= ["Time from [CET/CEST]", "MC Reference price [EUR/MWh]"], inplace=True)
    df.set_index("Time to [CET/CEST]")
    return df

# nur zum testen
df = read_spot_price(date.today() - timedelta(days=5))
df.plot()
plt.show()