"""
EconoCausal - Causal Refutation Tests

Purpose:
    Prove that our DML estimate is genuinely causal, not just a
    coincidental correlation or overfitting artifact.

Tests:
    1. Placebo Treatment Test
       Randomly shuffle the treatment column and re-estimate.
       If our model is genuinely capturing a causal effect, the
       estimate on FAKE (shuffled) treatment should collapse close
       to zero. If it doesn't, the model may just be picking up
       noise/overfitting, not a real causal signal.

    2. Random Common Cause Test
       Add a random noise variable as an extra confounder and
       re-estimate. A robust causal estimate should stay roughly
       the same, since a random variable carries no real information.

    3. Data Subset Test
       Re-estimate on a random 80% subset of the data. A robust
       estimate should be similar in magnitude to the full-data
       estimate, not wildly different.
"""

import os
import json
import yaml
import numpy as np
import pandas as pd

from preprocessing import CausalPreprocessor
from model import CausalModelWrapper


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_data(config):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_path = os.path.join(project_root, config["paths"]["data_path"])
    return pd.read_csv(data_path)


def get_preprocessor(config):
    features = config["features"]
    all_features = features.get("covariates", []) + features.get("confounders", [])
    categorical_covariates = ["customer_segment"] if "customer_segment" in all_features else []
    numeric_covariates = [f for f in all_features if f != "customer_segment"]

    return CausalPreprocessor(
        categorical_covariates=categorical_covariates,
        numeric_covariates=numeric_covariates,
        treatment=features["treatment"],
        outcome=features["outcome"],
    )


def fit_and_get_mean_ite(X, W, Y, model_cfg, seed=42):
    """Fit a DML model and return the mean estimated ITE."""
    hyperparams = model_cfg.get("hyperparameters", {})
    model = CausalModelWrapper(
        model_type=model_cfg["type"],
        base_estimator=model_cfg["base_estimator"],
        seed=seed,
        hyperparams=hyperparams,
    )
    model.fit(X, W, Y)
    ite = model.predict_ite(X)
    return float(np.mean(ite))


def placebo_treatment_test(X, W, Y, model_cfg, original_mean_ite, seed=42):
    """
    Refute by replacing the real treatment with a randomly shuffled
    (fake) version. Expect the estimated effect to collapse toward zero.
    """
    print("\nRunning Placebo Treatment Test...")
    rng = np.random.default_rng(seed)
    W_shuffled = W.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    W_shuffled.index = W.index  # keep original index alignment with X, Y

    placebo_mean_ite = fit_and_get_mean_ite(X, W_shuffled, Y, model_cfg, seed=seed)

    # "Passes" if the placebo effect is small relative to the original effect.
    passed = abs(placebo_mean_ite) < 0.5 * abs(original_mean_ite)

    result = {
        "test": "placebo_treatment",
        "original_mean_ite": original_mean_ite,
        "placebo_mean_ite": placebo_mean_ite,
        "passed": bool(passed),
        "interpretation": (
            "Placebo effect is small relative to original estimate — "
            "supports that the original estimate reflects a real signal."
            if passed else
            "Placebo effect is not much smaller than the original estimate — "
            "this is a WARNING sign the model may be picking up noise."
        ),
    }
    print(f"  Original mean ITE: {original_mean_ite:.6f}")
    print(f"  Placebo mean ITE:  {placebo_mean_ite:.6f}")
    print(f"  Passed: {passed}")
    return result


def random_common_cause_test(X, W, Y, model_cfg, original_mean_ite, seed=42):
    """
    Refute by adding a random noise column as an extra covariate.
    Expect the estimate to stay roughly the same.
    """
    print("\nRunning Random Common Cause Test...")
    rng = np.random.default_rng(seed)
    X_with_noise = X.copy()
    X_with_noise["random_noise"] = rng.normal(0, 1, size=len(X_with_noise))

    noisy_mean_ite = fit_and_get_mean_ite(X_with_noise, W, Y, model_cfg, seed=seed)

    # "Passes" if the estimate doesn't change by more than ~20%.
    if original_mean_ite != 0:
        pct_change = abs(noisy_mean_ite - original_mean_ite) / abs(original_mean_ite)
    else:
        pct_change = abs(noisy_mean_ite)
    passed = pct_change < 0.20

    result = {
        "test": "random_common_cause",
        "original_mean_ite": original_mean_ite,
        "noisy_mean_ite": noisy_mean_ite,
        "percent_change": float(pct_change),
        "passed": bool(passed),
        "interpretation": (
            "Estimate is stable after adding random noise — supports robustness."
            if passed else
            "Estimate changed substantially after adding random noise — "
            "this is a WARNING sign of instability."
        ),
    }
    print(f"  Original mean ITE: {original_mean_ite:.6f}")
    print(f"  Noisy mean ITE:    {noisy_mean_ite:.6f}")
    print(f"  Percent change:    {pct_change:.2%}")
    print(f"  Passed: {passed}")
    return result


def data_subset_test(df, config, model_cfg, original_mean_ite, seed=42, frac=0.8):
    """
    Refute by re-estimating on a random subset of the data.
    Expect a similar magnitude estimate.
    """
    print("\nRunning Data Subset Test...")
    subset_df = df.sample(frac=frac, random_state=seed).reset_index(drop=True)

    preprocessor = get_preprocessor(config)
    X_sub, W_sub, Y_sub = preprocessor.fit_transform(subset_df)

    subset_mean_ite = fit_and_get_mean_ite(X_sub, W_sub, Y_sub, model_cfg, seed=seed)

    if original_mean_ite != 0:
        pct_change = abs(subset_mean_ite - original_mean_ite) / abs(original_mean_ite)
    else:
        pct_change = abs(subset_mean_ite)
    passed = pct_change < 0.20

    result = {
        "test": "data_subset",
        "subset_fraction": frac,
        "original_mean_ite": original_mean_ite,
        "subset_mean_ite": subset_mean_ite,
        "percent_change": float(pct_change),
        "passed": bool(passed),
        "interpretation": (
            "Estimate is stable on a data subset — supports robustness."
            if passed else
            "Estimate changed substantially on a data subset — "
            "this is a WARNING sign of instability."
        ),
    }
    print(f"  Original mean ITE: {original_mean_ite:.6f}")
    print(f"  Subset mean ITE:   {subset_mean_ite:.6f}")
    print(f"  Percent change:    {pct_change:.2%}")
    print(f"  Passed: {passed}")
    return result


def main():
    config = load_config()
    model_cfg = config["model"]
    seed = model_cfg.get("seed", 42)

    df = load_data(config)
    preprocessor = get_preprocessor(config)
    X, W, Y = preprocessor.fit_transform(df)

    print("Fitting original model to get baseline mean ITE...")
    original_mean_ite = fit_and_get_mean_ite(X, W, Y, model_cfg, seed=seed)
    print(f"Original mean ITE: {original_mean_ite:.6f}")

    results = []
    results.append(placebo_treatment_test(X, W, Y, model_cfg, original_mean_ite, seed=seed))
    results.append(random_common_cause_test(X, W, Y, model_cfg, original_mean_ite, seed=seed))
    results.append(data_subset_test(df, config, model_cfg, original_mean_ite, seed=seed))

    all_passed = all(r["passed"] for r in results)

    report = {
        "original_mean_ite": original_mean_ite,
        "tests": results,
        "all_tests_passed": bool(all_passed),
    }

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    report_path = os.path.join(project_root, "outputs", "refutation_report.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    print("\n" + "=" * 50)
    print("Refutation Test Summary:")
    print("=" * 50)
    for r in results:
        status = "PASS" if r["passed"] else "WARNING"
        print(f"  [{status}] {r['test']}")
    print(f"\nAll tests passed: {all_passed}")
    print(f"Report saved to: {report_path}")
    print("=" * 50)


if __name__ == "__main__":
    main()