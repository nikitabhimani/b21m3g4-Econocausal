"""
Load CSV data into Postgres `customers` table.

Usage:
  python backend/scripts/load_data.py --csv data/customers.csv

Environment:
  DATABASE_URL: Postgres DSN, e.g. postgresql://user:pass@localhost:5432/dbname
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg2


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load CSV into Postgres customers table")
    parser.add_argument("--csv", type=str, default=str(PROJECT_ROOT / "data" / "customers.csv"))
    parser.add_argument("--drop-existing", action="store_true", help="Truncate the customers table before load")
    return parser.parse_args()


def get_database_url() -> str:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable is not set.")
        sys.exit(2)
    return db_url


def load_csv_into_postgres(db_url: str, csv_path: str, drop_existing: bool = False) -> None:
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            if drop_existing:
                print("Truncating customers table...")
                cur.execute("TRUNCATE TABLE customers;")

            with open(csv_path, "r", encoding="utf-8") as f:
                print(f"Loading CSV from {csv_path} into customers table...")
                # Use COPY for performant bulk load. Assumes CSV has header matching table columns.
                cur.copy_expert("COPY customers FROM STDIN WITH CSV HEADER", f)

        conn.commit()
        print("Load completed successfully.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main() -> None:
    args = parse_args()
    csv_path = args.csv
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found: {csv_path}")
        sys.exit(2)

    db_url = get_database_url()
    load_csv_into_postgres(db_url, csv_path, drop_existing=args.drop_existing)


if __name__ == "__main__":
    main()
