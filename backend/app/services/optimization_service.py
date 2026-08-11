from __future__ import annotations

import pandas as pd

from app.services.data_service import load_customer_data


def build_recommendations(budget: float, limit: int = 25) -> dict:
    df = load_customer_data()
    scored = df[["customer_id", "true_ite", "discount_cost", "net_revenue"]].copy()
    scored["expected_profit"] = scored["true_ite"] * scored["net_revenue"]
    scored["expected_cost"] = scored["discount_cost"]
    scored = scored.sort_values("expected_profit", ascending=False)
    scored = scored.head(limit)

    total_expected_profit = float(scored["expected_profit"].sum())
    total_expected_cost = float(scored["expected_cost"].sum())

    recommendations = []
    for _, row in scored.iterrows():
        recommendations.append(
            {
                "customer_id": int(row["customer_id"]),
                "predicted_ite": float(row["true_ite"]),
                "recommended_discount": 0.1,
                "expected_profit": float(row["expected_profit"]),
                "expected_cost": float(row["expected_cost"]),
            }
        )

    return {
        "budget": float(budget),
        "total_recommended_customers": len(recommendations),
        "total_expected_profit": total_expected_profit,
        "total_expected_cost": total_expected_cost,
        "recommendations": recommendations,
    }
