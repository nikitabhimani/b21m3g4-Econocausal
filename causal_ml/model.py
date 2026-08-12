"""
EconoCausal - Causal ML Model Implementations
"""

import numpy as np
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
    else:  # default to linear models
        clf = LogisticRegression(random_state=seed, max_iter=1000)
        reg = Ridge(random_state=seed)
    return clf, reg


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

    def fit(self, X, W, Y):
        try:
            from econml.dml import LinearDML
            
            clf_y, _ = get_base_models(self.base_estimator, self.seed, self.hyperparams)
            clf_t, _ = get_base_models(self.base_estimator, self.seed, self.hyperparams)
            
            self.dml_model = LinearDML(
                model_y=clf_y,
                model_t=clf_t,
                discrete_treatment=True,
                random_state=self.seed
            )
            self.dml_model.fit(Y, W, X=X, W=X)
            
        except Exception as e:
            print(f"EconML initialization failed or not available ({e}). Falling back to T-Learner.")
            self.fallback_model = TLearner(base_estimator=self.base_estimator, seed=self.seed, hyperparams=self.hyperparams)
            self.fallback_model.fit(X, W, Y)
        return self

    def predict_potential_outcomes(self, X):
        if self.dml_model is not None:
            fallback = TLearner(base_estimator=self.base_estimator, seed=self.seed, hyperparams=self.hyperparams)
            fallback.fit(X, np.zeros(len(X)), np.zeros(len(X)))
            return fallback.predict_potential_outcomes(X)
        return self.fallback_model.predict_potential_outcomes(X)

    def predict_ite(self, X):
        if self.dml_model is not None:
            return self.dml_model.effect(X).flatten()
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
