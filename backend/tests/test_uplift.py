import numpy as np
import pandas as pd
import pytest
from uplift.segmentation import assign_uplift_segments
from uplift.metrics import calculate_qini_curve, calculate_auuc, calculate_metrics
from uplift.optimization import optimize_discount_allocation


def test_assign_uplift_segments():
    # Construct mock predictions dataframe
    df = pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4],
            "baseline_probability": [0.2, 0.6, 0.1, 0.4],
            "ite": [0.15, 0.01, 0.02, -0.12],
        }
    )

    segmented = assign_uplift_segments(df, ite_threshold=0.05, baseline_threshold=0.5)

    assert segmented.loc[0, "uplift_segment"] == "persuadable"  # ITE (0.15) >= 0.05
    assert segmented.loc[1, "uplift_segment"] == "sure thing"  # ITE (0.01) < 0.05, baseline (0.6) >= 0.5
    assert segmented.loc[2, "uplift_segment"] == "lost cause"  # ITE (0.02) < 0.05, baseline (0.1) < 0.5
    assert segmented.loc[3, "uplift_segment"] == "sleeping dog"  # ITE (-0.12) <= -0.05


def test_calculate_qini_curve_and_auuc():
    # Construct mock outcomes dataframe
    df = pd.DataFrame(
        {
            "ite": [0.5, 0.4, 0.3, 0.2, 0.1],
            "treatment_received": [1, 1, 0, 0, 1],
            "purchase": [1, 0, 1, 0, 1],
        }
    )

    qini = calculate_qini_curve(df, score_col="ite", treatment_col="treatment_received", outcome_col="purchase")
    assert len(qini) == 5
    assert isinstance(qini, np.ndarray)

    auuc = calculate_auuc(qini)
    assert auuc >= 0


def test_calculate_metrics():
    df = pd.DataFrame(
        {
            "ite": [0.2, 0.1, 0.3],
            "true_ite": [0.22, 0.08, 0.31],
            "treatment_received": [1, 0, 1],
            "purchase": [1, 0, 1],
        }
    )

    res = calculate_metrics(df)
    assert "mae" in res
    assert "rmse" in res
    assert "correlation" in res
    assert "qini_coefficient" in res
    assert res["mae"] < 0.02


def test_optimize_discount_allocation():
    # Greedy optimization test
    df = pd.DataFrame(
        {
            "customer_id": [1, 2, 3],
            "ite": [0.2, 0.1, 0.3],
            "discount_cost": [50.0, 10.0, 30.0],
            "net_revenue": [100.0, 100.0, 100.0],
        }
    )

    # ROI ratios:
    # 1: 0.2 * 100 / 50 = 0.4
    # 2: 0.1 * 100 / 10 = 1.0 (Best ROI)
    # 3: 0.3 * 100 / 30 = 1.0 (Best ROI)
    # Budget = 40.0 should select customer 2 and 3 (cost = 10 + 30 = 40)
    optimized = optimize_discount_allocation(df, budget=40.0, method="greedy")
    assert list(optimized[optimized["selected"] == 1]["customer_id"]) == [2, 3]

    # Budget = 20.0 should select customer 2 only
    optimized_small = optimize_discount_allocation(df, budget=20.0, method="greedy")
    assert list(optimized_small[optimized_small["selected"] == 1]["customer_id"]) == [2]
