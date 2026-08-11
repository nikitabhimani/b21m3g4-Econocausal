from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = PROJECT_ROOT / "data" / "customers.csv"


def load_customer_data() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH)


def build_summary() -> dict:
    df = load_customer_data()
    return {
        "customers": int(len(df)),
        "treated_customers": int((df["treatment_received"] == 1).sum()),
        "control_customers": int((df["treatment_received"] == 0).sum()),
        "treatment_rate": float(df["treatment_received"].mean()),
        "purchase_rate": float(df["purchase"].mean()),
        "average_true_ite": float(df["true_ite"].mean()),
        "total_revenue": float(df["purchase_value"].sum()),
        "total_discount_cost": float(df["discount_cost"].sum()),
    }


def get_customer_by_id(customer_id: int) -> dict | None:
    df = load_customer_data()
    row = df[df["customer_id"] == customer_id]
    if row.empty:
        return None
    return row.iloc[0].to_dict()
