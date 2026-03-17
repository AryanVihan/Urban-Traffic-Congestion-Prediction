"""
mcp_servers/insights_server.py
--------------------------------
FastMCP server — AI Insight Engine & Recommendations.

Tools
-----
explain_prediction_for_conditions   Human-readable explanation of a prediction
get_action_plan                     Immediate + contextual actions for a level
get_system_insights                 Evidence-backed insights from 6 years of data
get_level_description               Emoji, summary, and impact for a congestion level
generate_congestion_narrative       Full natural-language report for given conditions

Resources
---------
traffic://insights/system          All system insights (HIGH priority first)
traffic://insights/level_guide     All four level descriptions as reference card
traffic://insights/rush_schedule   Rush hours, peak day, worst month

Run standalone:
    python -m mcp_servers.insights_server
"""

import json
from mcp.server.fastmcp import FastMCP
from . import core

mcp = FastMCP(
    "Traffic Insights Server",
    instructions=(
        "Rule-based AI insight and recommendation engine for Metro I-94 traffic. "
        "Explains why predictions were made, generates action plans for traffic managers, "
        "and provides evidence-backed system-level insights from 6 years of data. "
        "Does not require a trained model — pure analytical intelligence."
    ),
)


# ─────────────────────────────────────────────────────────────────────────────
#  TOOLS
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def explain_prediction_for_conditions(
    prediction_label: str,
    hour: int,
    day_of_week: int,
    rain_1h: float = 0.0,
    snow_1h: float = 0.0,
    traffic_lag_1h: float = 3000.0,
    is_rush_hour: int = 0,
    is_weekend: int = 0,
    is_holiday: int = 0,
    weather_code: float = 0.0,
) -> dict:
    """
    Generate a human-readable explanation for a traffic prediction.

    Identifies and ranks the contributing factors that led to the
    given congestion level, plus a plain-English narrative summary.

    Parameters
    ----------
    prediction_label  'Low', 'Medium', 'High', or 'Severe'
    hour              Hour of day (0–23)
    day_of_week       0=Monday … 6=Sunday
    rain_1h           Rainfall mm/hr
    snow_1h           Snowfall cm/hr
    traffic_lag_1h    Vehicle count from last hour
    is_rush_hour      1 if within rush hour window (7–9 AM or 4–6 PM)
    is_weekend        1 if Saturday or Sunday
    is_holiday        1 if public holiday
    weather_code      0=Clear, 1=Clouds, 2=Haze, 3=Rain, 4=Fog/Snow, 5=Squall

    Returns
    -------
    dict with keys:
      contributing_factors  List of { factor, impact, detail }
      prediction_narrative  Plain-English summary string
      level_info            { emoji, summary, impact }
    """
    from insights import explain_prediction
    fi_df = core.get_fi()

    fv = {
        "hour":          hour,
        "day_of_week":   day_of_week,
        "is_rush_hour":  is_rush_hour,
        "is_weekend":    is_weekend,
        "is_holiday":    is_holiday,
        "rain_1h":       rain_1h,
        "snow_1h":       snow_1h,
        "traffic_lag_1h": traffic_lag_1h,
        "weather_code":  weather_code,
    }
    result = explain_prediction(prediction_label, fv, fi_df)
    return {
        "contributing_factors":  result["contributing_factors"],
        "prediction_narrative":  result["prediction_narrative"],
        "level_info":            result["level_info"],
    }


@mcp.tool()
def get_action_plan(
    congestion_level: str,
    is_rush_hour: int = 0,
    rain_1h: float = 0.0,
    hour: int = 12,
    model_confidence: float = 90.0,
) -> dict:
    """
    Return an actionable response plan for the given congestion level.

    Combines standard recommendations (from the insight engine) with
    context-specific actions based on the current conditions.

    Parameters
    ----------
    congestion_level  'Low', 'Medium', 'High', or 'Severe'
    is_rush_hour      1 if within rush hour window
    rain_1h           Current rainfall mm/hr
    hour              Current hour (used for overnight maintenance tip)
    model_confidence  Model confidence % (< 60 adds verification advisory)

    Returns
    -------
    dict with keys:
      immediate_actions   Standard response actions for the level
      contextual_actions  Condition-specific additions
      urgency             'LOW', 'NORMAL', 'HIGH', or 'CRITICAL'
      congestion_level    Echo of the input level
    """
    from insights import get_recommendations_for_level

    immediate   = get_recommendations_for_level(congestion_level)
    contextual  = []

    if is_rush_hour and congestion_level in ("High", "Severe"):
        contextual.append("📱 Push mobile alert: Heavy traffic — consider delaying departure 30 min.")
    if rain_1h > 2.0:
        contextual.append("🌧️ Activate wet-weather speed advisory signs on variable message boards.")
    if hour < 6:
        contextual.append("🌙 Low-traffic window: ideal for road maintenance or sensor inspections.")
    if model_confidence < 60.0:
        contextual.append("⚠️ Model confidence below 60% — verify with live sensor or camera data.")
    if congestion_level == "Severe" and is_rush_hour:
        contextual.append("🚔 Request police traffic assistance at major interchange points.")

    urgency_map = {"Severe": "CRITICAL", "High": "HIGH", "Medium": "NORMAL", "Low": "LOW"}
    return {
        "congestion_level":  congestion_level,
        "immediate_actions": immediate,
        "contextual_actions": contextual,
        "urgency":           urgency_map.get(congestion_level, "NORMAL"),
    }


@mcp.tool()
def get_system_insights() -> list:
    """
    Return evidence-backed system-level insights from 6 years of I-94 data.

    Insights cover rush-hour dominance, weekday/weekend disparity, holiday
    effects, weather impacts, seasonal patterns, and temporal momentum.

    Returns
    -------
    List of insight dicts: { title, finding, recommendation, priority }
    Sorted HIGH → MEDIUM → LOW priority.
    """
    from insights import generate_system_insights
    _, peak = core.get_df_and_peak()
    insights = generate_system_insights(peak)
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    return sorted(insights, key=lambda x: priority_order.get(x["priority"], 3))


@mcp.tool()
def get_level_description(level: str) -> dict:
    """
    Return the definition, emoji, and travel-time impact for a congestion level.

    Parameters
    ----------
    level  'Low', 'Medium', 'High', or 'Severe'

    Returns
    -------
    dict with keys: emoji, summary, impact
    """
    from insights import LEVEL_DESCRIPTIONS
    if level not in LEVEL_DESCRIPTIONS:
        return {"error": f"Unknown level '{level}'. Use: Low, Medium, High, Severe."}
    return LEVEL_DESCRIPTIONS[level]


@mcp.tool()
def generate_congestion_narrative(
    hour: int,
    day_of_week: int,
    month: int,
    rain_1h: float = 0.0,
    temp_celsius: float = 15.0,
    traffic_lag_1h: float = 3000.0,
    weather_main: str = "Clear",
    is_holiday: int = 0,
) -> dict:
    """
    Generate a complete natural-language traffic intelligence report.

    Runs prediction + explanation + action plan and assembles a
    structured narrative report suitable for briefings or alerts.

    Parameters
    ----------
    hour            Hour of day (0–23)
    day_of_week     0=Monday … 6=Sunday
    month           1–12
    rain_1h         Rainfall mm/hr
    temp_celsius    Temperature °C
    traffic_lag_1h  Last known vehicle count
    weather_main    Weather condition label
    is_holiday      1 if public holiday

    Returns
    -------
    dict with keys:
      headline        One-sentence alert headline
      level           Predicted congestion level
      confidence      Model confidence %
      narrative       Multi-sentence explanation
      action_plan     { immediate_actions, contextual_actions, urgency }
      conditions_summary  Brief conditions description
    """
    from insights import get_recommendations_for_level

    lag24 = traffic_lag_1h * 0.95
    roll3 = traffic_lag_1h * 0.98
    roll6 = traffic_lag_1h * 0.96

    pred = core.run_prediction(
        hour=hour, day_of_week=day_of_week, month=month,
        temp_celsius=temp_celsius, rain_1h=rain_1h,
        traffic_lag_1h=traffic_lag_1h, traffic_lag_24h=lag24,
        traffic_rolling_3h=roll3, traffic_rolling_6h=roll6,
        weather_main=weather_main, is_holiday=is_holiday,
    )
    label      = pred["prediction"]["label"]
    confidence = pred["prediction"]["confidence"]
    narrative  = pred["explanation"]["narrative"]
    is_rush    = pred["conditions"]["is_rush_hour"]

    day_names  = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    month_names= ["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    emoji_map  = {"Low": "🟢", "Medium": "🟡", "High": "🟠", "Severe": "🔴"}
    urgency_map= {"Severe": "CRITICAL", "High": "HIGH", "Medium": "NORMAL", "Low": "LOW"}

    headline   = (
        f"{emoji_map[label]} Metro I-94 Traffic Alert — "
        f"{label} congestion predicted at {hour:02d}:00 on "
        f"{day_names[day_of_week]}, {month_names[month]}"
    )

    conditions_parts = [f"{hour:02d}:00"]
    if rain_1h > 0:
        conditions_parts.append(f"Rain {rain_1h:.1f}mm/hr")
    if is_holiday:
        conditions_parts.append("Holiday")
    if is_rush:
        conditions_parts.append("Rush hour")
    conditions_parts.append(f"{temp_celsius:.0f}°C")
    conditions_summary = " · ".join(conditions_parts)

    immediate  = get_recommendations_for_level(label)
    contextual = []
    if is_rush and label in ("High", "Severe"):
        contextual.append("📱 Push mobile alert for commuters.")
    if rain_1h > 2.0:
        contextual.append("🌧️ Activate wet-weather speed advisory signs.")

    return {
        "headline":           headline,
        "level":              label,
        "confidence":         confidence,
        "narrative":          narrative,
        "conditions_summary": conditions_summary,
        "action_plan": {
            "urgency":           urgency_map.get(label, "NORMAL"),
            "immediate_actions": immediate,
            "contextual_actions": contextual,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
#  RESOURCES
# ─────────────────────────────────────────────────────────────────────────────

@mcp.resource("traffic://insights/system")
def system_insights_resource() -> str:
    """
    All system-level insights derived from 6 years of Metro I-94 data,
    sorted HIGH → MEDIUM → LOW priority.
    """
    from insights import generate_system_insights
    _, peak = core.get_df_and_peak()
    insights = generate_system_insights(peak)
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    sorted_insights = sorted(insights, key=lambda x: priority_order.get(x["priority"], 3))
    return json.dumps(sorted_insights, indent=2)


@mcp.resource("traffic://insights/level_guide")
def level_guide() -> str:
    """
    Reference card for all four congestion levels:
    emoji, one-line summary, and travel-time impact for each.
    """
    from insights import LEVEL_DESCRIPTIONS
    return json.dumps(LEVEL_DESCRIPTIONS, indent=2)


@mcp.resource("traffic://insights/rush_schedule")
def rush_schedule() -> str:
    """
    Metro I-94 rush hour schedule, peak day, and worst month
    derived from 6 years of historical data.
    """
    _, peak = core.get_df_and_peak()
    from insights import MONTH_NAMES
    schedule = {
        "morning_rush":  {"start": 7, "end": 9,  "label": "7:00 – 9:00 AM"},
        "evening_rush":  {"start": 16, "end": 18, "label": "4:00 – 6:00 PM"},
        "peak_day":      peak["peak_day"],
        "worst_month":   int(peak["worst_month"]),
        "worst_month_name": MONTH_NAMES[int(peak["worst_month"])],
        "rush_avg_volume":  round(float(peak["rush_avg"]), 1),
        "weekday_avg_volume": round(float(peak["weekday_avg"]), 1),
    }
    return json.dumps(schedule, indent=2)


if __name__ == "__main__":
    mcp.run()
