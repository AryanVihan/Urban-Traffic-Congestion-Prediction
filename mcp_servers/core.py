"""
mcp_servers/core.py
-------------------
Shared business-logic layer for all MCP servers and the Streamlit bridge.

This module provides lazy-loaded singletons (model, DataFrame, peak data,
feature importance) and pure-function wrappers around the project's core
logic.  Every MCP server imports from here — no model or data loading is
duplicated across server processes.

All public functions return plain Python dicts / lists (JSON-serialisable).
"""

from __future__ import annotations
import os, sys, json, time
import numpy as np
from datetime import datetime, date
from functools import lru_cache
from typing import Optional

# ── Resolve project root so imports work regardless of cwd ────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

_MODEL_PATH = os.path.join(_ROOT, "model.pkl")
_DATA_PATH  = os.path.join(_ROOT, "Metro_Interstate_Traffic_Volume.csv")
_FI_PATH    = os.path.join(_ROOT, "feature_importance.csv")
_RES_PATH   = os.path.join(_ROOT, "model_results.json")

# ── Lazy singletons ───────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_model():
    """Load and cache the trained sklearn model from model.pkl."""
    import joblib
    if not os.path.exists(_MODEL_PATH):
        raise FileNotFoundError(
            "model.pkl not found. Run 'Train / Retrain' in the Streamlit sidebar first."
        )
    return joblib.load(_MODEL_PATH)


@lru_cache(maxsize=1)
def get_df_and_peak():
    """Run the full data pipeline and cache (df, peak_data)."""
    from data_processing import full_pipeline, get_peak_hours_analysis
    df, _, _ = full_pipeline(_DATA_PATH)
    peak     = get_peak_hours_analysis(df)
    return df, peak


@lru_cache(maxsize=1)
def get_fi():
    """Load and cache feature importance CSV (returns None if not found)."""
    import pandas as pd
    if os.path.exists(_FI_PATH):
        return pd.read_csv(_FI_PATH)
    return None


@lru_cache(maxsize=1)
def get_model_results():
    """Load model comparison results JSON (returns {} if not found)."""
    if os.path.exists(_RES_PATH):
        with open(_RES_PATH) as f:
            return json.load(f)
    return {}


# ── Feature-vector builder (single source of truth) ──────────────────────────

def build_feature_vector(
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
    Build the full 27-feature engineering vector.
    This is the single authoritative implementation used by all MCP servers,
    the bridge, and transitively by every prediction function.
    """
    from data_processing import FEATURE_COLS

    _W_MAP = {
        "Clear": 0, "Clouds": 1, "Haze": 1, "Smoke": 2, "Drizzle": 2,
        "Rain": 3, "Mist": 3, "Fog": 4, "Thunderstorm": 4, "Snow": 4, "Squall": 5,
    }
    is_weekend      = 1 if day_of_week >= 5 else 0
    is_morning_rush = 1 if 7  <= hour <= 9  else 0
    is_evening_rush = 1 if 16 <= hour <= 18 else 0
    is_rush_hour    = int(bool(is_morning_rush or is_evening_rush))
    rush_type       = 1 if is_morning_rush else (2 if is_evening_rush else 0)
    rain_sev        = (0 if rain_1h == 0 else 1 if rain_1h < 2.5 else 2 if rain_1h < 7.6 else 3)
    weather_code    = float(_W_MAP.get(weather_main, 2))
    today           = date.today()

    fv = {
        "hour": hour, "day_of_week": day_of_week, "month": month,
        "year": today.year, "day_of_year": today.timetuple().tm_yday,
        "is_weekend": is_weekend, "is_rush_hour": is_rush_hour,
        "rush_type": rush_type, "is_morning_rush": is_morning_rush,
        "is_evening_rush": is_evening_rush,
        "hour_sin":  np.sin(2 * np.pi * hour  / 24),
        "hour_cos":  np.cos(2 * np.pi * hour  / 24),
        "month_sin": np.sin(2 * np.pi * month / 12),
        "month_cos": np.cos(2 * np.pi * month / 12),
        "is_holiday":        int(is_holiday),
        "temp_celsius":      float(temp_celsius),
        "rain_1h":           float(rain_1h),
        "snow_1h":           float(snow_1h),
        "clouds_all":        float(clouds_all),
        "is_raining":        int(rain_1h > 0),
        "is_snowing":        int(snow_1h > 0),
        "weather_severity":  float(rain_sev + int(snow_1h > 0)),
        "weather_code":      weather_code,
        "traffic_lag_1h":    float(traffic_lag_1h),
        "traffic_lag_24h":   float(traffic_lag_24h),
        "traffic_rolling_3h": float(traffic_rolling_3h),
        "traffic_rolling_6h": float(traffic_rolling_6h),
    }
    # Return only FEATURE_COLS in correct order as dict
    return {col: fv[col] for col in FEATURE_COLS}


# ── Core prediction ───────────────────────────────────────────────────────────

def run_prediction(
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
    Run ML inference for the given conditions.
    Returns a complete prediction report with label, confidence,
    probabilities, inference timing, and explanation.
    """
    from data_processing import FEATURE_COLS, CONGESTION_LABELS
    from insights import explain_prediction

    model   = get_model()
    fi_df   = get_fi()

    fv_dict = build_feature_vector(
        hour, day_of_week, month, temp_celsius, rain_1h,
        traffic_lag_1h, traffic_lag_24h, traffic_rolling_3h, traffic_rolling_6h,
        snow_1h, clouds_all, weather_main, is_holiday,
    )

    X = np.array([[fv_dict[c] for c in FEATURE_COLS]])

    t0         = time.time()
    pred_code  = int(model.predict(X)[0])
    elapsed_ms = (time.time() - t0) * 1000
    pred_label = CONGESTION_LABELS[pred_code]

    confidence = None
    proba_dict = {}
    if hasattr(model, "predict_proba"):
        proba      = model.predict_proba(X)[0]
        confidence = round(float(proba[pred_code]) * 100, 1)
        proba_dict = {
            CONGESTION_LABELS[i]: round(float(p) * 100, 1)
            for i, p in enumerate(proba)
        }

    explanation = explain_prediction(pred_label, fv_dict, fi_df)

    return {
        "prediction": {
            "label":             pred_label,
            "code":              pred_code,
            "confidence":        confidence,
            "probabilities":     proba_dict,
            "inference_ms":      round(elapsed_ms, 1),
        },
        "explanation": {
            "narrative":          explanation["prediction_narrative"],
            "contributing_factors": [
                {"factor": f["factor"], "impact": f["impact"], "detail": f["detail"]}
                for f in explanation["contributing_factors"]
            ],
            "level_info": explanation["level_info"],
        },
        "conditions": {
            "hour": hour, "day_of_week": day_of_week, "month": month,
            "is_rush_hour":  fv_dict["is_rush_hour"],
            "is_weekend":    fv_dict["is_weekend"],
            "temp_celsius":  temp_celsius,
            "rain_1h":       rain_1h,
            "weather_main":  weather_main,
        },
    }


def run_current_prediction(
    rain_1h: float = 0.0,
    temp_celsius: float = 15.0,
    lag_1h: float = 3000.0,
    snow_1h: float = 0.0,
    weather_main: str = "Clear",
) -> dict:
    """
    Run prediction for the current real-world time (system clock).
    Useful for 'what is traffic like right now?' queries.
    """
    now  = datetime.now()
    lag24  = lag_1h * 0.95
    roll3  = lag_1h * 0.98
    roll6  = lag_1h * 0.96

    result = run_prediction(
        hour=now.hour, day_of_week=now.weekday(), month=now.month,
        temp_celsius=temp_celsius, rain_1h=rain_1h,
        traffic_lag_1h=lag_1h, traffic_lag_24h=lag24,
        traffic_rolling_3h=roll3, traffic_rolling_6h=roll6,
        snow_1h=snow_1h, weather_main=weather_main,
    )
    result["timestamp"]  = now.isoformat()
    result["local_time"] = now.strftime("%H:%M")
    result["day_name"]   = now.strftime("%A")
    result["date"]       = now.strftime("%Y-%m-%d")
    return result


def run_24h_risk(
    day_of_week: int,
    month: int,
    is_holiday: int = 0,
    weather_code: float = 0.0,
    rain_1h: float = 0.0,
    temp_celsius: float = 15.0,
) -> list[dict]:
    """
    Run 24-hour risk forecast using compute_24h_risk from analytics.py.
    Returns list of 24 dicts with hour, label, confidence, risk_score.
    """
    from analytics import compute_24h_risk
    df, _ = get_df_and_peak()
    model  = get_model()
    risk_df = compute_24h_risk(
        model       = model,
        day_of_week = day_of_week,
        month       = month,
        is_holiday  = is_holiday,
        weather_code= weather_code,
        rain_1h     = rain_1h,
        temp_c      = temp_celsius,
        df_ref      = df,
    )
    return risk_df.to_dict(orient="records")


# ── Analytics helpers ─────────────────────────────────────────────────────────

def get_dataset_stats() -> dict:
    """Return high-level dataset statistics."""
    df, peak = get_df_and_peak()
    return {
        "total_records":  len(df),
        "date_range":     {
            "start": str(df["date_time"].min().date()),
            "end":   str(df["date_time"].max().date()),
        },
        "years_covered":   int(df["date_time"].dt.year.nunique()),
        "avg_volume":      round(float(df["traffic_volume"].mean()), 1),
        "median_volume":   float(df["traffic_volume"].median()),
        "max_volume":      int(df["traffic_volume"].max()),
        "min_volume":      int(df["traffic_volume"].min()),
        "peak_hour":       peak["peak_hour"],
        "trough_hour":     peak["trough_hour"],
        "peak_day":        peak["peak_day"],
        "weekday_avg":     round(peak["weekday_avg"], 1),
        "weekend_avg":     round(peak["weekend_avg"], 1),
        "holiday_avg":     round(peak["holiday_avg"], 1),
        "rush_avg":        round(peak["rush_avg"],    1),
    }


def get_hourly_profile() -> dict:
    """Return average traffic volume for each hour (0–23)."""
    _, peak = get_df_and_peak()
    return {
        "hourly_avg":  {int(k): round(v, 1) for k, v in peak["hourly_avg"].items()},
        "peak_hour":   peak["peak_hour"],
        "trough_hour": peak["trough_hour"],
    }


def get_congestion_distribution() -> dict:
    """Return count and percentage per congestion level."""
    df, _ = get_df_and_peak()
    n     = len(df)
    counts = df["congestion_label"].value_counts().to_dict()
    return {
        lvl: {"count": int(counts.get(lvl, 0)),
              "pct":   round(counts.get(lvl, 0) / n * 100, 1)}
        for lvl in ["Low", "Medium", "High", "Severe"]
    }


def get_weather_impact() -> list[dict]:
    """Return weather conditions sorted by average traffic volume."""
    _, peak = get_df_and_peak()
    return [
        {"condition": k, "avg_volume": round(v, 1)}
        for k, v in sorted(peak["weather_impact"].items(), key=lambda x: -x[1])
    ]


def get_rush_stats() -> dict:
    """Return rush-hour statistics."""
    _, peak = get_df_and_peak()
    weekday_avg = peak["weekday_avg"]
    rush_avg    = peak["rush_avg"]
    return {
        "morning_rush": {"start": 7,  "end": 9},
        "evening_rush": {"start": 16, "end": 18},
        "rush_avg":        round(rush_avg,    1),
        "weekday_avg":     round(weekday_avg, 1),
        "weekend_avg":     round(peak["weekend_avg"], 1),
        "holiday_avg":     round(peak["holiday_avg"], 1),
        "rush_premium_pct": round((rush_avg - weekday_avg) / max(weekday_avg, 1) * 100, 1),
    }


def compare_weekday_weekend() -> dict:
    """Return weekday vs weekend detailed comparison."""
    df, peak = get_df_and_peak()
    wkday = df[df["is_weekend"] == 0]
    wkend = df[df["is_weekend"] == 1]
    peak_wkday_hour = int(wkday.groupby("hour")["traffic_volume"].mean().idxmax())
    peak_wkend_hour = int(wkend.groupby("hour")["traffic_volume"].mean().idxmax())
    wkday_avg = peak["weekday_avg"]
    wkend_avg = peak["weekend_avg"]
    return {
        "weekday_avg":      round(wkday_avg, 1),
        "weekend_avg":      round(wkend_avg, 1),
        "diff_pct":         round((wkday_avg - wkend_avg) / max(wkday_avg, 1) * 100, 1),
        "peak_weekday_hour": peak_wkday_hour,
        "peak_weekend_hour": peak_wkend_hour,
    }


# ── Map / corridor helpers ────────────────────────────────────────────────────

def get_segment_congestion(
    hour: int,
    day_of_week: int,
    month: int,
    rain_1h: float = 0.0,
    temp_celsius: float = 18.0,
    traffic_lag_1h: float = 3500.0,
    is_holiday: int = 0,
) -> dict:
    """
    Compute per-segment congestion for the I-94 corridor without Folium.
    Returns base prediction + list of segment dicts with label/color.
    """
    from map_view import I94_SEGMENTS, LABELS, COLORS, _code_for_factor

    lag24  = traffic_lag_1h * 0.95
    roll3  = traffic_lag_1h * 0.98
    roll6  = traffic_lag_1h * 0.96

    base_result = run_prediction(
        hour=hour, day_of_week=day_of_week, month=month,
        temp_celsius=temp_celsius, rain_1h=rain_1h,
        traffic_lag_1h=traffic_lag_1h, traffic_lag_24h=lag24,
        traffic_rolling_3h=roll3, traffic_rolling_6h=roll6,
        is_holiday=is_holiday,
    )
    base_code  = base_result["prediction"]["code"]
    base_label = base_result["prediction"]["label"]

    segments = []
    for seg in I94_SEGMENTS:
        seg_code  = _code_for_factor(base_code, seg["factor"])
        seg_label = LABELS[seg_code]
        color     = COLORS[seg_label]
        mid_idx   = len(seg["coords"]) // 2
        segments.append({
            "name":             seg["name"],
            "exit":             seg["exit"],
            "factor":           seg["factor"],
            "is_bottleneck":    seg["factor"] > 1.0,
            "segment_label":    seg_label,
            "segment_code":     seg_code,
            "color_hex":        color,
            "lat_center":       seg["coords"][mid_idx][0],
            "lon_center":       seg["coords"][mid_idx][1],
            "coords":           seg["coords"],
        })

    severe_segs  = [s for s in segments if s["segment_label"] == "Severe"]
    high_segs    = [s for s in segments if s["segment_label"] == "High"]
    worst_seg    = max(segments, key=lambda s: (s["segment_code"], s["factor"]))
    safest_seg   = min(segments, key=lambda s: (s["segment_code"], -s["factor"]))

    return {
        "base_prediction": {
            "label":      base_label,
            "code":       base_code,
            "confidence": base_result["prediction"]["confidence"],
        },
        "segments": segments,
        "summary": {
            "severe_count":     len(severe_segs),
            "high_count":       len(high_segs),
            "total_segments":   len(segments),
            "worst_segment":    worst_seg["name"],
            "safest_segment":   safest_seg["name"],
        },
        "conditions": base_result["conditions"],
    }


def get_model_info() -> dict:
    """Return model metadata and performance info."""
    results = get_model_results()
    fi_df   = get_fi()

    best_model = None
    best_f1    = 0.0
    for name, metrics in results.items():
        f1 = metrics.get("F1 (Weighted)", 0)
        if f1 > best_f1:
            best_f1    = f1
            best_model = name

    top_features = []
    if fi_df is not None:
        top_features = fi_df.head(10)[["feature", "importance"]].to_dict(orient="records")

    return {
        "best_model":       best_model,
        "f1_weighted":      round(best_f1, 4),
        "feature_count":    27,
        "congestion_classes": ["Low", "Medium", "High", "Severe"],
        "congestion_bins":  {"Low": "0–1000", "Medium": "1001–2500",
                             "High": "2501–4500", "Severe": "4501–7280"},
        "top_features":     top_features,
        "all_results":      results,
    }


def get_segments_metadata() -> list[dict]:
    """Return I-94 segment metadata (name, exit, factor, center coords)."""
    from map_view import I94_SEGMENTS
    result = []
    for seg in I94_SEGMENTS:
        mid_idx = len(seg["coords"]) // 2
        result.append({
            "name":       seg["name"],
            "exit":       seg["exit"],
            "factor":     seg["factor"],
            "lat_center": seg["coords"][mid_idx][0],
            "lon_center": seg["coords"][mid_idx][1],
            "is_bottleneck": seg["factor"] > 1.0,
        })
    return result
