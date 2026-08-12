"""
Validate data in Postgres `customers` table.

Runs a set of checks similar to `scripts/generate_data.py` but against
the live database. Exits with code 0 on success, 1 on validation failure.

Usage:
  python backend/scripts/validate_db.py --database $DATABASE_URL

Environment:
  or use --database to provide a DSN directly.
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import List

import psycopg2


REQUIRED_COLUMNS = [
    "customer_id",
    "age",
    "tenure_months",
    "customer_segment",
    "historical_orders",
    "historical_revenue",
    "avg_order_value",
    "days_since_last_purchase",
    "website_visits",
    "email_opens",
    "email_clicks",
    "previous_campaign_response",
    "treatment_received",
    "discount_percentage",
    "purchase",
    "purchase_value",
    "discount_cost",
    "net_revenue",
    "true_baseline_purchase_probability",
    "true_treatment_purchase_probability",
    "true_ite",
    "true_treatment_probability",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--database", type=str, default=os.environ.get("DATABASE_URL"))
    p.add_argument("--table", type=str, default="customers")
    p.add_argument("--ite-threshold", type=float, default=1e-5)
    return p.parse_args()


def get_connection(dsn: str):
    if not dsn:
        print("ERROR: No database DSN provided via --database or DATABASE_URL env var.")
        sys.exit(2)
    return psycopg2.connect(dsn)


def fetch_table_columns(cur, table: str) -> List[str]:
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
        """,
        (table,),
    )
    return [r[0] for r in cur.fetchall()]


def main() -> None:
    args = parse_args()
    dsn = args.database
    table = args.table
    threshold = float(args.ite_threshold)

    conn = get_connection(dsn)
    cur = conn.cursor()

    errors: List[str] = []

    # 1) Check required columns
    columns = fetch_table_columns(cur, table)
    missing = [c for c in REQUIRED_COLUMNS if c not in columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")

    # 2) Duplicate customer_id
    cur.execute(f"SELECT COUNT(*) - COUNT(DISTINCT customer_id) FROM {table}")
    dup_count = cur.fetchone()[0]
    if dup_count and dup_count > 0:
        errors.append(f"customer_id contains {dup_count} duplicate rows")

    # 3) Null values (report first few columns with nulls)
    null_columns = []
    for col in REQUIRED_COLUMNS:
        if col in columns:
            cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL")
            cnt = cur.fetchone()[0]
            if cnt and cnt > 0:
                null_columns.append((col, cnt))

    if null_columns:
        errors.append(
            "Columns contain NULLs: "
            + ", ".join([f"{c}({n})" for c, n in null_columns])
        )

    # 4) Treatment must be binary
    if "treatment_received" in columns:
        cur.execute(f"SELECT DISTINCT treatment_received FROM {table} ORDER BY treatment_received")
        vals = [r[0] for r in cur.fetchall()]
        if not set(v for v in vals if v is not None).issubset({0, 1}):
            errors.append(f"treatment_received contains non-binary values: {vals}")

    # 5) Purchase must be binary
    if "purchase" in columns:
        cur.execute(f"SELECT DISTINCT purchase FROM {table} ORDER BY purchase")
        vals = [r[0] for r in cur.fetchall()]
        if not set(v for v in vals if v is not None).issubset({0, 1}):
            errors.append(f"purchase contains non-binary values: {vals}")

    # 6) Discount range
    if "discount_percentage" in columns:
        cur.execute(
            f"SELECT COUNT(*) FROM {table} WHERE discount_percentage < 0 OR discount_percentage > 1"
        )
        cnt = cur.fetchone()[0]
        if cnt and cnt > 0:
            errors.append(f"discount_percentage outside [0,1] for {cnt} rows")

    # 7) Control customers should not receive discounts
    if set(["treatment_received", "discount_percentage"]).issubset(columns):
        cur.execute(
            f"SELECT COUNT(*) FROM {table} WHERE treatment_received = 0 AND discount_percentage != 0"
        )
        cnt = cur.fetchone()[0]
        if cnt and cnt > 0:
            errors.append(f"{cnt} control customers have non-zero discount_percentage")

    # 8) Treated customers should have a positive discount
    if set(["treatment_received", "discount_percentage"]).issubset(columns):
        cur.execute(
            f"SELECT COUNT(*) FROM {table} WHERE treatment_received = 1 AND (discount_percentage <= 0 OR discount_percentage IS NULL)"
        )
        cnt = cur.fetchone()[0]
        if cnt and cnt > 0:
            errors.append(f"{cnt} treated customers have non-positive discount_percentage")

    # 9) Purchase value should be zero when no purchase happened
    if set(["purchase", "purchase_value"]).issubset(columns):
        cur.execute(f"SELECT COUNT(*) FROM {table} WHERE purchase = 0 AND purchase_value != 0")
        cnt = cur.fetchone()[0]
        if cnt and cnt > 0:
            errors.append(f"{cnt} rows have purchase=0 but non-zero purchase_value")

    # 10) ITE consistency
    if set([
        "true_treatment_purchase_probability",
        "true_baseline_purchase_probability",
        "true_ite",
    ]).issubset(columns):
        cur.execute(
            f"SELECT MAX(ABS((true_treatment_purchase_probability - true_baseline_purchase_probability) - true_ite)) FROM {table}"
        )
        max_diff = cur.fetchone()[0] or 0.0
        if float(max_diff) > threshold:
            errors.append(
                f"true_ite inconsistent with potential outcomes: max difference {max_diff} > threshold {threshold}"
            )

    # Finalize
    if errors:
        print("VALIDATION FAILED:\n")
        for e in errors:
            print(" - ", e)
        sys.exit(1)
    else:
        print("Validation passed. All checks OK.")
        sys.exit(0)


if __name__ == "__main__":
    main()
