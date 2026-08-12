"""
EconoCausal - Causal ML Inference / Prediction CLI
"""

import os
import yaml
import joblib
import pandas as pd


def main():
    print("Starting causal predictions generation...")
    
    # 1. Load config
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    paths = config["paths"]
    
    # Resolve relative paths from project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_path = os.path.join(project_root, paths["data_path"])
    model_save_path = os.path.join(project_root, paths["model_path"])
    predictions_save_path = os.path.join(project_root, paths["predictions_path"])
    
    # 2. Load model and preprocessor
    print(f"Loading model artifacts from: {model_save_path}")
    if not os.path.exists(model_save_path):
        raise FileNotFoundError(f"Model file not found at {model_save_path}. Please run train.py first.")
        
    artifacts = joblib.load(model_save_path)
    preprocessor = artifacts["preprocessor"]
    model = artifacts["model"]
    
    # 3. Load dataset and run transform
    print(f"Loading raw data from: {data_path}")
    df = pd.read_csv(data_path)
    
    print("Preprocessing data for inference...")
    X, _, _ = preprocessor.transform(df)
    
    # 4. Predict potential outcomes and ITE
    print("Generating predictions...")
    mu_0, mu_1 = model.predict_potential_outcomes(X)
    ite = model.predict_ite(X)
    
    # 5. Save results to CSV
    results_df = pd.DataFrame({
        "customer_id": df["customer_id"].astype(int),
        "baseline_probability": mu_0,
        "treatment_probability": mu_1,
        "ite": ite
    })
    
    os.makedirs(os.path.dirname(predictions_save_path), exist_ok=True)
    print(f"Saving predictions to: {predictions_save_path}")
    results_df.to_csv(predictions_save_path, index=False)
    
    print("Prediction pipeline executed successfully.")


if __name__ == "__main__":
    main()
