"""
EconoCausal - Causal ML Model Implementations
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge


def get_base_models(estimator_name, seed=42, hyperparams=None):
    """Factory to get scikit-learn base classifiers and regressors with hyperparameters."""
    hp = hyperparams or {}
    n_est = hp.get("n_estimators", 100)
    max_d = hp.get("max_depth", 4)
    min_split = hp.get("min_samples_split", 10)
    lr = hp.get("learning_rate", 0.1)

    if estimator_name == "gradient_boosting":
        clf = GradientBoostingClassifier(
            random_state=seed, max_depth=max_d, n_estimators=n_est,
            min_samples_split=min_split, learning_rate=lr
        )
        reg = GradientBoostingRegressor(
            random_state=seed, max_depth=max_d, n_estimators=n_est,
            min_samples_split=min_split, learning_rate=lr
        )
    elif estimator_name == "random_forest":
        clf = RandomForestClassifier(
            random_state=seed, max_depth=max_d, n_estimators=n_est,
            min_samples_split=min_split, n_jobs=-1
        )
        reg = RandomForestRegressor(
            random_state=seed, max_depth=max_d, n_estimators=n_est,
            min_samples_split=min_split, n_jobs=-1
        )
    elif estimator_name == "lightgbm":
        from lightgbm import LGBMClassifier, LGBMRegressor
        clf = LGBMClassifier(
            random_state=seed, max_depth=max_d, n_estimators=n_est,
            learning_rate=lr, verbosity=-1
        )
        reg = LGBMRegressor(
            random_state=seed, max_depth=max_d, n_estimators=n_est,
            learning_rate=lr, verbosity=-1
        )
    else:  # default to linear models
        clf = LogisticRegression(random_state=seed, max_iter=1000)
        reg = Ridge(random_state=seed)
    return clf, reg


# ---------------------------------------------------------------------------
# Shared covariate selection used by DoubleMachineLearning.fit() AND
# DoubleMachineLearning.predict_ite(). Defined ONCE here so both methods
# are always guaranteed to use the identical column set -- this is what
# caused the earlier "Dimension mis-match of X with fitted X" crash: fit()
# and predict_ite() had drifted out of sync when edited separately.
#
# These are the columns that drive HETEROGENEITY in the true_ite formula
# in the data generator (see generator.py):
#   - age, tenure_months, customer_segment  -> included from the start
#   - previous_campaign_response, website_visits, days_since_last_purchase,
#     historical_revenue -> also directly affect responsiveness/recency_effect
#     in true_ite, so DML needs to see them to model heterogeneity well.
# ---------------------------------------------------------------------------
_HETEROGENEITY_NUMERIC_COLS = [
    'age',
    'tenure_months',
    'previous_campaign_response',
    'website_visits',
    'days_since_last_purchase',
    'historical_revenue',
]

_TREATMENT_COL_NAME = '__treatment__'


def _get_covariate_cols(X):
    """Return the covariate (heterogeneity) column list for a given X."""
    return [
        col for col in X.columns
        if col in _HETEROGENEITY_NUMERIC_COLS or col.startswith('customer_segment')
    ]


class TLearner:
    """T-Learner (Two-Learner) for binary treatment and binary outcome."""
    def __init__(self, base_estimator="gradient_boosting", seed=42, hyperparams=None):
        self.base_estimator = base_estimator
        self.seed = seed
        self.hyperparams = hyperparams
        self.clf_control = None
        self.clf_treated = None

    def fit(self, X, W, Y):
        clf_c, _ = get_base_models(self.base_estimator, self.seed, self.hyperparams)
        clf_t, _ = get_base_models(self.base_estimator, self.seed, self.hyperparams)

        self.clf_control = clf_c.fit(X[W == 0], Y[W == 0])
        self.clf_treated = clf_t.fit(X[W == 1], Y[W == 1])
        return self

    def predict_potential_outcomes(self, X):
        mu_0 = self.clf_control.predict_proba(X)[:, 1]
        mu_1 = self.clf_treated.predict_proba(X)[:, 1]
        return mu_0, mu_1

    def predict_ite(self, X):
        mu_0, mu_1 = self.predict_potential_outcomes(X)
        return mu_1 - mu_0


class XLearner:
    """X-Learner with propensity weighting."""
    def __init__(self, base_estimator="gradient_boosting", seed=42, hyperparams=None):
        self.base_estimator = base_estimator
        self.seed = seed
        self.hyperparams = hyperparams
        self.t_learner = None
        self.reg_effect_control = None
        self.reg_effect_treated = None
        self.propensity_model = None

    def fit(self, X, W, Y):
        # Step 1: Train a T-Learner
        self.t_learner = TLearner(base_estimator=self.base_estimator, seed=self.seed, hyperparams=self.hyperparams)
        self.t_learner.fit(X, W, Y)

        mu_0, mu_1 = self.t_learner.predict_potential_outcomes(X)

        # Step 2: Impute treatment effects
        D_1 = Y[W == 1] - mu_0[W == 1]
        D_0 = mu_1[W == 0] - Y[W == 0]

        # Train regression models to predict imputed effects
        _, reg_c = get_base_models(self.base_estimator, self.seed, self.hyperparams)
        _, reg_t = get_base_models(self.base_estimator, self.seed, self.hyperparams)

        self.reg_effect_control = reg_c.fit(X[W == 0], D_0)
        self.reg_effect_treated = reg_t.fit(X[W == 1], D_1)

        # Step 3: Train propensity model P(W=1 | X)
        prop_model, _ = get_base_models(self.base_estimator, self.seed, self.hyperparams)
        self.propensity_model = prop_model.fit(X, W)
        return self

    def predict_potential_outcomes(self, X):
        return self.t_learner.predict_potential_outcomes(X)

    def predict_ite(self, X):
        tau_0 = self.reg_effect_control.predict(X)
        tau_1 = self.reg_effect_treated.predict(X)

        # Propensity score weighting
        e_x = self.propensity_model.predict_proba(X)[:, 1]
        return e_x * tau_0 + (1.0 - e_x) * tau_1


class DoubleMachineLearning:
    """Double Machine Learning using EconML wrapper or custom fallback."""
    def __init__(self, base_estimator="gradient_boosting", seed=42, hyperparams=None):
        self.base_estimator = base_estimator
        self.seed = seed
        self.hyperparams = hyperparams
        self.dml_model = None
        self.fallback_model = None
        # Auxiliary outcome model used ONLY to estimate baseline/treatment
        # probability (see fit()/predict_potential_outcomes() below). It
        # does NOT affect the CATE/ITE estimate from dml_model.effect().
        self.outcome_model = None
        self._outcome_model_columns = None

    def fit(self, X, W, Y):
        try:
            from econml.dml import LinearDML

            clf_t, _ = get_base_models(self.base_estimator, self.seed, self.hyperparams)
            _, reg_y = get_base_models(self.base_estimator, self.seed, self.hyperparams)

            self.dml_model = LinearDML(
                model_y=reg_y,
                model_t=clf_t,
                discrete_treatment=True,
                random_state=self.seed
            )

            if hasattr(X, "columns"):
                # IMPORTANT: covariate_cols is computed via _get_covariate_cols()
                # so fit() and predict_ite() can never drift out of sync again.
                covariate_cols = _get_covariate_cols(X)
                confounder_cols = [col for col in X.columns if col not in ['age', 'tenure_months']]
                X_cov = X[covariate_cols]
                X_conf = X[confounder_cols]
            else:
                X_cov = X
                X_conf = X

            self.dml_model.fit(Y, W, X=X_cov, W=X_conf)

            # -----------------------------------------------------------
            # OPTION A FIX: LinearDML.effect() gives us the CATE (ITE)
            # directly, but does not give us baseline/treatment purchase
            # probabilities on its own. Previously predict_potential_outcomes()
            # returned NaN for DML, which silently propagated into
            # downstream outputs (recommendations.json -> expected_conversion
            # was NaN for all 99,998 customers).
            #
            # Fix: train a SEPARATE auxiliary classifier that predicts the
            # outcome (Y) directly from [all covariates/confounders + the
            # treatment indicator as a feature]. At prediction time, we
            # query this classifier twice per customer -- once with
            # treatment forced to 0 (baseline) and once forced to 1
            # (treated) -- using the SAME customer covariates both times.
            # This gives real, non-NaN probability estimates.
            #
            # This auxiliary model is fully independent of dml_model, so
            # it has NO effect on the ITE/CATE estimate used elsewhere
            # (predict_ite() still uses dml_model.effect() unchanged).
            # -----------------------------------------------------------
            if hasattr(X, "columns"):
                outcome_clf, _ = get_base_models(self.base_estimator, self.seed, self.hyperparams)
                X_for_outcome = X.copy()
                X_for_outcome[_TREATMENT_COL_NAME] = np.asarray(W)
                self._outcome_model_columns = X_for_outcome.columns.tolist()
                outcome_clf.fit(X_for_outcome, Y)
                self.outcome_model = outcome_clf

        except Exception as e:
            print(f"EconML initialization failed or not available ({e}). Falling back to T-Learner.")
            self.dml_model = None
            self.outcome_model = None
            self.fallback_model = TLearner(base_estimator=self.base_estimator, seed=self.seed, hyperparams=self.hyperparams)
            self.fallback_model.fit(X, W, Y)
        return self

    def predict_potential_outcomes(self, X):
        if self.dml_model is not None:
            if self.outcome_model is not None and hasattr(X, "columns"):
                X_control = X.copy()
                X_control[_TREATMENT_COL_NAME] = 0
                X_treated = X.copy()
                X_treated[_TREATMENT_COL_NAME] = 1

                # Ensure column order matches what the outcome model was
                # trained on.
                X_control = X_control[self._outcome_model_columns]
                X_treated = X_treated[self._outcome_model_columns]

                mu_0 = self.outcome_model.predict_proba(X_control)[:, 1]
                mu_1 = self.outcome_model.predict_proba(X_treated)[:, 1]
                return mu_0, mu_1

            # Fallback: if outcome_model wasn't trained for some reason
            # (e.g. X had no .columns), return NaN rather than fabricating
            # values, same as before.
            n_samples = len(X)
            nan_probs = np.full(n_samples, np.nan)
            return nan_probs, nan_probs
        return self.fallback_model.predict_potential_outcomes(X)

    def predict_ite(self, X):
        if self.dml_model is not None:
            if hasattr(X, "columns"):
                # Same _get_covariate_cols() call as fit() -- guaranteed match.
                covariate_cols = _get_covariate_cols(X)
                X_cov = X[covariate_cols]
            else:
                X_cov = X
            return self.dml_model.effect(X_cov).flatten()
        return self.fallback_model.predict_ite(X)


class CausalModelWrapper:
    """Wrapper class supporting all model types and hyperparameters."""
    def __init__(self, model_type="t_learner", base_estimator="gradient_boosting", seed=42, hyperparams=None):
        self.model_type = model_type
        self.base_estimator = base_estimator
        self.seed = seed
        self.hyperparams = hyperparams

        if model_type == "t_learner":
            self.estimator = TLearner(base_estimator=base_estimator, seed=seed, hyperparams=hyperparams)
        elif model_type == "x_learner":
            self.estimator = XLearner(base_estimator=base_estimator, seed=seed, hyperparams=hyperparams)
        elif model_type == "dml":
            self.estimator = DoubleMachineLearning(base_estimator=base_estimator, seed=seed, hyperparams=hyperparams)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

    def fit(self, X, W, Y):
        self.estimator.fit(X, W, Y)
        return self

    def predict_potential_outcomes(self, X):
        return self.estimator.predict_potential_outcomes(X)

    def predict_ite(self, X):
        return self.estimator.predict_ite(X)