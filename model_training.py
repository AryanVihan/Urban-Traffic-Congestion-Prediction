"""
model_training.py
-----------------
Trains and compares 3 models, saves best as model.pkl
Uses permutation importance for reliable feature ranking.
"""

import numpy as np
import pandas as pd
import joblib, time, json, os, warnings
warnings.filterwarnings("ignore")

from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    RandomForestClassifier,
    ExtraTreesClassifier,
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, accuracy_score, classification_report, confusion_matrix
from sklearn.inspection import permutation_importance

from data_processing import full_pipeline, FEATURE_COLS, CONGESTION_LABELS

MODELS = {
    "HistGradientBoosting": HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.08, max_depth=8,
        min_samples_leaf=20, l2_regularization=0.1, random_state=42,
        early_stopping=True, validation_fraction=0.1, n_iter_no_change=20,
    ),
    "RandomForest": RandomForestClassifier(
        n_estimators=300, max_depth=15, min_samples_leaf=10,
        n_jobs=-1, random_state=42, class_weight="balanced",
    ),
    "ExtraTrees": ExtraTreesClassifier(
        n_estimators=300, max_depth=15, min_samples_leaf=10,
        n_jobs=-1, random_state=42, class_weight="balanced",
    ),
}


def train_and_compare(X, y, test_size=0.15, random_state=42):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    print(f"Train: {len(X_train):,} | Test: {len(X_test):,}")

    results, trained_models = {}, {}
    for name, model in MODELS.items():
        print(f"\n▶ Training {name}...")
        t0 = time.time()
        model.fit(X_train, y_train)
        elapsed = time.time() - t0

        y_pred = model.predict(X_test)
        acc    = accuracy_score(y_test, y_pred)
        f1     = f1_score(y_test, y_pred, average="weighted")
        report = classification_report(y_test, y_pred,
                                        target_names=CONGESTION_LABELS, output_dict=True)

        results[name] = {
            "accuracy": round(acc, 4), "f1_weighted": round(f1, 4),
            "train_time_sec": round(elapsed, 1), "report": report,
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        }
        trained_models[name] = model
        print(f"  Accuracy: {acc:.4f} | F1: {f1:.4f} | Time: {elapsed:.1f}s")

    best_name  = max(results, key=lambda k: results[k]["f1_weighted"])
    best_model = trained_models[best_name]
    print(f"\n✅ Best: {best_name} (F1={results[best_name]['f1_weighted']})")
    return best_model, best_name, results, trained_models, X_train, X_test, y_train, y_test


def compute_feature_importance(model, X_test, y_test, feature_names, n_sample=5000):
    """
    Uses permutation importance — works for ALL model types reliably.
    Samples test set for speed.
    """
    print("  Computing permutation importance (this takes ~20s)...")
    rng = np.random.default_rng(42)
    if len(X_test) > n_sample:
        idx     = rng.choice(len(X_test), size=n_sample, replace=False)
        X_s     = X_test.iloc[idx] if hasattr(X_test, 'iloc') else X_test[idx]
        y_s     = y_test[idx]
    else:
        X_s, y_s = X_test, y_test

    result = permutation_importance(model, X_s, y_s,
                                     n_repeats=5, random_state=42,
                                     n_jobs=-1, scoring="f1_weighted")
    fi_df = pd.DataFrame({
        "feature":    feature_names,
        "importance": result.importances_mean,
        "std":        result.importances_std,
    }).sort_values("importance", ascending=False).reset_index(drop=True)

    print(f"  Top 5: {fi_df.head()['feature'].tolist()}")
    return fi_df


def save_artifacts(model, results, fi_df, output_dir="."):
    os.makedirs(output_dir, exist_ok=True)
    joblib.dump(model, os.path.join(output_dir, "model.pkl"))
    print("✅ model.pkl saved")
    fi_df[["feature","importance"]].to_csv(
        os.path.join(output_dir, "feature_importance.csv"), index=False)
    print("✅ feature_importance.csv saved")
    clean = {n: {"accuracy": r["accuracy"], "f1_weighted": r["f1_weighted"],
                 "train_time_sec": r["train_time_sec"]} for n, r in results.items()}
    with open(os.path.join(output_dir, "model_results.json"), "w") as f:
        json.dump(clean, f, indent=2)
    print("✅ model_results.json saved")
    
    # Save full comparison results with confusion matrices and per-class metrics
    full_results = {}
    for n, r in results.items():
        full_results[n] = {
            "accuracy": r["accuracy"],
            "f1_weighted": r["f1_weighted"],
            "train_time_sec": r["train_time_sec"],
            "confusion_matrix": r["confusion_matrix"],
            "classification_report": {k: v for k, v in r["report"].items() 
                                     if k in CONGESTION_LABELS or k in ["accuracy", "macro avg", "weighted avg"]},
        }
    with open(os.path.join(output_dir, "model_comparison.json"), "w") as f:
        json.dump(full_results, f, indent=2)
    print("✅ model_comparison.json saved")


def run_full_training(data_path: str, output_dir: str = "."):
    print("=" * 55)
    print("  TRAFFIC CONGESTION MODEL TRAINING")
    print("=" * 55)

    print("\n[1/4] Data pipeline...")
    df, X, y = full_pipeline(data_path)
    print(f"  {len(df):,} rows | {X.shape[1]} features")

    print("\n[2/4] Training & comparing models...")
    (best_model, best_name, results, trained_models,
     X_train, X_test, y_train, y_test) = train_and_compare(X, y)

    print("\n[3/4] Feature importance (permutation)...")
    fi_df = compute_feature_importance(best_model, X_test, y_test, FEATURE_COLS)

    print("\n[4/4] Saving artifacts...")
    save_artifacts(best_model, results, fi_df, output_dir)

    print("\n✅ TRAINING COMPLETE")
    return best_model, best_name, results, fi_df, df, trained_models


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "Metro_Interstate_Traffic_Volume.csv"
    run_full_training(path, output_dir=os.path.dirname(os.path.abspath(__file__)))
