
import pandas as pd

def get_last_complete_day(df: pd.DataFrame, time_col="DateTimeUtc") -> pd.Timestamp:
    last_ts = pd.to_datetime(df[time_col]).max()
    return last_ts.floor("D")