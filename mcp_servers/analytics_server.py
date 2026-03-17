"""
mcp_servers/analytics_server.py
---------------------------------
FastMCP server — Traffic Analytics & Dataset Insights.

Tools
-----
get_hourly_traffic_profile      Average volume per hour (0–23), peak/trough
get_congestion_distribution     Count + % per level (Low/Medium/High/Severe)
get_weather_impact_summary      Weather conditions ranked by avg traffic volume
get_rush_hour_stats             Rush hour analytics vs weekday/weekend baseline
compare_weekday_vs_weekend      Weekday vs weekend comparison with peak hours
get_segment_risk_for_hour       Per-segment congestion data without Folium

Resources
---------
traffic://dataset/summary       High-level dataset statistics
traffic://dataset/peak_analysis Full peak_data dict (hourly/daily/monthly avgs)
traffic://segments/metadata     I-94 segment names, exits, factors, center coords

Run standalone:
    python -m mcp_servers.analytics_server
"""

import json
from mcp.server.fastmcp import FastMCP
from . import core

mcp = FastMCP(
    "Traffic Analytics Server",
    instructions=(
        "Provides statistical analysis of 48,204 hourly records from "
        "Metro I-94 (Minneapolis – Saint Paul, 2012–2018). "
        "Use these tools to understand traffic patterns, weather effects, "
        "and per-segment congestion data."
    ),
)


# ─────────────────────────────────────────────────────────────────────────────
#  TOOLS
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_hourly_traffic_profile() -> dict:
    """
    Return average traffic volume for each hour of the day (0–23).

    Returns
    -------
    dict with keys:
      hourly_avg   {hour_int: avg_vehicles_per_hr} for 0–23
      peak_hour    Hour with highest average volume
      trough_hour  Hour with lowest average volume
    """
    return core.get_hourly_profile()


@mcp.tool()
def get_congestion_distribution() -> dict:
    """
    Return the distribution of congestion levels across the full dataset.

    Returns
    -------
    dict mapping each level (Low/Medium/High/Severe) to
    { count: int, pct: float }
    """
    return core.get_congestion_distribution()


@mcp.tool()
def get_weather_impact_summary() -> list:
    """
    Return weather conditions ranked by their average traffic volume impact.

    Higher volume = more trips (not necessarily more congestion).
    Extreme weather (fog, squalls) suppresses total trips.

    Returns
    -------
    List of { condition: str, avg_volume: float } sorted descending by volume.
    """
    return core.get_weather_impact()


@mcp.tool()
def get_rush_hour_stats() -> dict:
    """
    Return rush-hour statistics vs baseline.

    Returns
    -------
    dict with keys:
      morning_rush        { start: 7, end: 9 }
      evening_rush        { start: 16, end: 18 }
      rush_avg            Average vehicles/hr during rush periods
      weekday_avg         Average vehicles/hr on weekdays
      weekend_avg         Average vehicles/hr on weekends
      holiday_avg         Average vehicles/hr on holidays
      rush_premium_pct    Percent above weekday average during rush hours
    """
    return core.get_rush_stats()


@mcp.tool()
def compare_weekday_vs_weekend() -> dict:
    """
    Compare weekday and weekend traffic patterns.

    Returns
    -------
    dict with keys:
      weekday_avg         Average vehicles/hr Mon–Fri
      weekend_avg         Average vehicles/hr Sat–Sun
      diff_pct            Weekday premium over weekend (%)
      peak_weekday_hour   Hour with highest weekday traffic
      peak_weekend_hour   Hour with highest weekend traffic
    """
    return core.compare_weekday_weekend()


@mcp.tool()
def get_segment_risk_for_hour(
    hour: int,
    day_of_week: int,
    month: int,
    rain_1h: float = 0.0,
    temp_celsius: float = 18.0,
    traffic_lag_1h: float = 3500.0,
    is_holiday: int = 0,
) -> dict:
    """
    Return per-segment congestion data for the I-94 corridor.

    Each of the 16 named segments gets its own congestion prediction
    by applying a spatial bottleneck factor to the model's global output.
    Returns pure data (no Folium/map library needed).

    Parameters
    ----------
    hour            Hour of day (0–23)
    day_of_week     0=Monday … 6=Sunday
    month           1–12
    rain_1h         Rainfall mm/hr (default 0)
    temp_celsius    Temperature °C (default 18)
    traffic_lag_1h  Last known vehicle count (default 3500)
    is_holiday      1 if public holiday (default 0)

    Returns
    -------
    dict with keys:
      base_prediction   { label, code, confidence } — global model output
      segments          list of 16 segment dicts with label, color, coords
      summary           { severe_count, high_count, worst_segment, safest_segment }
      conditions        Echo of input conditions used
    """
    return core.get_segment_congestion(
        hour=hour, day_of_week=day_of_week, month=month,
        rain_1h=rain_1h, temp_celsius=temp_celsius,
        traffic_lag_1h=traffic_lag_1h, is_holiday=is_holiday,
    )


@mcp.tool()
def get_bottleneck_segments(
    hour: int,
    day_of_week: int,
    month: int,
    min_label: str = "High",
    rain_1h: float = 0.0,
    temp_celsius: float = 18.0,
    traffic_lag_1h: float = 3500.0,
) -> list:
    """
    Return only I-94 segments at or above the specified congestion level.

    Useful for alert generation: 'which segments are currently High or Severe?'

    Parameters
    ----------
    hour            Hour of day (0–23)
    day_of_week     0=Monday … 6=Sunday
    month           1–12
    min_label       Minimum level to include: 'Low', 'Medium', 'High', 'Severe'
    rain_1h         Rainfall mm/hr
    temp_celsius    Temperature °C
    traffic_lag_1h  Last known vehicle count

    Returns
    -------
    List of segment dicts that meet or exceed min_label threshold.
    Empty list means all segments are below the threshold (good news).
    """
    _code_for_label = {"Low": 0, "Medium": 1, "High": 2, "Severe": 3}
    min_code = _code_for_label.get(min_label, 2)

    corridor = core.get_segment_congestion(
        hour=hour, day_of_week=day_of_week, month=month,
        rain_1h=rain_1h, temp_celsius=temp_celsius,
        traffic_lag_1h=traffic_lag_1h,
    )
    return [
        s for s in corridor["segments"]
        if s["segment_code"] >= min_code
    ]


@mcp.tool()
def get_dataset_overview() -> dict:
    """
    Return high-level statistics about the Metro I-94 dataset.

    Returns
    -------
    dict with total_records, date_range, years_covered, volume stats,
    peak_hour, peak_day, and weekday/weekend/holiday/rush averages.
    """
    return core.get_dataset_stats()


# ─────────────────────────────────────────────────────────────────────────────
#  RESOURCES
# ─────────────────────────────────────────────────────────────────────────────

@mcp.resource("traffic://dataset/summary")
def dataset_summary() -> str:
    """High-level Metro I-94 dataset statistics (48K records, 2012–2018)."""
    return json.dumps(core.get_dataset_stats(), indent=2)


@mcp.resource("traffic://dataset/peak_analysis")
def peak_analysis() -> str:
    """
    Full peak analysis dict including hourly_avg, daily_avg, monthly_avg,
    weather_impact, peak_hour, peak_day, rush_avg, weekday/weekend/holiday averages.
    """
    _, peak = core.get_df_and_peak()
    # Convert to serializable form
    serializable = {
        "hourly_avg":     {int(k): float(v) for k, v in peak["hourly_avg"].items()},
        "daily_avg":      {k: float(v) for k, v in peak["daily_avg"].items()},
        "monthly_avg":    {int(k): float(v) for k, v in peak["monthly_avg"].items()},
        "weather_impact": {k: float(v) for k, v in peak["weather_impact"].items()},
        "peak_hour":      int(peak["peak_hour"]),
        "trough_hour":    int(peak["trough_hour"]),
        "peak_day":       peak["peak_day"],
        "worst_month":    int(peak["worst_month"]),
        "weekend_avg":    round(float(peak["weekend_avg"]), 1),
        "weekday_avg":    round(float(peak["weekday_avg"]), 1),
        "holiday_avg":    round(float(peak["holiday_avg"]), 1),
        "rush_avg":       round(float(peak["rush_avg"]), 1),
    }
    return json.dumps(serializable, indent=2)


@mcp.resource("traffic://segments/metadata")
def segments_metadata() -> str:
    """
    All 16 I-94 corridor segments: name, exit, spatial factor,
    bottleneck flag, and center coordinates.
    """
    return json.dumps(core.get_segments_metadata(), indent=2)


if __name__ == "__main__":
    mcp.run()
