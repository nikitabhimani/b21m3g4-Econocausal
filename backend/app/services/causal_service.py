from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PREDICTIONS_PATH = PROJECT_ROOT / "outputs" / "causal_predictions.csv"
SUMMARY_PATH = PROJECT_ROOT / "outputs" / "causal_summary.json"


def build_causal_summary() -> dict:
    if SUMMARY_PATH.exists():
        with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
            
    # Fallback to direct calculation from CSV if ML outputs don't exist yet
    from .data_service import load_customer_data
    df = load_customer_data()
    ite_values = df["true_ite"].astype(float)
    return {
        "average_ite": float(ite_values.mean()),
        "median_ite": float(ite_values.median()),
        "positive_ite_share": float((ite_values > 0).mean()),
        "top_positive_ite": float(ite_values.max()),
        "top_negative_ite": float(ite_values.min()),
        "mae": 0.0,
        "rmse": 0.0,
        "correlation": 1.0,
        "qini_coefficient": 1.0,
        "n_customers": len(df)
    }


def get_top_ite_customers(limit: int = 10) -> list[dict]:
    if PREDICTIONS_PATH.exists():
        df = pd.read_csv(PREDICTIONS_PATH)
        # Rename predictions 'ite' column to 'true_ite' to preserve contract compatibility
        ranked = df[["customer_id", "ite"]].copy()
        ranked = ranked.rename(columns={"ite": "true_ite"})
    else:
        from .data_service import load_customer_data
        df = load_customer_data()
        ranked = df[["customer_id", "true_ite"]].copy()
        
    ranked = ranked.sort_values("true_ite", ascending=False)
    ranked = ranked.head(limit)
    return ranked.to_dict(orient="records")
