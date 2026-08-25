"""
EconoCausal - Data Drift Detector

Purpose:
    Compares the newly uploaded dataset against a baseline dataset (customers_export.csv)
    using Kolmogorov-Smirnov (KS) tests and the Population Stability Index (PSI) to
    identify changes in customer features that may necessitate model retraining.
"""

import os
import json
import numpy as np
import pandas as pd
from scipy import stats

def calculate_psi(baseline, target, num_bins=10):
    """Calculate the Population Stability Index (PSI) between baseline and target distributions."""
    # Compute quantiles based on baseline to create bins
    quantiles = np.linspace(0, 100, num_bins + 1)
    bins = np.percentile(baseline, quantiles)
    bins = np.unique(bins) # Deduplicate for uniform datasets
    
    if len(bins) < 2:
        return 0.0

    # Get counts for each bin
    baseline_counts, _ = np.histogram(baseline, bins=bins)
    target_counts, _ = np.histogram(target, bins=bins)

    # Convert counts to percentages
    baseline_props = baseline_counts / len(baseline)
    target_props = target_counts / len(target)

    # Epsilon adjustment to avoid log(0) or division by zero
    eps = 1e-4
    baseline_props = np.where(baseline_props == 0, eps, baseline_props)
    target_props = np.where(target_props == 0, eps, target_props)

    # Calculate PSI
    psi_value = np.sum((target_props - baseline_props) * np.log(target_props / baseline_props))
    return float(psi_value)

def detect_drift(baseline_path, target_path):
    """Compare baseline and target datasets to detect distribution drift."""
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"Baseline dataset not found at {baseline_path}")
    if not os.path.exists(target_path):
        raise FileNotFoundError(f"Target dataset not found at {target_path}")

    df_base = pd.read_csv(baseline_path)
    df_target = pd.read_csv(target_path)

    features = [
        "age", "income", "avg_order_value", "historical_orders", 
        "website_visits", "days_since_last_purchase"
    ]
    
    # Filter for features that exist in both datasets
    features = [f for f in features if f in df_base.columns and f in df_target.columns]

    drift_details = {}
    overall_status = "Stable"
    max_psi = 0.0

    for col in features:
        base_vals = df_base[col].dropna().values
        target_vals = df_target[col].dropna().values

        if len(base_vals) == 0 or len(target_vals) == 0:
            continue

        # Kolmogorov-Smirnov test
        ks_stat, ks_pval = stats.ks_2samp(base_vals, target_vals)
        
        # Population Stability Index
        psi = calculate_psi(base_vals, target_vals)
        max_psi = max(max_psi, psi)

        # Interpret PSI drift level
        if psi >= 0.25:
            status = "Significant Drift"
        elif psi >= 0.10:
            status = "Moderate Drift"
        else:
            status = "Stable"

        drift_details[col] = {
            "ks_statistic": float(ks_stat),
            "p_value": float(ks_pval),
            "psi": float(psi),
            "status": status,
            "drift_detected": bool(ks_pval < 0.05 or psi >= 0.10)
        }

    # Determine overall status based on maximum PSI
    if max_psi >= 0.25:
        overall_status = "Significant Drift"
    elif max_psi >= 0.10:
        overall_status = "Moderate Drift"
    else:
        overall_status = "Stable"

    report = {
        "overall_status": overall_status,
        "max_psi": float(max_psi),
        "drift_by_feature": drift_details,
        "baseline_record_count": len(df_base),
        "target_record_count": len(df_target),
        "needs_retraining": bool(overall_status in ["Moderate Drift", "Significant Drift"])
    }

    return report

def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    baseline_path = os.path.join(project_root, "data", "customers_export.csv")
    target_path = os.path.join(project_root, "data", "customers.csv")
    
    # If the active file customers.csv doesn't exist, fallback to econocausal_dataset.csv
    if not os.path.exists(target_path):
        target_path = os.path.join(project_root, "data", "econocausal_dataset.csv")

    try:
        report = detect_drift(baseline_path, target_path)
        output_path = os.path.join(project_root, "outputs", "drift_report.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)
        print(f"Drift detection run completed. Status: {report['overall_status']} (Max PSI: {report['max_psi']:.4f})")
        print(f"Report saved to: {output_path}")
    except Exception as e:
        print(f"Error during drift detection: {str(e)}")

if __name__ == "__main__":
    main()
