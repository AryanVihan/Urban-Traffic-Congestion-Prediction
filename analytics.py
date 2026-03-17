"""
analytics.py
------------
Advanced analytics and visualization functions.
Heatmaps, calendar views, weather analysis, weekday/weekend comparison,
and congestion risk scoring.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

DAY_NAMES  = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTH_NAMES = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

LEVEL_COLORS = {
    "Low":    "#22c55e",
    "Medium": "#eab308",
    "High":   "#f97316",
    "Severe": "#ef4444",
}
RISK_PALETTE = ["#22c55e", "#eab308", "#f97316", "#ef4444"]   # Low→Severe


# ── 1. HOUR × DAY HEATMAP ─────────────────────────────────────────────────────
def make_hour_day_heatmap(df: pd.DataFrame) -> go.Figure:
    """24-hour × 7-day heatmap of average traffic volume."""
    pivot = (
        df.groupby(["hour", "day_of_week"])["traffic_volume"]
        .mean()
        .round(0)
        .unstack(level="day_of_week")
    )
    pivot.columns = [DAY_NAMES[i] for i in pivot.columns]
    pivot.index   = [f"{h:02d}:00" for h in pivot.index]

    fig = go.Figure(go.Heatmap(
        z          = pivot.values,
        x          = pivot.columns.tolist(),
        y          = pivot.index.tolist(),
        colorscale = [
            [0.00, "#22c55e"],
            [0.35, "#eab308"],
            [0.65, "#f97316"],
            [1.00, "#ef4444"],
        ],
        colorbar   = dict(title="Vehicles/hr"),
        hoverongaps= False,
        hovertemplate="<b>%{y}</b> on <b>%{x}</b><br>Avg: %{z:.0f} vehicles/hr<extra></extra>",
    ))
    fig.update_layout(
        title      = "Traffic Volume Heatmap — Hour × Day of Week",
        xaxis_title= "Day of Week",
        yaxis_title= "Hour of Day",
        height     = 600,
        plot_bgcolor="#f9fafb",
        paper_bgcolor="#f9fafb",
        font       = dict(size=12),
        yaxis      = dict(autorange="reversed"),   # midnight at top
    )
    # Rush hour bands (no annotation_text to avoid Plotly 6 categorical-axis bug)
    for y0, y1 in [("07:00", "09:00"), ("16:00", "18:00")]:
        fig.add_shape(type="rect",
                      xref="paper", x0=0, x1=1,
                      yref="y",     y0=y0, y1=y1,
                      fillcolor="rgba(59,130,246,0.12)",
                      line_width=0, layer="below")
    return fig


# ── 2. CONGESTION HEATMAP (label instead of raw volume) ──────────────────────
def make_congestion_heatmap(df: pd.DataFrame) -> go.Figure:
    """Hour × Day heatmap using congestion_code (0–3)."""
    pivot = (
        df.assign(congestion_code_f=df["congestion_code"].astype(float))
          .groupby(["hour", "day_of_week"])["congestion_code_f"]
          .mean()
          .round(2)
          .unstack(level="day_of_week")
    )
    pivot.columns = [DAY_NAMES[i] for i in pivot.columns]
    pivot.index   = [f"{h:02d}:00" for h in pivot.index]

    fig = go.Figure(go.Heatmap(
        z          = pivot.values,
        x          = pivot.columns.tolist(),
        y          = pivot.index.tolist(),
        zmin=0, zmax=3,
        colorscale = [
            [0.00, "#22c55e"],
            [0.33, "#eab308"],
            [0.66, "#f97316"],
            [1.00, "#ef4444"],
        ],
        colorbar   = dict(
            title     = "Avg Level",
            tickvals  = [0, 1, 2, 3],
            ticktext  = ["Low", "Medium", "High", "Severe"],
        ),
        hovertemplate="<b>%{y}</b> on <b>%{x}</b><br>Avg congestion: %{z:.2f}<extra></extra>",
    ))
    fig.update_layout(
        title="Congestion Level Heatmap — Hour × Day",
        xaxis_title="Day of Week",
        yaxis_title="Hour of Day",
        height=600,
        plot_bgcolor="#f9fafb",
        paper_bgcolor="#f9fafb",
        yaxis=dict(autorange="reversed"),
    )
    return fig


# ── 3. CALENDAR HEATMAP (monthly view) ────────────────────────────────────────
def make_calendar_heatmap(df: pd.DataFrame, year: int = None) -> go.Figure:
    """Monthly calendar showing average daily traffic, GitHub-style."""
    df2 = df.copy()
    df2["date"] = df2["date_time"].dt.date
    daily = df2.groupby("date")["traffic_volume"].mean().reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    daily["year"]        = daily["date"].dt.year
    daily["week_of_year"]= daily["date"].dt.isocalendar().week.astype(int)
    daily["day_of_week"] = daily["date"].dt.dayofweek   # 0=Mon
    daily["month"]       = daily["date"].dt.month

    if year is None:
        year = daily["year"].mode()[0]

    subset = daily[daily["year"] == year].copy()

    fig = go.Figure(go.Scatter(
        x    = subset["week_of_year"],
        y    = subset["day_of_week"],
        mode = "markers",
        marker=dict(
            size       = 14,
            color      = subset["traffic_volume"],
            colorscale = [
                [0.00, "#22c55e"],
                [0.35, "#eab308"],
                [0.65, "#f97316"],
                [1.00, "#ef4444"],
            ],
            colorbar   = dict(title="Vehicles/hr"),
            showscale  = True,
            symbol     = "square",
            line       = dict(width=1, color="white"),
        ),
        text       = subset["date"].dt.strftime("%b %d"),
        customdata = subset["traffic_volume"].round(0),
        hovertemplate="<b>%{text}</b><br>Avg: %{customdata:.0f} vehicles/hr<extra></extra>",
    ))
    fig.update_layout(
        title      = f"Daily Traffic Calendar — {year}",
        xaxis      = dict(title="Week of Year", showgrid=False),
        yaxis      = dict(
            title    = "",
            tickvals = list(range(7)),
            ticktext = DAY_NAMES,
            showgrid = False,
            autorange= "reversed",
        ),
        height     = 320,
        plot_bgcolor="#f9fafb",
        paper_bgcolor="#f9fafb",
    )
    return fig


# ── 4. WEATHER IMPACT ANALYSIS ────────────────────────────────────────────────
def make_weather_box(df: pd.DataFrame) -> go.Figure:
    """Box plot of traffic volume by weather condition."""
    order = (df.groupby("weather_main")["traffic_volume"]
               .median()
               .sort_values(ascending=False)
               .index.tolist())

    fig = go.Figure()
    palette = px.colors.qualitative.Set2
    for i, cond in enumerate(order):
        vals = df[df["weather_main"] == cond]["traffic_volume"]
        fig.add_trace(go.Box(
            y    = vals,
            name = cond,
            marker_color = palette[i % len(palette)],
            boxmean=True,
        ))
    fig.update_layout(
        title      = "Traffic Volume Distribution by Weather Condition",
        yaxis_title= "Vehicles/hr",
        xaxis_title= "Weather Condition",
        height     = 420,
        showlegend = False,
        plot_bgcolor="#f9fafb",
        paper_bgcolor="#f9fafb",
    )
    return fig


def make_rain_scatter(df: pd.DataFrame) -> go.Figure:
    """Rain intensity vs traffic volume scatter."""
    rain_df = df[df["rain_1h"] > 0].sample(min(3000, len(df[df["rain_1h"] > 0])), random_state=42)
    fig = px.scatter(
        rain_df, x="rain_1h", y="traffic_volume",
        color="congestion_label",
        color_discrete_map=LEVEL_COLORS,
        opacity=0.45,
        labels={"rain_1h": "Rainfall (mm/hr)", "traffic_volume": "Traffic Volume (vehicles/hr)"},
        title="Rainfall Intensity vs Traffic Volume",
    )
    fig.update_layout(height=400, plot_bgcolor="#f9fafb", paper_bgcolor="#f9fafb")
    return fig


def make_temp_traffic(df: pd.DataFrame) -> go.Figure:
    """Temperature vs average traffic volume (binned)."""
    df2 = df.copy()
    df2["temp_bin"] = pd.cut(df2["temp_celsius"], bins=range(-30, 45, 5))
    binned = (df2.groupby("temp_bin", observed=True)["traffic_volume"]
                 .mean()
                 .reset_index())
    binned["temp_label"] = binned["temp_bin"].astype(str)
    fig = px.bar(binned, x="temp_label", y="traffic_volume",
                 labels={"temp_label": "Temperature Range (°C)",
                         "traffic_volume": "Avg Vehicles/hr"},
                 title="Temperature vs Average Traffic Volume",
                 color="traffic_volume",
                 color_continuous_scale=["#22c55e","#eab308","#f97316","#ef4444"])
    fig.update_layout(height=400, plot_bgcolor="#f9fafb", paper_bgcolor="#f9fafb",
                      coloraxis_showscale=False, xaxis_tickangle=-45)
    return fig


def make_weather_severity_bar(df: pd.DataFrame) -> go.Figure:
    """Average congestion by weather severity level."""
    sev_map = {0: "Clear/Dry", 1: "Light Rain", 2: "Moderate Rain",
               3: "Heavy Rain", 4: "Snow/Severe"}
    df2 = df.copy()
    df2["sev_label"] = df2["weather_severity"].clip(upper=4).astype(int).map(sev_map)
    agg = (df2.groupby("sev_label")["traffic_volume"]
              .mean()
              .reindex(list(sev_map.values()))
              .reset_index())
    fig = px.bar(agg, x="sev_label", y="traffic_volume",
                 color="traffic_volume",
                 color_continuous_scale=["#22c55e","#eab308","#f97316","#ef4444"],
                 labels={"sev_label":"Weather Severity","traffic_volume":"Avg Vehicles/hr"},
                 title="Average Traffic by Weather Severity")
    fig.update_layout(height=380, plot_bgcolor="#f9fafb", paper_bgcolor="#f9fafb",
                      coloraxis_showscale=False)
    return fig


# ── 5. WEEKDAY VS WEEKEND ────────────────────────────────────────────────────
def make_weekday_weekend_overlay(df: pd.DataFrame) -> go.Figure:
    """Overlay line chart: average hourly traffic, weekday vs weekend."""
    wkday = df[df["is_weekend"] == 0].groupby("hour")["traffic_volume"].mean()
    wkend = df[df["is_weekend"] == 1].groupby("hour")["traffic_volume"].mean()
    hours = [f"{h:02d}:00" for h in range(24)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours, y=wkday.values, name="Weekday",
        line=dict(color="#3b82f6", width=3),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.08)",
    ))
    fig.add_trace(go.Scatter(
        x=hours, y=wkend.values, name="Weekend",
        line=dict(color="#22c55e", width=3),
        fill="tozeroy", fillcolor="rgba(34,197,94,0.08)",
    ))
    # Rush hour bands (no annotation_text to avoid Plotly 6 categorical-axis bug)
    for x0, x1 in [("07:00","09:00"), ("16:00","18:00")]:
        fig.add_shape(type="rect",
                      xref="x",   x0=x0,  x1=x1,
                      yref="paper", y0=0,  y1=1,
                      fillcolor="rgba(234,179,8,0.15)",
                      line_width=0, layer="below")
    fig.update_layout(
        title      = "Weekday vs Weekend — Average Hourly Traffic",
        xaxis_title= "Hour of Day",
        yaxis_title= "Avg Vehicles/hr",
        height     = 420,
        plot_bgcolor="#f9fafb",
        paper_bgcolor="#f9fafb",
        legend     = dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis      = dict(tickangle=-45),
    )
    return fig


def make_weekday_weekend_by_month(df: pd.DataFrame) -> go.Figure:
    """Grouped bar: monthly avg for weekday vs weekend."""
    wkday = df[df["is_weekend"]==0].groupby("month")["traffic_volume"].mean().round(0)
    wkend = df[df["is_weekend"]==1].groupby("month")["traffic_volume"].mean().round(0)
    months = [MONTH_NAMES[m] for m in range(1, 13)]

    fig = go.Figure([
        go.Bar(name="Weekday", x=months, y=[wkday.get(m, 0) for m in range(1,13)],
               marker_color="#3b82f6"),
        go.Bar(name="Weekend", x=months, y=[wkend.get(m, 0) for m in range(1,13)],
               marker_color="#22c55e"),
    ])
    fig.update_layout(
        barmode    = "group",
        title      = "Monthly Traffic: Weekday vs Weekend",
        xaxis_title= "Month",
        yaxis_title= "Avg Vehicles/hr",
        height     = 380,
        plot_bgcolor="#f9fafb",
        paper_bgcolor="#f9fafb",
        legend     = dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def make_congestion_profile(df: pd.DataFrame) -> go.Figure:
    """Stacked area: congestion level composition over hours."""
    from data_processing import CONGESTION_LABELS
    hourly_dist = (
        df.groupby(["hour", "congestion_label"])
          .size()
          .unstack(fill_value=0)
    )
    # ensure correct column order and normalize to %
    hourly_dist = hourly_dist.reindex(columns=CONGESTION_LABELS, fill_value=0)
    hourly_pct  = hourly_dist.div(hourly_dist.sum(axis=1), axis=0) * 100
    hours       = [f"{h:02d}:00" for h in hourly_pct.index]

    fig = go.Figure()
    for lvl, col in zip(CONGESTION_LABELS, ["#22c55e","#eab308","#f97316","#ef4444"]):
        fig.add_trace(go.Scatter(
            x=hours, y=hourly_pct[lvl].values,
            name=lvl, mode="lines",
            line=dict(width=0, color=col),
            stackgroup="one",
            fillcolor=col,
            hovertemplate=f"<b>{lvl}</b>: %{{y:.1f}}%<extra></extra>",
        ))
    fig.update_layout(
        title      = "Congestion Level Composition by Hour (%)",
        xaxis_title= "Hour of Day",
        yaxis_title= "Share (%)",
        height     = 420,
        plot_bgcolor="#f9fafb",
        paper_bgcolor="#f9fafb",
        legend     = dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis      = dict(tickangle=-45),
    )
    return fig


# ── 6. RISK SCORING ──────────────────────────────────────────────────────────
def compute_24h_risk(model, day_of_week: int, month: int,
                     is_holiday: int, weather_code: float,
                     rain_1h: float, temp_c: float,
                     df_ref: pd.DataFrame) -> pd.DataFrame:
    """
    For each hour 0–23, predict congestion and produce a risk score.
    Uses historical median lag/rolling values per hour as context.
    """
    from data_processing import FEATURE_COLS, CONGESTION_LABELS
    import numpy as np
    from datetime import date

    # Pre-compute median lag features per hour from the dataset
    lag_by_hour = (df_ref.groupby("hour")[["traffic_lag_1h","traffic_lag_24h",
                                            "traffic_rolling_3h","traffic_rolling_6h"]]
                          .median())

    is_weekend      = 1 if day_of_week >= 5 else 0
    today           = date.today()
    day_of_year     = today.timetuple().tm_yday
    year            = today.year
    snow_1h         = 0.0
    rain_sev        = (0 if rain_1h == 0
                       else 1 if rain_1h < 2.5
                       else 2 if rain_1h < 7.6
                       else 3)

    records = []
    for hour in range(24):
        lags = lag_by_hour.loc[hour] if hour in lag_by_hour.index else lag_by_hour.median()

        is_morning_rush = 1 if 7  <= hour <= 9  else 0
        is_evening_rush = 1 if 16 <= hour <= 18 else 0
        is_rush_hour    = int(bool(is_morning_rush or is_evening_rush))
        rush_type       = 1 if is_morning_rush else (2 if is_evening_rush else 0)

        fv = {
            "hour": hour, "day_of_week": day_of_week, "month": month,
            "year": year, "day_of_year": day_of_year,
            "is_weekend": is_weekend, "is_rush_hour": is_rush_hour,
            "rush_type": rush_type, "is_morning_rush": is_morning_rush,
            "is_evening_rush": is_evening_rush,
            "hour_sin":  np.sin(2*np.pi*hour/24),
            "hour_cos":  np.cos(2*np.pi*hour/24),
            "month_sin": np.sin(2*np.pi*month/12),
            "month_cos": np.cos(2*np.pi*month/12),
            "is_holiday": is_holiday,
            "temp_celsius": temp_c, "rain_1h": rain_1h,
            "snow_1h": snow_1h, "clouds_all": 40,
            "is_raining": int(rain_1h > 0), "is_snowing": 0,
            "weather_severity": float(rain_sev),
            "weather_code": weather_code,
            "traffic_lag_1h":     float(lags["traffic_lag_1h"]),
            "traffic_lag_24h":    float(lags["traffic_lag_24h"]),
            "traffic_rolling_3h": float(lags["traffic_rolling_3h"]),
            "traffic_rolling_6h": float(lags["traffic_rolling_6h"]),
        }
        arr       = np.array([[float(fv.get(c, 0)) for c in FEATURE_COLS]])
        code      = int(model.predict(arr)[0])
        proba     = model.predict_proba(arr)[0]
        conf      = round(float(proba[code]) * 100, 1)
        label     = CONGESTION_LABELS[code]
        risk      = (code / 3) * 100          # 0–100 risk score

        records.append({
            "hour":       f"{hour:02d}:00",
            "hour_int":   hour,
            "label":      label,
            "code":       code,
            "confidence": conf,
            "risk_score": round(risk, 1),
        })
    return pd.DataFrame(records)


def make_risk_chart(risk_df: pd.DataFrame) -> go.Figure:
    """Vertical bar chart of 24-hour risk scores, coloured by congestion level."""
    COLOR_MAP = {"Low":"#22c55e","Medium":"#eab308","High":"#f97316","Severe":"#ef4444"}
    colors    = [COLOR_MAP[l] for l in risk_df["label"]]

    fig = go.Figure(go.Bar(
        x             = risk_df["hour"],
        y             = risk_df["risk_score"],
        marker_color  = colors,
        text          = risk_df["label"],
        textposition  = "outside",
        hovertemplate = (
            "<b>%{x}</b><br>"
            "Risk Score: %{y:.0f}/100<br>"
            "Level: %{text}<extra></extra>"
        ),
    ))
    # Reference lines
    for y, label in [(25,"Low threshold"),(50,"Medium threshold"),(75,"High threshold")]:
        fig.add_hline(y=y, line_dash="dot", line_color="gray", line_width=1,
                      annotation_text=label, annotation_position="right",
                      annotation_font_size=9)
    fig.update_layout(
        title      = "24-Hour Congestion Risk Score",
        xaxis_title= "Hour of Day",
        yaxis_title= "Risk Score (0–100)",
        yaxis_range= [0, 115],
        height     = 420,
        plot_bgcolor="#f9fafb",
        paper_bgcolor="#f9fafb",
        xaxis      = dict(tickangle=-45),
    )
    return fig


def make_risk_timeline(risk_df: pd.DataFrame) -> go.Figure:
    """Filled area showing congestion level across 24 hours."""
    COLOR_MAP = {"Low":"#22c55e","Medium":"#eab308","High":"#f97316","Severe":"#ef4444"}

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=risk_df["hour"], y=risk_df["risk_score"],
        mode="lines+markers",
        line=dict(color="#1d4ed8", width=2),
        marker=dict(size=8,
                    color=[COLOR_MAP[l] for l in risk_df["label"]],
                    line=dict(color="white", width=1)),
        fill="tozeroy",
        fillcolor="rgba(29,78,216,0.07)",
        hovertemplate="<b>%{x}</b> — %{customdata}<extra></extra>",
        customdata=risk_df["label"],
    ))
    for y0, y1, col in [(0,25,"rgba(34,197,94,0.08)"), (25,50,"rgba(234,179,8,0.08)"),
                         (50,75,"rgba(249,115,22,0.08)"), (75,100,"rgba(239,68,68,0.08)")]:
        fig.add_hrect(y0=y0, y1=y1, fillcolor=col, line_width=0)

    fig.update_layout(
        title="Risk Timeline — Congestion Through the Day",
        xaxis_title="Hour",
        yaxis_title="Risk Score",
        yaxis_range=[0,105],
        height=350,
        plot_bgcolor="#f9fafb",
        paper_bgcolor="#f9fafb",
        xaxis=dict(tickangle=-45),
    )
    return fig
