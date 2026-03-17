"""
app.py  ─  Urban Traffic Intelligence System
--------------------------------------------
Run: streamlit run app.py

Expects model.pkl, feature_importance.csv, model_results.json
in the same directory (produced by model_training.py).

Edit DATA_PATH below to point to your CSV file.
"""

import sys, os, json, warnings
warnings.filterwarnings("ignore")

# ── Point this at your CSV ───────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "Metro_Interstate_Traffic_Volume.csv")
# Override via: streamlit run app.py -- --data /path/to/file.csv
for i, arg in enumerate(sys.argv):
    if arg == "--data" and i + 1 < len(sys.argv):
        DATA_PATH = sys.argv[i + 1]

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)

import streamlit as st

st.set_page_config(
    page_title="Traffic Intelligence System",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

import pandas as pd
import numpy as np
import joblib

from data_processing import (
    full_pipeline, get_peak_hours_analysis,
    FEATURE_COLS, CONGESTION_LABELS, CONGESTION_MAP,
    MORNING_RUSH, EVENING_RUSH,
)
from insights import (
    LEVEL_DESCRIPTIONS, MONTH_NAMES,
    generate_system_insights, get_recommendations_for_level, explain_prediction,
)
from agents import AgentOrchestrator
from analytics import (
    make_hour_day_heatmap, make_congestion_heatmap,
    make_calendar_heatmap, make_weather_box, make_rain_scatter,
    make_temp_traffic, make_weather_severity_bar,
    make_weekday_weekend_overlay, make_weekday_weekend_by_month,
    make_congestion_profile, compute_24h_risk, make_risk_chart, make_risk_timeline,
)
from map_view import create_i94_map
from streamlit_folium import folium_static
from styles import (
    inject_styles, page_header, metric_row,
    glass_section, glass_badge, congestion_banner,
)
from mcp_servers.bridge import MCPBridge

# ── Inject design system (must be first after set_page_config) ────
inject_styles()


# ── Constants ────────────────────────────────────────────────────
LEVEL_COLORS = {"Low":"#22c55e","Medium":"#eab308","High":"#f97316","Severe":"#ef4444"}
LEVEL_BG     = {"Low":"#f0fdf4","Medium":"#fefce8","High":"#fff7ed","Severe":"#fef2f2"}
MODEL_PATH   = os.path.join(DIR, "model.pkl")
FI_PATH      = os.path.join(DIR, "feature_importance.csv")
RES_PATH     = os.path.join(DIR, "model_results.json")


# ── Cached loaders ───────────────────────────────────────────────
@st.cache_data(show_spinner="Processing dataset…")
def load_data(path):
    df, X, y = full_pipeline(path)
    peak     = get_peak_hours_analysis(df)
    return df, X, y, peak

@st.cache_resource(show_spinner="Loading model…")
def load_model(path):
    return joblib.load(path) if os.path.exists(path) else None

@st.cache_data
def load_fi():
    return pd.read_csv(FI_PATH) if os.path.exists(FI_PATH) else None

@st.cache_data
def load_results():
    return json.load(open(RES_PATH)) if os.path.exists(RES_PATH) else None

@st.cache_resource(show_spinner="Connecting MCP bridge…")
def get_mcp_bridge():
    return MCPBridge()


# ── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:18px 0 10px;">
      <div style="font-size:2.8rem;filter:drop-shadow(0 4px 14px rgba(99,102,241,0.4));
                  animation:float 5s ease-in-out infinite;">🚦</div>
      <div style="font-size:1.05rem;font-weight:800;letter-spacing:-0.01em;
                  background:linear-gradient(135deg,#6366f1,#8b5cf6);
                  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                  background-clip:text;margin-top:6px;">Traffic Intelligence</div>
      <div style="font-size:0.72rem;color:#94a3b8;font-weight:500;margin-top:2px;
                  letter-spacing:0.05em;text-transform:uppercase;">Urban Congestion AI</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    page = st.radio("Navigate", [
        "📊 Overview", "📈 Traffic Patterns",
        "🔮 Predict", "💡 AI Insights", "🏆 Model Report",
        "🗺️ Traffic Map", "🔥 Heatmaps", "🌦️ Weather Analysis",
        "🎯 Risk Scoring", "🤖 MCP Live Intelligence",
    ], label_visibility="collapsed")

    st.divider()
    st.markdown("""
    <div style="font-size:0.78rem;font-weight:700;text-transform:uppercase;
                letter-spacing:0.09em;color:#6366f1;margin-bottom:8px;">
      ⚙️ Pipeline Status</div>""", unsafe_allow_html=True)

    if os.path.exists(MODEL_PATH):
        st.markdown("""
        <div style="background:rgba(34,197,94,0.12);border:1px solid rgba(34,197,94,0.3);
                    border-radius:10px;padding:8px 12px;font-size:0.82rem;font-weight:600;
                    color:#16a34a;margin-bottom:10px;">
          ✅ Model ready · 93.6% F1</div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.3);
                    border-radius:10px;padding:8px 12px;font-size:0.82rem;font-weight:600;
                    color:#d97706;margin-bottom:10px;">
          ⚠️ Train model first</div>""", unsafe_allow_html=True)

    if st.button("🚀 Train / Retrain", type="primary", width="stretch"):
        from model_training import run_full_training
        with st.spinner("Training… (~60 s)"):
            run_full_training(DATA_PATH, output_dir=DIR)
        load_model.clear(); load_fi.clear(); load_results.clear()
        st.success("Done! Refresh to see updated results.")
        st.rerun()

    st.markdown(f"""
    <div style="margin-top:16px;padding:10px 12px;
                background:rgba(255,255,255,0.5);border-radius:10px;
                border:1px solid rgba(255,255,255,0.7);">
      <div style="font-size:0.68rem;color:#94a3b8;font-weight:600;
                  text-transform:uppercase;letter-spacing:0.08em;">Dataset</div>
      <div style="font-size:0.80rem;color:#475569;font-weight:500;margin-top:3px;">
        {os.path.basename(DATA_PATH)}</div>
      <div style="font-size:0.72rem;color:#94a3b8;margin-top:2px;">
        Metro I-94 · 2012–2018 · 48K records</div>
    </div>""", unsafe_allow_html=True)


# ── Load ─────────────────────────────────────────────────────────
try:
    df, X, y, peak_data = load_data(DATA_PATH)
    model   = load_model(MODEL_PATH)
    fi_df   = load_fi()
    results = load_results()
except Exception as e:
    st.error(f"❌ {e}"); st.stop()


# ════════════════════════════════════════════════════════════════
#  PAGE 1 — OVERVIEW
# ════════════════════════════════════════════════════════════════
if page == "📊 Overview":
    st.markdown(page_header("📊", "Urban Traffic Intelligence System",
        "Metro I-94 Interstate · Minneapolis – Saint Paul · 2012–2018"), unsafe_allow_html=True)

    st.markdown(metric_row([
        {"icon": "📁", "value": f"{len(df):,}",                        "label": "Total Records",    "color": "#6366f1"},
        {"icon": "📅", "value": str(df['date_time'].dt.year.nunique()), "label": "Years of Data",    "color": "#8b5cf6"},
        {"icon": "🚗", "value": f"{int(df['traffic_volume'].mean()):,}","label": "Avg Vol / hr",     "color": "#06b6d4"},
        {"icon": "⏰", "value": f"{peak_data['peak_hour']}:00",         "label": "Peak Hour",        "color": "#f59e0b"},
        {"icon": "📆", "value": peak_data["peak_day"],                  "label": "Busiest Day",      "color": "#22c55e"},
    ]), unsafe_allow_html=True)

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(glass_section("Congestion Distribution", "🚦"), unsafe_allow_html=True)
        lvl_colors = {"Low":"#22c55e","Medium":"#f59e0b","High":"#f97316","Severe":"#ef4444"}
        lvl_bgs    = {"Low":"rgba(34,197,94,0.08)","Medium":"rgba(245,158,11,0.08)",
                      "High":"rgba(249,115,22,0.08)","Severe":"rgba(239,68,68,0.08)"}
        for lvl in CONGESTION_LABELS:
            cnt = int(df["congestion_label"].value_counts().get(lvl, 0))
            pct = round(cnt / len(df) * 100, 1)
            col = lvl_colors[lvl]
            st.markdown(
                f"<div style='border-left:4px solid {col};background:{lvl_bgs[lvl]};"
                f"backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);"
                f"border:1px solid {col}22;border-radius:0 14px 14px 0;"
                f"padding:12px 18px;margin-bottom:10px;"
                f"box-shadow:0 2px 10px {col}18;"
                f"animation:fadeInLeft 0.4s ease both;"
                f"transition:transform 0.25s ease;'>"
                f"<div style='display:flex;justify-content:space-between;align-items:center'>"
                f"<span style='font-weight:700;font-size:0.92rem;color:#1e293b'>"
                f"{LEVEL_DESCRIPTIONS[lvl]['emoji']} {lvl}</span>"
                f"<span style='background:{col}22;color:{col};font-weight:800;"
                f"font-size:0.82rem;padding:3px 10px;border-radius:99px'>{pct}%</span></div>"
                f"<div style='margin-top:4px;font-size:0.78rem;color:#64748b;font-weight:500'>"
                f"{cnt:,} records</div></div>",
                unsafe_allow_html=True,
            )
    with col_b:
        st.markdown(glass_section("Dataset Summary", "📋"), unsafe_allow_html=True)
        summary = pd.DataFrame({
            "Metric": ["Date range","Min vol/hr","Max vol/hr","Median vol/hr",
                       "Rush hr avg","Weekend avg","Weekday avg","Holiday avg"],
            "Value":  [
                f"{df['date_time'].min().date()} → {df['date_time'].max().date()}",
                str(int(df["traffic_volume"].min())),
                str(int(df["traffic_volume"].max())),
                str(int(df["traffic_volume"].median())),
                f"{int(peak_data['rush_avg']):,}",
                f"{int(peak_data['weekend_avg']):,}",
                f"{int(peak_data['weekday_avg']):,}",
                f"{int(peak_data['holiday_avg']):,}",
            ]
        })
        st.dataframe(summary, hide_index=True, width="stretch")

    st.divider()
    st.subheader("Raw Data Sample (200 rows)")
    st.dataframe(
        df[["date_time","traffic_volume","congestion_label","hour",
            "is_rush_hour","is_weekend","weather_main","temp_celsius","rain_1h"]].head(200),
        hide_index=True, width="stretch",
    )


# ════════════════════════════════════════════════════════════════
#  PAGE 2 — TRAFFIC PATTERNS
# ════════════════════════════════════════════════════════════════
elif page == "📈 Traffic Patterns":
    st.markdown(page_header("📈", "Traffic Pattern Analysis",
        "Hourly, daily, weather and seasonal trends across 6 years of data"), unsafe_allow_html=True)

    t1,t2,t3,t4 = st.tabs(["⏰ Hourly","📅 Daily","🌤️ Weather","📆 Seasonal"])

    with t1:
        st.subheader("Average Traffic by Hour")
        hourly = pd.Series({f"{h}:00": v for h, v in peak_data["hourly_avg"].items()},
                           name="Avg Vehicles/hr")
        st.bar_chart(hourly, color="#f97316")
        st.markdown(f"🟡 **Morning rush:** {MORNING_RUSH[0]}–{MORNING_RUSH[1]}:00 &nbsp; "
                    f"🟠 **Evening rush:** {EVENING_RUSH[0]}–{EVENING_RUSH[1]}:00")
        st.markdown(metric_row([
            {"icon": "⏰", "value": f"{peak_data['peak_hour']}:00",    "label": "Peak Hour",   "color": "#f97316"},
            {"icon": "🌙", "value": f"{peak_data['trough_hour']}:00",  "label": "Quiet Hour",  "color": "#6366f1"},
            {"icon": "🚗", "value": f"{int(peak_data['rush_avg']):,}", "label": "Rush Avg/hr", "color": "#ef4444"},
        ]), unsafe_allow_html=True)

    with t2:
        st.subheader("Average Traffic by Day of Week")
        daily = pd.Series(peak_data["daily_avg"], name="Avg Vehicles/hr")
        st.bar_chart(daily, color="#3b82f6")
        st.subheader("Weekend vs Weekday")
        st.bar_chart(pd.DataFrame({"Weekday": [int(peak_data["weekday_avg"])],
                                    "Weekend": [int(peak_data["weekend_avg"])]}),
                     color=["#3b82f6","#22c55e"])

    with t3:
        st.subheader("Average Traffic by Weather Condition")
        w_series = pd.Series(peak_data["weather_impact"], name="Avg Vehicles/hr")\
                     .sort_values(ascending=False)
        st.bar_chart(w_series, color="#8b5cf6")
        st.caption("Severe weather (fog, squalls) suppresses trips — lower count but not safer driving.")

    with t4:
        st.subheader("Average Traffic by Month")
        monthly = pd.Series(
            {MONTH_NAMES[int(k)]: v for k, v in peak_data["monthly_avg"].items()},
            name="Avg Vehicles/hr"
        )
        st.bar_chart(monthly, color="#ec4899")
        st.metric("Busiest month", MONTH_NAMES[int(peak_data["worst_month"])])


# ════════════════════════════════════════════════════════════════
#  PAGE 3 — PREDICT
# ════════════════════════════════════════════════════════════════
elif page == "🔮 Predict":
    st.markdown(page_header("🔮", "Real-Time Congestion Prediction",
        "Set conditions below — the 4-agent AI pipeline returns a prediction with full explanation"), unsafe_allow_html=True)

    if model is None:
        st.warning("⚠️ Train the model first (sidebar button).")
        st.stop()

    with st.form("pred_form"):
        st.subheader("Input Conditions")
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown("**🕐 Time**")
            hour        = st.slider("Hour", 0, 23, 17)
            day_of_week = st.selectbox("Day",
                options=[0,1,2,3,4,5,6],
                format_func=lambda x: ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][x])
            month       = st.slider("Month", 1, 12, 8)
            is_holiday  = st.checkbox("Public Holiday?")

        with c2:
            st.markdown("**🌤️ Weather**")
            weather_main = st.selectbox("Condition",
                ["Clear","Clouds","Rain","Drizzle","Mist","Fog",
                 "Snow","Thunderstorm","Haze","Squall","Smoke"])
            temp_c  = st.slider("Temp (°C)", -30, 40, 18)
            rain_1h = st.slider("Rain (mm/hr)", 0.0, 50.0, 0.0, step=0.5)
            snow_1h = st.slider("Snow (cm)", 0.0, 0.5, 0.0, step=0.05)
            clouds  = st.slider("Cloud cover (%)", 0, 100, 40)

        with c3:
            st.markdown("**📊 Recent Traffic**")
            lag_1h     = st.slider("Last hour vol", 0, 7280, 3500)
            lag_24h    = st.slider("Same hr yesterday", 0, 7280, 4000)
            rolling_3h = st.slider("3-hr rolling avg", 0, 7280, 3800)
            rolling_6h = st.slider("6-hr rolling avg", 0, 7280, 3600)

        submitted = st.form_submit_button("🚀 Predict Congestion",
                                          type="primary", width="stretch")

    if submitted:
        is_weekend      = 1 if day_of_week >= 5 else 0
        is_morning_rush = 1 if MORNING_RUSH[0] <= hour <= MORNING_RUSH[1] else 0
        is_evening_rush = 1 if EVENING_RUSH[0] <= hour <= EVENING_RUSH[1] else 0
        is_rush_hour    = int(bool(is_morning_rush or is_evening_rush))
        rush_type       = 1 if is_morning_rush else (2 if is_evening_rush else 0)

        w_map = {"Clear":0,"Clouds":1,"Haze":1,"Smoke":2,"Drizzle":2,
                 "Rain":3,"Mist":3,"Fog":4,"Thunderstorm":4,"Snow":4,"Squall":5}
        rain_sev = 0 if rain_1h==0 else (1 if rain_1h<2.5 else (2 if rain_1h<7.6 else 3))

        from datetime import datetime
        now = datetime.now()
        input_features = {
            "hour": hour, "day_of_week": day_of_week, "month": month,
            "year": now.year, "day_of_year": now.timetuple().tm_yday,
            "is_weekend": is_weekend, "is_rush_hour": is_rush_hour,
            "rush_type": rush_type, "is_morning_rush": is_morning_rush,
            "is_evening_rush": is_evening_rush,
            "hour_sin":  np.sin(2*np.pi*hour/24),
            "hour_cos":  np.cos(2*np.pi*hour/24),
            "month_sin": np.sin(2*np.pi*month/12),
            "month_cos": np.cos(2*np.pi*month/12),
            "is_holiday": int(is_holiday),
            "temp_celsius": temp_c, "rain_1h": rain_1h, "snow_1h": snow_1h,
            "clouds_all": clouds, "is_raining": int(rain_1h>0),
            "is_snowing": int(snow_1h>0),
            "weather_severity": float(rain_sev + int(snow_1h>0)),
            "weather_code": float(w_map.get(weather_main, 2)),
            "traffic_lag_1h": lag_1h, "traffic_lag_24h": lag_24h,
            "traffic_rolling_3h": rolling_3h, "traffic_rolling_6h": rolling_6h,
        }

        orch   = AgentOrchestrator(model, df, fi_df)
        report = orch.run_prediction_pipeline(input_features)
        pred   = report["prediction"]
        expl   = report["explanation"]
        plan   = report["action_plan"]
        label  = pred["predicted_label"]
        col    = LEVEL_COLORS[label]
        emoji  = LEVEL_DESCRIPTIONS[label]["emoji"]

        st.markdown(congestion_banner(
            label, pred["confidence"], pred["inference_time_ms"],
            LEVEL_DESCRIPTIONS[label]["impact"]), unsafe_allow_html=True)

        if pred["class_probabilities"]:
            st.markdown(glass_section("Class Probabilities", "📊"), unsafe_allow_html=True)
            st.bar_chart(pd.Series(pred["class_probabilities"], name="Probability (%)"), color=col)

        col_e, col_p = st.columns(2)
        with col_e:
            st.markdown(glass_section("Why This Prediction?", "🧠"), unsafe_allow_html=True)
            st.markdown(
                f"<p style='font-style:italic;color:#475569;font-size:0.9rem;"
                f"line-height:1.6;padding:10px 14px;background:rgba(255,255,255,0.6);"
                f"border-radius:12px;border:1px solid rgba(255,255,255,0.8)'>"
                f"{expl['prediction_narrative']}</p>", unsafe_allow_html=True)
            for f in expl["contributing_factors"]:
                impact_icon = {"high":"🔴","moderate":"🟡","reducing":"🟢"}.get(f["impact"],"⚪")
                with st.expander(f"{impact_icon} {f['factor']}"):
                    st.write(f["detail"])
        with col_p:
            urgency_colors = {"CRITICAL":"#ef4444","HIGH":"#f97316","NORMAL":"#f59e0b","LOW":"#22c55e"}
            urg_col = urgency_colors.get(plan["urgency"], "#6366f1")
            st.markdown(glass_section(
                f"Action Plan &nbsp; {glass_badge(plan['urgency'], urg_col)}", "⚡"),
                unsafe_allow_html=True)
            for a in plan["immediate_actions"]:
                st.markdown(
                    f"<div style='padding:6px 12px;margin-bottom:6px;"
                    f"background:rgba(255,255,255,0.65);border-radius:10px;"
                    f"border-left:3px solid {urg_col};font-size:0.88rem;"
                    f"animation:fadeInLeft 0.3s ease both'>{a}</div>",
                    unsafe_allow_html=True)
            if plan["contextual_actions"]:
                st.markdown(
                    "<div style='font-size:0.78rem;font-weight:700;color:#64748b;"
                    "text-transform:uppercase;letter-spacing:0.08em;margin:12px 0 6px'>"
                    "Context-specific</div>", unsafe_allow_html=True)
                for a in plan["contextual_actions"]:
                    st.markdown(
                        f"<div style='padding:6px 12px;margin-bottom:6px;"
                        f"background:rgba(99,102,241,0.06);border-radius:10px;"
                        f"border-left:3px solid #6366f1;font-size:0.88rem'>{a}</div>",
                        unsafe_allow_html=True)

        with st.expander("🤖 Agent Execution Trace"):
            st.dataframe(pd.DataFrame(report["logs"]), hide_index=True, width="stretch")


# ════════════════════════════════════════════════════════════════
#  PAGE 4 — AI INSIGHTS
# ════════════════════════════════════════════════════════════════
elif page == "💡 AI Insights":
    st.markdown(page_header("💡", "AI-Generated System Insights",
        "Evidence-backed intelligence derived from 6 years of Metro I-94 data"), unsafe_allow_html=True)

    insights = generate_system_insights(peak_data)
    p_order  = {"HIGH":0,"MEDIUM":1,"LOW":2}
    p_color  = {"HIGH":"#ef4444","MEDIUM":"#f97316","LOW":"#22c55e"}

    for ins in sorted(insights, key=lambda x: p_order.get(x["priority"],3)):
        pc = p_color.get(ins["priority"],"#6366f1")
        st.markdown(
            f"<div style='"
            f"background:rgba(255,255,255,0.70);"
            f"backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);"
            f"border:1px solid rgba(255,255,255,0.70);"
            f"border-left:4px solid {pc};"
            f"border-radius:0 20px 20px 0;"
            f"padding:20px 24px;margin-bottom:14px;"
            f"box-shadow:0 4px 24px rgba(99,102,241,0.09);"
            f"animation:fadeInLeft 0.4s ease both;"
            f"transition:transform 0.28s ease,box-shadow 0.28s ease;'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px'>"
            f"<span style='font-size:1rem;font-weight:700;color:#1e293b'>{ins['title']}</span>"
            f"<span style='font-size:0.7rem;font-weight:800;color:{pc};"
            f"background:{pc}18;border:1px solid {pc}44;"
            f"padding:3px 10px;border-radius:99px;letter-spacing:0.06em'>{ins['priority']}</span></div>"
            f"<p style='margin:0 0 8px;color:#374151;font-size:0.9rem;line-height:1.6'>{ins['finding']}</p>"
            f"<div style='background:rgba(99,102,241,0.06);border-radius:10px;"
            f"padding:8px 12px;font-size:0.85rem;color:#1d4ed8'>"
            f"💼 <strong>Recommendation:</strong> {ins['recommendation']}</div></div>",
            unsafe_allow_html=True,
        )


# ════════════════════════════════════════════════════════════════
#  PAGE 5 — MODEL REPORT
# ════════════════════════════════════════════════════════════════
elif page == "🏆 Model Report":
    st.markdown(page_header("🏆", "Model Performance Report",
        "Comparison of 3 trained classifiers · Feature importance · Engineering summary"), unsafe_allow_html=True)

    if results:
        st.markdown(glass_section("Model Comparison", "🤖"), unsafe_allow_html=True)
        res_df = pd.DataFrame(results).T.reset_index()
        res_df.columns = ["Model","Accuracy","F1 (Weighted)","Train Time (s)"]
        res_df = res_df.sort_values("F1 (Weighted)", ascending=False)
        st.dataframe(
            res_df.style.highlight_max(subset=["Accuracy","F1 (Weighted)"], color="#bbf7d0"),
            hide_index=True, width="stretch",
        )
        st.success(f"✅ Best model: **{res_df.iloc[0]['Model']}**")
    else:
        st.warning("No results found — train first.")

    if fi_df is not None:
        st.divider()
        st.markdown(glass_section("Feature Importance (Top 15)", "📊"), unsafe_allow_html=True)
        top = fi_df.head(15).set_index("feature")["importance"].sort_values()
        st.bar_chart(top, color="#8b5cf6")
        st.caption("Previous-hour traffic lag + hour + day_of_week are the strongest predictors.")
        with st.expander("Full feature table"):
            st.dataframe(fi_df, hide_index=True, width="stretch")

    st.divider()
    st.subheader("Feature Engineering Summary")
    feat_df = pd.DataFrame({
        "Group":      ["Time raw","Rush hours","Cyclical","Calendar",
                       "Weather raw","Weather derived","Lag / rolling"],
        "Features":   [
            "hour, day_of_week, month, year, day_of_year",
            "is_rush_hour, rush_type, is_morning_rush, is_evening_rush",
            "hour_sin, hour_cos, month_sin, month_cos",
            "is_weekend, is_holiday",
            "temp_celsius, rain_1h, snow_1h, clouds_all",
            "is_raining, is_snowing, weather_severity, weather_code",
            "traffic_lag_1h, traffic_lag_24h, traffic_rolling_3h, traffic_rolling_6h",
        ],
        "Inspiration": [
            "All 3 notebooks","Problem statement","Notebook 1 (GRU cyclical)",
            "All 3 notebooks","Notebook 3 (TCI)","Notebook 2 + Domain knowledge",
            "Notebook 1 (sliding window)",
        ],
    })
    st.dataframe(feat_df, hide_index=True, width="stretch")

    st.divider()
    st.subheader("Congestion Label Thresholds")
    thresh_df = pd.DataFrame({
        "Level":["Low","Medium","High","Severe"],
        "Volume Range (vehicles/hr)":["0 – 1,000","1,001 – 2,500","2,501 – 4,500","4,501 – 7,280"],
        "Colour":["🟢","🟡","🟠","🔴"],
    })
    st.dataframe(thresh_df, hide_index=True, width="stretch")


# ════════════════════════════════════════════════════════════════
#  PAGE 6 — TRAFFIC MAP
# ════════════════════════════════════════════════════════════════
elif page == "🗺️ Traffic Map":
    st.markdown(page_header("🗺️", "Metro I-94 Live Traffic Map",
        "Interactive corridor map · Segments colour-coded by AI congestion prediction"), unsafe_allow_html=True)

    if model is None:
        st.warning("⚠️ Train the model first (sidebar button).")
        st.stop()

    # ── Map controls ──────────────────────────────────────────────
    with st.sidebar:
        st.divider()
        st.subheader("🗺️ Map Controls")
        map_hour       = st.slider("Hour of day", 0, 23, 17, key="map_hour")
        map_day        = st.selectbox("Day of week", range(7),
                             format_func=lambda x: ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][x],
                             key="map_day")
        map_month      = st.slider("Month", 1, 12, 8, key="map_month")
        map_holiday    = st.checkbox("Public holiday?", key="map_hol")
        map_rain       = st.slider("Rain (mm/hr)", 0.0, 30.0, 0.0, step=0.5, key="map_rain")
        map_temp       = st.slider("Temp (°C)", -20, 40, 15, key="map_temp")
        map_lag1h      = st.slider("Prior hour volume", 0, 7280, 3500, key="map_lag1h")

    # Derive rolling/lag approximations from lag_1h
    map_lag24  = int(map_lag1h * 0.95)
    map_roll3  = int(map_lag1h * 0.98)
    map_roll6  = int(map_lag1h * 0.96)

    with st.spinner("Generating traffic map…"):
        traffic_map = create_i94_map(
            model       = model,
            hour        = map_hour,
            day_of_week = map_day,
            month       = map_month,
            is_holiday  = map_holiday,
            rain_1h     = map_rain,
            temp_c      = map_temp,
            lag_1h      = float(map_lag1h),
            lag_24h     = float(map_lag24),
            rolling_3h  = float(map_roll3),
            rolling_6h  = float(map_roll6),
        )

    folium_static(traffic_map, width=1100, height=560)

    st.divider()
    st.subheader("📍 Segment Legend")
    lvl_meta = {"Low":("#22c55e","🟢"),"Medium":("#f59e0b","🟡"),"High":("#f97316","🟠"),"Severe":("#ef4444","🔴")}
    seg_cols = st.columns(4)
    for i, (lvl, (col, ico)) in enumerate(lvl_meta.items()):
        seg_cols[i].markdown(
            f"<div style='background:linear-gradient(135deg,{col},{col}cc);"
            f"color:white;text-align:center;padding:12px 8px;border-radius:14px;"
            f"font-weight:700;font-size:0.9rem;"
            f"box-shadow:0 4px 16px {col}55;"
            f"animation:cardPop 0.4s ease {i*0.08}s both'>{ico} {lvl}</div>",
            unsafe_allow_html=True,
        )
    st.caption(
        "Segment colours are adjusted by historical bottleneck factors. "
        "The I-35W interchange and downtown core are the most congested zones. "
        "Click any marker or segment for details."
    )


# ════════════════════════════════════════════════════════════════
#  PAGE 7 — HEATMAPS & CALENDAR
# ════════════════════════════════════════════════════════════════
elif page == "🔥 Heatmaps":
    st.markdown(page_header("🔥", "Traffic Heatmaps & Calendar",
        "Visualise when congestion is heaviest — hour × day matrix, daily calendar & level composition"), unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "⏱️ Volume Heatmap", "🚦 Congestion Heatmap",
        "📅 Daily Calendar", "📊 Level Composition",
    ])

    with tab1:
        st.subheader("Average Traffic Volume — Hour × Day")
        st.plotly_chart(make_hour_day_heatmap(df), use_container_width=True)
        st.caption(
            "Colour = average vehicles/hr. Rush-hour bands (7–9 AM, 4–6 PM) are highlighted in blue. "
            "Friday afternoon peak is consistently the highest cell."
        )

    with tab2:
        st.subheader("Average Congestion Level — Hour × Day")
        st.plotly_chart(make_congestion_heatmap(df), use_container_width=True)
        st.caption(
            "Colour = average congestion code (0=Low, 3=Severe). "
            "Weekday rush hours show the deepest red zones."
        )

    with tab3:
        st.subheader("Peak Traffic Prediction Calendar")
        years = sorted(df["year"].unique())
        sel_year = st.selectbox("Select year", years, index=len(years)-1)
        st.plotly_chart(make_calendar_heatmap(df, year=int(sel_year)),
                        use_container_width=True)
        st.caption(
            "Each square = one day. Colour = average traffic volume. "
            "Hover to see exact date and volume."
        )

    with tab4:
        st.subheader("Congestion Level Composition by Hour")
        st.plotly_chart(make_congestion_profile(df), use_container_width=True)
        st.caption(
            "Stacked area showing what % of historical records in each hour "
            "fell into each congestion level. Late night is almost entirely Low; "
            "5 PM peaks with High and Severe."
        )


# ════════════════════════════════════════════════════════════════
#  PAGE 8 — WEATHER ANALYSIS
# ════════════════════════════════════════════════════════════════
elif page == "🌦️ Weather Analysis":
    st.markdown(page_header("🌦️", "Weather Impact Analysis",
        "Temperature, rainfall and weather condition effects on Metro I-94 traffic over 6 years"), unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "🌤️ Condition Breakdown", "🌧️ Rain vs Traffic",
        "🌡️ Temperature Effect", "⚡ Severity Scale",
    ])

    with tab1:
        st.subheader("Traffic Volume by Weather Condition")
        st.plotly_chart(make_weather_box(df), use_container_width=True)
        c1, c2, c3 = st.columns(3)
        weather_means = df.groupby("weather_main")["traffic_volume"].mean().round(0)
        best_w  = weather_means.idxmax()
        worst_w = weather_means.idxmin()
        c1.metric("Highest-volume condition", best_w,
                  f"{int(weather_means[best_w]):,} avg vehicles/hr")
        c2.metric("Lowest-volume condition",  worst_w,
                  f"{int(weather_means[worst_w]):,} avg vehicles/hr")
        c3.metric("Clear-to-Severe difference",
                  f"{int(weather_means.get('Clear',0) - weather_means.get('Squall',weather_means.min())):,} vehicles/hr")
        st.info(
            "💡 **Counter-intuitive:** Clear weather often shows *higher* traffic because "
            "people make more discretionary trips. Extreme weather (fog, squalls) "
            "suppresses total trips but the ones that occur are still congested."
        )

    with tab2:
        st.subheader("Rainfall Intensity vs Traffic Volume")
        st.plotly_chart(make_rain_scatter(df), use_container_width=True)
        rainy = df[df["rain_1h"] > 0]
        st.markdown(
            f"**{len(rainy):,}** rainy-hour records ({len(rainy)/len(df)*100:.1f}% of dataset). "
            f"Avg traffic when raining: **{int(rainy['traffic_volume'].mean()):,}** vs "
            f"**{int(df[df['rain_1h']==0]['traffic_volume'].mean()):,}** when dry."
        )

    with tab3:
        st.subheader("Temperature vs Average Traffic")
        st.plotly_chart(make_temp_traffic(df), use_container_width=True)
        st.caption(
            "Traffic peaks at moderate temperatures (10–25°C). "
            "Very cold winters and very hot summers both slightly suppress volume."
        )

    with tab4:
        st.subheader("Traffic by Weather Severity Score")
        st.plotly_chart(make_weather_severity_bar(df), use_container_width=True)
        st.caption(
            "Severity: 0=Clear/Dry, 1=Light Rain (<2.5mm), 2=Moderate Rain, "
            "3=Heavy Rain (>7.6mm), 4=Snow/Fog/Thunderstorm."
        )


# ════════════════════════════════════════════════════════════════
#  PAGE 9 — RISK SCORING & WEEKDAY VS WEEKEND
# ════════════════════════════════════════════════════════════════
elif page == "🎯 Risk Scoring":
    st.markdown(page_header("🎯", "Congestion Risk Scoring",
        "24-hour AI risk forecast · Weekday vs weekend patterns · Monthly breakdown"), unsafe_allow_html=True)

    if model is None:
        st.warning("⚠️ Train the model first.")
        st.stop()

    tab1, tab2, tab3 = st.tabs([
        "🎯 24-Hour Risk Forecast", "⚖️ Weekday vs Weekend", "📈 Monthly Comparison",
    ])

    with tab1:
        st.subheader("24-Hour Congestion Risk Forecast")
        rc1, rc2, rc3, rc4 = st.columns(4)
        risk_day   = rc1.selectbox("Day",   range(7),
                         format_func=lambda x: ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][x],
                         index=1, key="risk_day")
        risk_month = rc2.slider("Month", 1, 12, 8, key="risk_month")
        risk_hol   = rc3.checkbox("Holiday?", key="risk_hol")
        risk_rain  = rc4.slider("Rain (mm/hr)", 0.0, 20.0, 0.0, step=0.5, key="risk_rain")
        risk_temp  = st.slider("Temperature (°C)", -20, 40, 18, key="risk_temp")

        w_code_map = {0: "Clear/Clouds", 3: "Rain/Mist", 4: "Fog/Thunderstorm", 5: "Squall"}
        risk_weather = st.selectbox("Weather",
            options=list(w_code_map.keys()),
            format_func=lambda x: w_code_map[x],
            key="risk_weather")

        with st.spinner("Computing 24-hour risk scores…"):
            risk_df = compute_24h_risk(
                model       = model,
                day_of_week = risk_day,
                month       = risk_month,
                is_holiday  = int(risk_hol),
                weather_code= float(risk_weather),
                rain_1h     = risk_rain,
                temp_c      = risk_temp,
                df_ref      = df,
            )

        # KPI row
        severe_hrs = (risk_df["label"] == "Severe").sum()
        high_hrs   = (risk_df["label"] == "High").sum()
        peak_hr    = risk_df.loc[risk_df["risk_score"].idxmax(), "hour"]
        avg_risk   = risk_df["risk_score"].mean()

        st.markdown(metric_row([
            {"icon": "🔴", "value": f"{severe_hrs}/24",       "label": "Severe Hours",    "color": "#ef4444"},
            {"icon": "🟠", "value": f"{high_hrs}/24",         "label": "High Hours",      "color": "#f97316"},
            {"icon": "⏰", "value": peak_hr,                  "label": "Peak Risk Hour",  "color": "#8b5cf6"},
            {"icon": "📊", "value": f"{avg_risk:.0f}/100",    "label": "Avg Risk Score",  "color": "#6366f1"},
        ]), unsafe_allow_html=True)

        st.plotly_chart(make_risk_chart(risk_df),    use_container_width=True)
        st.plotly_chart(make_risk_timeline(risk_df), use_container_width=True)

        st.subheader("Hourly Risk Table")
        display_df = risk_df[["hour","label","confidence","risk_score"]].copy()
        display_df.columns = ["Hour","Congestion Level","Model Confidence (%)","Risk Score (0–100)"]

        def _style_row(row):
            color_map = {"Low":"#f0fdf4","Medium":"#fefce8","High":"#fff7ed","Severe":"#fef2f2"}
            bg = color_map.get(row["Congestion Level"], "white")
            return [f"background-color:{bg}"]*len(row)

        st.dataframe(
            display_df.style.apply(_style_row, axis=1),
            hide_index=True, width="stretch",
        )

    with tab2:
        st.subheader("Weekday vs Weekend — Hourly Overlay")
        st.plotly_chart(make_weekday_weekend_overlay(df), use_container_width=True)

        wkday_avg = df[df["is_weekend"]==0]["traffic_volume"].mean()
        wkend_avg = df[df["is_weekend"]==1]["traffic_volume"].mean()
        diff_pct  = (wkday_avg - wkend_avg) / wkday_avg * 100
        st.markdown(metric_row([
            {"icon": "💼", "value": f"{int(wkday_avg):,}", "label": "Weekday Avg / hr", "color": "#3b82f6"},
            {"icon": "🏖️", "value": f"{int(wkend_avg):,}", "label": "Weekend Avg / hr", "color": "#22c55e"},
            {"icon": "📈", "value": f"+{diff_pct:.1f}%",   "label": "Weekday Premium",  "color": "#f97316"},
        ]), unsafe_allow_html=True)

        st.info(
            "💡 **Key finding:** Weekday traffic peaks sharply at 8 AM and 5 PM. "
            "Weekend traffic rises gradually, peaks around noon–2 PM, and lacks the "
            "sharp evening rush. This confirms the commuter-dominated nature of I-94."
        )

    with tab3:
        st.subheader("Monthly Weekday vs Weekend Breakdown")
        st.plotly_chart(make_weekday_weekend_by_month(df), use_container_width=True)
        peak_month_wk  = df[df["is_weekend"]==0].groupby("month")["traffic_volume"].mean().idxmax()
        peak_month_wkd = df[df["is_weekend"]==1].groupby("month")["traffic_volume"].mean().idxmax()
        st.markdown(
            f"Weekday peak month: **{MONTH_NAMES[peak_month_wk]}** &nbsp;·&nbsp; "
            f"Weekend peak month: **{MONTH_NAMES[peak_month_wkd]}**"
        )


# ════════════════════════════════════════════════════════════════
#  PAGE 10 — MCP LIVE INTELLIGENCE
# ════════════════════════════════════════════════════════════════
elif page == "🤖 MCP Live Intelligence":
    st.markdown(page_header("🤖", "MCP Live Intelligence",
        "Real-time traffic intelligence powered by 4 MCP-compatible servers"), unsafe_allow_html=True)

    if model is None:
        st.warning("⚠️ Train the model first (sidebar button).")
        st.stop()

    bridge = get_mcp_bridge()

    # ── Live weather controls (sidebar) ──────────────────────────────────────
    with st.sidebar:
        st.divider()
        st.subheader("🌤️ Live Conditions")
        live_rain   = st.slider("Rain (mm/hr)", 0.0, 30.0, 0.0, step=0.5, key="live_rain")
        live_temp   = st.slider("Temp (°C)", -20, 40, 15, key="live_temp")
        live_lag    = st.slider("Last hr volume", 0, 7280, 3000, key="live_lag")
        live_snow   = st.slider("Snow (cm/hr)", 0.0, 0.5, 0.0, step=0.05, key="live_snow")
        live_wx     = st.selectbox("Weather", [
            "Clear","Clouds","Rain","Drizzle","Mist","Fog",
            "Snow","Thunderstorm","Haze","Squall","Smoke"
        ], key="live_wx")
        refresh_btn = st.button("🔄 Refresh Intelligence", type="primary", width="stretch", key="live_refresh")

    tab_live, tab_forecast, tab_corridor, tab_servers = st.tabs([
        "⚡ Live Now", "📅 24h Forecast", "🗺️ Corridor Status", "🖥️ MCP Servers",
    ])

    # Compute full live report once for all tabs
    with st.spinner("Fetching live MCP intelligence…"):
        try:
            report = bridge.live_intelligence_report(
                rain_1h=live_rain, temp_celsius=live_temp,
                lag_1h=float(live_lag), snow_1h=live_snow, weather_main=live_wx,
            )
            mcp_ok = True
        except Exception as ex:
            st.error(f"❌ MCP Bridge error: {ex}")
            mcp_ok = False
            st.stop()

    # ── TAB 1: Live Now ──────────────────────────────────────────────────────
    with tab_live:
        now_pred  = report["current"]
        pred_info = now_pred["prediction"]
        label     = pred_info["label"]
        conf      = pred_info["confidence"]
        col_map   = {"Low":"#22c55e","Medium":"#f59e0b","High":"#f97316","Severe":"#ef4444"}
        col       = col_map[label]

        # Timestamp header
        st.markdown(
            f"<div style='text-align:center;font-size:0.85rem;color:#94a3b8;"
            f"font-weight:600;letter-spacing:0.06em;text-transform:uppercase;"
            f"margin-bottom:16px'>"
            f"🕐 {report['local_time']} · {report['day_name']} · {report['date']}</div>",
            unsafe_allow_html=True,
        )

        # Current prediction banner
        st.markdown(congestion_banner(
            label, conf, pred_info.get("inference_ms", 0.0),
            now_pred["explanation"]["level_info"]["impact"]
        ), unsafe_allow_html=True)

        # Next-hour outlook
        nxt        = report["next_hour"]
        nxt_col    = col_map[nxt["label"]]
        nxt_arrow  = "↗️" if nxt["label"] > label else ("↘️" if nxt["label"] < label else "→")
        st.markdown(
            f"<div style='background:rgba(255,255,255,0.65);backdrop-filter:blur(12px);"
            f"border:1px solid rgba(255,255,255,0.8);border-radius:16px;padding:14px 20px;"
            f"margin:12px 0;display:flex;align-items:center;gap:16px;"
            f"box-shadow:0 4px 20px rgba(99,102,241,0.08)'>"
            f"<div style='font-size:1.5rem'>{nxt_arrow}</div>"
            f"<div><div style='font-size:0.75rem;font-weight:700;text-transform:uppercase;"
            f"color:#94a3b8;letter-spacing:0.08em'>Next Hour Outlook ({nxt['hour']:02d}:00)</div>"
            f"<div style='font-size:1rem;font-weight:800;color:{nxt_col}'>{nxt['label']}</div>"
            f"<div style='font-size:0.78rem;color:#64748b'>Confidence: {nxt['confidence']}%</div></div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Alert panel
        alerts = report["alerts"]
        if alerts["alert_active"]:
            st.markdown(
                f"<div style='background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.3);"
                f"border-radius:14px;padding:14px 18px;margin:12px 0'>"
                f"<div style='font-weight:700;color:#dc2626;font-size:0.95rem;margin-bottom:8px'>"
                f"🚨 Active Alert — {alerts['alert_count']} segment(s) High or above</div>",
                unsafe_allow_html=True,
            )
            for seg in alerts["high_or_severe_segments"]:
                seg_col = col_map.get(seg["segment_label"], "#6366f1")
                st.markdown(
                    f"<div style='padding:4px 10px;margin-bottom:4px;font-size:0.84rem;"
                    f"border-left:3px solid {seg_col};color:#374151'>"
                    f"<b>{seg['name']}</b> · {seg['exit']} "
                    f"<span style='background:{seg_col}22;color:{seg_col};font-weight:700;"
                    f"padding:2px 8px;border-radius:99px;font-size:0.75rem'>"
                    f"{seg['segment_label']}</span></div>",
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.success("✅ No active alerts — all segments at Medium or below")

        # Conditions used
        cond = now_pred["conditions"]
        st.markdown(metric_row([
            {"icon": "⏰", "value": f"{cond['hour']:02d}:00",  "label": "Current Hour",   "color": "#6366f1"},
            {"icon": "🌡️", "value": f"{live_temp}°C",          "label": "Temperature",    "color": "#06b6d4"},
            {"icon": "🌧️", "value": f"{live_rain}mm/hr",       "label": "Rainfall",       "color": "#3b82f6"},
            {"icon": "🚗", "value": f"{live_lag:,}",           "label": "Lag Volume",     "color": "#8b5cf6"},
        ]), unsafe_allow_html=True)

        # Explanation
        st.markdown(glass_section("Why This Prediction?", "🧠"), unsafe_allow_html=True)
        st.markdown(
            f"<p style='font-style:italic;color:#475569;font-size:0.9rem;line-height:1.6;"
            f"padding:10px 14px;background:rgba(255,255,255,0.6);border-radius:12px;"
            f"border:1px solid rgba(255,255,255,0.8)'>"
            f"{now_pred['explanation']['narrative']}</p>",
            unsafe_allow_html=True,
        )

    # ── TAB 2: 24h Forecast ──────────────────────────────────────────────────
    with tab_forecast:
        import pandas as pd
        risk_records = report["risk_forecast"]
        risk_df = pd.DataFrame(risk_records)

        severe_hrs = sum(1 for r in risk_records if r["label"] == "Severe")
        high_hrs   = sum(1 for r in risk_records if r["label"] == "High")
        peak_risk  = max(risk_records, key=lambda r: r["risk_score"])
        avg_risk   = round(sum(r["risk_score"] for r in risk_records) / len(risk_records), 1)

        st.markdown(metric_row([
            {"icon": "🔴", "value": f"{severe_hrs}/24",       "label": "Severe Hours",    "color": "#ef4444"},
            {"icon": "🟠", "value": f"{high_hrs}/24",         "label": "High Hours",      "color": "#f97316"},
            {"icon": "⏰", "value": peak_risk["hour"],        "label": "Peak Risk Hour",  "color": "#8b5cf6"},
            {"icon": "📊", "value": f"{avg_risk:.0f}/100",    "label": "Avg Risk Score",  "color": "#6366f1"},
        ]), unsafe_allow_html=True)

        st.plotly_chart(make_risk_chart(risk_df), use_container_width=True)
        st.plotly_chart(make_risk_timeline(risk_df), use_container_width=True)

        # Rush hour detail
        st.markdown(glass_section("Rush Hour Predictions (MCP batch)", "⚡"), unsafe_allow_html=True)
        from datetime import datetime as _dt
        rush_hours = [7, 8, 9, 16, 17, 18]
        rush_preds = bridge.predict_batch(
            hours=rush_hours,
            day_of_week=_dt.now().weekday(), month=_dt.now().month,
            temp_celsius=live_temp, rain_1h=live_rain,
            traffic_lag_1h=float(live_lag), weather_main=live_wx,
        )
        rush_cols = st.columns(len(rush_hours))
        for i, rp in enumerate(rush_preds):
            rc = col_map.get(rp["label"], "#6366f1")
            rush_cols[i].markdown(
                f"<div style='background:linear-gradient(135deg,{rc}22,{rc}11);"
                f"border:1px solid {rc}44;border-radius:14px;padding:10px 8px;"
                f"text-align:center;margin:0 2px'>"
                f"<div style='font-size:0.72rem;color:#94a3b8;font-weight:700'>"
                f"{rp['hour']:02d}:00</div>"
                f"<div style='font-size:0.85rem;font-weight:800;color:{rc}'>{rp['label']}</div>"
                f"<div style='font-size:0.68rem;color:#64748b'>{rp['confidence']}%</div></div>",
                unsafe_allow_html=True,
            )

    # ── TAB 3: Corridor Status ───────────────────────────────────────────────
    with tab_corridor:
        corridor     = report["corridor"]
        base_pred    = corridor["base_prediction"]
        segments_lst = corridor["segments"]
        summary      = corridor["summary"]

        # Summary KPIs
        b_col = col_map.get(base_pred["label"], "#6366f1")
        st.markdown(metric_row([
            {"icon": "🚦", "value": base_pred["label"],           "label": "Global Forecast",  "color": b_col},
            {"icon": "🔴", "value": str(summary["severe_count"]), "label": "Severe Segments",  "color": "#ef4444"},
            {"icon": "🟠", "value": str(summary["high_count"]),   "label": "High Segments",    "color": "#f97316"},
            {"icon": "📍", "value": summary["worst_segment"][:14]+"…" if len(summary["worst_segment"])>14 else summary["worst_segment"],
                           "label": "Worst Segment",              "color": "#8b5cf6"},
        ]), unsafe_allow_html=True)

        # Segment cards grid
        st.markdown(glass_section("All 16 I-94 Segments", "🗺️"), unsafe_allow_html=True)
        seg_cols_a = st.columns(2)
        for i, seg in enumerate(segments_lst):
            sc = col_map.get(seg["segment_label"], "#6366f1")
            factor_icon = "⚠️" if seg["is_bottleneck"] else "✅"
            seg_cols_a[i % 2].markdown(
                f"<div style='background:rgba(255,255,255,0.65);backdrop-filter:blur(10px);"
                f"border:1px solid {sc}33;border-radius:14px;padding:10px 14px;"
                f"margin-bottom:8px;border-left:4px solid {sc};"
                f"animation:fadeInLeft 0.3s ease {(i%8)*0.04}s both'>"
                f"<div style='display:flex;justify-content:space-between;align-items:center'>"
                f"<span style='font-weight:700;font-size:0.82rem;color:#1e293b'>"
                f"{factor_icon} {seg['name']}</span>"
                f"<span style='background:{sc};color:white;font-weight:800;font-size:0.7rem;"
                f"padding:2px 8px;border-radius:99px'>{seg['segment_label']}</span></div>"
                f"<div style='font-size:0.72rem;color:#64748b;margin-top:3px'>"
                f"{seg['exit']} · factor {seg['factor']:.2f}</div></div>",
                unsafe_allow_html=True,
            )

        st.caption(
            "🔴 Segments with factor > 1.0 are historical bottlenecks. "
            "Colors: 🟢 Low · 🟡 Medium · 🟠 High · 🔴 Severe"
        )

    # ── TAB 4: MCP Server Health ─────────────────────────────────────────────
    with tab_servers:
        st.markdown(glass_section("MCP Server Registry", "🖥️"), unsafe_allow_html=True)

        import json as _json
        _cfg_path = os.path.join(DIR, "mcp_config.json")
        _cfg      = _json.load(open(_cfg_path)) if os.path.exists(_cfg_path) else {}
        servers   = _cfg.get("mcpServers", {})

        server_icons = {
            "traffic-prediction": "🔮",
            "traffic-analytics":  "📊",
            "traffic-insights":   "💡",
            "traffic-map":        "🗺️",
        }

        for srv_name, srv_info in servers.items():
            icon = server_icons.get(srv_name, "⚙️")
            st.markdown(
                f"<div style='background:rgba(255,255,255,0.70);backdrop-filter:blur(16px);"
                f"border:1px solid rgba(255,255,255,0.80);border-radius:20px;"
                f"padding:20px 24px;margin-bottom:14px;"
                f"box-shadow:0 4px 24px rgba(99,102,241,0.08);'>"
                f"<div style='display:flex;justify-content:space-between;align-items:flex-start'>"
                f"<div>"
                f"<div style='font-size:1rem;font-weight:800;color:#1e293b'>{icon} {srv_name}</div>"
                f"<div style='font-size:0.82rem;color:#475569;margin-top:4px'>{srv_info.get('description','')}</div>"
                f"<div style='font-size:0.72rem;color:#94a3b8;margin-top:6px;font-family:monospace'>"
                f"python {' '.join(srv_info.get('args', []))}</div></div>"
                f"<div style='background:rgba(34,197,94,0.15);border:1px solid rgba(34,197,94,0.4);"
                f"border-radius:99px;padding:3px 12px;font-size:0.72rem;font-weight:700;color:#16a34a;"
                f"white-space:nowrap;margin-top:4px'>✅ Registered</div></div>",
                unsafe_allow_html=True,
            )
            # Tools and resources
            tools_html = "".join(
                f"<span style='background:rgba(99,102,241,0.10);color:#4f46e5;"
                f"padding:3px 10px;border-radius:99px;font-size:0.72rem;margin:2px;"
                f"display:inline-block;font-weight:600'>{t}</span>"
                for t in srv_info.get("tools", [])
            )
            resources_html = "".join(
                f"<span style='background:rgba(6,182,212,0.10);color:#0284c7;"
                f"padding:3px 10px;border-radius:99px;font-size:0.72rem;margin:2px;"
                f"display:inline-block;font-family:monospace'>{r}</span>"
                for r in srv_info.get("resources", [])
            )
            if tools_html or resources_html:
                st.markdown(
                    f"<div style='margin-top:10px;padding:10px 14px;"
                    f"background:rgba(248,250,252,0.8);border-radius:12px'>"
                    f"{'<div style=margin-bottom:6px><b style=font-size:0.75rem;color:#64748b>TOOLS</b><br>' + tools_html + '</div>' if tools_html else ''}"
                    f"{'<div><b style=font-size:0.75rem;color:#64748b>RESOURCES</b><br>' + resources_html + '</div>' if resources_html else ''}"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown("</div>", unsafe_allow_html=True)

        # Integration info
        st.divider()
        st.markdown(glass_section("Claude Desktop Integration", "🔗"), unsafe_allow_html=True)
        st.info(
            "**To use these MCP servers with Claude Desktop:**\n\n"
            "Add the `mcpServers` block from `mcp_config.json` to your Claude Desktop config:\n"
            "- **Windows:** `%APPDATA%\\Claude\\claude_desktop_config.json`\n"
            "- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`\n\n"
            "Then ask Claude: *'What is the congestion on I-94 at 5 PM on Friday?'*"
        )

        # Example queries
        st.markdown(glass_section("Example MCP Queries", "💬"), unsafe_allow_html=True)
        example_queries = [
            ("🔮 Prediction", "What will congestion be at 5 PM on Friday in August with light rain?"),
            ("📊 Analytics",  "Which hour of the day has the highest average traffic on I-94?"),
            ("💡 Insights",   "Why is traffic predicted as Severe at 5 PM on a Friday?"),
            ("🗺️ Map",        "What is the worst hour for the I-35W interchange segment?"),
        ]
        for server_type, query in example_queries:
            st.markdown(
                f"<div style='padding:8px 14px;margin-bottom:6px;"
                f"background:rgba(255,255,255,0.60);border-radius:12px;"
                f"border-left:3px solid #6366f1;font-size:0.85rem;"
                f"animation:fadeInLeft 0.3s ease both'>"
                f"<span style='font-weight:700;color:#6366f1'>{server_type}</span> "
                f"<span style='color:#374151'>{query}</span></div>",
                unsafe_allow_html=True,
            )
