"""
mcp_servers/map_server.py
--------------------------
FastMCP server — I-94 Corridor Map & Spatial Intelligence.

Returns corridor geometry and per-segment congestion as pure JSON data —
no Folium or map library needed by the client.

Tools
-----
get_corridor_congestion_map   Full corridor state: base prediction + all 16 segments
get_bottleneck_segments       Only segments at or above a congestion threshold
get_segment_history           Per-hour forecast for a named segment across 24 hours

Resources
---------
traffic://map/segments            Static geometry for all 16 I-94 segments
traffic://map/bottleneck_factors  Segments ranked by spatial congestion factor

Run standalone:
    python -m mcp_servers.map_server
"""

import json
from mcp.server.fastmcp import FastMCP
from . import core

mcp = FastMCP(
    "Traffic Map Server",
    instructions=(
        "Returns spatial congestion intelligence for Metro I-94 "
        "(Plymouth/I-494 → East Saint Paul, 16 named segments). "
        "Provides segment-level congestion data as JSON — no map library required. "
        "Spatial factors encode historical bottleneck severity per segment; "
        "the I-35W interchange (factor 1.5) is the worst bottleneck."
    ),
)

# Congestion level order for threshold filtering
_LEVEL_CODE = {"Low": 0, "Medium": 1, "High": 2, "Severe": 3}


# ─────────────────────────────────────────────────────────────────────────────
#  TOOLS
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_corridor_congestion_map(
    hour: int,
    day_of_week: int,
    month: int,
    rain_1h: float = 0.0,
    temp_celsius: float = 18.0,
    traffic_lag_1h: float = 3500.0,
    is_holiday: int = 0,
) -> dict:
    """
    Return the full I-94 corridor congestion state for given conditions.

    The model produces a global prediction; each of the 16 named segments
    then gets an adjusted prediction via its spatial bottleneck factor
    (factor > 1 = historically worse than corridor average).

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
      segments          List of 16 dicts:
                          name, exit, factor, is_bottleneck,
                          segment_label, segment_code, color_hex,
                          lat_center, lon_center, coords
      summary           { severe_count, high_count, total_segments,
                          worst_segment, safest_segment }
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
    Return only I-94 segments at or above the specified congestion threshold.

    Ideal for alert generation workflows:
    'Which segments are currently High or Severe?'

    Parameters
    ----------
    hour            Hour of day (0–23)
    day_of_week     0=Monday … 6=Sunday
    month           1–12
    min_label       Minimum level to include: 'Low', 'Medium', 'High', 'Severe'
                    (default 'High')
    rain_1h         Rainfall mm/hr
    temp_celsius    Temperature °C
    traffic_lag_1h  Last known vehicle count

    Returns
    -------
    List of segment dicts meeting or exceeding min_label.
    Empty list = all segments below threshold (good conditions).
    Each dict includes: name, exit, factor, segment_label, color_hex,
                        lat_center, lon_center.
    """
    min_code = _LEVEL_CODE.get(min_label, 2)
    corridor  = core.get_segment_congestion(
        hour=hour, day_of_week=day_of_week, month=month,
        rain_1h=rain_1h, temp_celsius=temp_celsius,
        traffic_lag_1h=traffic_lag_1h,
    )
    return [
        {k: s[k] for k in ("name", "exit", "factor", "segment_label",
                             "color_hex", "lat_center", "lon_center", "is_bottleneck")}
        for s in corridor["segments"]
        if s["segment_code"] >= min_code
    ]


@mcp.tool()
def get_segment_history(
    segment_name: str,
    day_of_week: int,
    month: int,
    rain_1h: float = 0.0,
    temp_celsius: float = 18.0,
    traffic_lag_1h: float = 3500.0,
) -> dict:
    """
    Return predicted congestion for a named I-94 segment across all 24 hours.

    Enables queries like 'What is the worst hour for the I-35W interchange?'
    This is not available in the Streamlit app which only handles one time point.

    Parameters
    ----------
    segment_name    Exact segment name (see traffic://map/segments for names),
                    or a partial match (case-insensitive substring)
    day_of_week     0=Monday … 6=Sunday
    month           1–12
    rain_1h         Rainfall mm/hr
    temp_celsius    Temperature °C
    traffic_lag_1h  Baseline vehicle count (lag values derived at 95–98%)

    Returns
    -------
    dict with keys:
      segment_name    Matched segment name
      segment_factor  Spatial bottleneck factor for this segment
      hourly_forecast List of 24 dicts: { hour, label, code, risk_score }
      peak_hour       Hour with worst congestion for this segment
      safe_hours      List of hours with Low congestion
    """
    from map_view import I94_SEGMENTS, LABELS, _code_for_factor

    # Find segment by name (exact or partial)
    matched = None
    for seg in I94_SEGMENTS:
        if seg["name"].lower() == segment_name.lower():
            matched = seg
            break
    if matched is None:
        for seg in I94_SEGMENTS:
            if segment_name.lower() in seg["name"].lower():
                matched = seg
                break
    if matched is None:
        return {
            "error": f"Segment '{segment_name}' not found.",
            "available_segments": [s["name"] for s in I94_SEGMENTS],
        }

    factor = matched["factor"]
    hourly = []
    for h in range(24):
        lag24 = traffic_lag_1h * 0.95
        roll3 = traffic_lag_1h * 0.98
        roll6 = traffic_lag_1h * 0.96
        base  = core.run_prediction(
            hour=h, day_of_week=day_of_week, month=month,
            temp_celsius=temp_celsius, rain_1h=rain_1h,
            traffic_lag_1h=traffic_lag_1h, traffic_lag_24h=lag24,
            traffic_rolling_3h=roll3, traffic_rolling_6h=roll6,
        )
        base_code  = base["prediction"]["code"]
        seg_code   = _code_for_factor(base_code, factor)
        seg_label  = LABELS[seg_code]
        risk_score = round((seg_code / 3) * 100, 1)
        hourly.append({
            "hour":       h,
            "hour_str":   f"{h:02d}:00",
            "label":      seg_label,
            "code":       seg_code,
            "risk_score": risk_score,
        })

    peak_rec   = max(hourly, key=lambda r: r["risk_score"])
    safe_hours = [r["hour_str"] for r in hourly if r["label"] == "Low"]

    return {
        "segment_name":    matched["name"],
        "segment_factor":  factor,
        "is_bottleneck":   factor > 1.0,
        "hourly_forecast": hourly,
        "peak_hour":       peak_rec["hour_str"],
        "peak_label":      peak_rec["label"],
        "safe_hours":      safe_hours,
    }


@mcp.tool()
def list_segments() -> list:
    """
    Return the names and spatial factors of all 16 I-94 corridor segments.

    Useful for discovering valid segment names before calling get_segment_history.
    Segments are ordered west-to-east (Plymouth → East Saint Paul).

    Returns
    -------
    List of { name, exit, factor, is_bottleneck } dicts.
    """
    from map_view import I94_SEGMENTS
    return [
        {
            "name":          s["name"],
            "exit":          s["exit"],
            "factor":        s["factor"],
            "is_bottleneck": s["factor"] > 1.0,
        }
        for s in I94_SEGMENTS
    ]


# ─────────────────────────────────────────────────────────────────────────────
#  RESOURCES
# ─────────────────────────────────────────────────────────────────────────────

@mcp.resource("traffic://map/segments")
def map_segments() -> str:
    """
    Full geometry for all 16 I-94 corridor segments:
    name, exit label, spatial factor, center lat/lon, and coordinate list.
    """
    return json.dumps(core.get_segments_metadata(), indent=2)


@mcp.resource("traffic://map/bottleneck_factors")
def bottleneck_factors() -> str:
    """
    All 16 segments ranked by spatial bottleneck factor (highest = worst).
    Factor > 1.0 means historically worse than corridor average.
    I-35W interchange (1.50) is the worst; Plymouth/I-494 (0.70) is best.
    """
    from map_view import I94_SEGMENTS
    ranked = sorted(
        [{"name": s["name"], "exit": s["exit"], "factor": s["factor"],
          "is_bottleneck": s["factor"] > 1.0}
         for s in I94_SEGMENTS],
        key=lambda x: -x["factor"],
    )
    return json.dumps(ranked, indent=2)


if __name__ == "__main__":
    mcp.run()
