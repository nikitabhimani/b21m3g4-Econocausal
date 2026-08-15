"""Load the frozen v1 customer contract into PostgreSQL from CSV or JSON.

Examples:
  python backend/scripts/load_data.py --input data/customers.csv --batch-size 5000
  python backend/scripts/load_data.py --input data/customers.json --drop-existing
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Iterable, Iterator

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ModuleNotFoundError:  # Allows contract-only tooling to run without DB extras.
    psycopg2 = None
    execute_values = None


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REQUIRED_COLUMNS = (
    "customer_id", "age", "tenure_months", "customer_segment", "historical_orders",
    "historical_revenue", "avg_order_value", "days_since_last_purchase", "website_visits",
    "email_opens", "email_clicks", "previous_campaign_response", "treatment_received",
    "discount_percentage", "purchase", "purchase_value", "discount_cost", "net_revenue",
    "true_baseline_purchase_probability", "true_treatment_purchase_probability", "true_ite",
    "true_treatment_probability",
)
OPTIONAL_COLUMNS = ("campaign_id",)
INSERT_COLUMNS = OPTIONAL_COLUMNS + REQUIRED_COLUMNS


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({"level": record.levelname, "event": record.getMessage()})


def get_logger() -> logging.Logger:
    logger = logging.getLogger("econocausal.loader")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load CSV or JSON customers into PostgreSQL")
    parser.add_argument("--input", "--csv", dest="input_path", default=str(PROJECT_ROOT / "data" / "customers.csv"))
    parser.add_argument("--format", choices=("csv", "json"), help="Overrides format inferred from input suffix")
    parser.add_argument("--batch-size", type=int, default=5_000)
    parser.add_argument("--drop-existing", action="store_true", help="Truncate customers and dependent data before load")
    return parser.parse_args()


def get_database_url() -> str:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set.")
    return db_url


def batches(rows: Iterable[dict[str, Any]], batch_size: int) -> Iterator[list[dict[str, Any]]]:
    batch: list[dict[str, Any]] = []
    for row in rows:
        batch.append(row)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def validate_columns(rows: Iterable[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    for row_number, row in enumerate(rows, start=2):
        missing = [column for column in REQUIRED_COLUMNS if column not in row or row[column] in (None, "")]
        unknown = set(row).difference(INSERT_COLUMNS)
        if missing or unknown:
            details = []
            if missing:
                details.append(f"missing required columns: {', '.join(missing)}")
            if unknown:
                details.append(f"unknown columns: {', '.join(sorted(unknown))}")
            raise ValueError(f"Invalid input row {row_number}: {'; '.join(details)}")
        yield row


def read_rows(input_path: Path, input_format: str) -> Iterator[dict[str, Any]]:
    if input_format == "csv":
        with input_path.open("r", encoding="utf-8", newline="") as source:
            yield from validate_columns(csv.DictReader(source))
        return

    with input_path.open("r", encoding="utf-8") as source:
        payload = json.load(source)
    rows = payload.get("customers") if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("JSON input must be an array of customers or an object containing a customers array.")
    yield from validate_columns(rows)


def load_rows(db_url: str, rows: Iterable[dict[str, Any]], *, batch_size: int, drop_existing: bool, logger: logging.Logger) -> int:
    if psycopg2 is None or execute_values is None:
        raise RuntimeError("psycopg2-binary is required for database imports; install requirements.txt")
    columns_sql = ", ".join(INSERT_COLUMNS)
    update_sql = ", ".join(f"{column} = EXCLUDED.{column}" for column in INSERT_COLUMNS if column != "customer_id")
    statement = f"INSERT INTO customers ({columns_sql}) VALUES %s ON CONFLICT (customer_id) DO UPDATE SET {update_sql}"
    count = 0
    with psycopg2.connect(db_url) as conn:
        with conn.cursor() as cur:
            if drop_existing:
                cur.execute("TRUNCATE TABLE customers CASCADE")
                logger.info("customers_truncated")
            for batch in batches(rows, batch_size):
                values = [tuple(row.get(column) for column in INSERT_COLUMNS) for row in batch]
                execute_values(cur, statement, values, page_size=batch_size)
                count += len(batch)
                logger.info(f"batch_loaded rows={len(batch)} total_rows={count}")
    return count


def main() -> None:
    args = parse_args()
    if args.batch_size <= 0:
        raise SystemExit("ERROR: --batch-size must be greater than zero.")
    input_path = Path(args.input_path)
    if not input_path.exists():
        raise SystemExit(f"ERROR: input file not found: {input_path}")
    input_format = args.format or input_path.suffix.lstrip(".").lower()
    if input_format not in {"csv", "json"}:
        raise SystemExit("ERROR: input format must be CSV or JSON.")

    logger = get_logger()
    try:
        logger.info(f"load_started path={input_path} format={input_format} batch_size={args.batch_size}")
        count = load_rows(get_database_url(), read_rows(input_path, input_format), batch_size=args.batch_size, drop_existing=args.drop_existing, logger=logger)
        logger.info(f"load_completed rows={count}")
    except Exception as error:
        logger.error(f"load_failed error={error}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
