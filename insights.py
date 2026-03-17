"""
insights.py
-----------
Rule-based AI Insight Engine.
Generates human-readable, actionable insights from model outputs and data patterns.
"""

import numpy as np
import pandas as pd

CONGESTION_LABELS = ["Low", "Medium", "High", "Severe"]
CONGESTION_MAP    = {"Low": 0, "Medium": 1, "High": 2, "Severe": 3}

LEVEL_DESCRIPTIONS = {
    "Low":    {"emoji": "🟢", "summary": "Traffic is flowing smoothly.", "impact": "Travel times near-optimal."},
    "Medium": {"emoji": "🟡", "summary": "Moderate traffic — some slowdowns.", "impact": "Expect 10–20% longer travel times."},
    "High":   {"emoji": "🟠", "summary": "Heavy traffic causing noticeable congestion.", "impact": "Travel times 30–50% above normal."},
    "Severe": {"emoji": "🔴", "summary": "Severe congestion — gridlock possible.", "impact": "Travel times may double. Avoid if possible."},
}

MONTH_NAMES = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def explain_prediction(prediction_label: str, input_features: dict, fi_df=None) -> dict:
    """Explains why a specific prediction was made."""
    factors = []
    hour    = input_features.get("hour", 12)
    dow     = input_features.get("day_of_week", 2)
    is_rush = input_features.get("is_rush_hour", 0)
    is_wknd = input_features.get("is_weekend", 0)
    is_hol  = input_features.get("is_holiday", 0)
    rain    = input_features.get("rain_1h", 0)
    snow    = input_features.get("snow_1h", 0)
    lag_1h  = input_features.get("traffic_lag_1h", 3000)
    w_code  = input_features.get("weather_code", 1)

    if is_rush:
        period = "morning" if hour < 12 else "evening"
        factors.append({"factor": f"{period.capitalize()} rush hour ({hour}:00)", "impact": "high",
                         "detail": "Commuter demand spikes during peak hours (7–9 AM, 4–6 PM)."})
    if is_wknd:
        factors.append({"factor": "Weekend", "impact": "reducing",
                         "detail": "Weekend traffic is ~25% lower than weekdays."})
    else:
        day_names = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        factors.append({"factor": f"Weekday ({day_names[int(dow)]})", "impact": "moderate",
                         "detail": "Weekday commuter patterns drive sustained traffic load."})
    if is_hol:
        factors.append({"factor": "Public Holiday", "impact": "reducing",
                         "detail": "Holiday reduces commuter trips significantly."})

    if rain > 5.0:
        factors.append({"factor": f"Heavy rain ({rain:.1f} mm/hr)", "impact": "high",
                         "detail": "Heavy rain reduces road speeds and increases accidents."})
    elif rain > 0.5:
        factors.append({"factor": f"Light rain ({rain:.1f} mm/hr)", "impact": "moderate",
                         "detail": "Rain causes cautious driving and minor slowdowns."})
    if snow > 0:
        factors.append({"factor": f"Snow ({snow:.2f} cm)", "impact": "high",
                         "detail": "Snow significantly reduces safe travel speeds."})
    if w_code >= 4:
        factors.append({"factor": "Poor visibility (fog/thunderstorm)", "impact": "high",
                         "detail": "Low visibility forces drivers to slow down."})

    if lag_1h > 4500:
        factors.append({"factor": f"Prior hour also heavy ({int(lag_1h):,} vehicles)", "impact": "high",
                         "detail": "Traffic persists — congestion from last hour is still clearing."})
    elif lag_1h < 1000:
        factors.append({"factor": f"Prior hour was light ({int(lag_1h):,} vehicles)", "impact": "reducing",
                         "detail": "Low prior-hour volume suggests conditions are improving."})
    if hour < 5 or hour >= 23:
        factors.append({"factor": f"Late night / early morning ({hour}:00)", "impact": "reducing",
                         "detail": "Traffic demand is naturally very low at this hour."})

    high_factors     = [f for f in factors if f["impact"] == "high"]
    reducing_factors = [f for f in factors if f["impact"] == "reducing"]

    narrative = [LEVEL_DESCRIPTIONS[prediction_label]["summary"]]
    if high_factors:
        narrative.append(f"Primary drivers: {', '.join(f['factor'] for f in high_factors)}.")
    if reducing_factors:
        narrative.append(f"Mitigating factors: {', '.join(f['factor'] for f in reducing_factors)}.")
    narrative.append(LEVEL_DESCRIPTIONS[prediction_label]["impact"])

    return {
        "level_info": LEVEL_DESCRIPTIONS[prediction_label],
        "contributing_factors": factors,
        "prediction_narrative": " ".join(narrative),
    }


def generate_system_insights(peak_data: dict) -> list:
    """Generates system-level insights from aggregated peak analysis."""
    insights = []

    peak_hour   = peak_data.get("peak_hour", 17)
    trough_hour = peak_data.get("trough_hour", 3)
    peak_day    = peak_data.get("peak_day", "Thu")
    worst_month = peak_data.get("worst_month", 8)
    weekday_avg = peak_data.get("weekday_avg", 3600)
    weekend_avg = peak_data.get("weekend_avg", 2700)
    holiday_avg = peak_data.get("holiday_avg", 2000)
    rush_avg    = peak_data.get("rush_avg", 5000)
    weather_impact = peak_data.get("weather_impact", {})

    rush_pct = round((rush_avg - weekday_avg) / max(weekday_avg, 1) * 100, 1)
    insights.append({
        "title":          "⏰ Rush Hour Dominates Congestion",
        "finding":        f"Rush hour generates ~{rush_pct}% more traffic than the daily average. "
                          f"Peak traffic at {peak_hour}:00, quietest at {trough_hour}:00.",
        "recommendation": "Implement adaptive signal control 7–9 AM and 4–6 PM. "
                          "Incentivize staggered work hours for large employers.",
        "priority":       "HIGH",
    })

    diff_pct = round((weekday_avg - weekend_avg) / max(weekday_avg, 1) * 100, 1)
    insights.append({
        "title":          "📅 Weekday vs Weekend Disparity",
        "finding":        f"Weekdays average {int(weekday_avg):,} vehicles/hr vs {int(weekend_avg):,} on weekends "
                          f"({diff_pct}% difference). {peak_day} is the busiest day.",
        "recommendation": "Dynamic tolling or congestion pricing for weekday peak windows. "
                          "Schedule road maintenance on weekends or overnight.",
        "priority":       "MEDIUM",
    })

    hol_pct = round((weekday_avg - holiday_avg) / max(weekday_avg, 1) * 100, 1)
    insights.append({
        "title":          "🎉 Holidays Provide Significant Relief",
        "finding":        f"Holidays reduce traffic to {int(holiday_avg):,} vehicles/hr "
                          f"({hol_pct}% below weekday avg) — confirming commuter demand is the primary driver.",
        "recommendation": "Use holiday patterns to benchmark baseline model performance. "
                          "Plan infrastructure work around high-holiday months.",
        "priority":       "LOW",
    })

    if weather_impact:
        sw = sorted(weather_impact.items(), key=lambda x: x[1], reverse=True)
        top_w, low_w = sw[0], sw[-1]
        insights.append({
            "title":          "🌧️ Weather Effects on Traffic Flow",
            "finding":        f"'{top_w[0]}' correlates with highest traffic ({int(top_w[1]):,}/hr); "
                              f"'{low_w[0]}' lowest ({int(low_w[1]):,}/hr). Extreme weather suppresses trips.",
            "recommendation": "Integrate real-time weather feeds into signal control. "
                              "Deploy variable message signs for weather-related advisories.",
            "priority":       "MEDIUM",
        })

    insights.append({
        "title":          f"📆 Seasonal Peak: {MONTH_NAMES[int(worst_month)]}",
        "finding":        f"{MONTH_NAMES[int(worst_month)]} shows the highest average congestion, "
                          "aligning with seasonal commute and school patterns.",
        "recommendation": f"Pre-deploy traffic management resources in {MONTH_NAMES[int(worst_month)]}. "
                          "Consider temporary HOV lanes during peak seasonal months.",
        "priority":       "MEDIUM",
    })

    insights.append({
        "title":          "📈 Traffic Has Strong Temporal Momentum",
        "finding":        "The previous hour's volume is the single most predictive feature — "
                          "congestion builds and clears gradually, rarely spiking instantly.",
        "recommendation": "Trigger preemptive signal changes when volume rises >15% above "
                          "the trailing 3-hour average, not just absolute thresholds.",
        "priority":       "HIGH",
    })

    return insights


def get_recommendations_for_level(level: str) -> list:
    """Returns immediate action recommendations for a given congestion level."""
    recs = {
        "Low": [
            "✅ No immediate action required.",
            "📊 Use this window for system diagnostics and data validation.",
            "🚧 Schedule planned road maintenance now.",
        ],
        "Medium": [
            "🚦 Activate adaptive signal timing on high-volume corridors.",
            "📻 Push real-time traffic updates to navigation apps.",
            "🚌 Monitor public transit capacity — divert demand from roads.",
        ],
        "High": [
            "🚨 Alert traffic control center.",
            "🚦 Extend green phases on primary arterials by 15–20%.",
            "📣 Broadcast delay warnings via VMS and radio.",
            "🚌 Increase bus frequency on parallel routes.",
            "🔄 Activate contraflow lanes if available.",
        ],
        "Severe": [
            "🚨 CRITICAL: Activate full incident management protocol.",
            "🚔 Deploy traffic officers to key intersections.",
            "🔒 Activate ramp metering on highway on-ramps.",
            "📣 Issue public advisory to avoid the corridor.",
            "🏥 Ensure emergency vehicle corridors remain clear.",
        ],
    }
    return recs.get(level, [])
