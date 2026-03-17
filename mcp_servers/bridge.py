"""
mcp_servers/bridge.py
----------------------
Synchronous bridge to the MCP server logic for use in the Streamlit app.

The bridge calls core.py functions directly — no subprocess or network
overhead — giving Streamlit instant access to the same capabilities the
MCP servers expose over the MCP protocol.

Why not use async MCP client in Streamlit?
  Streamlit reruns the script on every interaction. Starting subprocesses
  and async event loops per-rerun is fragile. The bridge pattern gives
  clean synchronous access while keeping the MCP servers independently
  runnable for external clients (Claude Desktop, Claude API, agents).

Usage
-----
    from mcp_servers.bridge import MCPBridge

    bridge = MCPBridge()
    # current real-time prediction
    now = bridge.predict_now()
    # 24h risk forecast for Tuesday in August
    risk = bridge.forecast_24h(day_of_week=1, month=8)
    # full corridor map data
    corridor = bridge.corridor_map(hour=17, day_of_week=1, month=8)
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional

from . import core


class MCPBridge:
    """
    Synchronous access to all four MCP server domains.

    Methods mirror the MCP tool signatures but return Python dicts/lists
    directly rather than JSON strings.
    """

    # ── Prediction domain ─────────────────────────────────────────────────────

    def predict(
        self,
        hour: int,
        day_of_week: int,
        month: int,
        temp_celsius: float = 15.0,
        rain_1h: float = 0.0,
        traffic_lag_1h: float = 3000.0,
        traffic_lag_24h: Optional[float] = None,
        traffic_rolling_3h: Optional[float] = None,
        traffic_rolling_6h: Optional[float] = None,
        snow_1h: float = 0.0,
        clouds_all: int = 40,
        weather_main: str = "Clear",
        is_holiday: int = 0,
    ) -> dict:
        """Full prediction with explanation and conditions."""
        lag24 = traffic_lag_24h   if traffic_lag_24h   is not None else traffic_lag_1h * 0.95
        roll3 = traffic_rolling_3h if traffic_rolling_3h is not None else traffic_lag_1h * 0.98
        roll6 = traffic_rolling_6h if traffic_rolling_6h is not None else traffic_lag_1h * 0.96
        return core.run_prediction(
            hour=hour, day_of_week=day_of_week, month=month,
            temp_celsius=temp_celsius, rain_1h=rain_1h,
            traffic_lag_1h=traffic_lag_1h, traffic_lag_24h=lag24,
            traffic_rolling_3h=roll3, traffic_rolling_6h=roll6,
            snow_1h=snow_1h, clouds_all=clouds_all,
            weather_main=weather_main, is_holiday=is_holiday,
        )

    def predict_now(
        self,
        rain_1h: float = 0.0,
        temp_celsius: float = 15.0,
        lag_1h: float = 3000.0,
        snow_1h: float = 0.0,
        weather_main: str = "Clear",
    ) -> dict:
        """
        Prediction for the current real-world time.
        Includes timestamp, local_time, day_name, date fields.
        """
        return core.run_current_prediction(
            rain_1h=rain_1h, temp_celsius=temp_celsius,
            lag_1h=lag_1h, snow_1h=snow_1h, weather_main=weather_main,
        )

    def predict_batch(
        self,
        hours: list,
        day_of_week: int,
        month: int,
        temp_celsius: float = 15.0,
        rain_1h: float = 0.0,
        traffic_lag_1h: float = 3000.0,
        weather_main: str = "Clear",
        is_holiday: int = 0,
    ) -> list:
        """Predict multiple specific hours in one call."""
        lag24 = traffic_lag_1h * 0.95
        roll3 = traffic_lag_1h * 0.98
        roll6 = traffic_lag_1h * 0.96
        results = []
        for h in hours:
            r = core.run_prediction(
                hour=h, day_of_week=day_of_week, month=month,
                temp_celsius=temp_celsius, rain_1h=rain_1h,
                traffic_lag_1h=traffic_lag_1h, traffic_lag_24h=lag24,
                traffic_rolling_3h=roll3, traffic_rolling_6h=roll6,
                weather_main=weather_main, is_holiday=is_holiday,
            )
            results.append({
                "hour":       h,
                "label":      r["prediction"]["label"],
                "code":       r["prediction"]["code"],
                "confidence": r["prediction"]["confidence"],
            })
        return results

    def forecast_24h(
        self,
        day_of_week: int,
        month: int,
        is_holiday: int = 0,
        weather_code: float = 0.0,
        rain_1h: float = 0.0,
        temp_celsius: float = 15.0,
    ) -> list:
        """
        24-hour risk forecast (uses historical median lags per hour).
        Returns list of 24 dicts: hour, label, confidence, risk_score.
        """
        return core.run_24h_risk(
            day_of_week=day_of_week, month=month, is_holiday=is_holiday,
            weather_code=weather_code, rain_1h=rain_1h, temp_celsius=temp_celsius,
        )

    # ── Analytics domain ──────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """High-level dataset statistics."""
        return core.get_dataset_stats()

    def get_hourly_profile(self) -> dict:
        """Average traffic volume per hour (0–23)."""
        return core.get_hourly_profile()

    def get_congestion_distribution(self) -> dict:
        """Count and % per congestion level."""
        return core.get_congestion_distribution()

    def get_weather_impact(self) -> list:
        """Weather conditions ranked by average traffic volume."""
        return core.get_weather_impact()

    def get_rush_stats(self) -> dict:
        """Rush hour statistics vs weekday/weekend baseline."""
        return core.get_rush_stats()

    def compare_weekday_weekend(self) -> dict:
        """Weekday vs weekend comparison."""
        return core.compare_weekday_weekend()

    # ── Map / corridor domain ─────────────────────────────────────────────────

    def corridor_map(
        self,
        hour: int,
        day_of_week: int,
        month: int,
        rain_1h: float = 0.0,
        temp_celsius: float = 18.0,
        traffic_lag_1h: float = 3500.0,
        is_holiday: int = 0,
    ) -> dict:
        """
        Full corridor congestion state for all 16 I-94 segments.
        Returns base prediction + per-segment labels, colors, and coordinates.
        """
        return core.get_segment_congestion(
            hour=hour, day_of_week=day_of_week, month=month,
            rain_1h=rain_1h, temp_celsius=temp_celsius,
            traffic_lag_1h=traffic_lag_1h, is_holiday=is_holiday,
        )

    def bottleneck_segments(
        self,
        hour: int,
        day_of_week: int,
        month: int,
        min_label: str = "High",
        rain_1h: float = 0.0,
        temp_celsius: float = 18.0,
        traffic_lag_1h: float = 3500.0,
    ) -> list:
        """Segments at or above min_label congestion threshold."""
        min_code  = {"Low": 0, "Medium": 1, "High": 2, "Severe": 3}.get(min_label, 2)
        corridor  = core.get_segment_congestion(
            hour=hour, day_of_week=day_of_week, month=month,
            rain_1h=rain_1h, temp_celsius=temp_celsius,
            traffic_lag_1h=traffic_lag_1h,
        )
        return [s for s in corridor["segments"] if s["segment_code"] >= min_code]

    def segments_metadata(self) -> list:
        """Static list of all 16 I-94 segment names, exits, and factors."""
        return core.get_segments_metadata()

    # ── Insights domain ───────────────────────────────────────────────────────

    def system_insights(self) -> list:
        """Evidence-backed system insights (HIGH priority first)."""
        from insights import generate_system_insights
        _, peak = core.get_df_and_peak()
        insights = generate_system_insights(peak)
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        return sorted(insights, key=lambda x: priority_order.get(x["priority"], 3))

    def explain(
        self,
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
        """Explanation for a prediction label given conditions."""
        from insights import explain_prediction
        fi_df = core.get_fi()
        fv = {
            "hour": hour, "day_of_week": day_of_week,
            "is_rush_hour": is_rush_hour, "is_weekend": is_weekend,
            "is_holiday": is_holiday, "rain_1h": rain_1h, "snow_1h": snow_1h,
            "traffic_lag_1h": traffic_lag_1h, "weather_code": weather_code,
        }
        return explain_prediction(prediction_label, fv, fi_df)

    def action_plan(
        self,
        congestion_level: str,
        is_rush_hour: int = 0,
        rain_1h: float = 0.0,
        hour: int = 12,
        model_confidence: float = 90.0,
    ) -> dict:
        """Immediate + contextual action plan for a congestion level."""
        from insights import get_recommendations_for_level
        immediate  = get_recommendations_for_level(congestion_level)
        contextual = []
        if is_rush_hour and congestion_level in ("High", "Severe"):
            contextual.append("📱 Push mobile alert: Heavy traffic — consider delaying departure 30 min.")
        if rain_1h > 2.0:
            contextual.append("🌧️ Activate wet-weather speed advisory signs.")
        if hour < 6:
            contextual.append("🌙 Low-traffic window: ideal for maintenance or inspections.")
        if model_confidence < 60.0:
            contextual.append("⚠️ Moderate confidence — verify with live sensor data.")
        urgency = {"Severe": "CRITICAL", "High": "HIGH", "Medium": "NORMAL", "Low": "LOW"}
        return {
            "congestion_level":  congestion_level,
            "immediate_actions": immediate,
            "contextual_actions": contextual,
            "urgency":           urgency.get(congestion_level, "NORMAL"),
        }

    # ── Model metadata ────────────────────────────────────────────────────────

    def model_info(self) -> dict:
        """Model metadata, performance, and top feature importance."""
        return core.get_model_info()

    # ── Convenience: live intelligence panel ─────────────────────────────────

    def live_intelligence_report(
        self,
        rain_1h: float = 0.0,
        temp_celsius: float = 15.0,
        lag_1h: float = 3000.0,
        snow_1h: float = 0.0,
        weather_main: str = "Clear",
    ) -> dict:
        """
        Complete real-time intelligence snapshot.

        Returns current prediction + corridor map + 24h risk forecast
        + top bottleneck alerts in a single call.

        Designed for the MCP Live Intelligence page in the Streamlit app.
        """
        now = datetime.now()

        # Current prediction
        current = self.predict_now(
            rain_1h=rain_1h, temp_celsius=temp_celsius,
            lag_1h=lag_1h, snow_1h=snow_1h, weather_main=weather_main,
        )

        # Corridor map at current hour
        corridor = self.corridor_map(
            hour=now.hour, day_of_week=now.weekday(), month=now.month,
            rain_1h=rain_1h, temp_celsius=temp_celsius,
            traffic_lag_1h=lag_1h,
        )

        # 24h risk forecast for today
        weather_code_map = {
            "Clear": 0.0, "Clouds": 1.0, "Haze": 1.0, "Smoke": 2.0, "Drizzle": 2.0,
            "Rain": 3.0, "Mist": 3.0, "Fog": 4.0, "Thunderstorm": 4.0,
            "Snow": 4.0, "Squall": 5.0,
        }
        risk_forecast = self.forecast_24h(
            day_of_week=now.weekday(), month=now.month,
            weather_code=weather_code_map.get(weather_main, 0.0),
            rain_1h=rain_1h, temp_celsius=temp_celsius,
        )

        # Alert: segments at High or above right now
        alerts = self.bottleneck_segments(
            hour=now.hour, day_of_week=now.weekday(), month=now.month,
            min_label="High", rain_1h=rain_1h, temp_celsius=temp_celsius,
            traffic_lag_1h=lag_1h,
        )

        # Next-hour outlook
        next_hour = (now.hour + 1) % 24
        next_pred = self.predict(
            hour=next_hour, day_of_week=now.weekday(), month=now.month,
            temp_celsius=temp_celsius, rain_1h=rain_1h,
            traffic_lag_1h=lag_1h, weather_main=weather_main,
        )

        return {
            "timestamp":     now.isoformat(),
            "local_time":    now.strftime("%H:%M"),
            "date":          now.strftime("%Y-%m-%d"),
            "day_name":      now.strftime("%A"),
            "current":       current,
            "next_hour":     {
                "hour":  next_hour,
                "label": next_pred["prediction"]["label"],
                "confidence": next_pred["prediction"]["confidence"],
            },
            "corridor":      corridor,
            "risk_forecast": risk_forecast,
            "alerts": {
                "high_or_severe_segments": alerts,
                "alert_count":  len(alerts),
                "alert_active": len(alerts) > 0,
            },
        }
