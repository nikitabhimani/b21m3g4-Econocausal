import numpy as np
import pandas as pd
from scipy.optimize import linprog


def optimize_discount_allocation_greedy(
    df: pd.DataFrame,
    budget: float,
    ite_col: str = "ite",
    cost_col: str = "discount_cost",
    revenue_col: str = "net_revenue",
) -> pd.DataFrame:
    """
    Greedy Knapsack approximation solver.
    Selects customers by expected profit-to-cost ratio.
    O(N log N) time complexity. Extremely fast for N=100,000.
    """
    df = df.copy()
    df["expected_profit"] = df[ite_col] * df[revenue_col]
    df["expected_cost"] = df[cost_col]
    df["allocation_fraction"] = 0.0

    # Filter candidates with positive profit and cost to prevent division by zero or counter-productive selection
    candidates = df[(df["expected_profit"] > 0) & (df["expected_cost"] > 0)].copy()
    candidates["roi_ratio"] = candidates["expected_profit"] / candidates["expected_cost"]

    # Sort descending by ROI ratio
    candidates = candidates.sort_values(by="roi_ratio", ascending=False).reset_index(drop=True)
    candidates["cum_cost"] = candidates["expected_cost"].cumsum()
    candidates["selected"] = (candidates["cum_cost"] <= budget).astype(int)

    selected_ids = set(candidates[candidates["selected"] == 1]["customer_id"])
    df["selected"] = df["customer_id"].isin(selected_ids).astype(int)
    df.loc[df["selected"] == 1, "allocation_fraction"] = 1.0
    return df


def optimize_discount_allocation_lp(
    df: pd.DataFrame,
    budget: float,
    ite_col: str = "ite",
    cost_col: str = "discount_cost",
    revenue_col: str = "net_revenue",
) -> pd.DataFrame:
    """
    Fractional Knapsack LP relaxation solver using scipy.optimize.linprog.
    Maximizes expected profit subject to expected cost <= budget.
    """
    df = df.copy()
    df["gross_expected_profit"] = df[ite_col] * df[revenue_col]
    df["gross_expected_cost"] = df[cost_col]

    n_customers = len(df)

    # Coefficients for objective function (minimize -profit to maximize profit)
    c = -df["gross_expected_profit"].values

    # Inequality constraint: cost * x <= budget
    A = [df["gross_expected_cost"].values]
    b = [budget]

    # Bounds: 0 <= x_i <= 1
    bounds = [(0, 1) for _ in range(n_customers)]

    # Solve linear programming problem
    res = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method="highs")

    if res.success:
        df["allocation_fraction"] = res.x
        df["selected"] = (res.x > 0).astype(int)
        df["expected_profit"] = df["gross_expected_profit"] * df["allocation_fraction"]
        df["expected_cost"] = df["gross_expected_cost"] * df["allocation_fraction"]
    else:
        # Fallback to greedy if solver fails
        return optimize_discount_allocation_greedy(df, budget, ite_col, cost_col, revenue_col)

    return df


def optimize_discount_allocation(
    df: pd.DataFrame,
    budget: float,
    ite_col: str = "ite",
    cost_col: str = "discount_cost",
    revenue_col: str = "net_revenue",
    method: str = "greedy",
) -> pd.DataFrame:
    """
    Main entrypoint for budget-constrained targeting optimization.
    Supported methods: 'greedy' (default, fast), 'lp' (using scipy.optimize.linprog)
    """
    required = [ite_col, cost_col, revenue_col, "customer_id"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame.")

    if method == "lp":
        return optimize_discount_allocation_lp(df, budget, ite_col, cost_col, revenue_col)
    if method == "greedy":
        return optimize_discount_allocation_greedy(df, budget, ite_col, cost_col, revenue_col)
    raise ValueError("method must be either 'greedy' or 'lp'.")
