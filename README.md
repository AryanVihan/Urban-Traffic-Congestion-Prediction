# 🚦 Urban Traffic Intelligence System

AI-powered traffic congestion prediction and explanation system built for the hackathon.

## Quick Start (3 steps)

```bash
# 1. Install dependencies
pip install pandas scikit-learn joblib streamlit

# 2. Train the model (one command, ~60 seconds)
python model_training.py Metro_Interstate_Traffic_Volume.csv

# 3. Launch the dashboard
streamlit run app.py -- --data Metro_Interstate_Traffic_Volume.csv
```

## System Architecture

```
CSV → data_processing.py → model_training.py → model.pkl
                                                    ↓
                          agents.py (orchestrator) ← insights.py
                                  ↓
                            app.py (Streamlit UI)
```

## Files

| File | Purpose |
|---|---|
| `data_processing.py` | Clean, engineer 27 features, label congestion levels |
| `model_training.py`  | Train 3 models, compare, save best as model.pkl |
| `insights.py`        | Rule-based AI explanation & insight engine |
| `agents.py`          | 4-agent workflow: Data → Predict → Explain → Recommend |
| `app.py`             | Streamlit dashboard (5 pages) |

## Model Performance

| Model | Accuracy | F1 (Weighted) | Train Time |
|---|---|---|---|
| **HistGradientBoosting** ✅ | **93.6%** | **0.936** | 15s |
| RandomForest | 92.6% | 0.927 | 16s |
| ExtraTrees | 91.0% | 0.911 | 7s |

## Feature Engineering (27 features)

- **Time:** hour, day_of_week, month, year, day_of_year
- **Rush hours:** is_rush_hour, rush_type, is_morning_rush, is_evening_rush
- **Cyclical:** hour_sin, hour_cos, month_sin, month_cos
- **Calendar:** is_weekend, is_holiday
- **Weather:** temp_celsius, rain_1h, snow_1h, clouds_all, is_raining, is_snowing, weather_severity, weather_code
- **Lag/Rolling:** traffic_lag_1h, traffic_lag_24h, traffic_rolling_3h, traffic_rolling_6h

## Congestion Thresholds

| Level  | Vehicles/hr | Colour |
|--------|-------------|--------|
| Low    | 0 – 1,000   | 🟢 |
| Medium | 1,001–2,500 | 🟡 |
| High   | 2,501–4,500 | 🟠 |
| Severe | 4,501–7,280 | 🔴 |

## Dashboard Pages

1. **Overview** — KPIs, congestion distribution, raw data
2. **Traffic Patterns** — Hourly, daily, weather, seasonal charts
3. **Predict** — Interactive form → AI prediction + explanation + action plan
4. **AI Insights** — 6 system-level intelligence cards with recommendations
5. **Model Report** — Comparison table, feature importance, engineering summary

## What Makes This Stand Out

- **4-agent AI workflow** (Data Agent → Prediction Agent → Insight Agent → Recommendation Agent)
- **Lag/rolling features** inspired by GRU notebook for temporal awareness
- **27 engineered features** combining best practices from 3 reference notebooks
- **Per-prediction AI explanation** with contributing factors and urgency classification
- **One-click training** from the Streamlit sidebar
- **93.6% F1 score** on held-out test set
- **No API keys needed** — fully offline capable

## Dataset

Metro Interstate I-94 Traffic Volume (Kaggle)
- 48,204 hourly records · 2012–2018
- Features: weather, temperature, holidays, datetime
