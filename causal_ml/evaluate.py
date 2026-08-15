"""
causal_ml/evaluate.py

Compares T-Learner vs DML predicted ITE against the dataset's ground-truth true_ite.
Run from inside causal_ml/: python evaluate.py
"""
import os
import yaml
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

from preprocessing import CausalPreprocessor
from model import CausalModelWrapper


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_data(config):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_path = os.path.join(project_root, config["paths"]["data_path"])
    df = pd.read_csv(data_path)
    if "true_ite" not in df.columns:
        raise ValueError("true_ite column not found — cannot evaluate against ground truth.")
    return df


def evaluate_model(model_type, X_train, W_train, Y_train, X_test, true_ite_test,
                    base_estimator, seed, hyperparams):
    model = CausalModelWrapper(
        model_type=model_type,
        base_estimator=base_estimator,
        seed=seed,
        hyperparams=hyperparams,
    )
    model.fit(X_train, W_train, Y_train)
    predicted_ite = model.predict_ite(X_test)

    mae = mean_absolute_error(true_ite_test, predicted_ite)
    corr = np.corrcoef(true_ite_test, predicted_ite)[0, 1]

    return {
        "model_type": model_type,
        "mae": round(mae, 6),
        "correlation_with_ground_truth": round(corr, 4),
    }


def main():
    config = load_config()
    features = config["features"]
    model_cfg = config["model"]

    df = load_data(config)

    preprocessor = CausalPreprocessor(
        categorical_covariates=features["categorical_covariates"],
        numeric_covariates=features["numeric_covariates"],
        treatment=features["treatment"],
        outcome=features["outcome"],
    )
    X, W, Y = preprocessor.fit_transform(df)
    true_ite = df["true_ite"].values

    X_train, X_test, W_train, W_test, Y_train, Y_test, ite_train, ite_test = train_test_split(
        X, W, Y, true_ite, test_size=0.2, random_state=42
    )

    hyperparams = model_cfg.get("hyperparameters", {})
    seed = model_cfg.get("seed", 42)
    base_estimator = model_cfg.get("base_estimator", "gradient_boosting")

    results = []
    for model_type in ["t_learner", "dml"]:
        print(f"\nTraining and evaluating: {model_type}")
        result = evaluate_model(
            model_type, X_train, W_train, Y_train, X_test, ite_test,
            base_estimator, seed, hyperparams,
        )
        results.append(result)
        print(result)

    print("\n=== Summary ===")
    for r in results:
        print(f"{r['model_type']:12s} | MAE: {r['mae']:.6f} | Correlation: {r['correlation_with_ground_truth']:.4f}")


if __name__ == "__main__":
    main()