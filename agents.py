"""
agents.py
---------
4-agent AI workflow: DataAgent → PredictionAgent → InsightAgent → RecommendationAgent
"""

import time
import numpy as np
import pandas as pd
from datetime import datetime


class AgentLog:
    def __init__(self):
        self.logs = []

    def log(self, agent, message, level="INFO"):
        entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "agent": agent,
            "level": level,
            "message": message,
        }
        self.logs.append(entry)

    def to_df(self):
        return pd.DataFrame(self.logs)


class DataAgent:
    name = "DataAgent"

    def run(self, df, logger):
        logger.log(self.name, "Starting dataset analysis...")
        from data_processing import CONGESTION_LABELS

        profile = {
            "total_records":    len(df),
            "date_range_start": str(df["date_time"].min().date()),
            "date_range_end":   str(df["date_time"].max().date()),
            "years_covered":    df["date_time"].dt.year.nunique(),
            "congestion_dist":  df["congestion_label"].value_counts().to_dict(),
        }

        anomalies = []
        zero_count = (df["traffic_volume"] == 0).sum()
        if zero_count > 0:
            anomalies.append(f"{zero_count} zero-volume readings detected.")
        profile["anomalies"] = anomalies

        severe_rush_pct = round(
            len(df[(df["congestion_label"] == "Severe") & (df["is_rush_hour"] == 1)]) /
            max(len(df[df["congestion_label"] == "Severe"]), 1) * 100, 1
        )
        profile["severe_during_rush_pct"] = severe_rush_pct

        logger.log(self.name, f"Analyzed {len(df):,} records across {profile['years_covered']} years.")
        logger.log(self.name, f"Severe congestion during rush hour: {severe_rush_pct}%")
        logger.log(self.name, "Data profiling complete.", level="SUCCESS")
        return profile


class PredictionAgent:
    name = "PredictionAgent"

    def __init__(self, model):
        self.model = model

    def run(self, input_features, logger):
        from data_processing import FEATURE_COLS, CONGESTION_LABELS
        logger.log(self.name, "Building feature vector...")

        fv = [float(input_features.get(col, 0)) for col in FEATURE_COLS]
        X  = np.array([fv])

        t0       = time.time()
        pred_code = int(self.model.predict(X)[0])
        elapsed  = (time.time() - t0) * 1000

        pred_label = CONGESTION_LABELS[pred_code]
        confidence = None
        proba_dict = {}

        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(X)[0]
            confidence = round(float(proba[pred_code]) * 100, 1)
            proba_dict = {CONGESTION_LABELS[i]: round(float(p) * 100, 1)
                          for i, p in enumerate(proba)}

        logger.log(self.name, f"Prediction: {pred_label} | Confidence: {confidence}% | {elapsed:.1f}ms")
        logger.log(self.name, "Prediction complete.", level="SUCCESS")

        return {
            "predicted_label":     pred_label,
            "predicted_code":      pred_code,
            "confidence":          confidence,
            "class_probabilities": proba_dict,
            "inference_time_ms":   round(elapsed, 1),
            "feature_vector":      dict(zip(FEATURE_COLS, fv)),
        }


class InsightAgent:
    name = "InsightAgent"

    def __init__(self, fi_df=None):
        self.fi_df = fi_df

    def run(self, prediction_result, logger):
        from insights import explain_prediction
        label    = prediction_result["predicted_label"]
        features = prediction_result["feature_vector"]

        logger.log(self.name, f"Explaining '{label}' prediction...")
        explanation = explain_prediction(label, features, self.fi_df)

        high_count = len([f for f in explanation["contributing_factors"] if f["impact"] == "high"])
        logger.log(self.name, f"{len(explanation['contributing_factors'])} factors found ({high_count} high-impact).")
        logger.log(self.name, "Explanation ready.", level="SUCCESS")
        return explanation


class RecommendationAgent:
    name = "RecommendationAgent"

    def run(self, prediction_result, explanation, logger):
        from insights import get_recommendations_for_level
        label    = prediction_result["predicted_label"]
        features = prediction_result["feature_vector"]

        logger.log(self.name, f"Building action plan for {label} congestion...")

        immediate = get_recommendations_for_level(label)

        hour     = int(features.get("hour", 12))
        is_rush  = int(features.get("is_rush_hour", 0))
        rain     = float(features.get("rain_1h", 0))
        confidence = prediction_result.get("confidence", 50)

        contextual = []
        if is_rush and label in ["High", "Severe"]:
            contextual.append("📱 Push mobile alert: Heavy traffic — consider delaying departure 30 min.")
        if rain > 2:
            contextual.append("🌧️ Activate wet-weather speed advisory signs.")
        if hour < 6:
            contextual.append("🌙 Low-traffic window: ideal for maintenance or inspections.")
        if confidence and confidence < 60:
            contextual.append("⚠️ Moderate model confidence — verify with live sensor data.")

        urgency = {"Severe": "CRITICAL", "High": "HIGH", "Medium": "NORMAL", "Low": "LOW"}.get(label, "LOW")

        logger.log(self.name, f"Generated {len(immediate)} immediate + {len(contextual)} contextual actions.")
        logger.log(self.name, "Action plan ready.", level="SUCCESS")

        return {
            "congestion_level":   label,
            "immediate_actions":  immediate,
            "contextual_actions": contextual,
            "urgency":            urgency,
        }


class AgentOrchestrator:
    def __init__(self, model, df, fi_df=None):
        self.model  = model
        self.df     = df
        self.fi_df  = fi_df
        self.logger = AgentLog()

        self.data_agent    = DataAgent()
        self.pred_agent    = PredictionAgent(model)
        self.insight_agent = InsightAgent(fi_df)
        self.reco_agent    = RecommendationAgent()

    def run_analysis(self):
        self.logger = AgentLog()
        profile = self.data_agent.run(self.df, self.logger)
        return {"data_profile": profile, "logs": self.logger.logs}

    def run_prediction_pipeline(self, input_features: dict) -> dict:
        self.logger = AgentLog()
        self.logger.log("Orchestrator", "🚀 Starting Traffic Intelligence Pipeline...")

        pred_result = self.pred_agent.run(input_features, self.logger)
        explanation = self.insight_agent.run(pred_result, self.logger)
        action_plan = self.reco_agent.run(pred_result, explanation, self.logger)

        self.logger.log("Orchestrator", "✅ Pipeline complete.")

        return {
            "prediction":  pred_result,
            "explanation": explanation,
            "action_plan": action_plan,
            "logs":        self.logger.logs,
        }

    def run_system_insights(self, peak_data: dict) -> list:
        from insights import generate_system_insights
        return generate_system_insights(peak_data)
