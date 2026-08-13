"""
EconoCausal - Causal ML Model Training CLI
"""

import os
import json
import yaml
import joblib
import datetime
import pandas as pd

from preprocessing import CausalPreprocessor
from model import CausalModelWrapper


def main():
    print("Starting causal model training...")
    
    # 1. Load config
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    paths = config["paths"]
    features = config["features"]
    model_cfg = config["model"]
    
    # Resolve relative paths from project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_path = os.path.join(project_root, paths["data_path"])
    model_save_path = os.path.join(project_root, paths["model_path"])
    meta_save_path = os.path.join(project_root, "outputs", "model_meta.json")
    
    print(f"Loading raw data from: {data_path}")
    df = pd.read_csv(data_path)
    
    # 2. Preprocessing
    print("Preprocessing dataset...")
    preprocessor = CausalPreprocessor(
        categorical_covariates=features["categorical_covariates"],
        numeric_covariates=features["numeric_covariates"],
        treatment=features["treatment"],
        outcome=features["outcome"]
    )
    
    X, W, Y = preprocessor.fit_transform(df)
    print(f"Preprocessed features shape: {X.shape}")
    
    # 3. Model initialization & training
    hyperparams = model_cfg.get("hyperparameters", {})
    print(f"Training model of type: {model_cfg['type']} (Base estimator: {model_cfg['base_estimator']})...")
    print(f"Hyperparameters: {hyperparams}")
    
    model = CausalModelWrapper(
        model_type=model_cfg["type"],
        base_estimator=model_cfg["base_estimator"],
        seed=model_cfg["seed"],
        hyperparams=hyperparams
    )
    
    model.fit(X, W, Y)
    print("Model training complete.")
    
    # 4. Save artifacts
    os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
    print(f"Saving preprocessor and model to: {model_save_path}")
    joblib.dump({
        "preprocessor": preprocessor,
        "model": model
    }, model_save_path)
    
    # 5. Save model metadata
    print(f"Saving model metadata history to: {meta_save_path}")
    metadata = {
        "model_type": model_cfg["type"],
        "base_estimator": model_cfg["base_estimator"],
        "seed": model_cfg["seed"],
        "hyperparameters": hyperparams,
        "trained_at": datetime.datetime.utcnow().isoformat() + "Z",
        "features": features,
        "preprocessing_warnings": preprocessor.warnings
    }
    with open(meta_save_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    
    print("Training pipeline executed successfully.")


if __name__ == "__main__":
    main()
