"""Import generated causal predictions and budget-safe recommendations into PostgreSQL.

Run after `scripts/setup_db.sh` and `scripts/generate_uplift_outputs.py`:
  DATABASE_URL=... python backend/scripts/import_artifacts.py --replace
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from uplift.optimization import optimize_discount_allocation


ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", default=os.environ.get("DATABASE_URL"))
    parser.add_argument("--replace", action="store_true", help="Remove prior imported model runs and linked records.")
    parser.add_argument("--budget", type=float, default=1_000_000.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.database:
        raise SystemExit("DATABASE_URL or --database is required.")
    predictions = pd.read_csv(ROOT / "outputs" / "causal_predictions.csv")
    required = ["customer_id", "baseline_probability", "treatment_probability", "ite"]
    if predictions[required].isnull().any().any() or not predictions[required].apply(lambda col: pd.api.types.is_numeric_dtype(col)).all():
        raise SystemExit("Predictions must contain finite numeric causal contract fields.")
    if not predictions[required].apply(lambda col: np.isfinite(col)).all().all():
        raise SystemExit("Predictions contain non-finite values.")

    customers = pd.read_csv(ROOT / "data" / "customers.csv").drop(columns=["true_ite"], errors="ignore")
    scored = customers.merge(predictions, on="customer_id", how="inner")
    optimized = optimize_discount_allocation(scored, budget=args.budget, method="greedy")
    recommendations = optimized[optimized["selected"] == 1]

    with psycopg2.connect(args.database) as conn, conn.cursor() as cur:
        if args.replace:
            cur.execute("DELETE FROM model_runs WHERE model_name = %s", ("causal_pipeline",))
        cur.execute(
            "INSERT INTO model_runs (model_name, model_version, metrics) VALUES (%s, %s, %s) RETURNING id",
            ("causal_pipeline", "v1", "{}"),
        )
        model_run_id = cur.fetchone()[0]
        execute_values(
            cur,
            """INSERT INTO predictions (customer_id, model_run_id, baseline_probability, treatment_probability, ite)
               VALUES %s""",
            [
                (int(row.customer_id), model_run_id, float(row.baseline_probability), float(row.treatment_probability), float(row.ite))
                for row in predictions.itertuples()
            ],
            page_size=5000,
        )
        execute_values(
            cur,
            """INSERT INTO recommendations (customer_id, model_run_id, predicted_ite, recommended_discount, expected_profit, expected_cost)
               VALUES %s""",
            [
                (int(row.customer_id), model_run_id, float(row.ite), float(row.discount_percentage), float(row.expected_profit), float(row.expected_cost))
                for row in recommendations.itertuples()
            ],
            page_size=5000,
        )
    print(f"Imported {len(predictions)} predictions and {len(recommendations)} recommendations for model run {model_run_id}.")


if __name__ == "__main__":
    main()
