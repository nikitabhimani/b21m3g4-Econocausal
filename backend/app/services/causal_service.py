from __future__ import annotations

import pandas as pd

from app.services.data_service import load_customer_data


def build_causal_summary() -> dict:
    df = load_customer_data()
    ite_values = df["true_ite"].astype(float)
    return {
        "average_ite": float(ite_values.mean()),
        "median_ite": float(ite_values.median()),
        "positive_ite_share": float((ite_values > 0).mean()),
        "top_positive_ite": float(ite_values.max()),
        "top_negative_ite": float(ite_values.min()),
    }


def get_top_ite_customers(limit: int = 10) -> list[dict]:
    df = load_customer_data()
    ranked = df[["customer_id", "true_ite"]].copy()
    ranked = ranked.sort_values("true_ite", ascending=False)
    ranked = ranked.head(limit)
    return ranked.to_dict(orient="records")
