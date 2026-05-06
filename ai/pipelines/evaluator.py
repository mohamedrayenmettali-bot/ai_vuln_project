import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, classification_report

# Setup paths for local imports
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.config import TARGET_COL, DEFECTDOJO_CSV, DATA_DIR
from ai.pipelines.advanced_trainer import load_artifacts, predict
from ai.pipelines.data_loader import load_defectdojo, summarize
from ai.utils.ml_utils import score_to_severity

def main():
    print("\n--- AI Risk Model Evaluator ---")
    
    # 1. Load Artifacts
    print("[Evaluator] Loading model artifacts...")
    try:
        models, feature_cols, selector, pca, nlp_model, scaler = load_artifacts()
    except FileNotFoundError:
        print("[Error] Model artifacts not found. Please train the model first.")
        return

    # 2. Load Validation Data
    validation_csv = str(DEFECTDOJO_CSV)
    print(f"[Evaluator] Loading validation data from: {validation_csv}")
    
    # We load it twice: once via data_loader (for features) and once normally (to keep metadata)
    df_features = load_defectdojo(validation_csv)
    df_original = pd.read_csv(validation_csv)
    
    summarize(df_features, "Validation Set (Features Only)")

    # 3. Prepare for Inference
    # We need 'description' if PCA is enabled
    # In features.csv, 'title' is used as a proxy for description if 'description' is missing
    descriptions = []
    if "description" in df_original.columns:
        descriptions = df_original["description"].fillna("").astype(str).tolist()
    elif "title" in df_original.columns:
        print("[Evaluator] 'description' column missing, using 'title' for NLP.")
        descriptions = df_original["title"].fillna("").astype(str).tolist()
    else:
        print("[Evaluator] No text columns found for NLP.")
        descriptions = [""] * len(df_features)

    # 4. Run Inference
    print(f"[Evaluator] Running batch inference on {len(df_features)} findings...")
    y_pred = predict(descriptions, df_features)
    
    # 5. Calculate Metrics
    y_true = df_features[TARGET_COL]
    
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred)
    
    print("\n" + "="*50)
    print(f"  PERFORMANCE METRICS (vs {TARGET_COL})")
    print("="*50)
    print(f"  MAE  : {mae:.4f}")
    print(f"  RMSE : {rmse:.4f}")
    print(f"  R2   : {r2:.4f}")
    print("="*50)

    # 6. Severity Classification Report
    pred_sev = [str(score_to_severity(s)) for s in y_pred]
    true_sev = [str(score_to_severity(s)) for s in y_true]
    
    print("\n[Evaluator] Test Set Severity Distribution (Actual):")
    print(pd.Series(true_sev).value_counts().to_string())
    
    print("\n[Evaluator] Test Set Severity Distribution (Predicted):")
    print(pd.Series(pred_sev).value_counts().to_string())

    print("\n[Evaluator] Severity Classification Report:")
    print(classification_report(true_sev, pred_sev, zero_division=0))

    # 7. Comparative Analysis & Export
    results_df = df_original.copy()
    results_df["new_ai_risk_score"] = np.round(y_pred, 3)
    results_df["new_ai_severity"] = pred_sev
    
    # Calculate delta if legacy scores exist
    if "ai_risk_score" in results_df.columns:
        results_df["risk_score_delta"] = np.round(results_df["new_ai_risk_score"] - results_df["ai_risk_score"], 3)
        avg_delta = results_df["risk_score_delta"].abs().mean()
        print(f"\n[Evaluator] Comparison with legacy scores (ai_risk_score):")
        print(f"  Average Absolute Delta: {avg_delta:.4f}")

    output_path = DATA_DIR / "evaluation_results.csv"
    results_df.to_csv(output_path, index=False)
    print(f"\n[Evaluator] Results exported to: {output_path}")

if __name__ == "__main__":
    main()
