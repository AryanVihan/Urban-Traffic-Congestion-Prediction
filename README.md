# Urban Traffic Intelligence System
## ForgeML — Metro I-94 Congestion Predictor

An AI-powered traffic congestion prediction and explanation system for the Metro I-94 Interstate corridor (Minneapolis–Saint Paul, MN). Built with a 4-agent orchestration pipeline, 27 engineered features, a 93.7% accurate multi-class classifier, an 11-page interactive Streamlit dashboard, and Model Context Protocol (MCP) servers for Claude Desktop integration.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Project Overview](#project-overview)
3. [System Architecture](#system-architecture)
4. [Dataset](#dataset)
5. [Data Processing & Feature Engineering](#data-processing--feature-engineering)
6. [Model Training & Evaluation](#model-training--evaluation)
7. [4-Agent AI Workflow](#4-agent-ai-workflow)
8. [Rule-Based Explanation Engine](#rule-based-explanation-engine)
9. [Analytics & Visualizations](#analytics--visualizations)
10. [Interactive Map (I-94 Corridor)](#interactive-map-i-94-corridor)
11. [Dashboard Pages](#dashboard-pages)
12. [MCP Servers (Claude Desktop Integration)](#mcp-servers-claude-desktop-integration)
13. [File Reference](#file-reference)
14. [Dependencies](#dependencies)
15. [Configuration](#configuration)
16. [Feature Importance](#feature-importance)
17. [Congestion Thresholds](#congestion-thresholds)
18. [Key Design Decisions](#key-design-decisions)

---

## Quick Start

```bash
# 1. Install dependencies
pip install pandas numpy scikit-learn joblib streamlit plotly folium streamlit-folium mcp fastmcp

# 2. Train the model (~60 seconds, one-time)
python model_training.py

# 3. Launch the dashboard
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`. Training can also be triggered from the sidebar's **Train/Retrain** button inside the dashboard.

---

## Project Overview

### What It Does

This system ingests 6 years of hourly traffic sensor data from the Metro I-94 interstate and delivers:

- **Congestion prediction** — classifies any hour into Low / Medium / High / Severe based on time, day, weather, and recent traffic history
- **Plain-English explanation** — a rule-based engine describes *why* a given prediction was made (contributing factors, impact levels)
- **Actionable recommendations** — per-level response plans ranging from "no action needed" to full incident protocol
- **24-hour risk forecasting** — a 0–100 risk score for every hour of any selected day
- **Historical pattern analysis** — hourly, daily, monthly, and weather-stratified visualizations across 48,204 records
- **Spatial intelligence** — per-segment congestion predictions across 16 I-94 corridor segments with individual bottleneck factors
- **AI integration** — 4 MCP servers expose 25+ tools to Claude Desktop and other AI clients

### What Makes It Stand Out

- **4-agent orchestration** (Data → Predict → Explain → Recommend) for modular, traceable predictions
- **Temporal memory** via lag/rolling features — previous hour's traffic alone accounts for 36% of model importance
- **Per-prediction explainability** powered by a transparent rule engine (not a black-box SHAP approximation)
- **Spatial awareness** via 16 I-94 segments with individual bottleneck multipliers
- **Fully offline** — no external API keys or internet connection required
- **MCP-native** — plug directly into Claude Desktop for natural-language traffic queries

---

## System Architecture

```
Metro_Interstate_Traffic_Volume.csv (48,204 rows)
            │
            ▼
   data_processing.py
   ┌──────────────────────────────┐
   │  1. Load raw CSV             │
   │  2. Clean (dedup, temp fix)  │
   │  3. Engineer 27 features     │
   │  4. Label 4 congestion tiers │
   └──────────────────────────────┘
            │
            ▼
   model_training.py
   ┌──────────────────────────────┐
   │  Train 3 models (85/15 split)│
   │  Permutation importance      │
   │  Save model.pkl + artifacts  │
   └──────────────────────────────┘
            │
            ▼
        model.pkl  ◄──────────────────────────────┐
            │                                      │
            ▼                                      │
        agents.py (AgentOrchestrator)              │
   ┌───────────────────────────┐                   │
   │  DataAgent                │                   │
   │  PredictionAgent ─────────┼───────────────────┘
   │  InsightAgent             │
   │  RecommendationAgent      │
   └───────────────────────────┘
            │
            ▼
        app.py (Streamlit — 11 pages)
   ┌──────────────────────────────────────────┐
   │  analytics.py   — 18 Plotly chart types  │
   │  map_view.py    — Folium I-94 corridor   │
   │  insights.py    — Rule-based explanations│
   │  styles.py      — Dark theme + CSS       │
   └──────────────────────────────────────────┘
            │
            ▼
   mcp_servers/ (4 MCP servers, 25+ tools)
   ┌──────────────────────────────┐
   │  prediction_server.py        │
   │  analytics_server.py         │
   │  insights_server.py          │
   │  map_server.py               │
   └──────────────────────────────┘
            │
            ▼
   Claude Desktop / External AI Clients
```

---

## Dataset

**Source:** Metro Interstate I-94 Traffic Volume (UCI Machine Learning Repository / Kaggle)  
**Location on disk:** `Metro_Interstate_Traffic_Volume.csv` (3.2 MB)  
**Time span:** October 2012 – September 2018 (6 years)  
**Records:** 48,204 hourly observations (48,187 after deduplication)  
**Coverage:** Single sensor station on I-94 between Minneapolis and Saint Paul

### Raw Columns

| Column | Type | Description |
|--------|------|-------------|
| `holiday` | string / NaN | US national holiday name, or NaN |
| `temp` | float | Air temperature in Kelvin |
| `rain_1h` | float | Rainfall accumulation in mm/hr |
| `snow_1h` | float | Snowfall accumulation in cm/hr |
| `clouds_all` | int | Cloud cover percentage (0–100) |
| `weather_main` | string | Weather category (Clear, Clouds, Rain, Snow, Fog, Haze, Drizzle, Thunderstorm) |
| `weather_description` | string | Detailed weather description |
| `date_time` | datetime | Hourly timestamp (UTC offset) |
| `traffic_volume` | int | **Target:** vehicles per hour (0–7,280) |

### Data Quality Issues Fixed

| Issue | Fix Applied |
|-------|------------|
| ~17 duplicate rows | Removed entirely |
| `temp = 0 K` (sensor failure) | Replaced with hourly median temperature |
| Extreme rain outliers (e.g. 9,831 mm/hr) | Capped at 50 mm/hr |
| Missing holiday names | Filled with `"None"` string |

---

## Data Processing & Feature Engineering

**File:** `data_processing.py`

The full pipeline runs as: `load_raw()` → `clean()` → `engineer_features()` → `create_congestion_labels()`

### 27 Engineered Features

| Category | Features | Count |
|----------|----------|-------|
| **Time** | `hour`, `day_of_week`, `month`, `year`, `day_of_year` | 5 |
| **Rush Hours** | `is_morning_rush` (7–9 AM), `is_evening_rush` (4–6 PM), `is_rush_hour`, `rush_type` | 4 |
| **Cyclical Encoding** | `hour_sin`, `hour_cos`, `month_sin`, `month_cos` | 4 |
| **Calendar** | `is_weekend`, `is_holiday` | 2 |
| **Weather** | `temp_celsius` (K→°C), `rain_1h`, `snow_1h`, `clouds_all`, `is_raining`, `is_snowing`, `weather_severity` (0–3), `weather_code` | 8 |
| **Lag/Rolling** | `traffic_lag_1h`, `traffic_lag_24h`, `traffic_rolling_3h`, `traffic_rolling_6h` | 4 |
| | **Total** | **27** |

**Why cyclical encoding?**  
Encoding `hour` as raw integer (0–23) creates a false discontinuity between 23 and 0. Sine/cosine encoding preserves the circular nature of time so the model understands 11 PM and 1 AM are close together.

**Why lag/rolling features?**  
Traffic is strongly autocorrelated — congestion tends to persist. The previous hour's volume (`traffic_lag_1h`) alone explains 36% of the model's predictive power, more than all weather features combined.

### Congestion Label Assignment

```python
def create_congestion_labels(df):
    bins   = [0, 1000, 2500, 4500, 10000]
    labels = ['Low', 'Medium', 'High', 'Severe']
```

| Level | Vehicles/hr | Label Code |
|-------|-------------|-----------|
| Low | 0 – 1,000 | 0 |
| Medium | 1,001 – 2,500 | 1 |
| High | 2,501 – 4,500 | 2 |
| Severe | 4,501 – 7,280 | 3 |

---

## Model Training & Evaluation

**File:** `model_training.py`

### Training Protocol

1. Run `full_pipeline()` from `data_processing.py` to produce feature matrix `X` (27 columns) and label vector `y`
2. Stratified 85/15 train/test split (stratification preserves class proportions)
3. Train all 3 models, time each training run
4. Evaluate on the held-out 15% test set (7,229 rows)
5. Compute permutation importance on 5,000 test samples (5 repeats per feature)
6. Save artifacts: `model.pkl`, `feature_importance.csv`, `model_results.json`, `model_comparison.json`

### Model Comparison

| Model | Accuracy | F1 (Weighted) | Train Time |
|-------|----------|---------------|-----------|
| **HistGradientBoosting** ✅ | **93.69%** | **0.9368** | 5.0s |
| RandomForest | 92.54% | 0.9259 | 4.4s |
| ExtraTrees | 91.06% | 0.9111 | 2.1s |

**Why F1 over accuracy?**  
The dataset is class-imbalanced (Medium is underrepresented). Weighted F1 penalizes models that sacrifice rare-class performance, making it a fairer selection criterion.

### Best Model Hyperparameters (HistGradientBoosting)

```python
HistGradientBoostingClassifier(
    max_iter=300,
    learning_rate=0.08,
    max_depth=8,
    min_samples_leaf=20,
    l2_regularization=0.1,
    early_stopping=True,
    validation_fraction=0.1,
    n_iter_no_change=20,
    random_state=42,
)
```

### Per-Class Performance (HistGradientBoosting)

| Class | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| Low | 97.6% | 98.4% | 98.0% |
| Medium | 89.2% | 87.8% | 88.5% |
| High | 90.7% | 90.4% | 90.5% |
| Severe | 95.3% | 95.6% | 95.4% |

### Confusion Matrix

```
           Predicted →
           Low   Med   High  Severe
Actual Low  [1622   27     0      0]
Actual Med  [  39  859    80      0]
Actual High [   1   76  1862    121]
Actual Sev  [   0    1   111   2430]
```

### Saved Artifacts

| File | Contents |
|------|---------|
| `model.pkl` | Joblib-serialized HistGradientBoosting classifier |
| `feature_importance.csv` | 27 features sorted by permutation importance score |
| `model_results.json` | Accuracy, F1, and training time for all 3 models |
| `model_comparison.json` | Confusion matrices + per-class precision/recall/F1 |

---

## 4-Agent AI Workflow

**File:** `agents.py`

Every prediction in the dashboard runs through a sequential 4-agent pipeline. Each agent is an independent class that can be tested and extended in isolation.

```
User Input (27 feature values)
        │
        ▼
[1] DataAgent
    • Profiles dataset: record count, date range, congestion distribution
    • Detects anomalies: zero-traffic readings, severe-during-rush ratio
        │
        ▼
[2] PredictionAgent
    • Builds feature vector from input dict
    • Calls model.predict() → congestion code (0–3)
    • Calls model.predict_proba() → confidence % per class
    • Records inference latency in milliseconds
        │
        ▼
[3] InsightAgent
    • Calls explain_prediction() from insights.py
    • Returns contributing factors with impact levels (HIGH / MODERATE / REDUCING)
    • Generates prediction narrative sentence
        │
        ▼
[4] RecommendationAgent
    • Gets base action list for congestion level
    • Adds contextual actions:
        - Rush hour + High/Severe  → mobile alert
        - Rain > 2mm/hr            → wet-weather signage
        - Hour < 6 AM              → maintenance window flag
        - Low confidence           → verify with field sensors
    • Assigns urgency: LOW / NORMAL / HIGH / CRITICAL
        │
        ▼
Result: prediction, confidence, factors, action_plan, agent_logs
```

### AgentLog

Every agent emits structured log entries (timestamp, agent name, level, message) that are displayed as an execution trace in the dashboard, giving full transparency into the prediction pipeline.

### AgentOrchestrator

The `AgentOrchestrator` class coordinates all four agents and exposes:

- `run_analysis()` — dataset profile + log
- `run_prediction_pipeline(input_features)` — full end-to-end prediction
- `run_system_insights(peak_data)` — 6 strategic insight cards

---

## Rule-Based Explanation Engine

**File:** `insights.py`

Predictions are explained by a deterministic rule engine that mirrors traffic-domain expert reasoning — not a statistical approximation. This makes every explanation auditable and consistent.

### Contributing Factors

The engine evaluates each condition and assigns an impact level:

| Condition | Impact |
|-----------|--------|
| Morning rush (7–9 AM) | HIGH |
| Evening rush (4–6 PM) | HIGH |
| Heavy rain > 5mm/hr | HIGH |
| Snow present | HIGH |
| Poor visibility (fog, thunderstorm) | HIGH |
| Prior hour traffic > 4,500 vehicles | HIGH |
| Light rain (0.5–5mm/hr) | MODERATE |
| Weekday (Mon–Fri) | MODERATE |
| Weekend | REDUCING (~25% less traffic) |
| Holiday | REDUCING (fewer commuters) |
| Late night / early morning (before 5 AM or after 11 PM) | REDUCING |
| Prior hour traffic < 1,000 vehicles | REDUCING |

### Recommendations by Congestion Level

| Level | Response |
|-------|----------|
| **Low** | No action needed. Use for infrastructure diagnostics. |
| **Medium** | Activate adaptive signal timing. Post traffic updates. |
| **High** | Alert traffic management center. Extend green phases. Consider contraflow lanes. |
| **Severe** | Full incident protocol. Deploy officers. Activate ramp metering. Issue public advisory. |

### System-Level Insights (6 Strategic Cards)

1. **Rush Hour Dominance** — Peak hour averages ~40% more traffic than off-peak
2. **Weekday vs Weekend** — 25%+ volume difference; identifies busiest day
3. **Holiday Relief** — Quantified reduction vs typical weekday average
4. **Weather Effects** — Highest and lowest volume conditions from historical data
5. **Seasonal Peak** — Worst historical month (typically August)
6. **Temporal Momentum** — Explains why `traffic_lag_1h` is the #1 feature at 36% importance

---

## Analytics & Visualizations

**File:** `analytics.py`

18 chart functions using Plotly (interactive) and Folium (maps).

### Traffic Pattern Charts

| Function | Chart Type | Description |
|----------|-----------|-------------|
| `make_hour_day_heatmap` | Heatmap | 24h × 7d average volume grid with rush hour bands |
| `make_congestion_heatmap` | Heatmap | Same grid but showing avg congestion code (0–3) |
| `make_calendar_heatmap` | Calendar heatmap | GitHub-style daily traffic calendar for a selected year |
| `make_weekday_weekend_overlay` | Line chart | Dual overlay: weekday vs weekend hourly traffic |
| `make_weekday_weekend_by_month` | Grouped bar | Monthly weekday vs weekend averages |
| `make_congestion_profile` | Stacked area | Hourly composition of Low/Medium/High/Severe % |

### Weather Analysis Charts

| Function | Chart Type | Description |
|----------|-----------|-------------|
| `make_weather_box` | Box plot | Traffic volume distribution by weather condition |
| `make_rain_scatter` | Scatter | Rainfall intensity vs traffic (3,000 samples, colored by level) |
| `make_temp_traffic` | Bar | Average traffic by temperature bin (5°C ranges) |
| `make_weather_severity_bar` | Bar | Avg traffic by severity (Clear → Heavy Rain → Snow) |

### Risk Scoring Charts

| Function | Description |
|----------|-------------|
| `compute_24h_risk` | For each hour 0–23: predict congestion, score as `(code/3) × 100` |
| `make_risk_chart` | Vertical bar chart of 24-hour risk scores, colored by level |
| `make_risk_timeline` | Filled area chart showing risk trend through the day |

### Model Comparison Charts

| Function | Description |
|----------|-------------|
| `make_model_metrics_comparison` | Side-by-side accuracy vs F1 for all 3 models |
| `make_model_training_time_comparison` | Training time per model |
| `make_confusion_matrix_heatmap` | 4×4 annotated heatmap per model |
| `make_per_class_metrics_comparison` | 4 subplots: F1 per class across models |
| `make_model_radar_comparison` | Multi-metric radar chart across models |

---

## Interactive Map (I-94 Corridor)

**File:** `map_view.py`

A Folium-based interactive map of the full I-94 corridor from I-494 West to I-694 East.

### 16 Corridor Segments

Each segment has:
- **Name** and **exit reference** (e.g. "Exit 15 – I-35W North/South")
- **Polyline coordinates** (GPS lat/lon pairs) drawn as thick colored lines
- **Bottleneck factor** (0.70 – 1.50) — a spatial multiplier applied to the model's base prediction

**Bottleneck factors reflect real-world engineering knowledge:**
- Factor 1.50 → Downtown Minneapolis / I-35W interchange (worst bottleneck)
- Factor 0.70 → Outlying rural sections (less congested than average)

### How Per-Segment Prediction Works

1. Compute a single global prediction from the user-selected hour, day, and weather
2. For each of the 16 segments, apply `_code_for_factor(base_code, factor)` to adjust the prediction
3. Color each segment polyline by its resulting congestion level:
   - Green (Low), Yellow (Medium), Orange (High), Red (Severe)
4. Animate severe segments with a pulsing overlay
5. Add 7 interchange markers and a legend with timestamp and day name

---

## Dashboard Pages

**File:** `app.py` — 11-page Streamlit dashboard

| Page | Icon | Contents |
|------|------|---------|
| **Overview** | 📊 | 5 KPI cards, congestion distribution bar, dataset summary |
| **Traffic Patterns** | 📈 | Hourly/daily bars, weather box plot, seasonal monthly chart |
| **Predict** | 🔮 | Interactive form → 4-agent pipeline → result + explanation |
| **AI Insights** | 💡 | 6 strategic intelligence cards with data-backed summaries |
| **Model Report** | 🏆 | Comparison table, top-15 feature importance, engineering summary |
| **Model Comparison** | 📊 | Side-by-side metrics, confusion matrices, per-class F1, radar chart |
| **Traffic Map** | 🗺️ | Interactive Folium map of 16 I-94 segments |
| **Heatmaps** | 🔥 | Hour×Day heatmap, congestion heatmap, GitHub-style calendar |
| **Weather Analysis** | 🌦️ | Box plot, rain scatter, temperature bins, severity bar |
| **Risk Scoring** | 🎯 | 24-hour risk bar + timeline for any day/month combination |
| **MCP Live Intelligence** | 🤖 | Real-time predictions via MCP servers, 24h forecast, corridor status |

### Sidebar

- Project logo and navigation radio buttons
- Model status indicator (trained / not trained)
- **Train/Retrain** button — runs the full training pipeline (~60s) and reloads artifacts

---

## MCP Servers (Claude Desktop Integration)

**Directory:** `mcp_servers/`  
**Config:** `mcp_config.json`

Four Model Context Protocol servers expose the system's intelligence to Claude Desktop and other MCP-compatible AI clients.

### Server Overview

| Server | File | Tools |
|--------|------|-------|
| Prediction | `prediction_server.py` | 5 |
| Analytics | `analytics_server.py` | 8 |
| Insights | `insights_server.py` | 5 |
| Map | `map_server.py` | 4 |

### Prediction Server (5 tools)

| Tool | Description |
|------|-------------|
| `predict_congestion` | Full prediction with explanation for given conditions |
| `predict_batch_hours` | Predict multiple hours in a single call |
| `compute_risk_forecast` | 24-hour risk score array (0–100 per hour) |
| `get_feature_vector` | Inspect the 27-feature vector for any input combination |
| `predict_now` | Real-time prediction using the system clock |

### Analytics Server (8 tools)

| Tool | Description |
|------|-------------|
| `get_hourly_traffic_profile` | Average volume per hour across all 6 years |
| `get_congestion_distribution` | Count and percentage for each congestion level |
| `get_weather_impact_summary` | Average traffic volume broken down by weather type |
| `get_rush_hour_stats` | Rush hour premium (%), timing, and weekday breakdown |
| `compare_weekday_vs_weekend` | Detailed weekday vs weekend hourly comparison |
| `get_segment_risk_for_hour` | Per-segment risk score for a specified hour |
| `get_bottleneck_segments` | List all segments with bottleneck factor > 1.0 |
| `get_dataset_overview` | High-level dataset statistics and metadata |

### Insights Server (5 tools)

| Tool | Description |
|------|-------------|
| `explain_prediction_for_conditions` | Why was a given congestion level predicted? |
| `get_action_plan` | Recommended response actions for a congestion level |
| `get_system_insights` | All 6 strategic insight cards |
| `get_level_description` | Emoji, summary text, and operational impact for a level |
| `generate_congestion_narrative` | Natural-language congestion report for conditions |

### Map Server (4 tools)

| Tool | Description |
|------|-------------|
| `get_corridor_congestion_map` | Per-segment congestion predictions for all 16 segments |
| `get_bottleneck_segments` | Segments with above-average congestion factors |
| `get_segment_history` | Historical average stats for a named segment |
| `list_segments` | All 16 segment names, exit references, and factors |

### Connecting to Claude Desktop

Add the following to your Claude Desktop config file:

**macOS:** `~/.config/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "traffic-prediction": {
      "command": "python",
      "args": ["-m", "mcp_servers.prediction_server"],
      "cwd": "/path/to/Urban-Traffic-Congestion-Prediction"
    },
    "traffic-analytics": {
      "command": "python",
      "args": ["-m", "mcp_servers.analytics_server"],
      "cwd": "/path/to/Urban-Traffic-Congestion-Prediction"
    },
    "traffic-insights": {
      "command": "python",
      "args": ["-m", "mcp_servers.insights_server"],
      "cwd": "/path/to/Urban-Traffic-Congestion-Prediction"
    },
    "traffic-map": {
      "command": "python",
      "args": ["-m", "mcp_servers.map_server"],
      "cwd": "/path/to/Urban-Traffic-Congestion-Prediction"
    }
  }
}
```

**Example Claude Desktop queries after connecting:**
- *"Predict congestion at 5 PM this Friday with light rain"*
- *"What's the 24-hour risk forecast for a Monday in August?"*
- *"Which I-94 segments have the worst bottleneck factors?"*
- *"Explain why the model predicts Severe congestion at 8 AM on a weekday"*
- *"Compare weekday vs weekend traffic patterns on I-94"*

---

## File Reference

| File | Size | Purpose |
|------|------|---------|
| `app.py` | ~70 KB | 11-page Streamlit dashboard |
| `model_training.py` | 6 KB | Train 3 models, save artifacts |
| `data_processing.py` | 6 KB | Clean data, engineer 27 features, label classes |
| `agents.py` | 7 KB | 4-agent orchestration workflow |
| `insights.py` | 10 KB | Rule-based explanation and recommendation engine |
| `analytics.py` | 26 KB | 18 Plotly chart and risk-scoring functions |
| `map_view.py` | 12 KB | Interactive Folium I-94 corridor map |
| `styles.py` | 32 KB | Custom dark-theme CSS and UI components |
| `mcp_servers/core.py` | — | Shared singletons (model, data, metadata) |
| `mcp_servers/prediction_server.py` | — | MCP prediction tools |
| `mcp_servers/analytics_server.py` | — | MCP analytics tools |
| `mcp_servers/insights_server.py` | — | MCP insight tools |
| `mcp_servers/map_server.py` | — | MCP corridor/segment tools |
| `mcp_servers/bridge.py` | — | Streamlit ↔ MCP integration layer |
| `Metro_Interstate_Traffic_Volume.csv` | 3.2 MB | Raw dataset (48,204 rows) |
| `model.pkl` | — | Serialized HistGradientBoosting classifier |
| `feature_importance.csv` | — | 27 features ranked by permutation importance |
| `model_results.json` | — | Accuracy/F1/time for all 3 models |
| `model_comparison.json` | — | Full confusion matrices + per-class metrics |
| `mcp_config.json` | 5 KB | MCP server registry and Claude Desktop instructions |
| `.streamlit/config.toml` | — | Dark theme, server settings |

---

## Dependencies

```
pandas>=1.3.0
numpy>=1.20.0
scikit-learn>=1.0.0
joblib>=1.0.0
streamlit>=1.20.0
plotly>=5.0.0
folium>=0.12.0
streamlit-folium>=0.12.0
matplotlib>=3.4.0
seaborn>=0.11.0
mcp>=0.1.0
fastmcp>=0.1.0
```

**Python version:** 3.9+  
**No GPU required.** Training completes in ~5 seconds on CPU.  
**No API keys required.** The system is fully self-contained and offline-capable.

---

## Configuration

### Streamlit Theme (`.streamlit/config.toml`)

```toml
[theme]
base                     = "dark"
primaryColor             = "#7c3aed"
backgroundColor          = "#080c18"
secondaryBackgroundColor = "#0f1426"
textColor                = "#e2e8f0"
font                     = "sans serif"

[browser]
gatherUsageStats = false

[server]
headless = true
```

### Congestion Thresholds

Thresholds are defined in `data_processing.py` and referenced consistently throughout:

```python
bins   = [0, 1000, 2500, 4500, 10000]
labels = ['Low', 'Medium', 'High', 'Severe']
```

To change thresholds, update this single location — all charts, maps, and explanations reference the same label system.

---

## Feature Importance

Computed via permutation importance on the test set (5 repeats per feature, F1-weighted scoring).

| Rank | Feature | Importance | Share |
|------|---------|-----------|-------|
| 1 | `traffic_lag_1h` | 0.3264 | 36.4% |
| 2 | `hour_cos` | 0.1968 | 21.9% |
| 3 | `hour` | 0.1370 | 15.3% |
| 4 | `day_of_week` | 0.0589 | 6.6% |
| 5 | `hour_sin` | 0.0221 | 2.5% |
| 6 | `traffic_rolling_3h` | 0.0151 | 1.7% |
| 7 | `traffic_rolling_6h` | 0.0128 | 1.4% |
| 8 | `year` | 0.0051 | 0.6% |
| 9 | `traffic_lag_24h` | 0.0046 | 0.5% |
| 10 | `temp_celsius` | 0.0036 | 0.4% |

**Key insight:** Previous hour traffic (36.4%) + time-of-day features combined (hour, hour_sin, hour_cos ≈ 40%) account for ~76% of all predictive power. Weather features (rain, snow, temperature, cloud cover) have near-zero importance — congestion on I-94 follows time patterns far more reliably than weather conditions.

---

## Congestion Thresholds

| Level | Vehicles/hr | Color | Response Protocol |
|-------|-------------|-------|-------------------|
| Low | 0 – 1,000 | Green | No action |
| Medium | 1,001 – 2,500 | Yellow | Adaptive signals, traffic updates |
| High | 2,501 – 4,500 | Orange | Center alert, extend green phases, contraflow |
| Severe | 4,501 – 7,280 | Red | Full incident protocol, ramp metering, public advisory |

---

## Key Design Decisions

**Why HistGradientBoosting over XGBoost or LightGBM?**  
It is part of scikit-learn's standard library (no extra install), supports native missing-value handling, includes built-in early stopping, and achieved the highest F1 among the three trained models.

**Why rule-based explanations instead of SHAP?**  
SHAP values are statistically derived and can produce explanations that are difficult to act on operationally. The rule engine in `insights.py` mirrors the reasoning a traffic engineer would apply, making every explanation auditable, consistent, and operationally meaningful.

**Why permutation importance instead of tree-based impurity importance?**  
Impurity (Gini) importance is biased toward high-cardinality features and can be misleading. Permutation importance directly measures the drop in F1 when a feature's values are shuffled, giving a model-agnostic, test-set-based measure of true predictive value.

**Why 4 agents instead of a monolithic prediction function?**  
Modularity enables independent testing, logging, and extension of each stage. It also provides a visible execution trace in the dashboard, so users can see exactly what each agent contributed to the final output.

**Why a 85/15 stratified split instead of a time-based split?**  
The dataset spans 6 years with stable seasonal and daily patterns. A stratified random split preserves congestion class proportions in both train and test sets. A pure time-based split (e.g., last 6 months as test) would underrepresent summer peak patterns in the test set, making evaluation less representative of real-world deployment.

---

## Performance Summary

| Metric | Value |
|--------|-------|
| Dataset size | 48,204 hourly records |
| Feature count | 27 engineered features |
| Models trained | 3 (HistGradientBoosting selected) |
| Best model F1 (weighted) | 0.9368 (93.7%) |
| Best model accuracy | 93.69% |
| Inference latency | 1–3 ms per prediction |
| Training time | ~5 seconds (CPU) |
| Dashboard pages | 11 |
| Chart types | 18+ |
| I-94 segments mapped | 16 |
| MCP tools exposed | 25+ |
| Offline capable | Yes |
| API keys required | None |
