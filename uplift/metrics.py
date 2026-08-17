import numpy as np
import pandas as pd


def calculate_qini_curve(
    df: pd.DataFrame,
    score_col: str = "ite",
    treatment_col: str = "treatment_received",
    outcome_col: str = "purchase",
) -> np.ndarray:
    """
    Computes cumulative Qini curve sorted by predicted uplift score descending.
    Formula: Q(u) = Y^t(u) - Y^c(u) * (N^t / N^c)
    """
    required = [score_col, treatment_col, outcome_col]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame.")

    # Sort descending by predicted scores
    sorted_df = df.sort_values(by=score_col, ascending=False).reset_index(drop=True)

    treated = (sorted_df[treatment_col] == 1).astype(int)
    control = (sorted_df[treatment_col] == 0).astype(int)

    y_treated = (treated * sorted_df[outcome_col]).astype(int)
    y_control = (control * sorted_df[outcome_col]).astype(int)

    cum_y_treated = y_treated.cumsum()
    cum_y_control = y_control.cumsum()

    total_treated = treated.sum()
    total_control = control.sum()

    ratio = total_treated / total_control if total_control > 0 else 1.0

    qini_vals = cum_y_treated - cum_y_control * ratio
    return qini_vals.values


def calculate_auuc(qini_curve: np.ndarray) -> float:
    """
    Computes Area Under Causal Curve (AUUC).
    """
    if len(qini_curve) <= 1:
        return 0.0
    return float(np.mean(qini_curve))


def calculate_metrics(
    df: pd.DataFrame,
    score_col: str = "ite",
    true_ite_col: str = "true_ite",
    treatment_col: str = "treatment_received",
    outcome_col: str = "purchase",
) -> dict:
    """
    Aggregates MAE, RMSE, Correlation, and Qini Coefficient.
    """
    metrics = {}

    # Error metrics
    if true_ite_col in df.columns and score_col in df.columns:
        pred_ite = df[score_col].values
        true_ite = df[true_ite_col].values
        metrics["mae"] = float(np.mean(np.abs(pred_ite - true_ite)))
        metrics["rmse"] = float(np.sqrt(np.mean((pred_ite - true_ite) ** 2)))
        
        corr_matrix = np.corrcoef(pred_ite, true_ite)
        metrics["correlation"] = float(corr_matrix[0, 1]) if not np.isnan(corr_matrix[0, 1]) else 0.0

    # Qini Coefficient
    if treatment_col in df.columns and outcome_col in df.columns:
        qini_model = calculate_qini_curve(df, score_col, treatment_col, outcome_col)
        n_samples = len(df)
        qini_random = np.linspace(0, qini_model[-1] if len(qini_model) > 0 else 0, n_samples)
        
        sort_col_perfect = true_ite_col if true_ite_col in df.columns else score_col
        qini_perfect = calculate_qini_curve(df, sort_col_perfect, treatment_col, outcome_col)

        area_model = calculate_auuc(qini_model)
        area_random = calculate_auuc(qini_random)
        area_perfect = calculate_auuc(qini_perfect)

        denominator = area_perfect - area_random
        metrics["qini_coefficient"] = float((area_model - area_random) / denominator) if denominator != 0.0 else 0.0

    if score_col in df.columns:
        metrics["average_ite"] = float(df[score_col].mean())

    return metrics
