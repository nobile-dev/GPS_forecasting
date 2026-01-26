# src/features.py

import numpy as np
import pandas as pd


# ============================================================
# Rolling slope (leakage-frei)
# ============================================================

def rolling_slope(series: pd.Series, window: int):
    y = series.to_numpy(float)
    n = len(y)

    if window > n:
        return np.full(n, np.nan)

    x = np.arange(window)
    x_mean = x.mean()
    x_var = np.sum((x - x_mean) ** 2)

    slopes = np.full(n, np.nan)

    for i in range(window - 1, n):
        y_win = y[i - window + 1 : i + 1]
        y_mean = y_win.mean()
        cov = np.sum((x - x_mean) * (y_win - y_mean))
        slopes[i] = cov / x_var

    return slopes


# ============================================================
# Feature Engineering (LEAKAGE-FREE)
# ============================================================

def make_features_no_leakage(
    series: pd.Series,
    temp_series: pd.Series | None = None,
    lag_list=(24, 48, 72, 168, 336),
    roll_windows=(6, 12, 24, 72, 168, 336),
    diff_list=(1, 24, 168),
):
    idx = series.index
    values = series.to_numpy(float)
    n = len(values)

    feats = {}
    s = pd.Series(values, index=idx)

    # ---------------- LAGS ----------------
    for L in lag_list:
        arr = np.full(n, np.nan)
        if L < n:
            arr[L:] = values[:-L]
        feats[f"lag_{L}"] = arr

    # ---------------- ROLLINGS ------------
    for w in roll_windows:
        roll = s.rolling(w, min_periods=1)

        feats[f"roll_mean_{w}"] = roll.mean().to_numpy()
        feats[f"roll_std_{w}"] = roll.std().to_numpy()
        feats[f"roll_min_{w}"] = roll.min().to_numpy()
        feats[f"roll_max_{w}"] = roll.max().to_numpy()

        feats[f"roll_slope_{w}"] = rolling_slope(s, w)

    # ---------------- DIFFS ---------------
    for d in diff_list:
        arr = np.full(n, np.nan)
        if d < n:
            arr[d:] = values[d:] - values[:-d]
        feats[f"diff_{d}"] = arr

    # ---------------- KALENDER ------------
    feats["hour"] = idx.hour
    feats["weekday"] = idx.weekday
    feats["month"] = idx.month
    feats["is_weekend"] = (idx.weekday >= 5).astype(int)

    # ---------------- TEMPERATUR ----------
    if temp_series is not None:
        temp_series = temp_series.reindex(idx)
        feats["temp"] = temp_series
        feats["temp_lag_24"] = temp_series.shift(24)
        feats["temp_lag_168"] = temp_series.shift(168)
        feats["temp_diff_24"] = temp_series - temp_series.shift(24)

    return pd.DataFrame(feats, index=idx)


# ============================================================
# Dataset Builder (Train/Test – leakage-frei)
# ============================================================

def build_dataset_leakage_free(
    series: pd.Series,
    train_start: pd.Timestamp,
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
    temp_series: pd.Series | None = None,
):
    max_window = 336

    series = series.asfreq("1h").astype(float)

    hist_start = train_start - pd.Timedelta(hours=max_window)

    s_hist = series[(series.index >= hist_start) & (series.index < train_start)]
    s_train = series[(series.index >= train_start) & (series.index < test_start)]
    s_test = series[(series.index >= test_start) & (series.index <= test_end)]

    hist_train = pd.concat([s_hist, s_train]).sort_index()
    hist_train = hist_train.ffill(limit=5000)

    y_train = hist_train.loc[s_train.index]
    y_test = s_test.dropna()

    feats_train_all = make_features_no_leakage(
        hist_train,
        temp_series=temp_series,
    )

    X_train = feats_train_all.loc[y_train.index]
    mask_tr = X_train.notna().all(axis=1) & y_train.notna()
    X_train = X_train[mask_tr]
    y_train = y_train[mask_tr]

    feats_test_all = make_features_no_leakage(
        pd.concat([hist_train, y_test]),
        temp_series=temp_series,
    )

    X_test = feats_test_all.loc[y_test.index]
    mask_te = X_test.notna().all(axis=1) & y_test.notna()
    X_test = X_test[mask_te]
    y_test = y_test[mask_te]

    return X_train, y_train, X_test, y_test
