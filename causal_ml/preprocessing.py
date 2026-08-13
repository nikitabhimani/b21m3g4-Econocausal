"""
EconoCausal - Data Preprocessing

Purpose:
    Prepare the EconoCausal synthetic dataset for Double Machine Learning.

Causal variables:
    T = treatment_received
    Y = purchase
    W = observed confounders
    X = additional covariates
"""

from pathlib import Path

import pandas as pd
import yaml


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = PROJECT_ROOT / "data" / "econocausal_dataset.csv"
CONFIG_PATH = PROJECT_ROOT / "causal_ml" / "config.yaml"


# ============================================================
# LOAD CONFIG
# ============================================================

def load_config(config_path=CONFIG_PATH):
    """
    Load and validate config.yaml.
    """

    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    required_keys = [
        "treatment",
        "outcome",
        "confounders",
        "covariates",
        "model"
    ]

    missing_keys = [
        key for key in required_keys
        if key not in config
    ]

    if missing_keys:
        raise ValueError(
            f"Missing keys in config.yaml: {missing_keys}"
        )

    return config


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset(data_path=DATA_PATH):
    """
    Load generated CSV dataset.
    """

    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at: {data_path}"
        )

    df = pd.read_csv(data_path)

    if df.empty:
        raise ValueError("Dataset is empty.")

    return df


# ============================================================
# VALIDATE CONFIG COLUMNS
# ============================================================

def validate_columns(df, config):
    """
    Check that every column specified in config.yaml
    exists in the dataset.
    """

    treatment = config["treatment"]
    outcome = config["outcome"]

    confounders = config["confounders"]
    covariates = config["covariates"]

    required_columns = (
        [treatment]
        + [outcome]
        + confounders
        + covariates
    )

    # Remove duplicates while preserving order
    required_columns = list(dict.fromkeys(required_columns))

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "The following columns are missing from the dataset:\n"
            f"{missing_columns}"
        )


# ============================================================
# VALIDATE TREATMENT
# ============================================================

def validate_treatment(df, treatment_column):
    """
    Treatment must be binary: 0 or 1.
    """

    if df[treatment_column].isna().any():
        raise ValueError(
            f"{treatment_column} contains missing values."
        )

    unique_values = sorted(
        df[treatment_column].unique().tolist()
    )

    if not set(unique_values).issubset({0, 1}):
        raise ValueError(
            f"{treatment_column} must contain only 0/1 values. "
            f"Found: {unique_values}"
        )


# ============================================================
# VALIDATE OUTCOME
# ============================================================

def validate_outcome(df, outcome_column):
    """
    Outcome must be binary: 0 or 1.
    """

    if df[outcome_column].isna().any():
        raise ValueError(
            f"{outcome_column} contains missing values."
        )

    unique_values = sorted(
        df[outcome_column].unique().tolist()
    )

    if not set(unique_values).issubset({0, 1}):
        raise ValueError(
            f"{outcome_column} must contain only 0/1 values. "
            f"Found: {unique_values}"
        )


# ============================================================
# ENCODE CATEGORICAL VARIABLES
# ============================================================

def encode_categorical_features(df):
    """
    One-hot encode categorical variables.

    Currently customer_segment is the main categorical
    variable in the causal model.

    Example:

        customer_segment
        ----------------
        budget
        standard
        premium
        vip

    becomes:

        customer_segment_budget
        customer_segment_standard
        customer_segment_premium
        customer_segment_vip
    """

    df = df.copy()

    categorical_columns = df.select_dtypes(
        include=["object", "category"]
    ).columns.tolist()

    if categorical_columns:
        df = pd.get_dummies(
            df,
            columns=categorical_columns,
            drop_first=False,
            dtype=float
        )

    return df


# ============================================================
# VALIDATE MISSING VALUES
# ============================================================

def validate_missing_values(df):
    """
    Ensure there are no missing values in model data.
    """

    missing = df.isnull().sum()

    missing = missing[missing > 0]

    if not missing.empty:
        raise ValueError(
            "Missing values found in model variables:\n"
            f"{missing.to_dict()}"
        )


# ============================================================
# PREPARE MODEL DATA
# ============================================================

def prepare_model_data(df, config):
    """
    Prepare treatment, outcome, confounders and covariates.

    Returns:
        customer_ids
        treatment
        outcome
        confounders
        covariates
    """

    treatment_column = config["treatment"]
    outcome_column = config["outcome"]

    confounder_columns = list(
        dict.fromkeys(config["confounders"])
    )

    covariate_columns = list(
        dict.fromkeys(config["covariates"])
    )

    # --------------------------------------------------------
    # Customer IDs
    # --------------------------------------------------------

    if "customer_id" not in df.columns:
        raise ValueError(
            "customer_id column not found in dataset."
        )

    customer_ids = df["customer_id"].copy()

    # --------------------------------------------------------
    # Remove overlap between confounders and covariates
    # --------------------------------------------------------

    overlapping_columns = set(confounder_columns).intersection(
        covariate_columns
    )

    if overlapping_columns:
        raise ValueError(
            "The following columns appear in both "
            "confounders and covariates:\n"
            f"{sorted(overlapping_columns)}"
        )

    # --------------------------------------------------------
    # Select only causal model variables
    # --------------------------------------------------------

    model_columns = (
        [treatment_column]
        + [outcome_column]
        + confounder_columns
        + covariate_columns
    )

    # Remove duplicates while preserving order
    model_columns = list(
        dict.fromkeys(model_columns)
    )

    model_df = df[model_columns].copy()

    # --------------------------------------------------------
    # Encode categorical variables
    # --------------------------------------------------------

    model_df = encode_categorical_features(model_df)

    # --------------------------------------------------------
    # Validate missing values
    # --------------------------------------------------------

    validate_missing_values(model_df)

    # --------------------------------------------------------
    # Separate T and Y
    # --------------------------------------------------------

    treatment = model_df[treatment_column].astype(int)

    outcome = model_df[outcome_column].astype(int)

    # --------------------------------------------------------
    # Find encoded confounder columns
    # --------------------------------------------------------

    confounder_features = []

    for column in confounder_columns:

        if column in model_df.columns:
            confounder_features.append(column)

        else:
            encoded_columns = [
                col
                for col in model_df.columns
                if col.startswith(column + "_")
            ]

            confounder_features.extend(
                encoded_columns
            )

    # --------------------------------------------------------
    # Find encoded covariate columns
    # --------------------------------------------------------

    covariate_features = []

    for column in covariate_columns:

        if column in model_df.columns:
            covariate_features.append(column)

        else:
            encoded_columns = [
                col
                for col in model_df.columns
                if col.startswith(column + "_")
            ]

            covariate_features.extend(
                encoded_columns
            )

    # --------------------------------------------------------
    # Create W and X
    # --------------------------------------------------------

    confounders = model_df[
        confounder_features
    ].astype(float)

    covariates = model_df[
        covariate_features
    ].astype(float)

    return {
        "customer_ids": customer_ids,
        "treatment": treatment,
        "outcome": outcome,
        "confounders": confounders,
        "covariates": covariates
    }


# ============================================================
# COMPLETE PREPROCESSING PIPELINE
# ============================================================

def preprocess(
    data_path=DATA_PATH,
    config_path=CONFIG_PATH
):
    """
    Run complete preprocessing pipeline.
    """

    # Load configuration
    config = load_config(config_path)

    # Load dataset
    df = load_dataset(data_path)

    # Validate dataset structure
    validate_columns(df, config)

    # Validate treatment
    validate_treatment(
        df,
        config["treatment"]
    )

    # Validate outcome
    validate_outcome(
        df,
        config["outcome"]
    )

    # Prepare model-ready data
    processed_data = prepare_model_data(
        df,
        config
    )

    return df, config, processed_data


# ============================================================
# TEST PREPROCESSING
# ============================================================

if __name__ == "__main__":

    df, config, data = preprocess()

    print("\nPreprocessing completed successfully!")
    print("=" * 60)

    print(f"Dataset shape: {df.shape}")

    print(
        f"Treatment: "
        f"{config['treatment']}"
    )

    print(
        f"Outcome: "
        f"{config['outcome']}"
    )

    print(
        f"Treatment values: "
        f"{data['treatment'].unique().tolist()}"
    )

    print(
        f"Outcome values: "
        f"{data['outcome'].unique().tolist()}"
    )

    print(
        f"\nConfounder shape: "
        f"{data['confounders'].shape}"
    )

    print(
        f"Covariate shape: "
        f"{data['covariates'].shape}"
    )

    print("\nConfounder columns:")
    for column in data["confounders"].columns:
        print(f"  - {column}")

    print("\nCovariate columns:")
    for column in data["covariates"].columns:
        print(f"  - {column}")

    print("\nPreprocessing test PASSED.")