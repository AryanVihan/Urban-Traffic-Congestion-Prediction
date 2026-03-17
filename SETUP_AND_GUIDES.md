# 🚦 ForgeML Traffic Congestion Predictor – Setup & Usage Guide

Welcome! This guide will walk you through setting up, running, and using your Urban Traffic Intelligence System.

---

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation & Setup](#installation--setup)
3. [Running the Application](#running-the-application)
4. [Using the Dashboard](#using-the-dashboard)
5. [MCP Servers (Advanced)](#mcp-servers-advanced)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you start, ensure you have:

- **Python 3.9+** installed ([Download](https://www.python.org/downloads/))
- **Git** installed ([Download](https://git-scm.com/))
- **At least 2GB RAM** for model training
- The project files from GitHub: [Urban-Traffic-Congestion-Prediction](https://github.com/AryanVihan/Urban-Traffic-Congestion-Prediction)

---

## Installation & Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/AryanVihan/Urban-Traffic-Congestion-Prediction.git
cd "Urban-Traffic-Congestion-Prediction"
```

### Step 2: Create a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` is missing, install these packages:
```bash
pip install streamlit pandas numpy scikit-learn joblib folium streamlit-folium plotly matplotlib seaborn
```

For MCP Server support (optional but recommended):
```bash
pip install mcp fastmcp
```

### Step 4: Verify Data Files

Ensure these files exist in the project root:
- ✅ `Metro_Interstate_Traffic_Volume.csv` — Raw traffic data (48K records)
- ✅ `model.pkl` — Pre-trained ML model (run Step 5 if missing)
- ✅ `feature_importance.csv` — Feature rankings
- ✅ `model_results.json` — Model performance metrics

**Missing the model?** Run the next step.

### Step 5: Train the Model (First Time Only)

```bash
python model_training.py
```

This will:
- Load & preprocess the 48K-record dataset
- Train a Random Forest classifier (93.6% F1 score)
- Generate `model.pkl`, `feature_importance.csv`, `model_results.json`
- Takes ~60 seconds on a modern machine

---

## Running the Application

### Option 1: Run the Main Dashboard (Recommended for Most Users)

```bash
streamlit run app.py
```

Then open your browser to:
```
http://localhost:8501
```

**What it does:**
- Loads the web dashboard with 10 interactive pages
- Connects to live MCP servers automatically
- Displays real-time traffic predictions & analytics

---

### Option 2: Run Individual MCP Servers (For Development/Integration)

MCP Servers expose tools for Claude Desktop, other AI apps, or custom integrations.

**Prediction Server** (5 tools: predict, batch, risk, feature vector, live forecast):
```bash
python -m mcp_servers.prediction_server
```

**Analytics Server** (8 tools: hourly profiles, weather impact, risk patterns):
```bash
python -m mcp_servers.analytics_server
```

**Insights Server** (5 tools: explanation, recommendations, narratives):
```bash
python -m mcp_servers.insights_server
```

**Map Server** (4 tools: corridor map, bottlenecks, 24h history):
```bash
python -m mcp_servers.map_server
```

**Integration Guide:**
See `mcp_config.json` (project root) for:
- Claude Desktop configuration
- Full tool/resource list
- Example queries per server

---

## Using the Dashboard

### 🎯 Dashboard Overview

The dashboard has **10 interactive pages** in the sidebar:

#### 1. **📊 Overview**
- System summary: Record count, years, peak hours
- Congestion distribution (Low/Medium/High/Severe)
- Model performance badge
- **Action:** Click **"🚀 Train / Retrain"** to update the model

#### 2. **📈 Traffic Patterns**
- Hourly traffic heatmaps (day × hour)
- Weekday vs. weekend comparison
- Calendar heatmap (identify seasonal patterns)
- Peak hours analysis

#### 3. **🔮 Predict**
- **Single prediction:** Enter hour, weather, and temperature
- **Batch predictions:** Generate 24-hour forecasts
- See raw probabilities for each congestion level
- Visual risk indicators

#### 4. **💡 AI Insights**
- AI-powered explanations of predictions
- Actionable recommendations
- System-level intelligence (bottlenecks, patterns)
- Congestion level descriptions

#### 5. **🏆 Model Report**
- Feature importance rankings
- Confusion matrix & classification metrics
- ROC-AUC curves
- Model training details (accuracy, precision, F1)

#### 6. **🗺️ Traffic Map**
- Interactive map of I-94 corridor (all 16 segments)
- Real-time color coding (Green/Yellow/Orange/Red)
- Click segments for detailed history
- Bottleneck identification

#### 7. **🔥 Heatmaps**
- Congestion heatmap (when is traffic worst?)
- Weather-traffic correlation
- Temperature-volume scatter plot
- Rain impact analysis

#### 8. **🌦️ Weather Analysis**
- Weather metrics and severity
- Weather-traffic relationships
- Temperature & precipitation effects
- Seasonal patterns

#### 9. **🎯 Risk Scoring**
- Daily risk assessment (0-100 score)
- 24-hour risk timeline
- Segment-by-segment risk breakdown
- Predictive alerts

#### 10. **🤖 MCP Live Intelligence**
- Real-time predictions powered by MCP servers
- 4 tabs:
  - **⚡ Live Now** — Current congestion + next-hour outlook
  - **📅 24h Forecast** — Risk chart & batch predictions
  - **🗺️ Corridor Status** — All 16 segments with live alerts
  - **🖥️ MCP Servers** — Server registry & integration guide

---

### 💡 Quick Tips

1. **Predictions are most accurate 24-48 hours ahead**
2. **Morning (7-9 AM) and evening (4-6 PM) are peak traffic times**
3. **Rain and cold weather increase congestion**
4. **Weekends have lower traffic than weekdays**
5. **Use the Risk Scoring page for route planning**

---

## MCP Servers (Advanced)

### What are MCP Servers?

MCP (Model Context Protocol) servers extend AI applications with tools & resources. This project includes 4 specialized servers for traffic prediction, analytics, insights, and mapping.

### Connect to Claude Desktop

1. Open **Claude Desktop settings** (~/.config/Claude/claude_desktop_config.json)
2. Add servers under `mcpServers`:

```json
{
  "mcpServers": {
    "traffic-prediction": {
      "command": "python",
      "args": ["-m", "mcp_servers.prediction_server"],
      "cwd": "/path/to/project"
    },
    "traffic-analytics": {
      "command": "python",
      "args": ["-m", "mcp_servers.analytics_server"],
      "cwd": "/path/to/project"
    },
    "traffic-insights": {
      "command": "python",
      "args": ["-m", "mcp_servers.insights_server"],
      "cwd": "/path/to/project"
    },
    "traffic-map": {
      "command": "python",
      "args": ["-m", "mcp_servers.map_server"],
      "cwd": "/path/to/project"
    }
  }
}
```

3. Restart Claude Desktop
4. Now Claude can use your traffic tools automatically!

### Example Queries for Claude

- **Prediction:** "What's the risk level for 8 AM on a rainy day?"
- **Analytics:** "Show me hourly congestion patterns for weekdays"
- **Insights:** "Explain the bottleneck on I-94 segment 5"
- **Mapping:** "Display the corridor status with color-coded segments"

---

## Troubleshooting

### ❌ "ModuleNotFoundError: No module named 'streamlit'"
**Solution:** Install dependencies:
```bash
pip install streamlit pandas numpy scikit-learn joblib folium streamlit-folium plotly
```

### ❌ "FileNotFoundError: model.pkl not found"
**Solution:** Train the model first:
```bash
python model_training.py
```

### ❌ "Port 8501 already in use"
**Solution:** Run on a different port:
```bash
streamlit run app.py --server.port 8502
```

### ❌ Dashboard loads but predictions show "NaN"
**Solution:** Check that `Metro_Interstate_Traffic_Volume.csv` is in the root directory and is readable.

### ❌ MCP servers fail to start
**Solution:** Install MCP packages:
```bash
pip install mcp fastmcp
```

### ❌ "Permission denied" on macOS/Linux
**Solution:** Make scripts executable:
```bash
chmod +x model_training.py
chmod +x app.py
```

---

## Project Structure

```
ForgeML Traffic Congestion Predictor/
├── app.py                              # Main Streamlit dashboard
├── model_training.py                   # Train/retrain ML model
├── data_processing.py                  # Data pipeline & feature engineering
├── analytics.py                        # Charting & analysis functions
├── insights.py                         # AI explanations & recommendations
├── agents.py                           # Agent orchestration
├── styles.py                           # UI styling & components
├── map_view.py                         # Interactive map visualization
│
├── mcp_servers/                        # MCP Server implementations
│   ├── core.py                         # Shared computation logic
│   ├── prediction_server.py            # Prediction tools
│   ├── analytics_server.py             # Analytics tools
│   ├── insights_server.py              # Insight tools
│   ├── map_server.py                   # Mapping tools
│   └── bridge.py                       # Streamlit-MCP bridge
│
├── mcp_config.json                     # MCP server registry (Claude Desktop)
│
├── Metro_Interstate_Traffic_Volume.csv # Raw data (48K records)
├── model.pkl                           # Trained model
├── feature_importance.csv              # Feature rankings
├── model_results.json                  # Performance metrics
│
├── README.md                           # Project overview
├── PROJECT_EXPLAINED.md                # Deep dive into system
└── SETUP_AND_GUIDES.md                # This file!
```

---

## Next Steps

1. ✅ **Install dependencies** (`pip install -r requirements.txt`)
2. ✅ **Train the model** (`python model_training.py`) — if needed
3. ✅ **Run the dashboard** (`streamlit run app.py`)
4. ✅ **Explore the 10 pages** in the sidebar
5. ✅ **(Optional) Set up MCP servers** for Claude Desktop integration

---

## Support & Documentation

- **Full Project Explanation:** See [PROJECT_EXPLAINED.md](PROJECT_EXPLAINED.md)
- **Model Details:** See [model_results.json](model_results.json)
- **Feature Importance:** See [feature_importance.csv](feature_importance.csv)
- **GitHub:** [Urban-Traffic-Congestion-Prediction](https://github.com/AryanVihan/Urban-Traffic-Congestion-Prediction)

---

## Questions?

If you encounter issues:
1. Check [Troubleshooting](#troubleshooting) section
2. Review the error message carefully
3. Ensure all dependencies are installed: `pip list | grep -E "streamlit|pandas|scikit"`
4. Try restarting the terminal and re-running the command

---

**Happy Traffic Predicting! 🚗💨**
