import numpy as np
import pandas as pd
import requests
from io import BytesIO
from datetime import date, timedelta
import matplotlib.pyplot as plt


def aggregate_string(day: date) -> str: 
    # create the day string for request
    return day.strftime("%Y-%m-%dT000000") + "/" + (day + timedelta(days=1)).strftime("%Y-%m-%dT000000")

#date auf day geändert wegen der übersichtlichkeit
def read_spot_price(day: date) -> pd.DataFrame:
    if day > date.today() + timedelta(days=1):
        raise ValueError("Date cannot be after tomorrow")
    day_str = aggregate_string(day)
    URL = "https://transparency.apg.at/api/v1/EXAAD1P/Download/English/PT15M/" + day_str + "?p_exaaMode=EXAA_Full&resolution=PT15M"

    r = requests.get(URL, timeout=30)
    r.raise_for_status()

    df = pd.read_csv(BytesIO(r.content), sep=",")
    if df.empty:
        raise ValueError(f"No data available for date: {day}")

    # delet BOM 
    df.columns = df.columns.str.replace("\ufeff", "").str.strip()
    df.drop(columns= ["Time from [CET/CEST]", "MC Reference price [EUR/MWh]"], inplace=True)
    
    #FIXES 
    df["Time to [CET/CEST]"] = pd.to_datetime(df["Time to [CET/CEST]"]) # in datetime64 objekt umwandeln, davor war zeit string kein datetime
    df = df.set_index("Time to [CET/CEST]") # set_index liefert einen neuen DataFrame; ohne Zuweisung bleibt df unverändert. Deshalb stand im plot auf der x-achse 0 bis 95
    print("df:", df)
    return df

# nur zum testen
df = read_spot_price(date.today() - timedelta(days=5))
df.plot()
plt.show()