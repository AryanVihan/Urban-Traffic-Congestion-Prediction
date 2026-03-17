# ForgeML Traffic Congestion Predictor — Deep Dive Explanation

## Table of Contents
1. [What This Project Does](#1-what-this-project-does)
2. [High-Level Architecture](#2-high-level-architecture)
3. [The Dataset](#3-the-dataset)
4. [data_processing.py — The Data Pipeline](#4-data_processingpy--the-data-pipeline)
5. [model_training.py — Training the AI](#5-model_trainingpy--training-the-ai)
6. [agents.py — The 4-Agent AI Workflow](#6-agentspy--the-4-agent-ai-workflow)
7. [insights.py — The Explanation Engine](#7-insightspy--the-explanation-engine)
8. [app.py — The Streamlit Dashboard](#8-apppy--the-streamlit-dashboard)
9. [How a Prediction Actually Works (End-to-End)](#9-how-a-prediction-actually-works-end-to-end)
10. [Model Performance & Feature Importance](#10-model-performance--feature-importance)
11. [Saved Artifacts](#11-saved-artifacts)
12. [How to Run the Project](#12-how-to-run-the-project)

---

## 1. What This Project Does

This is an **AI-powered traffic congestion prediction and explanation system** for the Metro I-94 Interstate highway in Minneapolis–Saint Paul, Minnesota.

Given inputs like the **time of day**, **day of week**, **weather conditions**, and **recent traffic volumes**, the system:
- **Predicts** which of 4 congestion levels traffic will be (Low / Medium / High / Severe)
- **Explains** *why* that prediction was made in plain English
- **Recommends** specific actions (e.g., signal timing changes, public alerts)
- **Visualizes** historical traffic patterns across 6 years of data

It does all of this **entirely offline** — no external AI APIs needed.

---

## 2. High-Level Architecture

```
Metro_Interstate_Traffic_Volume.csv   ← Raw hourly traffic data (48,204 rows)
            │
            ▼
  data_processing.py                  ← Cleans data, engineers 27 features,
            │                            assigns congestion labels
            ▼
  model_training.py                   ← Trains 3 ML models, picks the best,
            │                            computes feature importance
            ▼
  model.pkl                           ← Saved trained model (HistGradientBoosting)
  feature_importance.csv              ← Which features matter most
  model_results.json                  ← Accuracy/F1 scores for all 3 models
            │
            ▼
  app.py  (Streamlit UI)              ← 5-page interactive dashboard
            │
     ┌──────┴──────────────┐
     ▼                     ▼
  agents.py             insights.py
  (orchestrates the     (explains predictions,
   prediction pipeline)  generates insight cards)
```

There are **5 Python files**, each with a distinct role:

| File | Role |
|---|---|
| `data_processing.py` | Raw CSV → clean, feature-rich DataFrame |
| `model_training.py` | DataFrame → trained ML model + artifacts |
| `agents.py` | Coordinates prediction, explanation, recommendations |
| `insights.py` | Rule-based explanation and insight text generation |
| `app.py` | Streamlit web dashboard that ties everything together |

---

## 3. The Dataset

**File:** `Metro_Interstate_Traffic_Volume.csv`
**Source:** UCI ML Repository — Metro Interstate Traffic Volume dataset
**Size:** 48,204 hourly records from **October 2012 to September 2018** (6 years)

### Raw Columns (9 total)

| Column | Description | Example |
|---|---|---|
| `holiday` | US national holiday name or `NaN` | `"Columbus Day"` / `NaN` |
| `temp` | Air temperature in **Kelvin** | `288.28` (= 15.1°C) |
| `rain_1h` | Rainfall in the past hour (mm) | `0.0`, `2.5` |
| `snow_1h` | Snowfall in the past hour (cm) | `0.0`, `0.25` |
| `clouds_all` | Cloud cover percentage | `40` |
| `weather_main` | Short weather label | `"Clouds"`, `"Rain"`, `"Snow"` |
| `weather_description` | Detailed description | `"scattered clouds"` |
| `date_time` | Timestamp (hourly) | `"2012-10-02 09:00:00"` |
| `traffic_volume` | **Target:** vehicles per hour | `5545` |

### Why 48,204 → 48,187 rows after processing?
Duplicate rows are removed during cleaning, which drops ~17 entries.

---

## 4. data_processing.py — The Data Pipeline

This file transforms the raw CSV into a machine-learning-ready dataset. It runs in 5 stages:

### Stage 1: `load_raw()` — Load & Parse
```
CSV file → pandas DataFrame with date_time parsed as datetime
```
- Reads the CSV with `pd.read_csv()`
- Converts the `date_time` column to a proper datetime type so we can extract hours, months, etc.

### Stage 2: `clean()` — Fix Data Quality Issues

Three cleaning operations:

**a) Remove duplicates** — drops ~17 repeated rows.

**b) Fix temperature=0 sensor errors** — When `temp == 0` (physically impossible in Minnesota — it would be -273°C), it replaces those values with the **median temperature for that hour of day**. For example, a bad 3 PM reading gets replaced with the median of all valid 3 PM readings.

**c) Cap extreme rain outliers** — Clips `rain_1h` to a maximum of 50mm/hr to prevent outlier distortion. (Real extreme storms can show inflated sensor readings.)

**d) Fill holiday NaN** — Replaces `NaN` in the holiday column with the string `"None"` so it's consistent.

### Stage 3: `engineer_features()` — Create 27 Features

This is where the raw 9 columns become 27 meaningful features for the model. Grouped by category:

#### Time Features (5)
| Feature | How It's Made | Why It Matters |
|---|---|---|
| `hour` | `date_time.dt.hour` | Traffic peaks at specific hours |
| `day_of_week` | `date_time.dt.dayofweek` (0=Mon) | Weekday vs weekend patterns |
| `month` | `date_time.dt.month` | Seasonal variations |
| `year` | `date_time.dt.year` | Long-term trends |
| `day_of_year` | `date_time.dt.dayofyear` | Fine-grained seasonality |

#### Rush Hour Features (4)
| Feature | Logic | Why It Matters |
|---|---|---|
| `is_morning_rush` | `hour` between 7–9 | Morning commute spike |
| `is_evening_rush` | `hour` between 16–18 | Evening commute spike |
| `is_rush_hour` | Either morning OR evening rush | Binary: in rush or not |
| `rush_type` | 0=none, 1=morning, 2=evening | Differentiates the two peaks |

#### Cyclical Encoding (4)
Raw hour and month are **not** good for ML because hour 23 and hour 0 are adjacent in reality, but numerically far apart (23 vs 0). Cyclical encoding fixes this:

| Feature | Formula | Why It Matters |
|---|---|---|
| `hour_sin` | `sin(2π × hour / 24)` | Encodes circular time correctly |
| `hour_cos` | `cos(2π × hour / 24)` | Works with hour_sin to form a clock |
| `month_sin` | `sin(2π × month / 12)` | Encodes circular season correctly |
| `month_cos` | `cos(2π × month / 12)` | Works with month_sin |

#### Calendar Features (2)
| Feature | Logic |
|---|---|
| `is_weekend` | `day_of_week >= 5` (Sat/Sun) |
| `is_holiday` | `holiday != "None"` |

#### Weather Features (8)
| Feature | How It's Made |
|---|---|
| `temp_celsius` | `temp - 273.15` (convert from Kelvin) |
| `rain_1h` | Direct from dataset (already cleaned) |
| `snow_1h` | Direct from dataset |
| `clouds_all` | Direct from dataset |
| `is_raining` | `rain_1h > 0` (binary) |
| `is_snowing` | `snow_1h > 0` (binary) |
| `weather_severity` | Rain intensity (0–3) + snow flag: `pd.cut([0, 2.5, 7.6, 55])` |
| `weather_code` | Numeric encoding: Clear=0, Clouds=1, Haze=1, Smoke=2, Rain=3, Fog=4, Squall=5 |

#### Lag / Rolling Features (4) — The Most Important!
These capture **temporal momentum** — the idea that this hour's traffic heavily depends on recent hours:

| Feature | How It's Made | Meaning |
|---|---|---|
| `traffic_lag_1h` | `traffic_volume.shift(1)` | Volume from exactly 1 hour ago |
| `traffic_lag_24h` | `traffic_volume.shift(24)` | Volume at this same hour yesterday |
| `traffic_rolling_3h` | Rolling mean of last 3 hours | Short-term trend |
| `traffic_rolling_6h` | Rolling mean of last 6 hours | Medium-term trend |

For the very first rows (no prior data), missing values are filled with the dataset median.

### Stage 4: `create_congestion_labels()` — Define the Target

The raw `traffic_volume` (a number) is bucketed into 4 classes:

| Label | Volume Range | Code |
|---|---|---|
| Low | 0 – 1,000 vehicles/hr | 0 |
| Medium | 1,001 – 2,500 vehicles/hr | 1 |
| High | 2,501 – 4,500 vehicles/hr | 2 |
| Severe | 4,501 – 7,280 vehicles/hr | 3 |

This is a **multi-class classification** problem (not regression), which makes predictions more actionable.

### Stage 5: `get_peak_hours_analysis()` — Dashboard Stats

Computes aggregated statistics used in the dashboard:
- Hourly/daily/monthly average traffic
- Peak hour, quietest hour, busiest day, busiest month
- Weekday vs weekend averages
- Holiday average
- Rush hour average
- Weather condition averages

---

## 5. model_training.py — Training the AI

### Three Models Are Trained and Compared

| Model | Key Hyperparameters | Why Chosen |
|---|---|---|
| **HistGradientBoosting** | max_iter=300, lr=0.08, max_depth=8, early stopping | Fast, handles missing data, state-of-art |
| **RandomForest** | n_estimators=300, max_depth=15, balanced classes | Robust, interpretable, good baseline |
| **ExtraTrees** | n_estimators=300, max_depth=15, balanced classes | Faster variant of RandomForest |

### Training Process

1. **Split data:** 85% training / 15% test, using stratified split (ensures each congestion class is proportionally represented in both sets)
2. **Train each model** on training data, measure wall-clock time
3. **Evaluate** on held-out test set: accuracy + weighted F1 score
4. **Pick the winner** by highest F1 score

### Results
| Model | Accuracy | F1 (Weighted) | Train Time |
|---|---|---|---|
| **HistGradientBoosting** ✅ | **93.64%** | **0.9363** | 14.8s |
| RandomForest | 92.63% | 0.9267 | 15.6s |
| ExtraTrees | 91.04% | 0.9109 | 6.7s |

**Why F1 over accuracy?** The dataset is imbalanced (few "Severe" cases). F1 penalizes models that ignore rare classes, making it a fairer metric.

### Feature Importance via Permutation

Instead of using built-in feature importances (which can be biased for tree models), the code uses **permutation importance**:
1. Train the best model normally, record baseline F1
2. For each feature, randomly shuffle just that column, measure how much F1 drops
3. Bigger drop = more important feature

This is computed on up to 5,000 test samples with 5 repeats for reliability.

### What Gets Saved
- `model.pkl` — The trained HistGradientBoosting model (via joblib)
- `feature_importance.csv` — Feature names + importance scores, sorted descending
- `model_results.json` — Accuracy, F1, and training time for all 3 models

---

## 6. agents.py — The 4-Agent AI Workflow

This file implements an **agent-based architecture** where specialized agents each handle one task, coordinated by an orchestrator. This mirrors how enterprise AI systems are built.

### AgentLog
A simple structured logger. Each log entry records:
- `timestamp` — exact time (HH:MM:SS)
- `agent` — which agent logged this
- `level` — INFO or SUCCESS
- `message` — what happened

The full log is shown in the dashboard's "Agent Execution Trace" expander.

---

### Agent 1: DataAgent
**Job:** Profile the dataset and detect anomalies.

Computes:
- Total record count and date range
- Number of years covered
- Distribution of congestion levels (how many Low/Medium/High/Severe rows)
- Zero-traffic anomalies (sensors going offline)
- % of severe congestion that occurs during rush hours

This runs when you click "Predict" to give the orchestrator context about the data.

---

### Agent 2: PredictionAgent
**Job:** Run the ML model and return a prediction.

Steps:
1. Takes the `input_features` dict (27 keys) and converts it to a numeric array
2. Calls `model.predict()` → gets the congestion class code (0–3)
3. Calls `model.predict_proba()` → gets probabilities for all 4 classes
4. Measures inference time in milliseconds
5. Returns: predicted label, confidence %, all 4 class probabilities, timing

---

### Agent 3: InsightAgent
**Job:** Explain *why* the model made that specific prediction.

Calls `explain_prediction()` from `insights.py` (see next section). Returns a list of contributing factors with impact levels (high / moderate / reducing).

---

### Agent 4: RecommendationAgent
**Job:** Turn the prediction into an action plan.

- Gets the base set of **immediate actions** for the predicted congestion level from `insights.py`
- Adds **contextual actions** based on specific conditions:
  - Rush hour + High/Severe → push mobile delay alert
  - Rain > 2mm/hr → activate wet-weather speed signs
  - Hour < 6 AM → suggest maintenance window
  - Confidence < 60% → recommend verifying with live sensors
- Assigns an **urgency level**: LOW / NORMAL / HIGH / CRITICAL

---

### AgentOrchestrator
**Job:** Run all agents in sequence and collect results.

The `run_prediction_pipeline()` method:
```
Input features dict
      │
      ▼
PredictionAgent.run()    → prediction result
      │
      ▼
InsightAgent.run()       → explanation
      │
      ▼
RecommendationAgent.run() → action plan
      │
      ▼
Returns combined report dict + all logs
```

---

## 7. insights.py — The Explanation Engine

This is a **rule-based reasoning system** — no ML involved, just if/else logic that mirrors how a traffic expert would think.

### `explain_prediction()`

Given the predicted label and the input features, this function builds a list of factors explaining the prediction:

| Condition Checked | Factor Generated | Impact |
|---|---|---|
| `is_rush_hour == 1` | "Morning/Evening rush hour" | High |
| `is_weekend == 1` | "Weekend" | Reducing |
| `is_weekend == 0` | "Weekday (Monday...)" | Moderate |
| `is_holiday == 1` | "Public Holiday" | Reducing |
| `rain_1h > 5.0` | "Heavy rain" | High |
| `0.5 < rain_1h ≤ 5.0` | "Light rain" | Moderate |
| `snow_1h > 0` | "Snow" | High |
| `weather_code >= 4` | "Poor visibility (fog/thunderstorm)" | High |
| `traffic_lag_1h > 4500` | "Prior hour also heavy" | High |
| `traffic_lag_1h < 1000` | "Prior hour was light" | Reducing |
| `hour < 5 or hour >= 23` | "Late night / early morning" | Reducing |

Then assembles a **narrative sentence** like:
> *"Heavy traffic causing noticeable congestion. Primary drivers: Evening rush hour (17:00), Prior hour also heavy (5,200 vehicles). Travel times 30–50% above normal."*

### `generate_system_insights()`

Generates 6 data-driven insight cards from the aggregated peak analysis stats:

1. **Rush Hour Dominance** — how much % more traffic occurs during rush vs daily average
2. **Weekday vs Weekend Disparity** — quantified difference, busiest day
3. **Holiday Relief** — how much holidays reduce volume vs weekday average
4. **Weather Effects** — which weather correlates with highest/lowest volumes
5. **Seasonal Peak** — which month sees the most congestion
6. **Temporal Momentum** — explains why `traffic_lag_1h` is the #1 feature

### `get_recommendations_for_level()`

Returns a hardcoded list of action items per congestion level:

- **Low:** No action, use window for maintenance
- **Medium:** Activate adaptive signals, push traffic updates
- **High:** Alert traffic center, extend green phases, contraflow lanes
- **Severe:** Full incident protocol, deploy officers, ramp metering, public advisory

---

## 8. app.py — The Streamlit Dashboard

The dashboard has **5 pages** navigated via a sidebar radio button.

### Sidebar
- Navigation between 5 pages
- Shows whether `model.pkl` exists (pipeline status)
- **Train / Retrain button** — triggers the full `run_full_training()` pipeline (~60s), then clears Streamlit's cache and reruns the app
- Shows the data file name

### Page 1: Overview
- **5 KPI metrics:** Record count, years of data, average volume/hr, peak hour, peak day
- **Congestion distribution** — colored bar for each level showing count and percentage
- **Dataset summary table** — date range, min/max/median volumes, rush vs weekend vs holiday averages
- **Raw data sample** — first 200 rows of the processed DataFrame

### Page 2: Traffic Patterns
Four tabs of charts:

- **Hourly** — bar chart of average traffic by hour (0–23), with rush hour annotations
- **Daily** — bar chart by day of week + weekday vs weekend comparison
- **Weather** — bar chart of average traffic by weather condition (shows Clear has more traffic than Fog because people avoid driving in bad weather)
- **Seasonal** — bar chart by month, busiest month highlighted

### Page 3: Predict (the core feature)
1. **Input form** with 3 columns:
   - Time: hour slider, day dropdown, month slider, holiday checkbox
   - Weather: condition dropdown, temperature, rain, snow, cloud cover
   - Recent traffic: lag_1h, lag_24h, rolling_3h, rolling_6h sliders

2. On submit, manually computes derived features (cyclical encodings, rush hour flags, weather code) and calls `AgentOrchestrator.run_prediction_pipeline()`

3. **Result display:**
   - Large colored card showing level + confidence + inference time
   - Class probability bar chart
   - Contributing factors (expandable, with impact icons 🔴🟡🟢)
   - Action plan with urgency badge
   - Expandable agent execution trace log

### Page 4: AI Insights
- 6 insight cards sorted by priority (HIGH → MEDIUM → LOW)
- Each card shows: title, finding (evidence), recommendation, priority badge
- Color-coded borders (red=HIGH, orange=MEDIUM, green=LOW)

### Page 5: Model Report
- Model comparison table (styled to highlight best scores in green)
- Feature importance horizontal bar chart (top 15 features)
- Feature engineering summary table
- Congestion threshold reference table

---

## 9. How a Prediction Actually Works (End-to-End)

Let's say you set: **5 PM, Tuesday, August, clear weather, prior hour = 5,200 vehicles**.

### Step 1: Feature Vector Construction (app.py)
The app computes all 27 features from your inputs:
```python
hour=17, day_of_week=1, month=8, year=2026, day_of_year=229
is_weekend=0, is_rush_hour=1, rush_type=2 (evening)
is_morning_rush=0, is_evening_rush=1
hour_sin=sin(2π×17/24)=-0.866, hour_cos=cos(2π×17/24)=-0.5
month_sin=sin(2π×8/12)=-0.866, month_cos=cos(2π×8/12)=-0.5
is_holiday=0
temp_celsius=18.0, rain_1h=0.0, snow_1h=0.0, clouds_all=40
is_raining=0, is_snowing=0, weather_severity=0.0, weather_code=0.0
traffic_lag_1h=5200, traffic_lag_24h=4000, rolling_3h=4800, rolling_6h=4500
```

### Step 2: PredictionAgent
- Calls `model.predict([[...27 values...]])` → returns `3` (Severe)
- Calls `model.predict_proba()` → e.g., `[0.01, 0.02, 0.09, 0.88]`
- Confidence = 88% for Severe
- Inference time ~1–3 ms

### Step 3: InsightAgent / explain_prediction()
Checks each rule:
- `is_rush_hour=1` → "Evening rush hour (17:00)" — **HIGH impact**
- `is_weekend=0` → "Weekday (Tuesday)" — **moderate impact**
- `traffic_lag_1h=5200 > 4500` → "Prior hour also heavy (5,200 vehicles)" — **HIGH impact**

Narrative: *"Severe congestion — gridlock possible. Primary drivers: Evening rush hour (17:00), Prior hour also heavy (5,200 vehicles). Travel times may double. Avoid if possible."*

### Step 4: RecommendationAgent
- Immediate actions for Severe: deploy officers, ramp metering, public advisory, etc.
- Contextual: rush + severe → push mobile alert
- Urgency: **CRITICAL**

### Step 5: Dashboard renders the result
- 🔴 **Severe Congestion** card (red background)
- 88% confidence, ~2ms inference
- Contributing factors, action plan, full agent log

---

## 10. Model Performance & Feature Importance

### Why HistGradientBoosting Wins
- It's a gradient-boosted tree ensemble (similar to XGBoost/LightGBM)
- Handles the dataset's imbalanced classes well
- Built-in early stopping prevents overfitting
- Scikit-learn's native implementation — fast and no extra dependencies

### Top Feature Importances (from permutation analysis)

| Rank | Feature | Importance | Interpretation |
|---|---|---|---|
| 1 | `traffic_lag_1h` | 0.364 | **36%** — previous hour traffic is by far the biggest signal |
| 2 | `hour_cos` | 0.214 | Time of day (cyclical cosine component) |
| 3 | `hour` | 0.146 | Raw hour — combined with hour_cos, this is ~36% |
| 4 | `day_of_week` | 0.070 | Weekday patterns |
| 5 | `hour_sin` | 0.024 | Time of day (cyclical sine component) |
| 6 | `traffic_rolling_6h` | 0.023 | 6-hour rolling average |
| 7 | `traffic_rolling_3h` | 0.022 | 3-hour rolling average |
| 8 | `traffic_lag_24h` | 0.014 | Same-hour-yesterday volume |
| 9 | `day_of_year` | 0.013 | Fine seasonality |
| 10 | `temp_celsius` | 0.012 | Temperature (mild effect) |

**Key insight:** Weather features (`rain_1h`, `is_raining`) have near-zero importance. Traffic follows time patterns far more than weather. Bad weather suppresses trips entirely, but the trips that do happen follow the same time patterns — so the model learns time > weather.

---

## 11. Saved Artifacts

| File | Format | Contents |
|---|---|---|
| `model.pkl` | Binary (joblib) | Fitted HistGradientBoostingClassifier, ready to call `.predict()` |
| `feature_importance.csv` | CSV | `feature`, `importance`, `std` columns, sorted by importance |
| `model_results.json` | JSON | `{ModelName: {accuracy, f1_weighted, train_time_sec}}` for 3 models |

These are generated by `model_training.py` and read by `app.py` at startup. If they don't exist, the app shows a warning and the train button must be pressed.

---

## 12. How to Run the Project

### First Time (model already trained)
```bash
# Install dependencies
pip install pandas scikit-learn joblib streamlit

# Launch the dashboard
streamlit run app.py -- --data Metro_Interstate_Traffic_Volume.csv
```

### If You Want to Retrain the Model
```bash
# Retrain from scratch (~60 seconds)
python model_training.py Metro_Interstate_Traffic_Volume.csv

# Or use the sidebar "Train / Retrain" button in the running app
```

### Congestion Label Reference
| Level | Vehicles/hr | What It Means |
|---|---|---|
| 🟢 Low | 0–1,000 | Free flow, no delays |
| 🟡 Medium | 1,001–2,500 | Some slowdowns, 10–20% longer travel |
| 🟠 High | 2,501–4,500 | Heavy congestion, 30–50% longer travel |
| 🔴 Severe | 4,501–7,280 | Gridlock possible, travel times may double |
