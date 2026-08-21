"""
EconoCausal - Model Diagnostics and Causal Summary CLI
"""

import os
import json
import yaml
import numpy as np
import pandas as pd


def compute_qini_curve(df, sort_col):
    """
    Computes Qini curve coordinates.
    df must contain columns 'treatment_received', 'purchase'.
    Returns array of cumulative Qini values.
    """
    sorted_df = df.sort_values(by=sort_col, ascending=False).reset_index(drop=True)

    # Cumulative counts and purchases
    sorted_df['treated'] = (sorted_df['treatment_received'] == 1).astype(int)
    sorted_df['control'] = (sorted_df['treatment_received'] == 0).astype(int)

    sorted_df['y_treated'] = (sorted_df['treated'] & sorted_df['purchase']).astype(int)
    sorted_df['y_control'] = (sorted_df['control'] & sorted_df['purchase']).astype(int)

    cum_treated = sorted_df['treated'].cumsum()
    cum_control = sorted_df['control'].cumsum()
    cum_y_treated = sorted_df['y_treated'].cumsum()
    cum_y_control = sorted_df['y_control'].cumsum()

    total_treated = sorted_df['treated'].sum()
    total_control = sorted_df['control'].sum()

    ratio = total_treated / total_control if total_control > 0 else 1.0

    # Qini value: cum_y_treated - cum_y_control * ratio
    qini_vals = cum_y_treated - cum_y_control * ratio
    return qini_vals.values


def compute_area_under_curve(curve):
    """Computes area under a curve using simple sum / trapezoid rule."""
    n = len(curve)
    if n <= 1:
        return 0.0
    return float(np.sum(curve) / n)


def main():
    print("Starting causal diagnostics generation...")

    # 1. Load config
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    paths = config["paths"]

    # Resolve relative paths from project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_path = os.path.join(project_root, paths["data_path"])
    predictions_path = os.path.join(project_root, paths["predictions_path"])
    summary_save_path = os.path.join(project_root, paths["summary_path"])
    meta_path = os.path.join(project_root, "outputs", "model_meta.json")

    # 2. Load predictions and raw data
    print(f"Loading predictions from: {predictions_path}")
    if not os.path.exists(predictions_path):
        raise FileNotFoundError(f"Predictions file not found at {predictions_path}. Please run predict.py first.")

    pred_df = pd.read_csv(predictions_path)

    print(f"Loading raw data from: {data_path}")
    raw_df = pd.read_csv(data_path)

    if raw_df["customer_id"].duplicated().any() or pred_df["customer_id"].duplicated().any():
        raise ValueError("Customer IDs must be unique in both input and prediction data.")
    if len(pred_df) != len(raw_df) or set(pred_df["customer_id"]) != set(raw_df["customer_id"]):
        missing = sorted(set(raw_df["customer_id"]) - set(pred_df["customer_id"]))
        extra = sorted(set(pred_df["customer_id"]) - set(raw_df["customer_id"]))
        raise ValueError(
            f"Prediction coverage mismatch: missing={missing[:10]}, extra={extra[:10]}"
        )

    # 3. Merge for evaluation
    merged = pd.merge(pred_df, raw_df, on="customer_id")

    # 4. Compute error metrics
    pred_ite = merged["ite"].values
    true_ite = merged["true_ite"].values

    mae = float(np.mean(np.abs(pred_ite - true_ite)))
    rmse = float(np.sqrt(np.mean((pred_ite - true_ite) ** 2)))

    corr_matrix = np.corrcoef(pred_ite, true_ite)
    correlation = float(corr_matrix[0, 1]) if not np.isnan(corr_matrix[0, 1]) else 0.0

    # 5. Compute Qini / AUUC metrics
    print("Computing Qini curves and Area Under Causal Curves...")
    qini_model = compute_qini_curve(merged, "ite")

    # Random targeting Qini (linear interpolation from 0 to final Qini value)
    n_samples = len(merged)
    qini_random = np.linspace(0, qini_model[-1], n_samples)

    # Perfect targeting Qini (sorted by true_ite)
    qini_perfect = compute_qini_curve(merged, "true_ite")

    # Compute areas
    area_model = compute_area_under_curve(qini_model)
    area_random = compute_area_under_curve(qini_random)
    area_perfect = compute_area_under_curve(qini_perfect)

    # Qini coefficient (normalized area)
    denominator = (area_perfect - area_random)
    qini_coefficient = float((area_model - area_random) / denominator) if denominator != 0 else 0.0

    # 6. Aggregate causal statistics
    summary = {
        "average_ite": float(np.mean(pred_ite)),
        "median_ite": float(np.median(pred_ite)),
        "positive_ite_share": float(np.mean(pred_ite > 0)),
        "top_positive_ite": float(np.max(pred_ite)),
        "top_negative_ite": float(np.min(pred_ite)),
        "mae": mae,
        "rmse": rmse,
        "correlation": correlation,
        "qini_coefficient": qini_coefficient,
        "n_customers": int(len(merged))
    }

    # 7. Save causal summary
    os.makedirs(os.path.dirname(summary_save_path), exist_ok=True)
    print(f"Saving summary to: {summary_save_path}")
    with open(summary_save_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)

    # 8. Append metrics to model metadata history registry
    if os.path.exists(meta_path):
        print(f"Updating model metadata history registry at: {meta_path}")
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        metadata["evaluation_metrics"] = {
            "mae": mae,
            "rmse": rmse,
            "correlation": correlation,
            "qini_coefficient": qini_coefficient
        }
        metadata["aggregate_estimates"] = {
            "average_ite": summary["average_ite"],
            "median_ite": summary["median_ite"],
            "positive_ite_share": summary["positive_ite_share"]
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)

    print("\n" + "=" * 50)
    print("Causal Model Diagnostic Report:")
    print("=" * 50)
    print(f"Mean Absolute Error (MAE) : {mae:.6f}")
    print(f"Root Mean Squared Error    : {rmse:.6f}")
    print(f"Correlation (Pred vs True) : {correlation:.4%}")
    print(f"Normalized Qini Coefficient: {qini_coefficient:.4f}")
    print(f"Average Estimated ITE      : {summary['average_ite']:.6f}")
    print(f"Positive ITE share         : {summary['positive_ite_share']:.2%}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
