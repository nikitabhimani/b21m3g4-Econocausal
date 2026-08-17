import pandas as pd
import numpy as np


def assign_uplift_segments(
    df: pd.DataFrame,
    ite_col: str = "ite",
    baseline_col: str = "baseline_probability",
    ite_threshold: float = 0.05,
    baseline_threshold: float = 0.5,
) -> pd.DataFrame:
    """
    Assigns each customer to one of four uplift segments:
    - persuadable: high positive treatment effect (ITE >= ite_threshold)
    - sleeping dog: negative treatment effect (ITE <= -ite_threshold)
    - sure thing: low treatment effect and high baseline (>= baseline_threshold)
    - lost cause: low treatment effect and low baseline (< baseline_threshold)
    """
    df = df.copy()
    if ite_col not in df.columns:
        raise ValueError(f"Column '{ite_col}' not found in DataFrame.")
    if baseline_col not in df.columns:
        raise ValueError(f"Column '{baseline_col}' not found in DataFrame.")

    # Conditions for segmentation
    conditions = [
        df[ite_col] >= ite_threshold,
        df[ite_col] <= -ite_threshold,
        (df[ite_col] > -ite_threshold) & (df[ite_col] < ite_threshold) & (df[baseline_col] >= baseline_threshold),
        (df[ite_col] > -ite_threshold) & (df[ite_col] < ite_threshold) & (df[baseline_col] < baseline_threshold),
    ]
    choices = ["persuadable", "sleeping dog", "sure thing", "lost cause"]

    df["uplift_segment"] = np.select(conditions, choices, default="lost cause")
    return df
