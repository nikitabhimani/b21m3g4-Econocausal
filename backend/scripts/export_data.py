"""
Export data from Postgres `customers` table to CSV or JSON.

Usage:
  python backend/scripts/export_data.py --format csv --out data/customers_export.csv

Environment:
  DATABASE_URL must be set or pass --database
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg2


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--database", type=str, default=os.environ.get("DATABASE_URL"))
    p.add_argument("--format", choices=["csv", "json"], default="csv")
    p.add_argument("--out", type=str, default=str(Path("data") / "customers_export.csv"))
    p.add_argument("--query", type=str, default=None, help="Optional SQL query to export")
    return p.parse_args()


def get_connection(dsn: str):
    if not dsn:
        print("ERROR: DATABASE_URL not set and --database not provided.")
        sys.exit(2)
    return psycopg2.connect(dsn)


def export_csv(conn, out_path: str, query: str | None = None):
    with conn.cursor() as cur:
        if query:
            sql = query
        else:
            sql = "SELECT * FROM customers"

        with open(out_path, "w", encoding="utf-8") as f:
            cur.copy_expert(f"COPY ({sql}) TO STDOUT WITH CSV HEADER", f)


def export_json(conn, out_path: str, query: str | None = None):
    # Simple JSON export using rows -> list of dicts. Not optimized for very large tables.
    import json

    with conn.cursor() as cur:
        if query:
            cur.execute(query)
        else:
            cur.execute("SELECT * FROM customers")

        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()

    data = [dict(zip(cols, row)) for row in rows]

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def main():
    args = parse_args()
    conn = get_connection(args.database)

    out_path = args.out
    if args.format == "csv":
        export_csv(conn, out_path, query=args.query)
    else:
        export_json(conn, out_path, query=args.query)

    print(f"Exported data to {out_path}")


if __name__ == "__main__":
    main()
