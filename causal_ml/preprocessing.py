"""
EconoCausal - Data Preprocessing Module with Imbalance Validation Checks
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler


class CausalPreprocessor:
    def __init__(self, categorical_covariates, numeric_covariates, treatment, outcome):
        self.categorical_covariates = categorical_covariates
        self.numeric_covariates = numeric_covariates
        self.treatment = treatment
        self.outcome = outcome
        
        self.scaler = StandardScaler()
        self.encoded_columns = []
        self.feature_names = []
        self.is_fitted = False
        self.warnings = []

    def fit(self, df):
        """Fit scaler and learn categorical encoding columns."""
        # 1. Fit numerical features
        if self.numeric_covariates:
            self.scaler.fit(df[self.numeric_covariates].astype(float))
        
        # 2. Fit categorical features (learn unique values/dummies)
        dummy_df = pd.get_dummies(df[self.categorical_covariates], columns=self.categorical_covariates, dtype=float)
        self.encoded_columns = dummy_df.columns.tolist()
        
        # 3. Save final feature order (numeric + dummies)
        self.feature_names = self.numeric_covariates + self.encoded_columns
        self.is_fitted = True
        return self

    def check_imbalance(self, W, Y):
        """Check for class imbalance in treatment and outcome."""
        self.warnings = []
        if W is not None:
            t_rate = float(W.mean())
            print(f"Dataset treatment rate: {t_rate:.2%}")
            if t_rate < 0.05 or t_rate > 0.95:
                warn_msg = f"WARNING: Severe treatment class imbalance detected (treatment rate: {t_rate:.2%}). Causal estimators may be unstable."
                print(warn_msg)
                self.warnings.append(warn_msg)
                
        if Y is not None:
            o_rate = float(Y.mean())
            print(f"Dataset outcome purchase rate: {o_rate:.2%}")
            if o_rate < 0.05 or o_rate > 0.95:
                warn_msg = f"WARNING: Severe outcome class imbalance detected (outcome rate: {o_rate:.2%}). Estimators may fail to fit properly."
                print(warn_msg)
                self.warnings.append(warn_msg)
        return self.warnings

    def transform(self, df):
        """Transform data based on fitted parameters."""
        if not self.is_fitted:
            raise ValueError("Preprocessor has not been fitted yet.")
        
        # Scale numeric features
        if self.numeric_covariates:
            scaled_numeric = self.scaler.transform(df[self.numeric_covariates].astype(float))
            numeric_df = pd.DataFrame(scaled_numeric, columns=self.numeric_covariates, index=df.index)
        else:
            numeric_df = pd.DataFrame(index=df.index)

        # One-hot encode categoricals
        dummy_df = pd.get_dummies(df[self.categorical_covariates], columns=self.categorical_covariates, dtype=float)
        
        # Reindex dummies to ensure all categories learned during fit are present
        dummy_df = dummy_df.reindex(columns=self.encoded_columns, fill_value=0.0)
        
        # Combine
        X = pd.concat([numeric_df, dummy_df], axis=1)
        X = X[self.feature_names]  # Enforce correct column order
        
        # Treatment and Outcome (if present)
        W = df[self.treatment].astype(int) if self.treatment in df.columns else None
        Y = df[self.outcome].astype(float) if self.outcome in df.columns else None
        
        # Validate data shapes and imbalances
        self.check_imbalance(W, Y)
        
        return X, W, Y

    def fit_transform(self, df):
        return self.fit(df).transform(df)
