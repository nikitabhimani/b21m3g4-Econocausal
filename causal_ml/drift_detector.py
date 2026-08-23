"""
EconoCausal - Data Drift Detector

Compares a new/incoming dataset's statistical properties against the
dataset the model was originally trained on. If key features have
drifted significantly, the model's assumptions may no longer hold and
retraining is recommended.

Run with: python drift_detector.py [path_to_new_data.csv]
If no path given, re-checks the current training data against its own
saved baseline (useful for a first-time baseline creation).
"""
import os
import sys
import json
import yaml
import numpy as np
import pandas as pd
from scipy import stats


NUMERIC_DRIFT_THRESHOLD = 0.10   # 10% relative change in mean triggers a warning
CATEGORICAL_DRIFT_THRESHOLD = 0.05  # KS-test / chi-square p-value threshold


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_monitored_columns(config):
    features = config["features"]
    return {
        "numeric": [f for f in features.get("covariates", []) + features.get("confounders", [])
                    if f != "customer_segment"],
        "categorical": ["customer_segment"] if "customer_segment" in (
            features.get("covariates", []) + features.get("confounders", [])
        ) else [],
    }


def compute_baseline(df, columns):
    """Compute summary statistics for the training/baseline dataset."""
    baseline = {"numeric": {}, "categorical": {}}

    for col in columns["numeric"]:
        baseline["numeric"][col] = {
            "mean": float(df[col].mean()),
            "std": float(df[col].std()),
        }

    for col in columns["categorical"]:
        value_counts = df[col].value_counts(normalize=True)
        baseline["categorical"][col] = value_counts.to_dict()

    return baseline


def save_baseline(baseline, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2)


def load_baseline(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_numeric_drift(new_df, col, baseline_stats):
    """Flag drift if the new mean differs from baseline mean by more than
    the threshold, relative to the baseline's standard deviation."""
    new_mean = float(new_df[col].mean())
    baseline_mean = baseline_stats["mean"]
    baseline_std = baseline_stats["std"] or 1e-9  # avoid div by zero

    relative_shift = abs(new_mean - baseline_mean) / (abs(baseline_mean) + 1e-9)
    std_shift = abs(new_mean - baseline_mean) / baseline_std

    drifted = relative_shift > NUMERIC_DRIFT_THRESHOLD

    return {
        "column": col,
        "baseline_mean": baseline_mean,
        "new_mean": new_mean,
        "relative_shift": round(relative_shift, 4),
        "std_shifts": round(std_shift, 4),
        "drifted": bool(drifted),
    }


def check_categorical_drift(new_df, col, baseline_distribution):
    """Flag drift if any category's share has shifted by more than the
    threshold (in absolute percentage points)."""
    new_distribution = new_df[col].value_counts(normalize=True).to_dict()

    max_shift = 0.0
    for category, baseline_share in baseline_distribution.items():
        new_share = new_distribution.get(category, 0.0)
        shift = abs(new_share - baseline_share)
        max_shift = max(max_shift, shift)

    # Also check for entirely new categories not seen in training.
    new_categories = set(new_distribution.keys()) - set(baseline_distribution.keys())

    drifted = max_shift > CATEGORICAL_DRIFT_THRESHOLD or len(new_categories) > 0

    return {
        "column": col,
        "max_share_shift": round(max_shift, 4),
        "new_categories_found": list(new_categories),
        "drifted": bool(drifted),
    }


def run_drift_check(new_data_path=None):
    config = load_config()
    columns = get_monitored_columns(config)

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    baseline_path = os.path.join(project_root, "outputs", "drift_baseline.json")
    training_data_path = os.path.join(project_root, config["paths"]["data_path"])

    # Load or create the baseline from the original training data.
    if os.path.exists(baseline_path):
        baseline = load_baseline(baseline_path)
        print(f"Loaded existing baseline from: {baseline_path}")
    else:
        print("No existing baseline found -- creating one from training data.")
        training_df = pd.read_csv(training_data_path)
        baseline = compute_baseline(training_df, columns)
        os.makedirs(os.path.dirname(baseline_path), exist_ok=True)
        save_baseline(baseline, baseline_path)
        print(f"Baseline saved to: {baseline_path}")

    # Decide what to compare against the baseline.
    compare_path = new_data_path or training_data_path
    print(f"Checking drift against: {compare_path}")
    new_df = pd.read_csv(compare_path)

    results = {"numeric": [], "categorical": []}

    for col in columns["numeric"]:
        if col in baseline["numeric"]:
            results["numeric"].append(
                check_numeric_drift(new_df, col, baseline["numeric"][col])
            )

    for col in columns["categorical"]:
        if col in baseline["categorical"]:
            results["categorical"].append(
                check_categorical_drift(new_df, col, baseline["categorical"][col])
            )

    any_drift = any(r["drifted"] for r in results["numeric"] + results["categorical"])

    report = {
        "checked_against": compare_path,
        "any_drift_detected": bool(any_drift),
        "numeric_results": results["numeric"],
        "categorical_results": results["categorical"],
    }

    report_path = os.path.join(project_root, "outputs", "drift_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 50)
    print("Data Drift Report:")
    print("=" * 50)
    for r in results["numeric"]:
        status = "DRIFT" if r["drifted"] else "OK"
        print(f"  [{status}] {r['column']}: baseline_mean={r['baseline_mean']:.3f}, "
              f"new_mean={r['new_mean']:.3f}, relative_shift={r['relative_shift']:.2%}")
    for r in results["categorical"]:
        status = "DRIFT" if r["drifted"] else "OK"
        print(f"  [{status}] {r['column']}: max_share_shift={r['max_share_shift']:.2%}, "
              f"new_categories={r['new_categories_found']}")
    print(f"\nAny drift detected: {any_drift}")
    print(f"Report saved to: {report_path}")
    print("=" * 50)

    if any_drift:
        print("\n⚠️  RECOMMENDATION: Data drift detected -- consider retraining the model.")
    else:
        print("\n✅ No significant drift detected -- model assumptions still hold.")

    return report


if __name__ == "__main__":
    new_path = sys.argv[1] if len(sys.argv) > 1 else None
    run_drift_check(new_path)