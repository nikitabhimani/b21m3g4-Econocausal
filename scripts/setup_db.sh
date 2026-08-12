#!/usr/bin/env bash
set -euo pipefail

# Simple DB setup helper. Requires `psql` and `DATABASE_URL` to be set.
# It will apply `backend/schema.sql`, `backend/seed.sql` and then call the loader to bulk-load CSV.

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: Please set DATABASE_URL environment variable, e.g."
  echo "  export DATABASE_URL=postgresql://user:pass@localhost:5432/econocausal"
  exit 2
fi

echo "Applying schema: backend/schema.sql"
psql "$DATABASE_URL" -f backend/schema.sql

echo "Applying seed data: backend/seed.sql"
psql "$DATABASE_URL" -f backend/seed.sql

echo "Running loader to import data/customers.csv"
python3 backend/scripts/load_data.py --csv data/customers.csv

echo "Database setup complete."
