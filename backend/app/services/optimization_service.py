from __future__ import annotations

from ..repositories import ArtifactRepository
from .data_service import load_customer_data
from uplift.optimization import optimize_discount_allocation


def build_recommendations(budget: float, limit: int = 25) -> dict:
    customers = load_customer_data().drop(columns=["true_ite"], errors="ignore")
    predictions = ArtifactRepository().predictions()
    scored = customers.merge(predictions, on="customer_id", how="inner")
    scored = optimize_discount_allocation(scored, budget=budget, method="greedy")
    selected = scored[scored["selected"] == 1].sort_values("expected_profit", ascending=False)
    total_expected_profit = float(selected["expected_profit"].sum())
    total_expected_cost = float(selected["expected_cost"].sum())
    if total_expected_cost > budget + 1e-6:
        raise RuntimeError("Optimizer returned recommendations above the requested budget.")

    recommendations = []
    for _, row in selected.head(limit).iterrows():
        recommendations.append(
            {
                "customer_id": int(row["customer_id"]),
                "predicted_ite": float(row["ite"]),
                "recommended_discount": float(row["discount_percentage"]),
                "expected_profit": float(row["expected_profit"]),
                "expected_cost": float(row["expected_cost"]),
            }
        )

    return {
        "budget": float(budget),
        "total_recommended_customers": int(len(selected)),
        "total_expected_profit": total_expected_profit,
        "total_expected_cost": total_expected_cost,
        "recommendations": recommendations,
    }


def build_optimization(budget: float, method: str) -> dict:
    if method != "greedy":
        raise ValueError("Only the greedy integer-safe optimizer is available via the API.")
    result = build_recommendations(budget=budget, limit=100)
    result["method"] = method
    return result


def build_uplift() -> dict:
    artifacts = ArtifactRepository()
    return {"results": artifacts.uplift_results(), "scenarios": artifacts.scenario_comparison()}
