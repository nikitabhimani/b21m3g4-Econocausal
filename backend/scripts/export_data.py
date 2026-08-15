"""
Export standard EconoCausal datasets from PostgreSQL to CSV or JSON.

Usage:
  python backend/scripts/export_data.py --dataset model-input --format csv --out data/model_input.csv

Environment:
  DATABASE_URL must be set or pass --database
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg2


DATASET_QUERIES = {
    "customers": "SELECT * FROM customers ORDER BY customer_id",
    "model-input": """
        SELECT customer_id, age, tenure_months, customer_segment, historical_orders,
               historical_revenue, avg_order_value, days_since_last_purchase,
               website_visits, email_opens, email_clicks, previous_campaign_response,
               treatment_received, discount_percentage, purchase
        FROM customers ORDER BY customer_id
    """,
    "dashboard": """
        SELECT c.customer_id, c.campaign_id, c.customer_segment, c.treatment_received,
               c.discount_percentage, c.purchase, c.purchase_value, c.discount_cost,
               c.net_revenue, c.true_ite, p.baseline_probability,
               p.treatment_probability, p.ite AS predicted_ite,
               r.recommended_discount, r.expected_profit, r.expected_cost
        FROM customers c
        LEFT JOIN LATERAL (
            SELECT baseline_probability, treatment_probability, ite
            FROM predictions WHERE customer_id = c.customer_id
            ORDER BY created_at DESC, id DESC LIMIT 1
        ) p ON TRUE
        LEFT JOIN LATERAL (
            SELECT recommended_discount, expected_profit, expected_cost
            FROM recommendations WHERE customer_id = c.customer_id
            ORDER BY created_at DESC, id DESC LIMIT 1
        ) r ON TRUE
        ORDER BY c.customer_id
    """,
}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--database", type=str, default=os.environ.get("DATABASE_URL"))
    p.add_argument("--format", choices=["csv", "json"], default="csv")
    p.add_argument("--out", type=str, default=None)
    p.add_argument("--dataset", choices=sorted(DATASET_QUERIES), default="customers")
    p.add_argument("--query", type=str, default=None, help="Optional SQL query to export")
    return p.parse_args()


def get_connection(dsn: str):
    if not dsn:
        print("ERROR: DATABASE_URL not set and --database not provided.")
        sys.exit(2)
    return psycopg2.connect(dsn)


def export_csv(conn, out_path: str, query: str):
    with conn.cursor() as cur:
        with open(out_path, "w", encoding="utf-8") as f:
            cur.copy_expert(f"COPY ({query}) TO STDOUT WITH CSV HEADER", f)


def export_json(conn, out_path: str, query: str):
    # Simple JSON export using rows -> list of dicts. Not optimized for very large tables.
    import json

    with conn.cursor() as cur:
        cur.execute(query)

        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()

    data = [dict(zip(cols, row)) for row in rows]

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def main():
    args = parse_args()
    conn = get_connection(args.database)

    out_path = args.out or str(Path("data") / f"{args.dataset.replace('-', '_')}_export.{args.format}")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    query = args.query or DATASET_QUERIES[args.dataset]
    if args.format == "csv":
        export_csv(conn, out_path, query=query)
    else:
        export_json(conn, out_path, query=query)

    print(f"Exported data to {out_path}")


if __name__ == "__main__":
    main()
