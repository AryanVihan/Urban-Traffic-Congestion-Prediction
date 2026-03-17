"""
mcp_servers/prediction_server.py
---------------------------------
FastMCP server — Traffic Prediction & Risk Forecasting.

Tools
-----
predict_congestion      Full 4-agent-style prediction with explanation and action plan
predict_batch_hours     Predict congestion for a list of specific hours in one call
compute_risk_forecast   24-hour risk score forecast (0–100 per hour)
get_feature_vector      Inspect the 27-feature engineering vector without running inference

Resources
---------
traffic://model/info              Model metadata, performance, top features
traffic://model/thresholds        Congestion class bin edges (0-1000, etc.)
traffic://model/feature_importance  Full ranked feature importance list

Run standalone:
    python -m mcp_servers.prediction_server
"""

import json
from mcp.server.fastmcp import FastMCP
from . import core

mcp = FastMCP(
    "Traffic Prediction Server",
    instructions=(
        "Provides ML-powered traffic congestion predictions for Metro I-94 "
        "(Minneapolis – Saint Paul). Supply time, weather, and recent traffic "
        "volume to get congestion level, confidence, explanation, and actions."
    ),
)


# ─────────────────────────────────────────────────────────────────────────────
#  TOOLS
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def predict_congestion(
    hour: int,
    day_of_week: int,
    month: int,
    temp_celsius: float,
    rain_1h: float,
    traffic_lag_1h: float,
    traffic_lag_24h: float,
    traffic_rolling_3h: float,
    traffic_rolling_6h: float,
    snow_1h: float = 0.0,
    clouds_all: int = 40,
    weather_main: str = "Clear",
    is_holiday: int = 0,
) -> dict:
    """
    Predict congestion level for the given conditions.

    Parameters
    ----------
    hour                Hour of day (0–23)
    day_of_week         0=Monday … 6=Sunday
    month               1=January … 12=December
    temp_celsius        Air temperature in °C
    rain_1h             Rainfall in mm/hr
    traffic_lag_1h      Vehicle count from 1 hour ago
    traffic_lag_24h     Vehicle count from the same hour yesterday
    traffic_rolling_3h  3-hour rolling average vehicle count
    traffic_rolling_6h  6-hour rolling average vehicle count
    snow_1h             Snowfall in cm/hr (default 0)
    clouds_all          Cloud cover 0–100% (default 40)
    weather_main        Weather label: Clear, Clouds, Rain, Snow, Fog, etc.
    is_holiday          1 if public holiday, else 0

    Returns
    -------
    dict with keys: prediction, explanation, conditions
    """
    return core.run_prediction(
        hour=hour, day_of_week=day_of_week, month=month,
        temp_celsius=temp_celsius, rain_1h=rain_1h,
        traffic_lag_1h=traffic_lag_1h, traffic_lag_24h=traffic_lag_24h,
        traffic_rolling_3h=traffic_rolling_3h, traffic_rolling_6h=traffic_rolling_6h,
        snow_1h=snow_1h, clouds_all=clouds_all,
        weather_main=weather_main, is_holiday=is_holiday,
    )


@mcp.tool()
def predict_batch_hours(
    hours: list,
    day_of_week: int,
    month: int,
    temp_celsius: float,
    rain_1h: float,
    traffic_lag_1h: float,
    weather_main: str = "Clear",
    is_holiday: int = 0,
) -> list:
    """
    Predict congestion for multiple specific hours in a single call.

    Parameters
    ----------
    hours           List of hours to predict, e.g. [7, 8, 17, 18]
    day_of_week     0=Monday … 6=Sunday
    month           1–12
    temp_celsius    Temperature in °C
    rain_1h         Rainfall mm/hr
    traffic_lag_1h  Last known vehicle count (used to derive lag values)
    weather_main    Weather condition label
    is_holiday      1 if holiday

    Returns
    -------
    List of prediction dicts, one per hour, in the same order as `hours`.
    """
    results = []
    lag24  = traffic_lag_1h * 0.95
    roll3  = traffic_lag_1h * 0.98
    roll6  = traffic_lag_1h * 0.96
    for h in hours:
        r = core.run_prediction(
            hour=h, day_of_week=day_of_week, month=month,
            temp_celsius=temp_celsius, rain_1h=rain_1h,
            traffic_lag_1h=traffic_lag_1h, traffic_lag_24h=lag24,
            traffic_rolling_3h=roll3, traffic_rolling_6h=roll6,
            weather_main=weather_main, is_holiday=is_holiday,
        )
        results.append({
            "hour":        h,
            "label":       r["prediction"]["label"],
            "code":        r["prediction"]["code"],
            "confidence":  r["prediction"]["confidence"],
            "probabilities": r["prediction"]["probabilities"],
            "inference_ms": r["prediction"]["inference_ms"],
        })
    return results


@mcp.tool()
def compute_risk_forecast(
    day_of_week: int,
    month: int,
    weather_code: float,
    rain_1h: float,
    temp_celsius: float,
    is_holiday: int = 0,
) -> dict:
    """
    Compute a 24-hour congestion risk forecast.

    Uses historical median lag values per hour from the full dataset as context,
    so no recent traffic volume is required for this tool.

    Parameters
    ----------
    day_of_week     0=Monday … 6=Sunday
    month           1–12
    weather_code    0=Clear/Clouds, 1=Haze, 2=Smoke/Drizzle, 3=Rain/Mist,
                    4=Fog/Thunderstorm/Snow, 5=Squall
    rain_1h         Rainfall mm/hr
    temp_celsius    Temperature in °C
    is_holiday      1 if public holiday

    Returns
    -------
    dict with keys:
      hourly_risk   list of 24 dicts: hour, label, confidence, risk_score (0–100)
      peak_hour     Hour with highest risk score
      avg_risk      Average risk score across all 24 hours
      severe_hours  List of hours forecast as Severe
      high_hours    List of hours forecast as High
    """
    records = core.run_24h_risk(
        day_of_week=day_of_week, month=month, is_holiday=is_holiday,
        weather_code=weather_code, rain_1h=rain_1h, temp_celsius=temp_celsius,
    )
    peak_rec    = max(records, key=lambda r: r["risk_score"])
    avg_risk    = round(sum(r["risk_score"] for r in records) / len(records), 1)
    severe_hrs  = [r["hour"] for r in records if r["label"] == "Severe"]
    high_hrs    = [r["hour"] for r in records if r["label"] == "High"]

    return {
        "hourly_risk":  records,
        "peak_hour":    peak_rec["hour"],
        "avg_risk":     avg_risk,
        "severe_hours": severe_hrs,
        "high_hours":   high_hrs,
    }


@mcp.tool()
def get_feature_vector(
    hour: int,
    day_of_week: int,
    month: int,
    temp_celsius: float,
    rain_1h: float,
    traffic_lag_1h: float,
    weather_main: str = "Clear",
    is_holiday: int = 0,
) -> dict:
    """
    Return the fully engineered 27-feature vector without running inference.

    Useful for auditing, debugging, and understanding how raw inputs map
    to model features (cyclical encodings, rush-hour flags, severity codes).

    Parameters
    ----------
    hour            Hour of day (0–23)
    day_of_week     0=Monday … 6=Sunday
    month           1–12
    temp_celsius    Temperature °C
    rain_1h         Rainfall mm/hr
    traffic_lag_1h  Last hour vehicle count (lag_24h/rolling derived at 95–98%)
    weather_main    Weather label
    is_holiday      1 if holiday

    Returns
    -------
    dict mapping each of the 27 feature names to its computed value
    """
    lag24 = traffic_lag_1h * 0.95
    roll3 = traffic_lag_1h * 0.98
    roll6 = traffic_lag_1h * 0.96
    return core.build_feature_vector(
        hour=hour, day_of_week=day_of_week, month=month,
        temp_celsius=temp_celsius, rain_1h=rain_1h,
        traffic_lag_1h=traffic_lag_1h, traffic_lag_24h=lag24,
        traffic_rolling_3h=roll3, traffic_rolling_6h=roll6,
        weather_main=weather_main, is_holiday=is_holiday,
    )


@mcp.tool()
def predict_now(
    rain_1h: float = 0.0,
    temp_celsius: float = 15.0,
    lag_1h: float = 3000.0,
    snow_1h: float = 0.0,
    weather_main: str = "Clear",
) -> dict:
    """
    Predict congestion for the current real-world time (uses system clock).

    Returns the same prediction dict as predict_congestion, plus:
      timestamp   ISO-format current datetime
      local_time  HH:MM string
      day_name    e.g. 'Tuesday'
      date        YYYY-MM-DD string

    Parameters
    ----------
    rain_1h       Current rainfall mm/hr (default 0)
    temp_celsius  Current temperature °C (default 15)
    lag_1h        Most recent known vehicle count (default 3000)
    snow_1h       Current snowfall cm/hr (default 0)
    weather_main  Current weather condition (default Clear)
    """
    return core.run_current_prediction(
        rain_1h=rain_1h, temp_celsius=temp_celsius,
        lag_1h=lag_1h, snow_1h=snow_1h, weather_main=weather_main,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  RESOURCES
# ─────────────────────────────────────────────────────────────────────────────

@mcp.resource("traffic://model/info")
def model_info() -> str:
    """Model metadata, performance metrics, and top-10 feature importance."""
    return json.dumps(core.get_model_info(), indent=2)


@mcp.resource("traffic://model/thresholds")
def model_thresholds() -> str:
    """Congestion label definitions and vehicle-volume bin edges."""
    thresholds = {
        "Low":    {"volume_range": "0–1,000 vehicles/hr",   "code": 0},
        "Medium": {"volume_range": "1,001–2,500 vehicles/hr", "code": 1},
        "High":   {"volume_range": "2,501–4,500 vehicles/hr", "code": 2},
        "Severe": {"volume_range": "4,501–7,280 vehicles/hr", "code": 3},
        "note": "Labels assigned using pd.cut on traffic_volume column of Metro I-94 dataset.",
    }
    return json.dumps(thresholds, indent=2)


@mcp.resource("traffic://model/feature_importance")
def feature_importance() -> str:
    """Full ranked feature importance list from the best trained model."""
    fi_df = core.get_fi()
    if fi_df is None:
        return json.dumps({"error": "feature_importance.csv not found. Train the model first."})
    return fi_df[["feature", "importance"]].to_json(orient="records", indent=2)


if __name__ == "__main__":
    mcp.run()
