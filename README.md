# Urban Traffic Intelligence System
### ForgeML — Metro I-94 Congestion Predictor (Minneapolis – Saint Paul)

A production-grade ML pipeline and interactive intelligence platform for predicting, explaining, and visualising highway congestion. Built on 48,204 hourly sensor records (2012–2018), it trains three scikit-learn ensemble classifiers, selects the best by weighted F1, engineers 27 features including lag/rolling temporal memory, runs a 4-agent orchestration workflow for every prediction, and exposes the entire system through both an 11-page Streamlit dashboard and four Model Context Protocol (MCP) servers for Claude Desktop integration.

---

## Table of Contents

1. [Repository Layout](#repository-layout)
2. [System Architecture](#system-architecture)
3. [Dataset — Raw Schema and Data Quality](#dataset--raw-schema-and-data-quality)
4. [Data Pipeline — `data_processing.py`](#data-pipeline--data_processingpy)
5. [Feature Engineering — All 27 Features](#feature-engineering--all-27-features)
6. [Model Training — `model_training.py`](#model-training--model_trainingpy)
7. [Saved Artifacts](#saved-artifacts)
8. [Model Performance](#model-performance)
9. [Feature Importance (Permutation-Based)](#feature-importance-permutation-based)
10. [4-Agent Orchestration — `agents.py`](#4-agent-orchestration--agentspy)
11. [Rule-Based Insight Engine — `insights.py`](#rule-based-insight-engine--insightspy)
12. [Analytics and Visualisations — `analytics.py`](#analytics-and-visualisations--analyticspy)
13. [Interactive Corridor Map — `map_view.py`](#interactive-corridor-map--map_viewpy)
14. [Streamlit Dashboard — `app.py`](#streamlit-dashboard--apppy)
15. [MCP Servers — `mcp_servers/`](#mcp-servers--mcp_servers)
16. [MCP Bridge — `mcp_servers/bridge.py`](#mcp-bridge--mcp_serversbridgepy)
17. [UI Styling — `styles.py`](#ui-styling--stylespy)
18. [Configuration Files](#configuration-files)
19. [Dependencies](#dependencies)
20. [Quick Start](#quick-start)

---

## Repository Layout

```
Urban-Traffic-Congestion-Prediction/
│
├── app.py                               # Streamlit dashboard — 11 pages
├── model_training.py                    # Train 3 models, compute importance, save artifacts
├── data_processing.py                   # Raw CSV → 27-feature DataFrame + congestion labels
├── agents.py                            # 4-agent AI orchestrator
├── insights.py                          # Rule-based explanation + recommendation engine
├── analytics.py                         # 18 Plotly chart + risk-scoring functions
├── map_view.py                          # Folium I-94 corridor map (16 segments)
├── styles.py                            # Dark-theme CSS injection + UI components
│
├── mcp_servers/
│   ├── __init__.py
│   ├── core.py                          # Shared singletons (lru_cache model, df, peak)
│   ├── prediction_server.py             # FastMCP — 5 tools, 3 resources
│   ├── analytics_server.py              # FastMCP — 8 tools, 3 resources
│   ├── insights_server.py               # FastMCP — 5 tools, 3 resources
│   ├── map_server.py                    # FastMCP — 4 tools, 2 resources
│   └── bridge.py                        # Synchronous Python bridge for Streamlit
│
├── Metro_Interstate_Traffic_Volume.csv  # Source data — 48,204 rows × 9 columns
├── model.pkl                            # Serialised HistGradientBoosting classifier
├── feature_importance.csv               # 27 features ranked by permutation importance
├── model_results.json                   # Accuracy / F1 / time for all 3 models
├── model_comparison.json                # Confusion matrices + per-class reports
├── mcp_config.json                      # MCP server registry (Claude Desktop)
└── .streamlit/config.toml               # Dark theme + headless server settings
```

---

## System Architecture

```
Metro_Interstate_Traffic_Volume.csv  (48,204 rows, 9 raw columns)
                │
                ▼
        data_processing.py
   ┌─────────────────────────────────────┐
   │  load_raw()     parse date_time     │
   │  clean()        dedup, temp fix,    │
   │                 rain cap, holiday   │
   │  engineer_features()  27 features   │
   │  create_congestion_labels()  0–3    │
   │  build_X_y()    X(48187×27), y      │
   └─────────────────────────────────────┘
                │
                ▼
        model_training.py
   ┌─────────────────────────────────────┐
   │  train_test_split(stratify=y, 85/15)│
   │  HistGradientBoosting ──────────────┤ best by F1
   │  RandomForest                       │
   │  ExtraTrees                         │
   │  permutation_importance(n_repeats=5)│
   │  save_artifacts()  → 4 files        │
   └─────────────────────────────────────┘
                │
        ┌───────┴──────────────────────┐
        ▼                              ▼
    model.pkl                  feature_importance.csv
    model_results.json         model_comparison.json
        │
        ▼
   agents.py  ←─────────────────────── insights.py
   ┌────────────────────────────────┐
   │ AgentOrchestrator              │
   │  ├─ DataAgent                  │
   │  ├─ PredictionAgent (model)    │
   │  ├─ InsightAgent (fi_df)       │
   │  └─ RecommendationAgent        │
   └────────────────────────────────┘
        │
        ▼
   app.py  (Streamlit — 11 pages)
   ┌────────────────────────────────────────────────────┐
   │  analytics.py  18 chart functions (Plotly)         │
   │  map_view.py   Folium map, 16 I-94 segments        │
   │  styles.py     CSS injection, glassmorphism        │
   │  mcp_servers/bridge.py  synchronous core access    │
   └────────────────────────────────────────────────────┘
        │
        ▼
   mcp_servers/  (4 FastMCP processes — stdio transport)
   ┌────────────────────────────────────────────────────┐
   │  core.py  lru_cache singletons (model, df, peak)   │
   │  prediction_server.py   5 tools  3 resources       │
   │  analytics_server.py    8 tools  3 resources       │
   │  insights_server.py     5 tools  3 resources       │
   │  map_server.py          4 tools  2 resources       │
   └────────────────────────────────────────────────────┘
        │
        ▼
   Claude Desktop / Claude API / MCP-compatible AI clients
```

---

## Dataset — Raw Schema and Data Quality

**File:** `Metro_Interstate_Traffic_Volume.csv`  
**Source:** UCI Machine Learning Repository — Metro Interstate Traffic Volume  
**Sensor:** Single inductive-loop detector, I-94 between Minneapolis and Saint Paul  
**Span:** October 2012 – September 2018 (6 years, hourly cadence)  
**Raw rows:** 48,204 | **After cleaning:** 48,187

### Raw Columns

| Column | Dtype | Description |
|--------|-------|-------------|
| `holiday` | str / NaN | US national holiday name, or NaN if not a holiday |
| `temp` | float | Air temperature in **Kelvin** (e.g. 288.28 K = 15.13 °C) |
| `rain_1h` | float | Hourly precipitation in **mm** |
| `snow_1h` | float | Hourly snowfall in **cm** |
| `clouds_all` | int | Cloud cover percentage (0–100) |
| `weather_main` | str | Primary OpenWeatherMap category (Clear, Clouds, Rain, Snow, Fog, Haze, Drizzle, Thunderstorm, Squall, Smoke, Mist) |
| `weather_description` | str | Detailed OWM description (not used directly as a feature) |
| `date_time` | str→datetime | Hourly timestamp — parsed with `pd.to_datetime()` |
| `traffic_volume` | int | **Prediction target** — vehicles passing sensor per hour (0–7,280) |

### Data Cleaning (`clean()`)

```python
# 1. Remove exact duplicate rows
df = df.drop_duplicates()                          # removes ~17 rows

# 2. Fix sensor-failure readings where temp == 0 K (physically impossible)
bad  = df["temp"] == 0
medians = df.groupby(df["date_time"].dt.hour)["temp"].median()
df.loc[bad, "temp"] = df.loc[bad, "date_time"].dt.hour.map(medians)

# 3. Cap extreme rainfall outlier (max recorded: 9,831 mm/hr — data error)
df["rain_1h"] = df["rain_1h"].clip(upper=50.0)

# 4. Fill missing holiday names
df["holiday"] = df["holiday"].fillna("None")
```

---

## Data Pipeline — `data_processing.py`

All public constants and the full pipeline are defined here. Every downstream module (`agents.py`, `map_view.py`, `analytics.py`, `mcp_servers/core.py`) imports from this single file.

### Module-level constants

```python
CONGESTION_BINS   = [0, 1000, 2500, 4500, 7300]
CONGESTION_LABELS = ["Low", "Medium", "High", "Severe"]
CONGESTION_MAP    = {"Low": 0, "Medium": 1, "High": 2, "Severe": 3}
MORNING_RUSH = (7, 9)    # inclusive hours
EVENING_RUSH = (16, 18)  # inclusive hours
```

### `FEATURE_COLS` — authoritative ordered list

```python
FEATURE_COLS = [
    "hour", "day_of_week", "month", "year", "day_of_year",
    "is_weekend", "is_rush_hour", "rush_type",
    "is_morning_rush", "is_evening_rush",
    "hour_sin", "hour_cos", "month_sin", "month_cos",
    "is_holiday",
    "temp_celsius", "rain_1h", "snow_1h", "clouds_all",
    "is_raining", "is_snowing", "weather_severity", "weather_code",
    "traffic_lag_1h", "traffic_lag_24h",
    "traffic_rolling_3h", "traffic_rolling_6h",
]
```

This list defines the **exact column order** passed to every `model.predict()` call across the app, MCP servers, and bridge. Any divergence causes silent wrong predictions.

### `full_pipeline(filepath)` — entry point

```python
def full_pipeline(filepath):
    df = load_raw(filepath)
    df = clean(df)
    df = engineer_features(df)
    df = create_congestion_labels(df)
    df = df.dropna(subset=["congestion_code"]).reset_index(drop=True)
    X, y = build_X_y(df)
    return df, X, y          # df shape: ~(48187, 36+), X: (48187, 27), y: (48187,)
```

### `get_peak_hours_analysis(df)` — analytics aggregates

Computes and returns a single dict used by the dashboard Overview page, AI Insights cards, and MCP analytics server:

```python
{
  "hourly_avg":    {0: 892.3, 1: 541.1, ..., 23: 1203.4},   # avg vol per hour
  "daily_avg":     {"Mon": 3812.2, "Tue": 3890.1, ...},
  "monthly_avg":   {1: 2841.0, 2: 2790.3, ..., 12: 2910.1},
  "peak_hour":     17,       # hour with max avg volume
  "trough_hour":   3,        # hour with min avg volume
  "peak_day":      "Thu",
  "worst_month":   8,        # August historically worst
  "weekend_avg":   2745.3,
  "weekday_avg":   3812.7,
  "holiday_avg":   2103.5,
  "rush_avg":      5114.2,
  "weather_impact": {"Clear": 3920.1, "Rain": 3750.2, ...}
}
```

---

## Feature Engineering — All 27 Features

**Function:** `engineer_features(df)` — sorts by `date_time` before computing lag features to prevent future-data leakage.

### Group 1 — Raw Time Decomposition (5 features)

| Feature | Computation | dtype |
|---------|-------------|-------|
| `hour` | `dt.dt.hour` | int (0–23) |
| `day_of_week` | `dt.dt.dayofweek` (0=Mon, 6=Sun) | int |
| `month` | `dt.dt.month` (1–12) | int |
| `year` | `dt.dt.year` | int |
| `day_of_year` | `dt.dt.dayofyear` (1–366) | int |

### Group 2 — Rush-Hour Flags (4 features)

```python
df["is_morning_rush"] = df["hour"].between(7, 9).astype(int)    # [7, 9] inclusive
df["is_evening_rush"] = df["hour"].between(16, 18).astype(int)  # [16, 18] inclusive
df["is_rush_hour"]    = (df["is_morning_rush"] | df["is_evening_rush"]).astype(int)
df["rush_type"]       = 0   # then:
df.loc[df["is_morning_rush"] == 1, "rush_type"] = 1
df.loc[df["is_evening_rush"] == 1, "rush_type"] = 2
# 0 = not rush, 1 = morning, 2 = evening
```

### Group 3 — Cyclical Encoding (4 features)

Raw integers (e.g. `hour=0` and `hour=23`) are discontinuous at midnight. Sine/cosine encoding projects onto a unit circle, making distance between 23:00 and 00:00 equal to the distance between 12:00 and 13:00:

```python
df["hour_sin"]  = np.sin(2 * np.pi * df["hour"]  / 24)
df["hour_cos"]  = np.cos(2 * np.pi * df["hour"]  / 24)
df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
```

`hour_cos` is the second most important feature (21.9% permutation importance) — surpassing the raw `hour` integer (15.3%) because the model exploits the circular structure.

### Group 4 — Calendar Flags (2 features)

```python
df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)    # Sat=5, Sun=6
df["is_holiday"] = (df["holiday"] != "None").astype(int)   # US national holidays
```

### Group 5 — Weather Features (8 features)

```python
df["temp_celsius"] = df["temp"] - 273.15                    # Kelvin → Celsius
df["is_raining"]   = (df["rain_1h"] > 0).astype(int)
df["is_snowing"]   = (df["snow_1h"] > 0).astype(int)

# 4-level rain severity ordinal: 0=dry, 1=light(<2.5mm), 2=moderate(<7.6mm), 3=heavy
rain_sev = pd.cut(df["rain_1h"], bins=[-0.1, 0, 2.5, 7.6, 55], labels=[0,1,2,3]).astype(float)
df["weather_severity"] = rain_sev + (df["snow_1h"] > 0).astype(float)

# Ordinal code for weather_main string
weather_order = {
    "Clear":0, "Clouds":1, "Haze":1, "Smoke":2, "Drizzle":2,
    "Rain":3, "Mist":3, "Fog":4, "Thunderstorm":4, "Snow":4, "Squall":5
}
df["weather_code"] = df["weather_main"].map(weather_order).fillna(2)
# rain_1h, snow_1h, clouds_all also kept as raw numeric features
```

### Group 6 — Temporal Lag / Rolling Features (4 features)

These encode short-term traffic memory. The `.shift(1)` prevents data leakage — at prediction time for hour `h`, only hours `< h` are known:

```python
# Previous hour's volume
df["traffic_lag_1h"]  = df["traffic_volume"].shift(1).fillna(df["traffic_volume"].median())

# Same hour yesterday (captures daily recurrence patterns)
df["traffic_lag_24h"] = df["traffic_volume"].shift(24).fillna(df["traffic_volume"].median())

# Rolling mean of the 3 hours prior to the current hour
df["traffic_rolling_3h"] = (
    df["traffic_volume"].shift(1).rolling(3, min_periods=1).mean()
    .fillna(df["traffic_volume"].median())
)

# Rolling mean of the 6 hours prior
df["traffic_rolling_6h"] = (
    df["traffic_volume"].shift(1).rolling(6, min_periods=1).mean()
    .fillna(df["traffic_volume"].median())
)
```

`traffic_lag_1h` is the single most predictive feature at **36.4% permutation importance** — higher than all time-of-day features combined on any single feature, and higher than all 8 weather features summed.

### Congestion Label Creation

```python
CONGESTION_BINS   = [0, 1000, 2500, 4500, 7300]
CONGESTION_LABELS = ["Low", "Medium", "High", "Severe"]

df["congestion_label"] = pd.cut(
    df["traffic_volume"], bins=CONGESTION_BINS,
    labels=CONGESTION_LABELS, include_lowest=True
)
df["congestion_code"] = df["congestion_label"].map(CONGESTION_MAP)
```

| Class | Range (vehicles/hr) | Code | Operational Meaning |
|-------|---------------------|------|---------------------|
| Low | 0 – 1,000 | 0 | Free flow; travel near speed limit |
| Medium | 1,001 – 2,500 | 1 | Some slowdowns; 10–20% longer travel |
| High | 2,501 – 4,500 | 2 | Noticeable congestion; 30–50% longer |
| Severe | 4,501 – 7,280 | 3 | Gridlock possible; travel may double |

---

## Model Training — `model_training.py`

### Three Models Defined

```python
MODELS = {
    "HistGradientBoosting": HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.08,
        max_depth=8,
        min_samples_leaf=20,
        l2_regularization=0.1,
        random_state=42,
        early_stopping=True,         # uses 10% of train as internal val set
        validation_fraction=0.1,
        n_iter_no_change=20,         # stop if no improvement for 20 rounds
    ),
    "RandomForest": RandomForestClassifier(
        n_estimators=300,
        max_depth=15,
        min_samples_leaf=10,
        n_jobs=-1,
        random_state=42,
        class_weight="balanced",     # upweight underrepresented Medium class
    ),
    "ExtraTrees": ExtraTreesClassifier(
        n_estimators=300,
        max_depth=15,
        min_samples_leaf=10,
        n_jobs=-1,
        random_state=42,
        class_weight="balanced",
    ),
}
```

### Train / Test Split

```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.15,          # 7,228 test rows
    random_state=42,
    stratify=y               # preserves class proportions in both splits
)
# Train: 41,059 rows | Test: 7,128 rows
```

`stratify=y` is critical because the dataset is imbalanced (Medium class is smallest). Without stratification, test proportions would differ from training, making F1 scores unreliable.

### Evaluation

For each model:

```python
y_pred = model.predict(X_test)
acc    = accuracy_score(y_test, y_pred)
f1     = f1_score(y_test, y_pred, average="weighted")
report = classification_report(y_test, y_pred,
                                target_names=CONGESTION_LABELS, output_dict=True)
cm     = confusion_matrix(y_test, y_pred)
```

**Why weighted F1, not accuracy?**  
The class distribution is skewed — Severe (2,542) and High (2,060) dominate while Medium (978) is underrepresented. Accuracy rewards a model that ignores Medium. Weighted F1 accounts for each class proportionally and penalises poor Medium-class performance.

### Model Selection

```python
best_name = max(results, key=lambda k: results[k]["f1_weighted"])
```

### Permutation Importance

```python
def compute_feature_importance(model, X_test, y_test, feature_names, n_sample=5000):
    # Subsample test set for speed (5,000 rows)
    rng = np.random.default_rng(42)
    idx = rng.choice(len(X_test), size=n_sample, replace=False)
    X_s, y_s = X_test.iloc[idx], y_test[idx]

    result = permutation_importance(
        model, X_s, y_s,
        n_repeats=5,            # shuffle each feature 5 times, average the drop
        random_state=42,
        n_jobs=-1,
        scoring="f1_weighted"
    )
    fi_df = pd.DataFrame({
        "feature":    feature_names,
        "importance": result.importances_mean,   # mean F1 drop across 5 repeats
        "std":        result.importances_std,
    }).sort_values("importance", ascending=False)
```

Permutation importance measures how much weighted F1 drops when a feature's values are randomly shuffled. This is model-agnostic and cannot be biased by feature cardinality (unlike Gini impurity importance).

### `run_full_training()` — 4-stage orchestrator

```
[1/4] full_pipeline(data_path)          → df, X, y
[2/4] train_and_compare(X, y)           → best_model, results, X_test, y_test
[3/4] compute_feature_importance(...)   → fi_df
[4/4] save_artifacts(...)               → 4 files on disk
```

---

## Saved Artifacts

| File | Contents | Usage |
|------|----------|-------|
| `model.pkl` | `joblib.dump(best_model)` — full HistGradientBoosting classifier | Loaded by `core.get_model()` via `lru_cache(maxsize=1)` |
| `feature_importance.csv` | columns: `feature`, `importance` (float) — 27 rows sorted desc | Read by `core.get_fi()`, rendered in Model Report page |
| `model_results.json` | `{model_name: {accuracy, f1_weighted, train_time_sec}}` | Read by Model Comparison page charts |
| `model_comparison.json` | Same + `confusion_matrix` (list of lists) + `classification_report` dict | Used by confusion matrix heatmaps and per-class F1 charts |

---

## Model Performance

### Summary

| Model | Accuracy | F1 (Weighted) | Train Time |
|-------|----------|---------------|-----------|
| **HistGradientBoosting** | **93.69%** | **0.9368** | 5.0 s |
| RandomForest | 92.54% | 0.9259 | 4.4 s |
| ExtraTrees | 91.06% | 0.9111 | 2.1 s |

### Per-Class Report — HistGradientBoosting (Best Model)

| Class | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| Low | 97.6% | 98.4% | 98.0% | 1,649 |
| Medium | 89.2% | 87.8% | 88.5% | 978 |
| High | 90.7% | 90.4% | 90.5% | 2,060 |
| Severe | 95.3% | 95.6% | 95.4% | 2,542 |
| **Weighted avg** | — | — | **93.7%** | 7,229 |

### Confusion Matrix — HistGradientBoosting

```
                Predicted
               Low   Med  High  Sev
Actual Low   [1622    27     0    0]
Actual Med   [  39   859    80    0]
Actual High  [   1    76  1862  121]
Actual Sev   [   0     1   111 2430]
```

Key observation: The model never confuses Low with Severe or vice versa. Most errors are between adjacent classes (Medium↔High) — exactly where human experts would also disagree.

---

## Feature Importance (Permutation-Based)

Full ranked list from `feature_importance.csv`:

| Rank | Feature | Importance (mean F1 drop) | % of Total |
|------|---------|--------------------------|-----------|
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
| 11–27 | (weather, snow, holiday, cyclical month, etc.) | ≈0.000 | ~13% combined |

**Critical insight:** `traffic_lag_1h` alone (36.4%) + the three time-of-day representations (`hour_cos` + `hour` + `hour_sin` = 39.7%) account for **76% of all predictive power**. All 8 weather features combined contribute less than 1%. Congestion on I-94 is overwhelmingly a function of *when* it is and *what it was doing an hour ago* — not weather conditions.

---

## 4-Agent Orchestration — `agents.py`

Every prediction triggered from the dashboard or MCP servers passes through `AgentOrchestrator.run_prediction_pipeline()`. Each agent is an independent class with a single `run()` method, structured logging, and no shared state between runs.

### `AgentLog`

```python
class AgentLog:
    def log(self, agent, message, level="INFO"):
        self.logs.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "agent":     agent,
            "level":     level,     # "INFO" or "SUCCESS"
            "message":   message,
        })

    def to_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.logs)
```

The log DataFrame is rendered as a live execution trace table in the Predict dashboard page.

### `DataAgent`

Runs once per session (at app startup). Computes:
- Record count, date range, years covered
- Congestion level distribution (`value_counts()`)
- Anomaly detection: zero-volume readings, `severe_during_rush_pct`

```python
severe_rush_pct = round(
    len(df[(df["congestion_label"] == "Severe") & (df["is_rush_hour"] == 1)]) /
    max(len(df[df["congestion_label"] == "Severe"]), 1) * 100, 1
)
```

### `PredictionAgent`

```python
fv = [float(input_features.get(col, 0)) for col in FEATURE_COLS]  # ordered by FEATURE_COLS
X  = np.array([fv])                                                 # shape: (1, 27)

t0         = time.time()
pred_code  = int(model.predict(X)[0])                             # → 0/1/2/3
elapsed_ms = (time.time() - t0) * 1000

proba      = model.predict_proba(X)[0]                            # → [p0, p1, p2, p3]
confidence = round(float(proba[pred_code]) * 100, 1)
```

Returns: `predicted_label`, `predicted_code`, `confidence`, `class_probabilities` (dict), `inference_time_ms`, `feature_vector` (dict).

### `InsightAgent`

Wraps `explain_prediction()` from `insights.py`. Receives the feature vector dict from `PredictionAgent`. Counts high-impact vs reducing factors for the log entry.

### `RecommendationAgent`

Combines base recommendations (from `get_recommendations_for_level()`) with four conditional additions:

| Condition | Added contextual action |
|-----------|------------------------|
| `is_rush_hour=1` AND level in High/Severe | Push mobile commuter alert |
| `rain_1h > 2.0` | Activate wet-weather speed advisory signs |
| `hour < 6` | Flag as maintenance window |
| `confidence < 60` | Verify with live sensor data |

Urgency assignment:
```python
urgency = {"Severe": "CRITICAL", "High": "HIGH", "Medium": "NORMAL", "Low": "LOW"}[label]
```

### `AgentOrchestrator`

```python
class AgentOrchestrator:
    def __init__(self, model, df, fi_df=None):
        self.pred_agent    = PredictionAgent(model)
        self.insight_agent = InsightAgent(fi_df)
        self.reco_agent    = RecommendationAgent()
        self.data_agent    = DataAgent()

    def run_prediction_pipeline(self, input_features: dict) -> dict:
        self.logger = AgentLog()
        self.logger.log("Orchestrator", "Starting Traffic Intelligence Pipeline...")
        pred_result = self.pred_agent.run(input_features, self.logger)
        explanation = self.insight_agent.run(pred_result, self.logger)
        action_plan = self.reco_agent.run(pred_result, explanation, self.logger)
        self.logger.log("Orchestrator", "Pipeline complete.")
        return {
            "prediction":  pred_result,
            "explanation": explanation,
            "action_plan": action_plan,
            "logs":        self.logger.logs,
        }
```

---

## Rule-Based Insight Engine — `insights.py`

The explanation engine is deterministic and fully auditable — no statistical approximation (SHAP/LIME). Every contributing factor is a hand-coded conditional that mirrors traffic-domain reasoning.

### `explain_prediction(prediction_label, input_features, fi_df)`

Evaluates 9 independent rule blocks against the feature vector:

```python
# Rules evaluated in order:
if is_rush:              → HIGH: "Morning/Evening rush hour (H:00)"
if is_wknd:              → REDUCING: "Weekend (~25% less traffic)"
else:                    → MODERATE: "Weekday (DayName)"
if is_hol:               → REDUCING: "Public Holiday"
if rain > 5.0:           → HIGH: "Heavy rain (X.X mm/hr)"
elif rain > 0.5:         → MODERATE: "Light rain (X.X mm/hr)"
if snow > 0:             → HIGH: "Snow (X.XX cm)"
if weather_code >= 4:    → HIGH: "Poor visibility (fog/thunderstorm)"
if lag_1h > 4500:        → HIGH: "Prior hour also heavy (N,NNN vehicles)"
elif lag_1h < 1000:      → REDUCING: "Prior hour was light (NNN vehicles)"
if hour < 5 or >= 23:    → REDUCING: "Late night / early morning (H:00)"
```

Output structure:
```python
{
  "level_info": {
      "emoji":   "🔴",
      "summary": "Severe congestion — gridlock possible.",
      "impact":  "Travel times may double. Avoid if possible."
  },
  "contributing_factors": [
      {"factor": "Evening rush hour (17:00)", "impact": "high",
       "detail": "Commuter demand spikes during peak hours (7–9 AM, 4–6 PM)."},
      {"factor": "Weekday (Wednesday)", "impact": "moderate",
       "detail": "Weekday commuter patterns drive sustained traffic load."},
      ...
  ],
  "prediction_narrative": "Severe congestion — gridlock possible. Primary drivers: Evening rush hour (17:00). Travel times may double. Avoid if possible."
}
```

### `generate_system_insights(peak_data)`

Produces 6 evidence-backed insight cards with `title`, `finding`, `recommendation`, `priority`:

1. **Rush Hour Dominance** (HIGH) — computes `rush_pct = (rush_avg - weekday_avg) / weekday_avg * 100`
2. **Weekday vs Weekend Disparity** (MEDIUM) — `diff_pct = (weekday_avg - weekend_avg) / weekday_avg * 100`
3. **Holidays Provide Significant Relief** (LOW) — `hol_pct = (weekday_avg - holiday_avg) / weekday_avg * 100`
4. **Weather Effects on Traffic Flow** (MEDIUM) — sorts `weather_impact` dict by volume
5. **Seasonal Peak** (MEDIUM) — names `worst_month` using `MONTH_NAMES[]`
6. **Traffic Has Strong Temporal Momentum** (HIGH) — references `traffic_lag_1h` permutation importance

### `get_recommendations_for_level(level)`

Hard-coded action lists:

```python
"Low":    ["No immediate action", "Diagnostics window", "Schedule maintenance"]
"Medium": ["Adaptive signal timing", "Traffic app updates", "Monitor transit capacity"]
"High":   ["Alert TMC", "Extend green phases 15–20%", "Broadcast VMS/radio", "Increase bus freq", "Contraflow lanes"]
"Severe": ["Full incident protocol", "Deploy officers", "Ramp metering", "Public advisory", "Emergency corridors"]
```

---

## Analytics and Visualisations — `analytics.py`

All 18 chart functions return `plotly.graph_objects.Figure` objects. The consistent dark-neutral styling (`plot_bgcolor="#f9fafb"`) ensures charts blend with the dashboard's CSS.

### Traffic Pattern Charts

**`make_hour_day_heatmap(df)`**
Groups by `(hour, day_of_week)`, computes mean `traffic_volume`, unstacks into a 24×7 pivot, renders with a 4-stop colorscale (green→yellow→orange→red). Adds `add_shape` rectangles for rush-hour bands (07:00–09:00, 16:00–18:00) using `fillcolor="rgba(59,130,246,0.12)"`.

**`make_congestion_heatmap(df)`**
Same 24×7 pivot but uses `congestion_code` average (0.0–3.0). Colorbar tick labels set to `["Low","Medium","High","Severe"]` at `[0,1,2,3]`.

**`make_calendar_heatmap(df, year)`**
Groups by date → daily mean → overlays `week_of_year` (x-axis) × `day_of_week` (y-axis) as square markers coloured by volume. Filters to selected year (defaults to mode year).

**`make_weekday_weekend_overlay(df)`**
Splits DataFrame on `is_weekend`, computes hourly mean for each, renders as two filled `Scatter` traces. Yellow rectangle overlays mark rush hour bands.

**`make_weekday_weekend_by_month(df)`**
Grouped bar chart: 12 months × 2 series (weekday blue, weekend green).

**`make_congestion_profile(df)`**
Groups by `(hour, congestion_label)`, counts, normalises to percentages, renders as four stacked `Scatter` traces with `stackgroup="one"`.

### Weather Analysis Charts

**`make_weather_box(df)`**  
One `Box` trace per `weather_main` category, sorted by median volume descending, `boxmean=True` shows mean diamond.

**`make_rain_scatter(df)`**  
Filters `rain_1h > 0`, samples 3,000 rows, plots `rain_1h` vs `traffic_volume`, coloured by `congestion_label`.

**`make_temp_traffic(df)`**  
Bins `temp_celsius` into 5°C ranges with `pd.cut(bins=range(-30,45,5))`, plots avg volume per bin as a colour-scaled bar chart.

**`make_weather_severity_bar(df)`**  
Maps `weather_severity` to `{0:"Clear/Dry", 1:"Light Rain", 2:"Moderate Rain", 3:"Heavy Rain", 4:"Snow/Severe"}`, plots mean volume per severity.

### Risk Scoring

**`compute_24h_risk(model, day_of_week, month, ...)`**

Computes a risk forecast for every hour 0–23:

```python
# Pre-compute historical median lag values per hour from dataset
lag_by_hour = df_ref.groupby("hour")[
    ["traffic_lag_1h","traffic_lag_24h","traffic_rolling_3h","traffic_rolling_6h"]
].median()

for hour in range(24):
    lags = lag_by_hour.loc[hour]   # historical median, not user-supplied
    fv   = {27-feature dict}
    code = int(model.predict(arr)[0])
    risk = (code / 3) * 100        # 0=Low→0%, 3=Severe→100%
```

Using historical medians as lag values makes the forecast self-contained — no prior-hour volume needed from the user.

**`make_risk_chart(risk_df)`**  
Vertical bar chart, each bar coloured by its `label`. Dotted `add_hline` markers at y=25, 50, 75 (class boundaries).

**`make_risk_timeline(risk_df)`**  
Filled area chart with coloured `add_hrect` background bands (green 0–25, yellow 25–50, orange 50–75, red 75–100). Markers coloured by level.

### Model Comparison Charts

**`make_model_metrics_comparison(results)`**  
`make_subplots(rows=1, cols=2)` — left subplot: accuracy per model, right: weighted F1. Y-axis range set to `[0.85, 1.0]` for visual resolution.

**`make_model_training_time_comparison(results)`**  
Single bar chart of `train_time_sec` per model.

**`make_confusion_matrix_heatmap(cm, labels, model_name)`**  
`go.Heatmap` with `Blues` colorscale, `texttemplate="%{text}"` shows raw counts in each cell.

**`make_per_class_metrics_comparison(results, labels)`**  
`make_subplots(rows=1, cols=4)` — one subplot per congestion class, showing F1-score for each model. Y-axis range `[0, 1.0]`.

**`make_model_radar_comparison(results, labels)`**  
`go.Scatterpolar` with 6 axes: `Accuracy`, `Weighted F1`, `Low F1`, `Medium F1`, `High F1`, `Severe F1`. Radial range `[0.85, 1.0]`. One trace per model with `fill="toself"`.

---

## Interactive Corridor Map — `map_view.py`

### I-94 Segment Data

16 named segments defined as ordered polylines (west→east: Plymouth/I-494 → East Saint Paul/I-494 East):

```python
I94_SEGMENTS = [
    {
        "name":   "Plymouth / I-494 Exchange",
        "coords": [[44.9630, -93.4580], [44.9650, -93.4200], [44.9665, -93.3900]],
        "factor": 0.70,     # <1.0 → less congested than corridor average
        "exit":   "Exit 1A – Plymouth Rd",
    },
    # ...
    {
        "name":   "Downtown Minneapolis — I-35W Interchange",
        "coords": [[44.9775, -93.2630], [44.9778, -93.2580], [44.9775, -93.2510]],
        "factor": 1.50,     # worst bottleneck — 50% above corridor average
        "exit":   "Exit 15 – I-35W North/South",
    },
    # ...
]
```

Full factor range: 0.70 (Plymouth, least congested) → 1.50 (I-35W, worst bottleneck).

| Segment | Factor | Is Bottleneck |
|---------|--------|--------------|
| Plymouth / I-494 Exchange | 0.70 | No |
| Brooklyn Blvd / TH-100 Area | 0.80 | No |
| TH-280 / Energy Park Dr | 0.95 | No |
| Vandalia St / Hamline Ave | 0.85 | No |
| Lexington / Hamline Pkwy | 0.90 | No |
| East Saint Paul / I-494 East | 0.75 | No |
| Snelling Ave — Midway | 1.00 | No |
| Dale St / Marion St | 1.00 | No |
| I-394 Merge (Western Approach) | 1.10 | Yes |
| I-35E / Kellogg Blvd Interchange | 1.10 | Yes |
| University of Minnesota / Washington Ave | 1.05 | Yes |
| Minnesota State Capitol Area | 1.15 | Yes |
| Cedar-Riverside / 11th Ave | 1.20 | Yes |
| Downtown Saint Paul — Core | 1.30 | Yes |
| Downtown Minneapolis — West | 1.40 | Yes |
| Downtown Minneapolis — I-35W Interchange | 1.50 | Yes |

### Spatial Factor Algorithm

```python
def _code_for_factor(base_code: int, factor: float) -> int:
    """Apply spatial multiplier to global model prediction, clamp to 0–3."""
    adjusted = base_code * factor
    if adjusted < 0.5: return 0
    if adjusted < 1.5: return 1
    if adjusted < 2.5: return 2
    return 3
```

Example: global prediction = High (code=2), factor=1.50 → adjusted=3.0 → Severe.  
Example: global prediction = Medium (code=1), factor=0.70 → adjusted=0.70 → Low.

### `create_i94_map()` Rendering Pipeline

```
1. _congestion_from_features() → base_code (0–3)
2. folium.Map(location=[44.9670, -93.2200], zoom_start=12, tiles="OpenStreetMap")
3. For each segment:
     seg_code  = _code_for_factor(base_code, seg["factor"])
     folium.PolyLine(weight=10, color=COLORS[seg_label])
     if seg_label == "Severe":
         AntPath(delay=600)   # animated red dashes overlay
4. For each segment mid-point:
     folium.CircleMarker(popup=HTML with congestion badge)
5. For each of 7 major interchanges:
     folium.Marker(icon=folium.Icon(color="darkblue", prefix="glyphicon"))
6. Inject HTML legend (position:fixed, bottom-left)
7. return folium.Map object → rendered via streamlit_folium.folium_static()
```

---

## Streamlit Dashboard — `app.py`

### Startup Sequence

```python
# DATA_PATH resolved at module load:
DATA_PATH = os.path.join(os.path.dirname(__file__), "Metro_Interstate_Traffic_Volume.csv")
# Override: streamlit run app.py -- --data /path/to/file.csv

st.set_page_config(page_title="Traffic Intelligence System", page_icon="🚦",
                   layout="wide", initial_sidebar_state="expanded")
inject_styles()   # must be called before any st.* output
```

### Caching Strategy

```python
@st.cache_data(show_spinner="Processing dataset…")
def load_data(path):
    df, X, y = full_pipeline(path)
    peak      = get_peak_hours_analysis(df)
    return df, X, y, peak

@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)

@st.cache_data
def load_fi():
    return pd.read_csv(FI_PATH)
```

`st.cache_resource` for the model (single shared object, not picklable across sessions).  
`st.cache_data` for DataFrames and derived data (serialised per session key).

### Sidebar

- Radio navigation (11 page names)
- Model status indicator: green checkmark if `model.pkl` exists, red X otherwise
- **Train/Retrain** button → calls `run_full_training(DATA_PATH)` inline, then `st.cache_data.clear()` + `st.rerun()` to reload all artifacts

### All 11 Pages

**1. Overview (📊)**
- 5 KPI cards: total records, years covered, avg volume, peak hour, busiest day
- `st.bar_chart` of congestion level distribution (colour-mapped)
- Dataset summary table with data range and cleaning notes

**2. Traffic Patterns (📈)**
- Tab 1: Bar chart — hourly average volume (0–23)
- Tab 2: Bar chart — average volume by day of week
- Tab 3: Box plot — volume by weather condition (`make_weather_box`)
- Tab 4: Bar chart — monthly average (seasonal view)

**3. Predict (🔮)**
- Two-column form: col1 = temporal inputs (hour slider, day select, month select, holiday checkbox); col2 = weather inputs + lag/rolling sliders
- On submit: calls `AgentOrchestrator.run_prediction_pipeline(input_features)`
- Displays: congestion banner, confidence %, probability bars, contributing factors table, action plan, agent execution log DataFrame

**4. AI Insights (💡)**
- Calls `orchestrator.run_system_insights(peak_data)` → 6 insight cards
- Each card: title, priority badge (HIGH/MEDIUM/LOW), finding paragraph, recommendation bullet

**5. Model Report (🏆)**
- Model comparison table (`model_results.json`)
- Horizontal bar chart of top 15 features by permutation importance
- Feature engineering summary table (groups × features × count)
- Congestion threshold reference table

**6. Model Comparison (📊)**
- `make_model_metrics_comparison()` — accuracy vs F1 subplot
- For each model in `model_comparison.json`: `make_confusion_matrix_heatmap()`
- `make_per_class_metrics_comparison()` — 4 subplots × 3 models
- `make_model_radar_comparison()` — 6-axis radar

**7. Traffic Map (🗺️)**
- Hour slider (0–23), day select, month select, weather select, temperature, rain, lag inputs
- `create_i94_map(model, ...)` → `folium_static(m, width=1100, height=600)`

**8. Heatmaps (🔥)**
- Tab 1: `make_hour_day_heatmap(df)` — 24×7 volume
- Tab 2: `make_congestion_heatmap(df)` — 24×7 congestion code
- Tab 3: `make_calendar_heatmap(df, selected_year)` — GitHub-style calendar with year selector

**9. Weather Analysis (🌦️)**
- `make_weather_box(df)` — volume by condition
- `make_rain_scatter(df)` — rainfall vs volume
- `make_temp_traffic(df)` — temperature bins
- `make_weather_severity_bar(df)` — severity 0→4

**10. Risk Scoring (🎯)**
- Day-of-week + month + weather code + rain inputs
- `compute_24h_risk(model, ...)` → DataFrame
- `make_risk_chart(risk_df)` + `make_risk_timeline(risk_df)`
- Expandable table showing hour-by-hour label + confidence + score

**11. MCP Live Intelligence (🤖)**
- Uses `MCPBridge` to call `live_intelligence_report()` in one shot
- Displays: current prediction, next-hour outlook, corridor alert count, 24h forecast chart, per-segment JSON table
- All data is live (uses system clock)

---

## MCP Servers — `mcp_servers/`

All four servers are built with `fastmcp.FastMCP`. They communicate over **stdio** (standard MCP transport). Each server is independently runnable: `python -m mcp_servers.{server_name}`.

### `core.py` — Shared Singletons

All four servers import from `core.py`. Singletons use `@lru_cache(maxsize=1)` to load once per process and cache permanently:

```python
@lru_cache(maxsize=1)
def get_model():
    return joblib.load(_MODEL_PATH)

@lru_cache(maxsize=1)
def get_df_and_peak():
    df, _, _ = full_pipeline(_DATA_PATH)
    peak     = get_peak_hours_analysis(df)
    return df, peak

@lru_cache(maxsize=1)
def get_fi():
    return pd.read_csv(_FI_PATH) if os.path.exists(_FI_PATH) else None

@lru_cache(maxsize=1)
def get_model_results():
    return json.load(open(_RES_PATH)) if os.path.exists(_RES_PATH) else {}
```

`build_feature_vector()` in `core.py` is the **single authoritative** 27-feature builder used by all prediction paths. The Streamlit bridge, all 4 MCP servers, and `map_view.py` all delegate to this function.

### `prediction_server.py` — 5 Tools, 3 Resources

| Tool | Signature | Description |
|------|-----------|-------------|
| `predict_congestion` | `(hour, dow, month, temp, rain, lag1, lag24, roll3, roll6, snow=0, clouds=40, weather="Clear", holiday=0)` | Full prediction + explanation + conditions |
| `predict_batch_hours` | `(hours: list, dow, month, temp, rain, lag1, weather, holiday)` | Multiple hours; lag24/roll3/roll6 derived at 95–98% of lag1 |
| `compute_risk_forecast` | `(dow, month, weather_code, rain, temp, holiday)` | 24h risk array + peak_hour + avg_risk + severe/high hour lists |
| `get_feature_vector` | `(hour, dow, month, temp, rain, lag1, weather, holiday)` | Returns the 27-feature dict without running inference |
| `predict_now` | `(rain=0, temp=15, lag=3000, snow=0, weather="Clear")` | Uses `datetime.now()` for hour/dow/month; adds timestamp fields |

| Resource URI | Returns |
|-------------|---------|
| `traffic://model/info` | JSON: best_model, f1_weighted, 27 feature count, class bins, top 10 features |
| `traffic://model/thresholds` | JSON: bin edges and codes for all 4 congestion classes |
| `traffic://model/feature_importance` | JSON: full 27-feature ranked list from `feature_importance.csv` |

### `analytics_server.py` — 8 Tools, 3 Resources

| Tool | Returns |
|------|---------|
| `get_hourly_traffic_profile()` | `{hourly_avg: {0–23: float}, peak_hour, trough_hour}` |
| `get_congestion_distribution()` | `{Low: {count, pct}, Medium: ..., High: ..., Severe: ...}` |
| `get_weather_impact_summary()` | Sorted list of `{condition, avg_volume}` |
| `get_rush_hour_stats()` | Rush window definitions + rush_avg, weekday_avg, weekend_avg, holiday_avg, rush_premium_pct |
| `compare_weekday_vs_weekend()` | weekday_avg, weekend_avg, diff_pct, peak_weekday_hour, peak_weekend_hour |
| `get_segment_risk_for_hour(hour, dow, month, ...)` | Full 16-segment breakdown: base_prediction + segments array + summary |
| `get_bottleneck_segments(hour, dow, month, min_label, ...)` | Filtered segment list at or above min_label threshold |
| `get_dataset_overview()` | Total records, date range, volume stats, peak_hour, peak_day, averages |

| Resource URI | Returns |
|-------------|---------|
| `traffic://dataset/summary` | Same as `get_dataset_overview()` as JSON |
| `traffic://dataset/peak_analysis` | Full `peak_data` dict with hourly/daily/monthly/weather averages |
| `traffic://segments/metadata` | 16 segments: name, exit, factor, is_bottleneck, lat/lon center |

### `insights_server.py` — 5 Tools, 3 Resources

| Tool | Description |
|------|-------------|
| `explain_prediction_for_conditions(label, hour, dow, rain, snow, lag1, is_rush, is_wknd, is_hol, w_code)` | Returns contributing_factors, narrative, level_info |
| `get_action_plan(level, is_rush, rain, hour, confidence)` | Immediate + contextual actions + urgency; adds Severe+rush police advisory |
| `get_system_insights()` | All 6 system insights sorted HIGH→MEDIUM→LOW |
| `get_level_description(level)` | emoji, summary, impact for one level |
| `generate_congestion_narrative(hour, dow, month, rain, temp, lag1, weather, holiday)` | Full alert report: headline + level + confidence + narrative + action_plan + conditions_summary |

`generate_congestion_narrative` constructs the headline string:
```python
f"{emoji_map[label]} Metro I-94 Traffic Alert — {label} congestion predicted at {hour:02d}:00 on {day_names[dow]}, {month_names[month]}"
```

| Resource URI | Returns |
|-------------|---------|
| `traffic://insights/system` | Sorted insights JSON |
| `traffic://insights/level_guide` | All 4 `LEVEL_DESCRIPTIONS` dicts |
| `traffic://insights/rush_schedule` | Morning/evening rush windows, peak_day, worst_month, rush_avg, weekday_avg |

### `map_server.py` — 4 Tools, 2 Resources

| Tool | Description |
|------|-------------|
| `get_corridor_congestion_map(hour, dow, month, rain, temp, lag1, holiday)` | Delegates to `core.get_segment_congestion()` — returns base prediction + 16 segments + summary |
| `get_bottleneck_segments(hour, dow, month, min_label, rain, temp, lag1)` | Filters `corridor["segments"]` by `segment_code >= _LEVEL_CODE[min_label]`; returns 8 fields per segment |
| `get_segment_history(segment_name, dow, month, rain, temp, lag1)` | Loops over 24 hours for one named segment; does partial-name matching; returns hourly_forecast + peak_hour + safe_hours |
| `list_segments()` | Static list of all 16: name, exit, factor, is_bottleneck |

`get_segment_history` enables queries unavailable in the Streamlit app — e.g. *"What is the worst hour for the I-35W interchange on a Monday in August?"*

| Resource URI | Returns |
|-------------|---------|
| `traffic://map/segments` | Full geometry: name, exit, factor, center lat/lon, coords array |
| `traffic://map/bottleneck_factors` | All 16 segments sorted by factor descending |

### Claude Desktop Integration

Add to `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/.config/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "traffic-prediction": {
      "command": "python",
      "args": ["-m", "mcp_servers.prediction_server"],
      "cwd": "C:/path/to/Urban-Traffic-Congestion-Prediction"
    },
    "traffic-analytics": {
      "command": "python",
      "args": ["-m", "mcp_servers.analytics_server"],
      "cwd": "C:/path/to/Urban-Traffic-Congestion-Prediction"
    },
    "traffic-insights": {
      "command": "python",
      "args": ["-m", "mcp_servers.insights_server"],
      "cwd": "C:/path/to/Urban-Traffic-Congestion-Prediction"
    },
    "traffic-map": {
      "command": "python",
      "args": ["-m", "mcp_servers.map_server"],
      "cwd": "C:/path/to/Urban-Traffic-Congestion-Prediction"
    }
  }
}
```

Example natural-language queries after connecting:
- *"Predict congestion at 8 AM on a Tuesday in August with light rain"*
- *"Which I-94 segments will be severe during Monday evening rush?"*
- *"Give me the 24-hour risk forecast for a Friday in July"*
- *"What are the worst bottleneck segments on I-94?"*
- *"Explain why the model predicts Severe at 5 PM on a weekday"*

---

## MCP Bridge — `mcp_servers/bridge.py`

The bridge provides synchronous Python access to all four MCP domains directly from the Streamlit app — no subprocess, no async event loop, no network overhead.

**Why not run a local MCP client in Streamlit?**  
Streamlit reruns the entire script on every user interaction. Spinning up subprocesses and async event loops per-rerun is fragile and slow. The bridge calls `core.py` functions directly and returns Python dicts, giving Streamlit instant access to the same logic the MCP servers expose over the protocol.

```python
class MCPBridge:
    def predict(self, hour, day_of_week, month, temp_celsius=15.0, ...) -> dict:
        return core.run_prediction(...)

    def forecast_24h(self, day_of_week, month, ...) -> list:
        return core.run_24h_risk(...)

    def corridor_map(self, hour, day_of_week, month, ...) -> dict:
        return core.get_segment_congestion(...)

    def live_intelligence_report(self, rain_1h=0.0, temp_celsius=15.0, ...) -> dict:
        # Aggregates 4 calls in one shot:
        current      = self.predict_now(...)          # current-hour prediction
        corridor     = self.corridor_map(...)          # 16-segment state
        risk_forecast= self.forecast_24h(...)          # 24h risk array
        alerts       = self.bottleneck_segments(       # High/Severe segments now
                           min_label="High", ...)
        next_pred    = self.predict(hour=(now.hour+1)%24, ...)
        return {
            "timestamp", "local_time", "date", "day_name",
            "current", "next_hour", "corridor", "risk_forecast", "alerts"
        }
```

`live_intelligence_report()` is called by the **MCP Live Intelligence** page and renders a complete real-time snapshot in one round-trip.

---

## UI Styling — `styles.py`

### CSS Theme

```python
# Injected via st.markdown(unsafe_allow_html=True)
# Base palette:
--bg-primary:   #080c18   (dark navy)
--bg-secondary: #0f1426   (slightly lighter)
--accent:       #7c3aed   (purple)
--text:         #e2e8f0   (light gray)
```

Key design patterns:
- **Glass-morphism cards**: `background: rgba(255,255,255,0.03)`, `backdrop-filter: blur(10px)`, `border: 1px solid rgba(255,255,255,0.08)`
- **Gradient text**: `background: linear-gradient(135deg, #7c3aed, #3b82f6)` with `-webkit-background-clip: text`
- **CSS animations**: `@keyframes float` (2s ease-in-out), `@keyframes glow` (pulse border), `@keyframes pulse` (opacity)
- **Congestion colour palette**: Low `#22c55e`, Medium `#eab308`, High `#f97316`, Severe `#ef4444`

### UI Components

| Function | Parameters | Renders |
|----------|-----------|---------|
| `inject_styles()` | — | All CSS into `<head>` |
| `page_header(emoji, title, subtitle)` | strings | Large gradient heading + subtitle |
| `metric_row(cols, metrics)` | st.columns, list of dicts | Grid of KPI cards |
| `glass_section(title, icon)` | strings | Bordered glass container |
| `glass_badge(level, color)` | strings | Pill badge (Low/Medium/High/Severe) |
| `congestion_banner(level)` | string | Full-width coloured banner with description |

---

## Configuration Files

### `.streamlit/config.toml`

```toml
[theme]
base                     = "dark"
primaryColor             = "#7c3aed"
backgroundColor          = "#080c18"
secondaryBackgroundColor = "#0f1426"
textColor                = "#e2e8f0"
font                     = "sans serif"

[browser]
gatherUsageStats = false    # telemetry disabled

[server]
headless = true             # required for non-interactive/cloud deployment
```

`headless = true` suppresses the browser auto-open and is required for any server-side deployment.

### `mcp_config.json`

Defines all 4 servers with `command`, `args`, `cwd`, plus full lists of tools and resources per server, example queries, and Claude Desktop integration instructions.

---

## Dependencies

```
pandas>=1.3.0          # DataFrame, groupby, cut, shift, rolling
numpy>=1.20.0          # sin/cos encoding, array construction, default_rng
scikit-learn>=1.0.0    # HistGradientBoosting, RandomForest, ExtraTrees,
                       # train_test_split, permutation_importance, metrics
joblib>=1.0.0          # model serialisation (dump/load)
streamlit>=1.20.0      # web dashboard
plotly>=5.0.0          # all 18 chart functions (go + px)
folium>=0.12.0         # Leaflet.js map via Python
streamlit-folium>=0.12.0  # folium_static() integration
mcp>=0.1.0             # Model Context Protocol base
fastmcp>=0.1.0         # FastMCP decorator API (FastMCP class, @mcp.tool, @mcp.resource)
```

**Python:** 3.9+ (3.12 confirmed by `__pycache__` bytecode naming)  
**No GPU required.** Entire training pipeline runs in ~5 seconds on CPU.  
**No external API keys.** OpenStreetMap tiles (Folium) are fetched at map render time only.

---

## Quick Start

```bash
# 1. Install dependencies
pip install pandas numpy scikit-learn joblib streamlit plotly folium \
            streamlit-folium mcp fastmcp

# 2. Train the model (~5–60 seconds depending on hardware)
python model_training.py
# Produces: model.pkl, feature_importance.csv, model_results.json, model_comparison.json

# 3. Launch the dashboard
streamlit run app.py
# Opens at http://localhost:8501

# 4. (Optional) Run an MCP server for Claude Desktop
python -m mcp_servers.prediction_server
```

Training can also be triggered from the **Train/Retrain** button in the Streamlit sidebar without leaving the browser.

---

## Performance Reference

| Metric | Value |
|--------|-------|
| Raw dataset rows | 48,204 |
| Rows after cleaning | 48,187 |
| Feature matrix shape | (48,187 × 27) |
| Train set | 41,059 rows (85%) |
| Test set | 7,128 rows (15%) |
| Best model | HistGradientBoosting |
| Best model accuracy | 93.69% |
| Best model F1 (weighted) | 0.9368 |
| Best model training time | ~5 s (CPU) |
| Inference latency | 1–3 ms per prediction |
| Dashboard pages | 11 |
| Chart types | 18 |
| I-94 segments | 16 |
| MCP tools total | 22 (5+8+5+4) |
| MCP resources total | 11 (3+3+3+2) |
| External API keys required | 0 |
