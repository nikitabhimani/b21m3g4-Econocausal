"""Run repeatable database health and indexed-query checks."""
from __future__ import annotations

import os
import psycopg2


CHECKS = {
    "customer_summary": "SELECT * FROM customer_summary",
    "treatment_summary": "SELECT * FROM treatment_summary",
    "recommendation_lookup": "SELECT customer_id, ite FROM predictions ORDER BY ite DESC LIMIT 25",
}


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required.")
    with psycopg2.connect(database_url) as conn, conn.cursor() as cur:
        for name, query in CHECKS.items():
            cur.execute(f"EXPLAIN (ANALYZE, FORMAT TEXT) {query}")
            plan = "\n".join(row[0] for row in cur.fetchall())
            print(f"[{name}]\n{plan}\n")


if __name__ == "__main__":
    main()
