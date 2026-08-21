import os
import sys
import json
import math
import pandas as pd

# Resolve project root and append to sys.path to allow importing uplift module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from uplift.segmentation import assign_uplift_segments
from uplift.metrics import calculate_metrics
from uplift.optimization import optimize_discount_allocation


def write_json(path: str, payload: dict) -> None:
    """Write strict JSON so non-finite model values never reach an API/UI."""
    def assert_finite(value, location="root"):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"Non-finite value at {location}: {value}")
        if isinstance(value, dict):
            for key, child in value.items():
                assert_finite(child, f"{location}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                assert_finite(child, f"{location}[{index}]")

    assert_finite(payload)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, allow_nan=False)



def main():
    print("Generating Uplift & Optimization outputs...")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    predictions_path = os.path.join(project_root, "outputs", "causal_predictions.csv")
    customers_path = os.path.join(project_root, "data", "customers.csv")

    if not os.path.exists(predictions_path):
        raise FileNotFoundError(f"Predictions file not found at: {predictions_path}")
    if not os.path.exists(customers_path):
        raise FileNotFoundError(f"Customers file not found at: {customers_path}")

    pred_df = pd.read_csv(predictions_path)
    cust_df = pd.read_csv(customers_path)

    merged = pd.merge(pred_df, cust_df, on="customer_id")
    if len(pred_df) != len(cust_df) or set(pred_df["customer_id"]) != set(cust_df["customer_id"]):
        raise ValueError("Cannot generate uplift outputs from incomplete prediction coverage.")

    # Segment customers
    # We use baseline_threshold=0.25 based on the true baseline purchase probability distribution
    segmented = assign_uplift_segments(merged, ite_col="ite", baseline_col="baseline_probability", ite_threshold=0.05, baseline_threshold=0.25)

    # Proportions of segments
    segment_shares = segmented["uplift_segment"].value_counts(normalize=True).to_dict()
    segment_counts = segmented["uplift_segment"].value_counts().to_dict()

    # Causal metrics
    metrics = calculate_metrics(segmented, score_col="ite", true_ite_col="true_ite")

    # 1. Save outputs/uplift_results.json
    uplift_results = {
        "segment_shares": {k: float(v) for k, v in segment_shares.items()},
        "segment_counts": {k: int(v) for k, v in segment_counts.items()},
        "metrics": metrics,
    }

    results_path = os.path.join(project_root, "outputs", "uplift_results.json")
    write_json(results_path, uplift_results)
    print(f"Saved: {results_path}")

    # 2. Save outputs/recommendations.json (Default budget cap: ₹1,000,000)
    optimized = optimize_discount_allocation(segmented, budget=1000000.0, method="greedy")
    selected_recs = optimized[optimized["selected"] == 1].copy()

    recs_list = []
    for _, row in selected_recs.iterrows():
        roi = float(row["expected_profit"] / row["expected_cost"]) if row["expected_cost"] > 0 else 0.0
        recs_list.append(
            {
                "customer_id": int(row["customer_id"]),
                "ite": float(row["ite"]),
                "uplift_segment": str(row["uplift_segment"]),
                "expected_conversion": float(row["treatment_probability"]),
                "recommended_discount": float(row["discount_percentage"]),
                "expected_profit": float(row["expected_profit"]),
                "expected_cost": float(row["expected_cost"]),
                "roi": roi,
            }
        )

    recommendations = {
        "budget": 1000000.0,
        "total_recommended_customers": len(recs_list),
        "total_expected_profit": float(selected_recs["expected_profit"].sum()),
        "total_expected_cost": float(selected_recs["expected_cost"].sum()),
        "recommendations": recs_list,
    }

    recs_path = os.path.join(project_root, "outputs", "recommendations.json")
    write_json(recs_path, recommendations)
    print(f"Saved: {recs_path}")

    # 3. Save outputs/scenario_comparison.json
    # Evaluate at multiple budget levels: 25k, 50k, 100k, 250k, 500k, 1M, 2.5M
    budgets = [25000, 50000, 100000, 250000, 500000, 1000000, 2500000]
    scenarios = {}

    for b in budgets:
        opt_b = optimize_discount_allocation(segmented, budget=float(b), method="greedy")
        sel_b = opt_b[opt_b["selected"] == 1]

        # Random targeting baseline simulation
        pos_cost_df = segmented[segmented["discount_cost"] > 0].copy()
        shuffled = pos_cost_df.sample(frac=1, random_state=42).reset_index(drop=True)
        shuffled["cum_cost"] = shuffled["discount_cost"].cumsum()
        sel_rand = shuffled[shuffled["cum_cost"] <= b]

        scenarios[str(b)] = {
            "causal": {
                "customers_targeted": len(sel_b),
                "expected_profit": float(sel_b["expected_profit"].sum()),
                "expected_cost": float(sel_b["expected_cost"].sum()),
                "roi": float(sel_b["expected_profit"].sum() / sel_b["expected_cost"].sum()) if sel_b["expected_cost"].sum() > 0 else 0.0,
            },
            "random": {
                "customers_targeted": len(sel_rand),
                "expected_profit": float((sel_rand["true_ite"] * sel_rand["net_revenue"]).sum()),
                "expected_cost": float(sel_rand["discount_cost"].sum()),
                "roi": float((sel_rand["true_ite"] * sel_rand["net_revenue"]).sum() / sel_rand["discount_cost"].sum()) if sel_rand["discount_cost"].sum() > 0 else 0.0,
            },
        }

    scenarios_path = os.path.join(project_root, "outputs", "scenario_comparison.json")
    write_json(scenarios_path, scenarios)
    print(f"Saved: {scenarios_path}")
    print("Uplift output generation completed successfully.")


if __name__ == "__main__":
    main()
