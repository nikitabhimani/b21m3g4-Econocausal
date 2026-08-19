from __future__ import annotations

from pathlib import Path
import pandas as pd

from .data_service import load_customer_data
from uplift.segmentation import assign_uplift_segments

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PREDICTIONS_PATH = PROJECT_ROOT / "outputs" / "causal_predictions.csv"


def build_recommendations(budget: float, limit: int = 25, segment: str | None = None) -> dict:
    if PREDICTIONS_PATH.exists():
        pred_df = pd.read_csv(PREDICTIONS_PATH)
        df = load_customer_data()
        # Drop true_ite to use the predicted one from the ML pipeline
        df = df.drop(columns=["true_ite"], errors="ignore")
        # Merge both ite and baseline_probability from pred_df
        df = pd.merge(df, pred_df[["customer_id", "ite", "baseline_probability"]], on="customer_id")
        df = df.rename(columns={"ite": "true_ite"})
        # Assign uplift segments (ite threshold 0.05, baseline threshold 0.25 to match output generator)
        df = assign_uplift_segments(df, ite_col="true_ite", baseline_col="baseline_probability", ite_threshold=0.05, baseline_threshold=0.25)
    else:
        df = load_customer_data()
        df = assign_uplift_segments(df, ite_col="true_ite", baseline_col="true_baseline_purchase_probability", ite_threshold=0.05, baseline_threshold=0.25)

    scored = df[["customer_id", "true_ite", "discount_cost", "net_revenue", "uplift_segment"]].copy()
    scored["expected_profit"] = scored["true_ite"] * scored["net_revenue"]
    scored["expected_cost"] = scored["discount_cost"]

    if segment and segment != "all":
        scored = scored[scored["uplift_segment"] == segment]

    scored = scored.sort_values("expected_profit", ascending=False)
    scored = scored.head(limit)

    total_expected_profit = float(scored["expected_profit"].sum())
    total_expected_cost = float(scored["expected_cost"].sum())

    recommendations = []
    for _, row in scored.iterrows():
        recommendations.append(
            {
                "customer_id": int(row["customer_id"]),
                "predicted_ite": float(row["true_ite"]),
                "recommended_discount": 0.1,
                "expected_profit": float(row["expected_profit"]),
                "expected_cost": float(row["expected_cost"]),
                "uplift_segment": str(row["uplift_segment"]),
            }
        )

    return {
        "budget": float(budget),
        "total_recommended_customers": len(recommendations),
        "total_expected_profit": total_expected_profit,
        "total_expected_cost": total_expected_cost,
        "recommendations": recommendations,
    }

