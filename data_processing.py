"""
data_processing.py
------------------
Full data pipeline for the Metro Interstate Traffic dataset.
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

CONGESTION_BINS   = [0, 1000, 2500, 4500, 7300]
CONGESTION_LABELS = ["Low", "Medium", "High", "Severe"]
CONGESTION_MAP    = {"Low": 0, "Medium": 1, "High": 2, "Severe": 3}
MORNING_RUSH = (7, 9)
EVENING_RUSH = (16, 18)


def load_raw(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df["date_time"] = pd.to_datetime(df["date_time"])
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates()
    # Fix temp=0 (sensor errors)
    bad = df["temp"] == 0
    if bad.any():
        medians = df.groupby(df["date_time"].dt.hour)["temp"].median()
        df.loc[bad, "temp"] = df.loc[bad, "date_time"].dt.hour.map(medians)
    # Cap extreme rain outlier
    df["rain_1h"] = df["rain_1h"].clip(upper=50.0)
    # Fill holiday NaN
    df["holiday"] = df["holiday"].fillna("None")
    return df.reset_index(drop=True)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values("date_time").reset_index(drop=True)
    dt = df["date_time"]

    # Time
    df["hour"]        = dt.dt.hour
    df["day_of_week"] = dt.dt.dayofweek
    df["month"]       = dt.dt.month
    df["year"]        = dt.dt.year
    df["day_of_year"] = dt.dt.dayofyear
    df["is_weekend"]  = (df["day_of_week"] >= 5).astype(int)

    # Rush hours
    df["is_morning_rush"] = df["hour"].between(*MORNING_RUSH).astype(int)
    df["is_evening_rush"] = df["hour"].between(*EVENING_RUSH).astype(int)
    df["is_rush_hour"]    = (df["is_morning_rush"] | df["is_evening_rush"]).astype(int)
    df["rush_type"]       = 0
    df.loc[df["is_morning_rush"] == 1, "rush_type"] = 1
    df.loc[df["is_evening_rush"] == 1, "rush_type"] = 2

    # Cyclical encoding
    df["hour_sin"]  = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"]  = np.cos(2 * np.pi * df["hour"] / 24)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    df["is_holiday"] = (df["holiday"] != "None").astype(int)

    # Weather
    df["temp_celsius"] = df["temp"] - 273.15
    df["is_raining"]   = (df["rain_1h"] > 0).astype(int)
    df["is_snowing"]   = (df["snow_1h"] > 0).astype(int)
    rain_sev = pd.cut(df["rain_1h"], bins=[-0.1, 0, 2.5, 7.6, 55],
                      labels=[0, 1, 2, 3]).astype(float)
    df["weather_severity"] = rain_sev + (df["snow_1h"] > 0).astype(float)
    weather_order = {"Clear":0,"Clouds":1,"Haze":1,"Smoke":2,"Drizzle":2,
                     "Rain":3,"Mist":3,"Fog":4,"Thunderstorm":4,"Snow":4,"Squall":5}
    df["weather_code"] = df["weather_main"].map(weather_order).fillna(2)

    # Lag / rolling (time-series features)
    df["traffic_lag_1h"]     = df["traffic_volume"].shift(1).fillna(df["traffic_volume"].median())
    df["traffic_lag_24h"]    = df["traffic_volume"].shift(24).fillna(df["traffic_volume"].median())
    df["traffic_rolling_3h"] = df["traffic_volume"].shift(1).rolling(3, min_periods=1).mean().fillna(df["traffic_volume"].median())
    df["traffic_rolling_6h"] = df["traffic_volume"].shift(1).rolling(6, min_periods=1).mean().fillna(df["traffic_volume"].median())

    return df


def create_congestion_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["congestion_label"] = pd.cut(
        df["traffic_volume"], bins=CONGESTION_BINS,
        labels=CONGESTION_LABELS, include_lowest=True
    )
    df["congestion_code"] = df["congestion_label"].map(CONGESTION_MAP)
    return df


FEATURE_COLS = [
    "hour", "day_of_week", "month", "year", "day_of_year",
    "is_weekend", "is_rush_hour", "rush_type",
    "is_morning_rush", "is_evening_rush",
    "hour_sin", "hour_cos", "month_sin", "month_cos",
    "is_holiday",
    "temp_celsius", "rain_1h", "snow_1h", "clouds_all",
    "is_raining", "is_snowing", "weather_severity", "weather_code",
    "traffic_lag_1h", "traffic_lag_24h",
    "traffic_rolling_3h", "traffic_rolling_6h",
]


def build_X_y(df: pd.DataFrame):
    X = df[FEATURE_COLS].copy()
    y = df["congestion_code"].values
    return X, y


def full_pipeline(filepath: str):
    df = load_raw(filepath)
    df = clean(df)
    df = engineer_features(df)
    df = create_congestion_labels(df)
    df = df.dropna(subset=["congestion_code"]).reset_index(drop=True)
    X, y = build_X_y(df)
    return df, X, y


def get_peak_hours_analysis(df: pd.DataFrame) -> dict:
    hourly  = df.groupby("hour")["traffic_volume"].mean().round(1)
    daily   = df.groupby("day_of_week")["traffic_volume"].mean().round(1)
    monthly = df.groupby("month")["traffic_volume"].mean().round(1)

    day_names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    daily.index = [day_names[i] for i in daily.index]

    return {
        "hourly_avg":    {int(k): float(v) for k, v in hourly.items()},
        "daily_avg":     daily.to_dict(),
        "monthly_avg":   {int(k): float(v) for k, v in monthly.items()},
        "peak_hour":     int(hourly.idxmax()),
        "trough_hour":   int(hourly.idxmin()),
        "peak_day":      daily.idxmax(),
        "worst_month":   int(monthly.idxmax()),
        "weekend_avg":   float(df[df["is_weekend"]==1]["traffic_volume"].mean().round(1)),
        "weekday_avg":   float(df[df["is_weekend"]==0]["traffic_volume"].mean().round(1)),
        "holiday_avg":   float(df[df["is_holiday"]==1]["traffic_volume"].mean().round(1)) if df["is_holiday"].sum() > 0 else 0.0,
        "rush_avg":      float(df[df["is_rush_hour"]==1]["traffic_volume"].mean().round(1)),
        "weather_impact": df.groupby("weather_main")["traffic_volume"].mean().round(1).to_dict(),
    }
