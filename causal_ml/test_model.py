"""
EconoCausal - Unit Tests for Causal ML Config, Preprocessing, and Model

Run with: pytest causal_ml/test_model.py -v
(from repo root, or `pytest test_model.py -v` from inside causal_ml/)
"""
import os
import yaml
import numpy as np
import pandas as pd
import pytest

from preprocessing import CausalPreprocessor
from model import CausalModelWrapper, _get_covariate_cols


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

@pytest.fixture(scope="module")
def config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def small_sample_df():
    """A small synthetic dataset with the exact schema the real pipeline expects."""
    rng = np.random.default_rng(42)
    n = 200
    return pd.DataFrame({
        "customer_id": np.arange(1, n + 1),
        "age": rng.integers(18, 75, n),
        "tenure_months": rng.integers(1, 120, n),
        "customer_segment": rng.choice(["budget", "standard", "premium", "vip"], n),
        "historical_orders": rng.integers(0, 20, n),
        "historical_revenue": rng.uniform(0, 5000, n),
        "avg_order_value": rng.uniform(20, 500, n),
        "days_since_last_purchase": rng.integers(1, 180, n),
        "website_visits": rng.integers(0, 30, n),
        "email_opens": rng.integers(0, 20, n),
        "email_clicks": rng.integers(0, 10, n),
        "previous_campaign_response": rng.integers(0, 2, n),
        "treatment_received": rng.integers(0, 2, n),
        "purchase": rng.integers(0, 2, n),
    })


@pytest.fixture(scope="module")
def preprocessed(config, small_sample_df):
    features = config["features"]
    all_features = features.get("covariates", []) + features.get("confounders", [])
    categorical_covariates = ["customer_segment"] if "customer_segment" in all_features else []
    numeric_covariates = [f for f in all_features if f != "customer_segment"]

    preprocessor = CausalPreprocessor(
        categorical_covariates=categorical_covariates,
        numeric_covariates=numeric_covariates,
        treatment=features["treatment"],
        outcome=features["outcome"],
    )
    X, W, Y = preprocessor.fit_transform(small_sample_df)
    return X, W, Y


# ---------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------

def test_config_has_required_keys(config):
    assert "features" in config
    assert "model" in config
    assert "paths" in config


def test_config_treatment_and_outcome_defined(config):
    features = config["features"]
    assert features["treatment"] == "treatment_received"
    assert features["outcome"] == "purchase"


def test_config_no_duplicate_confounders(config):
    confounders = config["features"]["confounders"]
    assert len(confounders) == len(set(confounders)), (
        f"Duplicate entries found in confounders list: {confounders}"
    )


def test_config_no_overlap_between_treatment_outcome_and_features(config):
    features = config["features"]
    all_features = set(features.get("covariates", []) + features.get("confounders", []))
    assert features["treatment"] not in all_features
    assert features["outcome"] not in all_features


# ---------------------------------------------------------------------
# Preprocessing tests
# ---------------------------------------------------------------------

def test_preprocessing_output_shapes(preprocessed, small_sample_df):
    X, W, Y = preprocessed
    n = len(small_sample_df)
    assert len(X) == n
    assert len(W) == n
    assert len(Y) == n


def test_preprocessing_treatment_is_binary(preprocessed):
    _, W, _ = preprocessed
    assert set(W.unique()).issubset({0, 1})


def test_preprocessing_outcome_is_binary(preprocessed):
    _, _, Y = preprocessed
    assert set(Y.unique()).issubset({0, 1})


def test_preprocessing_no_nan_in_features(preprocessed):
    X, _, _ = preprocessed
    assert not X.isnull().any().any(), "NaN values found in preprocessed features"


# ---------------------------------------------------------------------
# Covariate-selection helper tests (guards against Bug #3's regression)
# ---------------------------------------------------------------------

def test_covariate_cols_includes_heterogeneity_drivers(preprocessed):
    X, _, _ = preprocessed
    cols = _get_covariate_cols(X)
    # These must be present or DML's heterogeneity estimate silently
    # collapses (see Bug #3 in project history).
    assert "age" in cols
    assert "tenure_months" in cols
    assert any(c.startswith("customer_segment") for c in cols)


# ---------------------------------------------------------------------
# Model smoke tests (T-Learner only -- fast, no EconML dependency needed)
# ---------------------------------------------------------------------

def test_t_learner_fits_and_predicts(preprocessed):
    X, W, Y = preprocessed
    model = CausalModelWrapper(model_type="t_learner", base_estimator="gradient_boosting", seed=42)
    model.fit(X, W, Y)
    ite = model.predict_ite(X)
    assert len(ite) == len(X)
    assert not np.isnan(ite).any(), "T-Learner produced NaN ITE values"


def test_t_learner_predict_potential_outcomes_no_nan(preprocessed):
    X, W, Y = preprocessed
    model = CausalModelWrapper(model_type="t_learner", base_estimator="gradient_boosting", seed=42)
    model.fit(X, W, Y)
    mu_0, mu_1 = model.predict_potential_outcomes(X)
    assert not np.isnan(mu_0).any()
    assert not np.isnan(mu_1).any()


def test_dml_predict_potential_outcomes_no_nan(preprocessed):
    """Regression test for Bug #4: DML's baseline/treatment probability
    used to be NaN for every row before the auxiliary outcome_model fix."""
    X, W, Y = preprocessed
    model = CausalModelWrapper(model_type="dml", base_estimator="lightgbm", seed=42)
    model.fit(X, W, Y)
    mu_0, mu_1 = model.predict_potential_outcomes(X)
    assert not np.isnan(mu_0).any(), "DML baseline_probability is NaN -- Bug #4 has regressed"
    assert not np.isnan(mu_1).any(), "DML treatment_probability is NaN -- Bug #4 has regressed"


def test_dml_ite_is_finite(preprocessed):
    X, W, Y = preprocessed
    model = CausalModelWrapper(model_type="dml", base_estimator="lightgbm", seed=42)
    model.fit(X, W, Y)
    ite = model.predict_ite(X)
    assert np.all(np.isfinite(ite)), "DML produced non-finite ITE values"