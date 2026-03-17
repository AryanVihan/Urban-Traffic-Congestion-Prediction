"""
map_view.py
-----------
Interactive traffic map of Metro I-94, Minneapolis – Saint Paul.
Uses Folium (OpenStreetMap tiles — no API key required).

The I-94 corridor is divided into named segments.  Each segment is given
a baseline congestion factor; the model prediction for the selected
hour/day/month is combined with that factor to produce a per-segment
congestion level that is colour-coded on the map.
"""

import numpy as np
import folium
from folium.plugins import AntPath

# ── Congestion colours ────────────────────────────────────────────────────────
COLORS = {
    "Low":    "#22c55e",   # green
    "Medium": "#eab308",   # yellow
    "High":   "#f97316",   # orange
    "Severe": "#ef4444",   # red
}
LABELS = ["Low", "Medium", "High", "Severe"]

# ── I-94 route segments  [lat, lon pairs] with metadata ──────────────────────
# The highway runs east-west.  Coordinates are (latitude, longitude).
I94_SEGMENTS = [
    {
        "name":   "Plymouth / I-494 Exchange",
        "coords": [[44.9630, -93.4580], [44.9650, -93.4200], [44.9665, -93.3900]],
        "factor": 0.70,   # < 1 → less congested than model global prediction
        "exit":   "Exit 1A – Plymouth Rd",
    },
    {
        "name":   "Brooklyn Blvd / TH-100 Area",
        "coords": [[44.9665, -93.3900], [44.9690, -93.3400], [44.9710, -93.3100]],
        "factor": 0.80,
        "exit":   "Exit 4 – TH-100",
    },
    {
        "name":   "I-394 Merge (Western Approach)",
        "coords": [[44.9710, -93.3100], [44.9740, -93.2940], [44.9758, -93.2800]],
        "factor": 1.10,
        "exit":   "Exit 13 – I-394",
    },
    {
        "name":   "Downtown Minneapolis — West",
        "coords": [[44.9758, -93.2800], [44.9770, -93.2720], [44.9775, -93.2630]],
        "factor": 1.40,   # > 1 → bottleneck zone
        "exit":   "Exit 14 – Hennepin / Lyndale",
    },
    {
        "name":   "Downtown Minneapolis — I-35W Interchange",
        "coords": [[44.9775, -93.2630], [44.9778, -93.2580], [44.9775, -93.2510]],
        "factor": 1.50,   # worst bottleneck
        "exit":   "Exit 15 – I-35W North/South",
    },
    {
        "name":   "Cedar-Riverside / 11th Ave",
        "coords": [[44.9775, -93.2510], [44.9770, -93.2440], [44.9760, -93.2360]],
        "factor": 1.20,
        "exit":   "Exit 16 – 11th Ave",
    },
    {
        "name":   "University of Minnesota / Washington Ave",
        "coords": [[44.9760, -93.2360], [44.9745, -93.2260], [44.9730, -93.2140]],
        "factor": 1.05,
        "exit":   "Exit 17 – Washington Ave",
    },
    {
        "name":   "TH-280 / Energy Park Dr",
        "coords": [[44.9730, -93.2140], [44.9700, -93.2020], [44.9665, -93.1920]],
        "factor": 0.95,
        "exit":   "Exit 18 – TH-280",
    },
    {
        "name":   "Vandalia St / Hamline Ave",
        "coords": [[44.9665, -93.1920], [44.9620, -93.1820], [44.9575, -93.1700]],
        "factor": 0.85,
        "exit":   "Exit 240 – Vandalia",
    },
    {
        "name":   "Snelling Ave — Midway",
        "coords": [[44.9575, -93.1700], [44.9545, -93.1620], [44.9530, -93.1530]],
        "factor": 1.00,
        "exit":   "Exit 241 – Snelling Ave",
    },
    {
        "name":   "Lexington / Hamline Pkwy",
        "coords": [[44.9530, -93.1530], [44.9515, -93.1450], [44.9510, -93.1360]],
        "factor": 0.90,
        "exit":   "Exit 242 – Lexington Pkwy",
    },
    {
        "name":   "Dale St / Marion St",
        "coords": [[44.9510, -93.1360], [44.9515, -93.1250], [44.9520, -93.1160]],
        "factor": 1.00,
        "exit":   "Exit 243 – Dale St",
    },
    {
        "name":   "Minnesota State Capitol Area",
        "coords": [[44.9520, -93.1160], [44.9528, -93.1080], [44.9530, -93.0970]],
        "factor": 1.15,
        "exit":   "Exit 244 – Marion / Capitol",
    },
    {
        "name":   "Downtown Saint Paul — Core",
        "coords": [[44.9530, -93.0970], [44.9530, -93.0900], [44.9525, -93.0830]],
        "factor": 1.30,
        "exit":   "Exit 245A – 7th St / 5th St",
    },
    {
        "name":   "I-35E / Kellogg Blvd Interchange",
        "coords": [[44.9525, -93.0830], [44.9515, -93.0750], [44.9505, -93.0650]],
        "factor": 1.10,
        "exit":   "Exit 245B – I-35E",
    },
    {
        "name":   "East Saint Paul / I-494 East",
        "coords": [[44.9505, -93.0650], [44.9480, -93.0500], [44.9450, -93.0300]],
        "factor": 0.75,
        "exit":   "Exit 250 – I-494 East",
    },
]

# Key interchange markers [lat, lon, label, icon]
MARKERS = [
    (44.9650, -93.4580, "I-94/I-494 West Interchange", "info-sign"),
    (44.9778, -93.2720, "Downtown Minneapolis", "home"),
    (44.9778, -93.2580, "I-35W Interchange ⚠️", "warning-sign"),
    (44.9760, -93.2360, "Univ. of Minnesota", "education"),
    (44.9530, -93.1680, "Midway – Snelling Ave", "map-marker"),
    (44.9530, -93.0900, "Downtown Saint Paul", "home"),
    (44.9505, -93.0650, "I-35E Interchange", "info-sign"),
]


def _code_for_factor(base_code: int, factor: float) -> int:
    """Apply spatial factor to the model's predicted code, clamp to 0–3."""
    adjusted = base_code * factor
    if adjusted < 0.5:
        return 0
    if adjusted < 1.5:
        return 1
    if adjusted < 2.5:
        return 2
    return 3


def _congestion_from_features(model, hour, day_of_week, month,
                               is_holiday, rain_1h, temp_c,
                               lag_1h, lag_24h, rolling_3h, rolling_6h) -> int:
    """Run the model for the given feature set and return congestion code 0–3."""
    from data_processing import FEATURE_COLS
    from datetime import date
    import numpy as np

    is_weekend      = 1 if day_of_week >= 5 else 0
    is_morning_rush = 1 if 7  <= hour <= 9  else 0
    is_evening_rush = 1 if 16 <= hour <= 18 else 0
    is_rush_hour    = int(bool(is_morning_rush or is_evening_rush))
    rush_type       = 1 if is_morning_rush else (2 if is_evening_rush else 0)
    rain_sev        = (0 if rain_1h == 0
                       else 1 if rain_1h < 2.5
                       else 2 if rain_1h < 7.6
                       else 3)
    today = date.today()

    fv = {
        "hour": hour, "day_of_week": day_of_week, "month": month,
        "year": today.year, "day_of_year": today.timetuple().tm_yday,
        "is_weekend": is_weekend, "is_rush_hour": is_rush_hour,
        "rush_type": rush_type, "is_morning_rush": is_morning_rush,
        "is_evening_rush": is_evening_rush,
        "hour_sin":  np.sin(2*np.pi*hour/24),
        "hour_cos":  np.cos(2*np.pi*hour/24),
        "month_sin": np.sin(2*np.pi*month/12),
        "month_cos": np.cos(2*np.pi*month/12),
        "is_holiday": int(is_holiday),
        "temp_celsius": temp_c, "rain_1h": rain_1h,
        "snow_1h": 0.0, "clouds_all": 40,
        "is_raining": int(rain_1h > 0), "is_snowing": 0,
        "weather_severity": float(rain_sev), "weather_code": 0.0,
        "traffic_lag_1h":     lag_1h,
        "traffic_lag_24h":    lag_24h,
        "traffic_rolling_3h": rolling_3h,
        "traffic_rolling_6h": rolling_6h,
    }
    arr = np.array([[float(fv.get(c, 0)) for c in FEATURE_COLS]])
    return int(model.predict(arr)[0])


def create_i94_map(
    model,
    hour: int,
    day_of_week: int,
    month: int,
    is_holiday: bool,
    rain_1h: float,
    temp_c: float,
    lag_1h: float,
    lag_24h: float,
    rolling_3h: float,
    rolling_6h: float,
) -> folium.Map:
    """
    Build and return a Folium map of Metro I-94 with segments coloured
    according to predicted congestion for the given inputs.
    """
    # 1. Global model prediction for the selected conditions
    base_code = _congestion_from_features(
        model, hour, day_of_week, month,
        is_holiday, rain_1h, temp_c,
        lag_1h, lag_24h, rolling_3h, rolling_6h,
    )
    base_label = LABELS[base_code]

    # 2. Create map centred on I-94 corridor (slightly west of St. Paul)
    m = folium.Map(
        location   = [44.9670, -93.2200],
        zoom_start = 12,
        tiles      = "OpenStreetMap",
        control_scale=True,
    )

    # 3. Draw each segment with its per-segment congestion colour
    for seg in I94_SEGMENTS:
        seg_code  = _code_for_factor(base_code, seg["factor"])
        seg_label = LABELS[seg_code]
        color     = COLORS[seg_label]

        # Main route line (thick)
        folium.PolyLine(
            locations = seg["coords"],
            color     = color,
            weight    = 10,
            opacity   = 0.85,
            tooltip   = (
                f"<b>{seg['name']}</b><br>"
                f"Congestion: <b>{seg_label}</b><br>"
                f"{seg['exit']}"
            ),
        ).add_to(m)

        # Thin animated outline for Severe segments
        if seg_label == "Severe":
            AntPath(
                locations = seg["coords"],
                color     = "#ef4444",
                weight    = 3,
                delay     = 600,
                opacity   = 0.6,
            ).add_to(m)

    # 4. Mid-point marker for each segment (shows details on click)
    for seg in I94_SEGMENTS:
        mid_idx = len(seg["coords"]) // 2
        mid_lat = seg["coords"][mid_idx][0]
        mid_lon = seg["coords"][mid_idx][1]
        seg_code  = _code_for_factor(base_code, seg["factor"])
        seg_label = LABELS[seg_code]
        color     = COLORS[seg_label]

        popup_html = f"""
        <div style='font-family:sans-serif;min-width:200px'>
          <h4 style='margin:0;color:{color}'>{seg_label} Congestion</h4>
          <hr style='margin:4px 0'>
          <b>{seg['name']}</b><br>
          <small>{seg['exit']}</small><br><br>
          <span style='background:{color};color:white;
                padding:2px 8px;border-radius:4px;font-size:12px'>
            {seg_label}
          </span>
        </div>"""

        folium.CircleMarker(
            location=[mid_lat, mid_lon],
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=1.0,
            popup=folium.Popup(popup_html, max_width=240),
        ).add_to(m)

    # 5. Major interchange markers
    for lat, lon, label, icon in MARKERS:
        folium.Marker(
            location=[lat, lon],
            tooltip=label,
            popup=folium.Popup(f"<b>{label}</b>", max_width=200),
            icon=folium.Icon(color="darkblue", icon=icon, prefix="glyphicon"),
        ).add_to(m)

    # 6. Legend
    day_names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    legend_html = f"""
    <div style='
        position:fixed; bottom:30px; left:30px; z-index:1000;
        background:white; padding:14px 18px; border-radius:10px;
        box-shadow:0 2px 12px rgba(0,0,0,0.18); font-family:sans-serif;
        min-width:200px;'>
      <b style='font-size:14px'>🚦 I-94 Traffic — {hour:02d}:00</b><br>
      <small style='color:#555'>{day_names[day_of_week]} · Month {month}</small>
      <hr style='margin:8px 0'>
      <div style='margin-bottom:4px'>
        <b>Overall forecast:</b>
        <span style='background:{COLORS[base_label]};color:white;
               padding:1px 8px;border-radius:4px;font-size:12px'>
          {base_label}
        </span>
      </div>
      <hr style='margin:8px 0'>
      {''.join(
          f"<div style='margin:3px 0'>"
          f"<span style='display:inline-block;width:28px;height:8px;"
          f"background:{COLORS[lvl]};border-radius:4px;vertical-align:middle'></span>"
          f" {lvl}</div>"
          for lvl in LABELS
      )}
      <hr style='margin:8px 0'>
      <small style='color:#888'>Click any segment for details</small>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))

    return m
